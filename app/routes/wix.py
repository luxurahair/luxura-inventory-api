# app/routes/wix.py

print("### LOADED app/routes/wix.py (v2 variants + entrepot inventory, CATALOG_V1) ###")

import logging
import os
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import DataError, IntegrityError
from sqlmodel import Session, select

from app.db import get_session
from app.models.inventory import InventoryItem
from app.models.product import Product
from app.models.salon import Salon
from app.services.catalog_normalizer import normalize_product, normalize_variant
from app.services.wix_client import WixClient

router = APIRouter(prefix="/wix", tags=["wix"])
log = logging.getLogger("uvicorn.error")

WIX_BASE_URL = "https://www.wixapis.com"

ENTREPOT_CODE = "ENTREPOT"
ENTREPOT_NAME = "Luxura Entrepôt"


# ---------------------------------------------------------
# CSV CATEGORIES (SOURCE DE VÉRITÉ)
# ---------------------------------------------------------
def load_categories_from_csv() -> Dict[str, List[str]]:
    """
    data/catalog_products.csv
    Colonnes attendues:
      - product_id
      - collection (séparée par ;)
    Retour:
      { wix_product_id: [cat1, cat2, ...] }
    """
    path = Path("data/catalog_products.csv")
    if not path.exists():
        print("[CSV] catalog_products.csv introuvable")
        return {}

    out: Dict[str, List[str]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("product_id") or "").strip()
            raw = (row.get("collection") or "").strip()
            if not pid or not raw:
                continue

            cats = [c.strip() for c in raw.split(";") if c.strip()]
            if cats:
                out[pid] = sorted(set(cats))

    print(f"[CSV] catégories chargées: {len(out)} produits")
    return out


# ---------------------------------------------------------
# Wix helpers (fallback requests)
# ---------------------------------------------------------
def _wix_headers() -> Dict[str, str]:
    api_key = os.getenv("WIX_API_KEY") or os.getenv("WIX_API_TOKEN")
    site_id = os.getenv("WIX_SITE_ID")
    if not api_key or not site_id:
        raise RuntimeError("WIX_API_KEY / WIX_SITE_ID manquants")
    return {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "wix-site-id": site_id,
    }


def _fetch_products_v1(limit: int) -> List[Dict[str, Any]]:
    url = f"{WIX_BASE_URL}/stores/v1/products/query"
    payload = {"query": {"paging": {"limit": limit}}}

    resp = requests.post(url, headers=_wix_headers(), json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(resp.text)

    data = resp.json() or {}
    return data.get("products") or data.get("items") or []


# ---------------------------------------------------------
# ENTREPOT helpers
# ---------------------------------------------------------
def get_or_create_entrepot(db: Session) -> Salon:
    salon = db.exec(select(Salon).where(Salon.code == ENTREPOT_CODE)).first()
    if not salon:
        salon = Salon(name=ENTREPOT_NAME, code=ENTREPOT_CODE, is_active=True)
        db.add(salon)
        db.commit()
        db.refresh(salon)
    return salon


def upsert_inventory_entrepot(db: Session, salon_id: int, product_id: int, qty: int) -> None:
    inv = db.exec(
        select(InventoryItem).where(
            InventoryItem.salon_id == salon_id,
            InventoryItem.product_id == product_id,
        )
    ).first()

    if not inv:
        db.add(InventoryItem(salon_id=salon_id, product_id=product_id, quantity=max(int(qty), 0)))
    else:
        inv.quantity = max(int(qty), 0)


# ---------------------------------------------------------
# Inventory mapping (CATALOG_V1)
# ---------------------------------------------------------
def _clean_str(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _build_inventory_map_v1(
    client: WixClient,
    page_limit: int = 100,
    max_pages: int = 50,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    inv_map: Dict[str, Dict[str, Any]] = {}
    pages = 0
    total_items = 0
    offset = 0

    while pages < max_pages:
        resp = client.query_inventory_items_v1(limit=page_limit, offset=offset)
        items = resp.get("inventoryItems") or resp.get("items") or []

        pages += 1
        total_items += len(items)

        for inv in items:
            pid = _clean_str(inv.get("productId"))
            if not pid:
                continue

            track = bool(inv.get("trackQuantity", False))
            variants = inv.get("variants") or []

            for v in variants:
                vid = _clean_str(v.get("variantId") or v.get("id"))
                if not vid:
                    continue

                qty = int(v.get("quantity") or 0)
                vendor_sku = (
                    _clean_str(v.get("sku"))
                    or _clean_str(v.get("stockKeepingUnit"))
                    or _clean_str(v.get("vendorSku"))
                    or _clean_str((v.get("skuData") or {}).get("sku"))
                    or None
                )

                inv_map[f"{pid}:{vid}"] = {
                    "track": track,
                    "qty": qty,
                    "vendor_sku": vendor_sku,
                }

        if len(items) < page_limit:
            break
        offset += page_limit

    meta = {"pages": pages, "total_inventory_items": total_items, "mapped_variants": len(inv_map)}
    return inv_map, meta


# ---------------------------------------------------------
# Sync Wix → Luxura (V2)
# ---------------------------------------------------------
@router.post("/sync")
def sync_wix_to_luxura(db: Session = Depends(get_session), limit: int = 200) -> Dict[str, Any]:
    client = WixClient()
    entrepot = get_or_create_entrepot(db)

    inv_map, inv_meta = _build_inventory_map_v1(client)
    csv_categories = load_categories_from_csv()

    parents = client.query_products_v1(limit=min(limit, 100))

    created = updated = skipped_no_sku = inv_written = 0

    try:
        for p in parents:
            wix_product_id = _clean_str(p.get("id"))
            if not wix_product_id:
                continue

            variants = client.query_variants_v1(wix_product_id)

            for v in variants:
                data = normalize_variant(p, v)
                if not data or not data.get("sku"):
                    skipped_no_sku += 1
                    continue

                # Injecter catégories CSV
                cats = csv_categories.get(wix_product_id)
                if cats:
                    opts = data.get("options") or {}
                    opts["categories"] = cats
                    data["options"] = opts

                sku = data["sku"]
                existing = db.exec(select(Product).where(Product.sku == sku)).first()

                if existing:
                    for k, val in data.items():
                        setattr(existing, k, val)
                    prod = existing
                    updated += 1
                else:
                    prod = Product(**data)
                    db.add(prod)
                    db.flush()
                    db.refresh(prod)
                    created += 1

                # Inventory ENTREPOT
                vid = data["options"].get("wix_variant_id")
                it = inv_map.get(f"{wix_product_id}:{vid}")
                if it and it["track"]:
                    upsert_inventory_entrepot(db, entrepot.id, prod.id, it["qty"])
                    inv_written += 1

        db.commit()

        return {
            "ok": True,
            "created": created,
            "updated": updated,
            "skipped_no_sku": skipped_no_sku,
            "inventory_written_entrepot": inv_written,
            "inventory_meta": inv_meta,
            "categories_from_csv": len(csv_categories),
        }

    except (IntegrityError, DataError) as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
