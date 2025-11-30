# app/services/wix_sync.py

"""
Synchro Wix → Luxura (produits + variantes).

✅ Ce que fait ce module :
- Appelle l’API Wix Stores pour récupérer tous les produits.
- Pour chaque produit, parcourt les VARIANTES.
- Crée / met à jour un Product par variante dans la DB Luxura.
- Utilise le SKU de la variante comme clé d’upsert.
- Si une variante n’a PAS de SKU -> on la LOG et on l’ignore (tu pourras
  lui mettre un SKU dans Wix plus tard, puis relancer la synchro).

⚠️ Hypothèses :
- Tu as les variables d’environnement suivantes sur Render :
    WIX_API_KEY  (token Wix Backend/API)
    WIX_SITE_ID  (ID du site Wix Luxura)
- L’API Wix utilisée est Stores v2 : /stores/v2/products/query

Si jamais Wix change un champ (ex: "products" vs "items"), tu auras
juste 1–2 noms de clés à ajuster, mais la structure globale restera bonne.
"""

import os
import json
from typing import Any, Dict, List, Tuple

import requests
from sqlmodel import Session, select

from app.db import engine
from app.models import Product


WIX_BASE_URL = "https://www.wixapis.com"


# ------------------------------------------------------------
#  Helpers Wix
# ------------------------------------------------------------
def _wix_headers() -> Dict[str, str]:
    api_key = os.getenv("WIX_API_KEY")
    site_id = os.getenv("WIX_SITE_ID")

    if not api_key or not site_id:
        raise RuntimeError(
            "WIX_API_KEY ou WIX_SITE_ID manquant dans les variables d'environnement."
        )

    return {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "wix-site-id": site_id,
    }


def _fetch_all_wix_products() -> List[Dict[str, Any]]:
    """
    Récupère tous les produits Wix (avec variantes) via /stores/v2/products/query
    en paginant si nécessaire.
    """
    url = f"{WIX_BASE_URL}/stores/v2/products/query"
    headers = _wix_headers()

    products: List[Dict[str, Any]] = []

    payload: Dict[str, Any] = {
        "query": {},  # pas de filtre : on veut tout
    }

    cursor: str | None = None

    while True:
        body = dict(payload)
        if cursor:
            body["cursorPaging"] = {"cursor": cursor}

        resp = requests.post(url, headers=headers, json=body, timeout=30)
        try:
            resp.raise_for_status()
        except Exception as e:
            print("[WIX SYNC] ERREUR HTTP sur /stores/v2/products/query :", e)
            print("[WIX SYNC] Réponse brute (début) :")
            print(resp.text[:500])
            raise

        data = resp.json()

        # Selon la version de l’API, ça peut être "products" ou "items"
        batch = data.get("products") or data.get("items") or []
        products.extend(batch)

        # Pagination : on essaie plusieurs conventions
        cursor = (
            data.get("nextCursor")
            or data.get("paging", {}).get("nextPageToken")
            or None
        )
        if not cursor:
            break

    print(f"[WIX SYNC] Produits reçus depuis Wix : {len(products)}")
    return products


# ------------------------------------------------------------
#  Mapping produit / variante -> Product DB
# ------------------------------------------------------------
def _extract_variant_length_color(choices: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """
    Essaie de deviner longueur et couleur à partir des choix de variante.

    Exemples de noms d’options qu’on peut rencontrer :
    - "Longueur", "Longueur & poids", "Taille"
    - "Couleur", "Color", "Teinte"
    """
    length: str | None = None
    color: str | None = None

    for opt_name, value in (choices or {}).items():
        if value is None:
            continue
        v = str(value).strip()
        name_l = (opt_name or "").lower()

        # Longueur / taille / poids
        if any(k in name_l for k in ("longueur", "length", "taille", "poids")):
            if not length:
                length = v
            continue

        # Couleur
        if any(k in name_l for k in ("couleur", "color", "shade", "ton")):
            if not color:
                color = v
            continue

    return length, color


def _build_product_from_variant(
    wix_product: Dict[str, Any],
    wix_variant: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Construit le dict de données pour notre modèle Product à partir :
    - du produit Wix (wix_product)
    - de la variante Wix (wix_variant)
    """

    # Nom : on garde le nom du produit parent
    name = (wix_product.get("name") or "").strip()

    # SKU : c'est TA vérité pour la variante (option A)
    # Si vide → on renverra un SKU vide et on filtrera plus haut.
    sku = (wix_variant.get("sku") or "").strip()

    # Prix : on préfère le prix de la variante, sinon celui du produit.
    price = None
    if isinstance(wix_variant.get("priceData"), dict):
        price = wix_variant["priceData"].get("price")
    if price is None and isinstance(wix_product.get("priceData"), dict):
        price = wix_product["priceData"].get("price")
    if price is None:
        price = 0.0

    # Actif : basé sur la visibilité du produit
    active = bool(wix_product.get("visible", True))

    # Description HTML brute
    description = wix_product.get("description") or ""

    # Catégorie : pour l’instant on ne fait pas de magie,
    # on marque simplement "Wix" si le produit fait partie d’au moins 1 collection.
    category: str | None = None
    collections = wix_product.get("collectionIds") or []
    if collections:
        category = "Wix"

    # Longueur / couleur depuis les choix de la variante
    choices = wix_variant.get("choices") or {}
    length, color = _extract_variant_length_color(choices)

    return {
        "sku": sku,
        "name": name,
        "length": length,
        "color": color,
        "category": category,
        "description": description,
        "price": float(price),
        "active": active,
    }


def _upsert_product_by_sku(session: Session, data: Dict[str, Any]) -> Tuple[int, int]:
    """
    Upsert d’un Product basé sur le SKU.
    Retourne (created, updated) = (0/1, 0/1).
    """
    sku = data["sku"]
    prod = session.exec(select(Product).where(Product.sku == sku)).first()

    if prod:
        # UPDATE
        prod.name = data["name"]
        prod.length = data["length"]
        prod.color = data["color"]
        prod.category = data["category"]
        prod.description = data["description"]
        prod.price = data["price"]
        prod.active = data["active"]
        return 0, 1
    else:
        # INSERT
        prod = Product(**data)
        session.add(prod)
        return 1, 0


# ------------------------------------------------------------
#  Synchro principale
# ------------------------------------------------------------
def sync_wix_to_luxura(source: str = "startup") -> Dict[str, Any]:
    """
    Synchro complète Wix → Luxura.

    - Récupère les produits via l’API Wix.
    - Pour chaque produit, parcourt les variantes.
    - Crée / met à jour un Product par variante (clé = SKU).
    - Ignore les variantes SANS SKU (pour éviter les doublons non gérables).

    `source` est juste un tag pour savoir si c’est :
      - "startup" (appel au démarrage de l’API)
      - "manual"  (appel depuis l’endpoint /wix/sync)
    """

    print("[WIX SYNC] Début synchro Wix → Luxura")

    created_products = 0
    updated_products = 0
    created_salons = 0  # pas encore géré ici
    updated_salons = 0  # pas encore géré ici

    products: List[Dict[str, Any]] = _fetch_all_wix_products()

    with Session(engine) as session:
        for wp in products:
            variants = wp.get("variants") or []

            # Si aucun variants → on traite le produit comme une "pseudo-variantes"
            if not variants:
                pseudo_variant = {}
                data = _build_product_from_variant(wp, pseudo_variant)
                sku = data["sku"]
                if not sku:
                    print(
                        f"[WIX SYNC] Produit sans SKU et sans variantes : "
                        f"{wp.get('name')!r} → ignoré."
                    )
                    continue
                c, u = _upsert_product_by_sku(session, data)
                created_products += c
                updated_products += u
                continue

            # Produit avec vraies variantes
            for wv in variants:
                data = _build_product_from_variant(wp, wv)
                sku = data["sku"]

                if not sku:
                    # Tu pourras revenir dans Wix, mettre un SKU propre,
                    # puis relancer /wix/sync : à partir de là, ce sera upserté.
                    print(
                        "[WIX SYNC] Variante ignorée (SKU vide) pour produit "
                        f"{wp.get('name')!r}, variant_id={wv.get('id')!r}"
                    )
                    continue

                c, u = _upsert_product_by_sku(session, data)
                created_products += c
                updated_products += u

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
