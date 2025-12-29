# app/services/wix_sync.py

import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError, DataError

from app.db.session import engine
from app.models.product import Product

WIX_BASE_URL = "https://www.wixapis.com"
WIX_API_KEY = os.getenv("WIX_API_KEY") or os.getenv("WIX_API_TOKEN")  # tolérant
WIX_SITE_ID = os.getenv("WIX_SITE_ID")


def _wix_headers() -> Dict[str, str]:
    """
    Auth API Key Wix (pas OAuth Bearer).
    """
    if not WIX_API_KEY or not WIX_SITE_ID:
        raise RuntimeError("WIX_API_KEY (ou WIX_API_TOKEN) et WIX_SITE_ID doivent être définis dans Render.")

    return {
        "Authorization": WIX_API_KEY,   # <-- pas "Bearer"
        "Content-Type": "application/json",
        "Accept": "application/json",
        "wix-site-id": WIX_SITE_ID,
    }


def _raise_wix(resp: requests.Response, context: str) -> None:
    if resp.status_code >= 400:
        body = (resp.text or "")[:1500]
        raise RuntimeError(f"Erreur Wix {context}: {resp.status_code} {body}")


# ----------------------------
# Fetch Wix Stores v1 products
# ----------------------------

def _fetch_wix_products_page_v1(cursor: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    url = f"{WIX_BASE_URL}/stores/v1/products/query"
    body: Dict[str, Any] = {"query": {}}
    if cursor:
        body["cursorPaging"] = {"cursor": cursor}

    resp = requests.post(url, headers=_wix_headers(), json=body, timeout=30)
    _raise_wix(resp, "stores/v1/products/query")
    data = resp.json() or {}

    items = data.get("products") or data.get("items") or []
    next_cursor = data.get("nextCursor") or data.get("cursorPaging", {}).get("nextCursor") or None
    return items, next_cursor


def _fetch_all_wix_products_v1() -> List[Dict[str, Any]]:
    all_items: List[Dict[str, Any]] = []
    cursor: Optional[str] = None

    while True:
        items, cursor = _fetch_wix_products_page_v1(cursor)
        all_items.extend(items)
        if not cursor:
            break

    print(f"[WIX SYNC] Wix v1 produits reçus: {len(all_items)}")
    return all_items


# ----------------------------
# Normalizers (fit Product)
# ----------------------------

def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


def _extract_price(p: Dict[str, Any]) -> float:
    # Wix Stores: souvent p["priceData"]["price"]
    price_data = p.get("priceData") or {}
    return _to_float(price_data.get("price", 0.0), 0.0)


def _extract_handle(p: Dict[str, Any]) -> Optional[str]:
    # Selon payload Wix: "slug", "handle", etc.
    for k in ("handle", "slug", "urlPart"):
        v = p.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _extract_sku(p: Dict[str, Any]) -> Optional[str]:
    sku = p.get("sku")
    if isinstance(sku, str) and sku.strip():
        return sku.strip()
    return None


def _extract_variants(p: Dict[str, Any]) -> List[Dict[str, Any]]:
    # plusieurs formats possibles
    return (
        p.get("variants")
        or p.get("productVariants")
        or p.get("managedVariants")
        or []
    ) or []


def _build_options_payload(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    On stocke tout ce qu'on peut dans Product.options (JSONB):
    - options/choices du produit
    - variantes normalisées
    - images (si présentes)
    - raw minimal utile
    """
    variants = _extract_variants(p)

    norm_variants: List[Dict[str, Any]] = []
    base_price = _extract_price(p)

    for idx, v in enumerate(variants):
        v_sku = (v.get("sku") or "").strip() or None
        v_price = _to_float((v.get("priceData") or {}).get("price", base_price), base_price)

        choices = v.get("choices") or v.get("options") or {}
        # Exemple: {"Longueur":"18\"","Couleur":"#60A"} etc.
        norm_variants.append({
            "index": idx + 1,
            "id": v.get("id") or v.get("_id") or v.get("variantId"),
            "sku": v_sku,
            "price": v_price,
            "choices": choices,
        })

    images = p.get("media") or p.get("images") or None

    return {
        "wix_raw_id": p.get("id") or p.get("_id"),
        "visible": not bool(p.get("hidden", False)),
        "base": {
            "sku": _extract_sku(p),
            "price": base_price,
            "handle": _extract_handle(p),
        },
        "variants": norm_variants,
        "images": images,
    }


def _compute_stock(p: Dict[str, Any]) -> Tuple[bool, int]:
    """
    Best effort: Wix peut avoir stock dans 'stock', 'inventory', etc.
    Si introuvable, on laisse in_stock True et quantity 0 (ton modèle default).
    """
    # tentatives
    stock = p.get("stock") or p.get("inventory") or {}
    qty = (
        stock.get("quantity")
        or stock.get("inStockQuantity")
        or stock.get("availableQuantity")
        or 0
    )
    quantity = 0
    try:
        quantity = int(qty)
    except Exception:
        quantity = 0

    # in_stock peut être un bool direct, ou calculé
    in_stock = stock.get("inStock")
    if isinstance(in_stock, bool):
        return in_stock, quantity

    # fallback: si qty > 0, en stock
    return (quantity > 0), quantity


def _normalize_product(p: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    wix_id = p.get("id") or p.get("_id")
    if not wix_id:
        return None

    name = p.get("name") or "Sans nom"
    description = p.get("description") or None

    price = _extract_price(p)
    sku = _extract_sku(p)
    handle = _extract_handle(p)

    is_in_stock, quantity = _compute_stock(p)
    options = _build_options_payload(p)

    return {
        "wix_id": str(wix_id),
        "sku": sku,
        "name": str(name),
        "price": price,
        "description": description,
        "handle": handle,
        "is_in_stock": is_in_stock,
        "quantity": quantity,
        "options": options,
    }


# ----------------------------
# Upsert DB (wix_id unique)
# ----------------------------

def _upsert_by_wix_id(session: Session, data: Dict[str, Any]) -> bool:
    """
    Upsert par wix_id (unique).
    Retourne True si updated, False si created.
    """
    wix_id = data["wix_id"]
    existing = session.exec(select(Product).where(Product.wix_id == wix_id)).first()

    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        return True

    session.add(Product(**data))
    return False


def sync_wix_to_luxura(limit: int = 500) -> Dict[str, Any]:
    """
    Sync complète Wix (Stores v1) → Luxura Product.
    1 produit Wix = 1 ligne Product (wix_id unique).
    Variantes stockées dans Product.options JSONB.
    """
    print("[WIX SYNC] Début synchro Wix → Luxura (stores v1)")

    wix_products = _fetch_all_wix_products_v1()
    # limite de sécurité si tu veux
    wix_products = wix_products[:limit] if limit else wix_products

    created = 0
    updated = 0
    skipped = 0

    with Session(engine) as session:
        for p in wix_products:
            data = _normalize_product(p)
            if not data:
                skipped += 1
                continue

            was_updated = _upsert_by_wix_id(session, data)
            if was_updated:
                updated += 1
            else:
                created += 1

        session.commit()

    summary = {
        "ok": True,
        "source": "wix_stores_v1",
        "created_products": created,
        "updated_products": updated,
        "skipped": skipped,
        "limit": limit,
    }

    print(f"[WIX SYNC] Terminé: {summary}")
    return summary
