# app/services/wix_sync.py

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlmodel import Session, select

from app.db import engine
from app.models import Product


# ------------------------------------------------
#  Config Wix
# ------------------------------------------------

WIX_BASE_URL = "https://www.wixapis.com"
WIX_API_KEY = os.getenv("WIX_API_KEY")  # doit être défini dans Render


def _wix_headers() -> Dict[str, str]:
    if not WIX_API_KEY:
        raise RuntimeError("WIX_API_KEY manquant dans les variables d'environnement.")
    return {
        "Authorization": WIX_API_KEY,
        "Content-Type": "application/json",
    }


# ------------------------------------------------
#  Fetch produits depuis Wix Stores v1
# ------------------------------------------------

def _fetch_all_wix_products_v1() -> List[Dict[str, Any]]:
    """
    Récupère tous les produits depuis Wix Stores v1 :
      POST https://www.wixapis.com/stores/v1/products/query

    On pagine tant qu'il y a des résultats.
    """
    url = f"{WIX_BASE_URL}/stores/v1/products/query"
    headers = _wix_headers()

    products: List[Dict[str, Any]] = []

    payload: Dict[str, Any] = {
        "query": {},  # pas de filtre : tout
        "paging": {
            "limit": 100
        },
    }

    cursor: Optional[str] = None

    while True:
        body = dict(payload)
        if cursor:
            body["paging"]["cursor"] = cursor

        resp = requests.post(url, headers=headers, json=body, timeout=30)

        try:
            resp.raise_for_status()
        except Exception as e:
            print("[WIX SYNC] ERREUR HTTP sur /stores/v1/products/query :", e)
            print("[WIX SYNC] Réponse brute (début) :")
            print(resp.text[:500])
            raise

        data = resp.json()

        items = data.get("products") or data.get("items") or []
        products.extend(items)

        cursor = data.get("paging", {}).get("nextCursor")
        if not cursor:
            break

    print(f"[WIX SYNC] Produits reçus depuis Wix (v1) : {len(products)}")
    return products


# ------------------------------------------------
#  Normalisation produit / variante
# ------------------------------------------------

def _extract_variants_from_product(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    On essaie d'extraire les variantes d'un produit Stores v1.
    Suivant la structure, elles peuvent se trouver sous différentes clés.
    """

    # Candidats possibles (Wix peut changer les noms, on est défensif)
    candidates = [
        "productVariants",
        "variants",
        "choices",
    ]

    for key in candidates:
        if key in item and isinstance(item[key], list):
            return item[key]

    # Certains schémas plus récents utilisent "managedVariants"
    if "managedVariants" in item and isinstance(item["managedVariants"], list):
        return item["managedVariants"]

    return []


def _normalize_product_and_variants(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    À partir d'un produit Wix, retourne une liste de "lignes produit"
    prêtes à être upsert dans notre table Product.

    - Si le produit a un SKU (item["sku"]) → on crée une ligne.
    - Si le produit a des variantes avec des SKU → une ligne par variante.
    - Si aucun SKU nulle part → on ignore ce produit.
    """

    result: List[Dict[str, Any]] = []

    name = item.get("name") or item.get("productName") or "Produit sans nom"
    description = item.get("description", None)
    active = not bool(item.get("archived", False))

    # 1) Variantes d'abord (ce que tu utilises pour extensions)
    variants = _extract_variants_from_product(item)

    for v in variants:
        sku = v.get("sku") or v.get("variantSku") or ""
        if not sku:
            # Variante sans SKU → on la saute
            continue

        # Longueur, couleur, etc. peuvent être stockés dans diverses structures.
        # On va essayer de récupérer quelque chose de lisible.
        length: Optional[str] = None
        color: Optional[str] = None

        # Exemple : options de type "Length", "Color"
        option_data = v.get("choices") or v.get("options") or {}
        if isinstance(option_data, dict):
            # ex: {"Length": "18\"", "Weight": "60g"}
            for opt_name, opt_value in option_data.items():
                label = (opt_name or "").lower()
                if "longueur" in label or "length" in label:
                    length = str(opt_value)
                if "couleur" in label or "color" in label:
                    color = str(opt_value)

        # Prix de la variante
        price = None

        # vieux schémas : "priceData": {"price": 123.45}
        price_data = v.get("priceData") or {}
        if isinstance(price_data, dict) and price_data.get("price") is not None:
            price = float(price_data["price"])

        # fallback : peut être au niveau du produit
        if price is None:
            prod_price_data = item.get("priceData") or {}
            if isinstance(prod_price_data, dict) and prod_price_data.get("price") is not None:
                price = float(prod_price_data["price"])

        if price is None:
            # dernière chance : 0.0
            price = 0.0

        result.append(
            {
                "sku": sku,
                "name": name,
                "length": length,
                "color": color,
                "category": "Wix",
                "description": description,
                "price": price,
                "active": active,
            }
        )

    # 2) Si aucune variante n’avait de SKU, on regarde le produit lui-même
    if not result:
        sku = item.get("sku") or ""
        if sku:
            price = 0.0
            price_data = item.get("priceData") or {}
            if isinstance(price_data, dict) and price_data.get("price") is not None:
                price = float(price_data["price"])

            result.append(
                {
                    "sku": sku,
                    "name": name,
                    "length": None,
                    "color": None,
                    "category": "Wix",
                    "description": description,
                    "price": price,
                    "active": active,
                }
            )
        else:
            # On log seulement pour debug
            print(
                f"[WIX SYNC] Produit sans SKU et sans variantes : '{name}' → ignoré."
            )

    return result


# ------------------------------------------------
#  Sync principale
# ------------------------------------------------

def sync_wix_to_luxura(source: str = "manual") -> Dict[str, Any]:
    """
    Synchro complète Wix → Luxura (produits uniquement pour l'instant).

    - Récupère tous les produits via Stores v1
    - Normalise produits + variantes
    - Upsert dans la table Product (clé = SKU)
    """

    print("[WIX SYNC] Début synchro Wix → Luxura")

    created_products = 0
    updated_products = 0
    created_salons = 0  # pas encore géré dans cette version
    updated_salons = 0

    try:
        wix_items = _fetch_all_wix_products_v1()
    except Exception as e:
        print("[WIX SYNC] ERREUR pendant la récupération des produits Wix :", e)
        summary_err = {
            "ok": False,
            "source": source,
            "created_products": 0,
            "updated_products": 0,
            "created_salons": 0,
            "updated_salons": 0,
        }
        print(f"[WIX SYNC] Terminé (erreur) : {summary_err}")
        return summary_err

    normalized_rows: List[Dict[str, Any]] = []
    for item in wix_items:
        normalized_rows.extend(_normalize_product_and_variants(item))

    with Session(engine) as session:
        for row in normalized_rows:
            sku = row["sku"]

            # On cherche un produit existant avec ce SKU
            existing = session.exec(
                select(Product).where(Product.sku == sku)
            ).first()

            if existing:
                # Mise à jour
                existing.name = row["name"]
                existing.length = row["length"]
                existing.color = row["color"]
                existing.category = row["category"]
                existing.description = row["description"]
                existing.price = row["price"]
                existing.active = row["active"]
                updated_products += 1
            else:
                # Création
                prod = Product(**row)
                session.add(prod)
                created_products += 1

        session.commit()

    summary: Dict[str, Any] = {
        "ok": True,
        "source": source,
        "created_products": created_products,
        "updated_products": updated_products,
        "created_salons": created_salons,
        "updated_salons": updated_salons,
    }

    print(f"[WIX SYNC] Terminé : {summary}")
    return summary
