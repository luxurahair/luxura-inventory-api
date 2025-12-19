# app/services/wix_sync.py

import os
from typing import Any, Dict, List, Optional

import requests
from sqlmodel import Session, select

from app.db import engine
from app.models import Product

# ---------------------------------------------------------
#  Config Wix
# ---------------------------------------------------------

WIX_BASE_URL = "https://www.wixapis.com"
WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")


def _wix_headers() -> Dict[str, str]:
    """
    Headers standard pour appeler l’API Wix.
    """
    if not WIX_API_KEY or not WIX_SITE_ID:
        raise RuntimeError(
            "WIX_API_KEY et WIX_SITE_ID doivent être définis dans Render."
        )

    return {
        "Authorization": WIX_API_KEY,
        "Content-Type": "application/json",
        "wix-site-id": WIX_SITE_ID,
    }


# ---------------------------------------------------------
#  Fetch produits Wix (v1) + variantes
# ---------------------------------------------------------

def _fetch_all_wix_products_v1() -> List[Dict[str, Any]]:
    """
    Récupère tous les produits Wix via /stores/v1/products/query
    (API Stores v1) en paginant si besoin.
    On récupère les produits *et* leurs variantes.
    """
    url = f"{WIX_BASE_URL}/stores/v1/products/query"
    headers = _wix_headers()

    products: List[Dict[str, Any]] = []
    payload: Dict[str, Any] = {"query": {}}
    cursor: Optional[str] = None

    while True:
        body = dict(payload)
        if cursor:
            body["cursorPaging"] = {"cursor": cursor}

        resp = requests.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("products") or data.get("items") or []
        products.extend(batch)

        cursor = (
            data.get("nextCursor")
            or data.get("paging", {}).get("nextPageToken")
            or None
        )
        if not cursor:
            break

    print(f"[WIX SYNC] Produits reçus depuis Wix (v1) : {len(products)}")
    return products


# ---------------------------------------------------------
#  Helpers DB
# ---------------------------------------------------------

def _upsert_product(
    session: Session,
    wix_id: str,
    sku: str,
    name: str,
    length: Optional[str],
    color: Optional[str],
    category: Optional[str],
    description: Optional[str],
    price: float,
    active: bool,
) -> None:
    """
    Crée ou met à jour un produit Luxura à partir d’un SKU.
    Le SKU est notre clé unique.
    """
    
stmt = select(Product).where(Product.wix_id == wix_id)
existing = session.exec(stmt).first()

if existing:
    existing.sku = sku
    existing.name = name
    existing.length = length
    existing.color = color
    existing.category = category
    existing.description = description
    existing.price = price
    existing.active = active
else:
    obj = Product(
        wix_id=wix_id,
        sku=sku,
        name=name,
        length=length,
        color=color,
        category=category,
        description=description,
        price=price,
        active=active,
    )
    session.add(obj)


def _extract_price_from_product(p: Dict[str, Any]) -> float:
    """
    Essaie de sortir un prix du produit Wix.
    """
    price_data = p.get("priceData") or {}
    price = price_data.get("price") or 0.0
    try:
        return float(price)
    except Exception:
        return 0.0


def _extract_price_from_variant(v: Dict[str, Any], fallback: float) -> float:
    """
    Prix pour une variante : si non présent, on prend le prix du produit.
    """
    price_data = v.get("priceData") or {}
    price = price_data.get("price") or fallback
    try:
        return float(price)
    except Exception:
        return fallback


# ---------------------------------------------------------
#  Import produits (produits simples + variantes)
# ---------------------------------------------------------

def _import_wix_products(session: Session) -> Dict[str, int]:
    """
    Importe / met à jour les produits Luxura à partir des produits Wix.
    - 1 produit simple → 1 ligne Product
    - 1 produit avec variantes → 1 ligne Product par variante (SKU variante)
    - Si aucune SKU n’est fournie → SKU auto "AUTO-<wixId>-<index>"
    """
    wix_products = _fetch_all_wix_products_v1()

    created_products = 0
    updated_products = 0

    for p in wix_products:
        wix_id = p.get("id") or p.get("_id") or "no-id"
        base_name = p.get("name") or "Sans nom"
        base_desc = p.get("description") or None
        category = "Wix"
        active = not p.get("hidden", False)

        base_price = _extract_price_from_product(p)

        # Variantes possibles selon la structure de Wix
        variants = (
            p.get("variants")
            or p.get("productVariants")
            or p.get("managedVariants")
            or []
        )

        # Cas 1 : PRODUIT AVEC VARIANTES
        if variants:
            for idx, v in enumerate(variants):
                raw_sku = (v.get("sku") or "").strip()

                # 👉 Nouvelle logique : si pas de SKU → on en fabrique une
                if not raw_sku:
                    raw_sku = f"AUTO-{wix_id}-{idx+1}"

                length: Optional[str] = None
                color: Optional[str] = None

                # Si l’API nous donne des "choices" ou "options", on tente
                # de remplir length / color à partir de là (best effort).
                choices = v.get("choices") or v.get("options") or {}
                # Ex : {"Longueur": "18\" 60 grammes", "Couleur": "#60A"}
                for key, value in choices.items():
                    key_lower = str(key).lower()
                    if "longueur" in key_lower or "length" in key_lower:
                        length = str(value)
                    if "couleur" in key_lower or "color" in key_lower:
                        color = str(value)

                price = _extract_price_from_variant(v, base_price)

                # Nom final : on garde le nom produit + éventuellement la longueur
                variant_name = base_name
                if length:
                    variant_name = f"{base_name} — {length}"

                # Upsert
                before = session.exec(
                    select(Product).where(Product.sku == raw_sku)
                ).first()

               _upsert_product(
                   session=session,
                   wix_id=wix_id,
                   sku=raw_sku,
                   name=variant_name,
                   length=length,
                   color=color,
                   category=category,
                   description=base_desc,
                   price=price,
                   active=active,
               )


                if before:
                    updated_products += 1
                else:
                    created_products += 1

        # Cas 2 : PRODUIT SANS VARIANTES → une seule ligne
        else:
            raw_sku = (p.get("sku") or "").strip()
            if not raw_sku:
                # 👉 Là aussi, on ne l’ignore plus : SKU auto
                raw_sku = f"AUTO-{wix_id}"

            before = session.exec(
                select(Product).where(Product.sku == raw_sku)
            ).first()

            _upsert_product(
                session=session,
                sku=raw_sku,
                name=base_name,
                length=None,
                color=None,
                category=category,
                description=base_desc,
                price=base_price,
                active=active,
            )

            if before:
                updated_products += 1
            else:
                created_products += 1

    return {
        "created_products": created_products,
        "updated_products": updated_products,
    }


# ---------------------------------------------------------
#  Entrée principale : sync_wix_to_luxura()
# ---------------------------------------------------------

def sync_wix_to_luxura() -> Dict[str, Any]:
    """
    Synchro complète Wix → Luxura.
    Pour l’instant : PRODUITS seulement (pas salons, pas inventaire détaillé).
    """
    print("[WIX SYNC] Début synchro Wix → Luxura")

    with Session(engine) as session:
        stats_prod = _import_wix_products(session)
        session.commit()

    summary: Dict[str, Any] = {
        "ok": True,
        "source": "manual",
        "created_products": stats_prod["created_products"],
        "updated_products": stats_prod["updated_products"],
        "created_salons": 0,
        "updated_salons": 0,
    }

    print(f"[WIX SYNC] Terminé : {summary}")
    return summary

