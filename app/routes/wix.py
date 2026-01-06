# app/routes/wix.py

print("### LOADED app/routes/wix.py (v2 variants + entrepot inventory) ###")

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, DataError
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.product import Product
from app.models.inventory import InventoryItem
from app.models.salon import Salon
from app.services.wix_client import WixClient
from app.services.catalog_normalizer import normalize_product, normalize_variant


router = APIRouter(prefix="/wix", tags=["wix"])
log = logging.getLogger("uvicorn.error")

WIX_BASE_URL = "https://www.wixapis.com"

ENTREPOT_CODE = "ENTREPOT"
ENTREPOT_NAME = "Luxura Entrepôt"


# ---------------------------------------------------------
# Wix helpers (fallback requests)
# ---------------------------------------------------------
def _wix_headers() -> Dict[str, str]:
    api_key = os.getenv("WIX_API_KEY") or os.getenv("WIX_API_TOKEN")
    site_id = os.getenv("WIX_SITE_ID")
    if not api_key or not site_id:
        raise RuntimeError("WIX_API_KEY (ou WIX_API_TOKEN) et WIX_SITE_ID manquants dans Render.")
    return {
        "Authorization": api_key,  # pas Bearer
        "Content-Type": "application/json",
        "Accept": "application/json",
        "wix-site-id": site_id,
    }


def _fetch_products_v1(limit: int) -> List[Dict[str, Any]]:
    """
    Fetch rapide côté route (debug). Pour la sync V2, on utilise WixClient (même endpoint).
    """
    url = f"{WIX_BASE_URL}/stores/v1/products/query"
    payload: Dict[str, Any] = {"query": {"paging": {"limit": limit}}}

    resp = requests.post(url, headers=_wix_headers(), json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Wix v1 products/query: {resp.status_code} {resp.text}")

    data = resp.json() or {}
    return data.get("products") or data.get("items") or []


# ---------------------------------------------------------
# ENTREPOT helpers (MUST be after _fetch_products_v1)
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
        inv = InventoryItem(salon_id=salon_id, product_id=product_id, quantity=max(int(qty), 0))
        db.add(inv)
    else:
        inv.quantity = max(int(qty), 0)


# ---------------------------------------------------------
# Debug endpoints
# ---------------------------------------------------------
@router.get("/debug-products")
def debug_wix_products() -> Dict[str, Any]:
    """
    Debug: produits parents + options (pas forcément SKU/qty variants).
    """
    try:
        raw_products = _fetch_products_v1(limit=20)
        normalized = [normalize_product(p, "CATALOG_V1") for p in raw_products]
        return {"catalog_version": "CATALOG_V1", "count": len(normalized), "products": normalized}
    except Exception as e:
        log.exception("❌ /wix/debug-products failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-variants/{product_id}")
def debug_wix_variants(product_id: str) -> Dict[str, Any]:
    """
    Debug: variants réels (SKU + choices + inventory si fourni).
    """
    try:
        client = WixClient()
        variants = client.query_variants_v1(product_id, limit=100)
        return {"product_id": product_id, "count": len(variants), "sample": variants[:5]}
    except Exception as e:
        log.exception("❌ /wix/debug-variants failed")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# Sync V2: 1 variant = 1 SKU, stock Wix -> ENTREPOT
# ---------------------------------------------------------
@router.post("/sync")
def sync_wix_to_luxura(db: Session = Depends(get_session), limit: int = 200) -> Dict[str, Any]:
    """
    Sync Wix -> Luxura (V2):
    - Fetch products parents
    - Pour chaque parent: fetch variants
    - 1 variant = 1 Product (clé = SKU)
    - Inventory Wix écrit UNIQUEMENT dans ENTREPOT (InventoryItem)
    """
    try:
        client = WixClient()
        entrepot = get_or_create_entrepot(db)
      
        inv_items = client.query_inventory_items_v3(limit=1000)
        print("[INV SAMPLE]", inv_items[:1])

        # Map: "<productId>:<variantId>" -> inventoryItem
        inv_map: Dict[str, Dict[str, Any]] = {}
        for it in inv_items:
            product_id = str(it.get("productId") or "").strip()
            variant_id = str(it.get("variantId") or "").strip()
            if not product_id or not variant_id:
                continue
            inv_map[f"{product_id}:{variant_id}"] = it

        # Sécurité: Wix limite 100 par page; on coupe ici pour pas DDOS Wix
        limit = int(limit or 200)
        per_page = min(max(limit, 1), 100)
        max_pages: Optional[int] = None
        if limit > 100:
            # on évite de tourner trop longtemps: 10 pages max (1000 produits)
            max_pages = 10

        parents = client.query_products_v1(limit=per_page, max_pages=max_pages)

    except Exception as e:
        log.exception("❌ Wix fetch parents failed")
        raise HTTPException(status_code=500, detail=str(e))

    created = 0
    updated = 0
    skipped_no_sku = 0
    inv_written = 0
    parents_processed = 0
    variants_seen = 0

    try:
        for p in parents:
            pid = p.get("id") or p.get("_id")
            if not pid:
                continue

            parents_processed += 1

            variants = client.query_variants_v1(str(pid), limit=100)  # variants d’un produit
            for v in variants:
                variants_seen += 1

                data = normalize_variant(p, v)
                if not data:
                    skipped_no_sku += 1
                    continue


                sku = (data.get("sku") or "").strip()
                if not sku:
                    skipped_no_sku += 1
                    continue

                existing = db.exec(select(Product).where(Product.sku == sku)).first()

                if existing:
                    for field, value in data.items():
                        setattr(existing, field, value)
                    prod = existing
                    updated += 1
                else:
                    prod = Product(**data)
                    db.add(prod)
                    db.commit()
                    db.refresh(prod)
                    created += 1

                # Stock Wix -> ENTREPOT via Inventory Items (v3)
                wix_product_id = str(pid).strip()
                wix_variant_id = (data.get("options") or {}).get("wix_variant_id")

                if wix_variant_id:
                    key = f"{wix_product_id}:{str(wix_variant_id).strip()}"
                    it = inv_map.get(key)

                    if it:
                        # selon la réponse v3, ces champs doivent exister
                        track_qty = bool(it.get("trackQuantity", False))
                        qty = int(it.get("quantity") or 0)

                        if track_qty:
                            upsert_inventory_entrepot(db, entrepot.id, prod.id, qty)
                            db.commit()
                            inv_written += 1

        db.commit()

        return {
            "ok": True,
            "catalog_version": "CATALOG_V1",
            "parents_processed": parents_processed,
            "variants_seen": variants_seen,
            "created": created,
            "updated": updated,
            "skipped_no_sku": skipped_no_sku,
            "inventory_written_entrepot": inv_written,
            "entrepot_code": ENTREPOT_CODE,
        }

    except IntegrityError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e))[:1500]
        log.exception("❌ DB IntegrityError on /wix/sync V2")
        raise HTTPException(status_code=500, detail=f"DB IntegrityError: {msg}")

    except DataError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e))[:1500]
        log.exception("❌ DB DataError on /wix/sync V2")
        raise HTTPException(status_code=500, detail=f"DB DataError: {msg}")

    except Exception as e:
        db.rollback()
        msg = str(e)[:1500]
        log.exception("❌ DB Error on /wix/sync V2")
        raise HTTPException(status_code=500, detail=f"DB Error: {msg}")
