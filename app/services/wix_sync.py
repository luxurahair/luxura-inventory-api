# app/services/wix_sync.py

import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlmodel import Session, select

from app.db.session import engine
from app.models.product import Product

# ---------------------------------------------------------
#  Config Wix
# ---------------------------------------------------------

WIX_BASE_URL = "https://www.wixapis.com"
WIX_API_KEY = os.getenv("WIX_API_KEY")  # API key "admin"
WIX_SITE_ID = os.getenv("WIX_SITE_ID")


def _wix_headers() -> Dict[str, str]:
    """
    Headers standard pour appeler l’API Wix avec API KEY (pas OAuth Bearer).
    """
    if not WIX_API_KEY or not WIX_SITE_ID:
        raise RuntimeError("WIX_API_KEY et WIX_SITE_ID doivent être définis dans Render.")

    return {
        "Authorization": WIX_API_KEY,          # <-- PAS "Bearer"
        "Content-Type": "application/json",
        "Accept": "application/json",
        "wix-site-id": WIX_SITE_ID,            # <-- site scope
    }


def _raise_wix(resp: requests.Response, context: str) -> None:
    """
    Remonte une erreur Wix avec détails (utile quand Wix renvoie 403 vide).
    """
    if resp.status_code >= 400:
        # tronque pour éviter d'exploser les logs
        body = (resp.text or "")[:1200]
        raise RuntimeError(f"Erreur Wix {context}: {resp.status_code} {body}")


# ---------------------------------------------------------
#  Fetch produits Wix (Stores v1) + pagination cursor
# ---------------------------------------------------------

def _fetch_wix_products_page_v1(cursor: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Retourne (items, next_cursor) pour /stores/v1/products/query
    """
    url = f"{WIX_BASE_URL}/stores/v1/products/query"
    headers = _wix_headers()

    body: Dict[str, Any] = {"query": {}}
    if cursor:
        body["cursorPaging"] = {"cursor": cursor}

    resp = requests.post(url, headers=headers, json=body, timeout=30)
    _raise_wix(resp, "products/query v1")
    data = resp.json() or {}

    items = data.get("products") or data.get("items") or []

    next_cursor = (
        data.get("nextCursor")
        or data.get("cursorPaging", {}).get("nextCursor")
        or None
    )

    return items, next_cursor


def _fetch_all_wix_products_v1() -> List[Dict[str, Any]]:
    """
    Récupère tous les produits Wix via /stores/v1/products/query en paginant.
    """
    all_items: List[Dict[str, Any]] = []
    cursor: Optional[str] = None

    while True:
        items, cursor = _fetch_wix_products_page_v1(cursor)
        all_items.extend(items)
        if not cursor:
            break

    print(f"[WIX SYNC] Produits reçus depuis Wix (v1): {len(all_items)}")
    return all_items


# ---------------------------------------------------------
#  Extract helpers
# ---------------------------------------------------------

def _extract_price_from_product(p: Dict[str, Any]) -> float:
    price_data = p.get("priceData") or {}
    price = price_data.get("price") or 0.0
    try:
        return float(price)
    except Exception:
        return 0.0


def _extract_price_from_variant(v: Dict[str, Any], fallback: float) -> float:
    price_data = v.get("priceData") or {}
    price = price_data.get("price")
    if price is None or price == "":
        price = fallback
    try:
        return float(price)
    except Exception:
        return fallback


def _extract_variant_identity(v: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Retourne (variant_id, choices/options dict)
    """
    variant_id = v.get("id") or v.get("_id") or v.get("variantId")
    choices = v.get("choices") or v.get("options") or {}
    return variant_id, choices


def _extract_length_color(choices: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    length: Optional[str] = None
    color: Optional[str] = None

    for key, value in (choices or {}).items():
        k = str(key).lower()
        v = str(value)
        if "longueur" in k or "length" in k:
            length = v
        if "couleur" in k or "color" in k:
            color = v

    return length, color


# ---------------------------------------------------------
#  DB upsert
# ---------------------------------------------------------

def _find_existing(session: Session, wix_id: str, wix_variant_id: Optional[str]) -> Optional[Product]:
    """
    Trouve un produit existant de manière stable:
    - si variante: (wix_id + wix_variant_id)
    - sinon: (wix_id + wix_variant_id NULL)
    """
    stmt = select(Product).where(Product.wix_id == wix_id)
    if wix_variant_id:
        stmt = stmt.where(Product.wix_variant_id == wix_variant_id)
    else:
        stmt = stmt.where(Product.wix_variant_id.is_(None))  # type: ignore

    return session.exec(stmt).first()


def _upsert_product(
    session: Session,
    *,
    wix_id: str,
    wix_variant_id: Optional[str],
    sku: str,
    name: str,
    length: Optional[str],
    color: Optional[str],
    category: Optional[str],
    description: Optional[str],
    price: float,
    active: bool,
) -> bool:
    """
    Upsert. Retourne True si UPDATED, False si CREATED.
    """
    existing = _find_existing(session, wix_id, wix_variant_id)

    if existing:
        existing.sku = sku
        existing.name = name
        existing.length = length
        existing.color = color
        existing.category = category
        existing.description = description
        existing.price = price
        existing.active = active
        return True

    obj = Product(
        wix_id=wix_id,
        wix_variant_id=wix_variant_id,
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
    return False


# ---------------------------------------------------------
#  Import Wix → DB (produits + variantes)
# ---------------------------------------------------------

def _import_wix_products(session: Session) -> Dict[str, int]:
    wix_products = _fetch_all_wix_products_v1()

    created = 0
    updated = 0

    for p in wix_products:
        wix_id = p.get("id") or p.get("_id")
        if not wix_id:
            continue

        base_name = p.get("name") or "Sans nom"
        base_desc = p.get("description") or None
        category = "Wix"
        active = not bool(p.get("hidden", False))

        base_price = _extract_price_from_product(p)

        variants = (
            p.get("variants")
            or p.get("productVariants")
            or p.get("managedVariants")
            or []
        )

        # -------------------------
        # Cas 1 : variantes
        # -------------------------
        if variants:
            for idx, v in enumerate(variants):
                variant_id, choices = _extract_variant_identity(v)

                raw_sku = (v.get("sku") or "").strip()
                if not raw_sku:
                    raw_sku = f"AUTO-{wix_id}-{idx+1}"

                length, color = _extract_length_color(choices)
                price = _extract_price_from_variant(v, base_price)

                name = base_name
                if length:
                    name = f"{base_name} — {length}"

                was_updated = _upsert_product(
                    session,
                    wix_id=wix_id,
                    wix_variant_id=variant_id,
                    sku=raw_sku,
                    name=name,
                    length=length,
                    color=color,
                    category=category,
                    description=base_desc,
                    price=price,
                    active=active,
                )

                if was_updated:
                    updated += 1
                else:
                    created += 1

        # -------------------------
        # Cas 2 : produit simple
        # -------------------------
        else:
            raw_sku = (p.get("sku") or "").strip()
            if not raw_sku:
                raw_sku = f"AUTO-{wix_id}"

            was_updated = _upsert_product(
                session,
                wix_id=wix_id,
                wix_variant_id=None,
                sku=raw_sku,
                name=base_name,
                length=None,
                color=None,
                category=category,
                description=base_desc,
                price=base_price,
                active=active,
            )

            if was_updated:
                updated += 1
            else:
                created += 1

    return {"created_products": created, "updated_products": updated}


# ---------------------------------------------------------
#  Entrée principale
# ---------------------------------------------------------

def sync_wix_to_luxura() -> Dict[str, Any]:
    """
    Synchro complète Wix → Luxura (produits seulement).
    """
    print("[WIX SYNC] Début synchro Wix → Luxura (Stores v1)")

    with Session(engine) as session:
        stats = _import_wix_products(session)
        session.commit()

    summary: Dict[str, Any] = {
        "ok": True,
        "source": "wix_stores_v1",
        "created_products": stats["created_products"],
        "updated_products": stats["updated_products"],
        "created_salons": 0,
        "updated_salons": 0,
    }

    print(f"[WIX SYNC] Terminé: {summary}")
    return summary
