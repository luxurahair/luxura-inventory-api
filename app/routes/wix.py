# app/routes/wix.py

print("### LOADED app/routes/wix.py (v2 variants + entrepot inventory, CATALOG_V1) ###")

import logging
import os
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
    url = f"{WIX_BASE_URL}/stores/v1/products/query"
    payload: Dict[str, Any] = {"query": {"paging": {"limit": limit}}}

    resp = requests.post(url, headers=_wix_headers(), json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Wix v1 products/query: {resp.status_code} {resp.text}")

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
        inv = InventoryItem(salon_id=salon_id, product_id=product_id, quantity=max(int(qty), 0))
        db.add(inv)
    else:
        inv.quantity = max(int(qty), 0)


# ---------------------------------------------------------
# Inventory mapping (CATALOG_V1)
# ---------------------------------------------------------
def _clean_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip()
    return str(x).strip()


def _build_inventory_map_v1(
    client: WixClient,
    page_limit: int = 100,
    max_pages: int = 50,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """
    inv_map key "<productId>:<variantId>" -> {
      "track": bool, "qty": int, "inStock": bool, "vendor_sku": Optional[str]
    }
    """
    inv_map: Dict[str, Dict[str, Any]] = {}
    pages = 0
    total_items = 0

    offset = 0
    page_limit = min(max(int(page_limit), 1), 100)

    while pages < max_pages:
        resp = client.query_inventory_items_v1(limit=page_limit, offset=offset)

        items = resp.get("inventoryItems") or resp.get("items") or []
        if not isinstance(items, list):
            items = []

        pages += 1
        total_items += len(items)

        for inv in items:
            pid = _clean_str(inv.get("productId") or inv.get("product_id"))
            if not pid:
                continue

            track = bool(inv.get("trackQuantity", False))

            variants = inv.get("variants") or []
            if not isinstance(variants, list):
                variants = []

            for v in variants:
                vid = _clean_str(v.get("variantId") or v.get("variant_id") or v.get("id"))
                if not vid:
                    continue

                try:
                    qty = int(v.get("quantity") or 0)
                except Exception:
                    qty = 0

                in_stock_val = v.get("inStock")
                instock = bool(in_stock_val) if isinstance(in_stock_val, bool) else (qty > 0)

                vendor_sku = (
                    _clean_str(v.get("sku"))
                    or _clean_str(v.get("stockKeepingUnit"))
                    or _clean_str(v.get("vendorSku"))
                    or _clean_str((v.get("skuData") or {}).get("sku") if isinstance(v.get("skuData"), dict) else None)
                )
                vendor_sku = vendor_sku or None

                inv_map[f"{pid}:{vid}"] = {
                    "track": track,
                    "qty": qty,
                    "inStock": instock,
                    "vendor_sku": vendor_sku,
                }

        if len(items) < page_limit:
            break
        offset += page_limit

    meta = {
        "pages": pages,
        "total_inventory_items": total_items,
        "mapped_variants": len(inv_map),
    }
    return inv_map, meta


# ---------------------------------------------------------
# Debug endpoints
# ---------------------------------------------------------
@router.get("/debug-products")
def debug_wix_products() -> Dict[str, Any]:
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
    Debug: variants réels + où Wix met le SKU.
    """
    try:
        client = WixClient()
        variants = client.query_variants_v1(product_id, limit=100)

        def pick(*vals: Any) -> Optional[str]:
            for x in vals:
                if isinstance(x, str) and x.strip():
                    return x.strip()
            return None

        def find_gw_paths(
            obj: Any,
            prefix: str = "",
            out: Optional[List[Dict[str, Any]]] = None,
        ) -> List[Dict[str, Any]]:
            if out is None:
                out = []

            if isinstance(obj, dict):
                for k, v in obj.items():
                    p = f"{prefix}.{k}" if prefix else str(k)
                    find_gw_paths(v, p, out)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    p = f"{prefix}[{i}]"
                    find_gw_paths(v, p, out)
            else:
                if isinstance(obj, str) and "gw" in obj.lower():
                    out.append({"path": prefix, "value": obj})

            return out

        debug: List[Dict[str, Any]] = []
        for v in variants[:20]:
            sku_a = v.get("sku")
            sku_b = (v.get("variant") or {}).get("sku")
            sku_c = (sku_a or {}).get("value") if isinstance(sku_a, dict) else None
            sku_d = v.get("stockKeepingUnit")
            sku_e = (v.get("skuData") or {}).get("sku")
            sku_f = v.get("vendorSku")
            sku_g = v.get("itemNumber")

            chosen = pick(
                sku_a if isinstance(sku_a, str) else None,
                sku_b,
                sku_c,
                sku_d,
                sku_e,
                sku_f,
                sku_g,
            )

            debug.append(
                {
                    "variant_id": v.get("id") or v.get("_id") or v.get("variantId"),
                    "choices": v.get("choices") or v.get("options") or {},
                    "raw_sku_paths": {
                        "v.sku": sku_a,
                        "v.variant.sku": sku_b,
                        "v.sku.value": sku_c,
                        "v.stockKeepingUnit": sku_d,
                        "v.skuData.sku": sku_e,
                        "v.vendorSku": sku_f,
                        "v.itemNumber": sku_g,
                    },
                    "raw_sku_chosen": chosen,
                    "gw_hits": find_gw_paths(v)[:10],
                    "keys": sorted(list(v.keys()))[:50],
                }
            )

        return {
            "product_id": product_id,
            "count": len(variants),
            "debug": debug,
            "note": "Si gw_hits est vide et raw_sku_chosen est vide, alors l'endpoint variants/query ne fournit pas ton SKU humain.",
        }

    except Exception as e:
        msg = str(e)
        log.exception("❌ /wix/debug-variants failed")
        if "PRODUCT_NOT_FOUND" in msg or "was not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=500, detail=msg)


# ---------------------------------------------------------
# Sync V2: 1 variant = 1 Product, stock -> ENTREPOT (V1 inventory)
# ---------------------------------------------------------
@router.post("/sync")
def sync_wix_to_luxura(db: Session = Depends(get_session), limit: int = 200) -> Dict[str, Any]:
    client = WixClient()
    entrepot = get_or_create_entrepot(db)

    # 1) inventory map
    try:
        inv_map, inv_meta = _build_inventory_map_v1(client, page_limit=100, max_pages=50)
        print("[INV META]", inv_meta)
    except Exception as e:
        inv_map = {}
        inv_meta = {"error": str(e)[:500]}

    # 2) parents
    try:
        limit = int(limit or 200)
        per_page = min(max(limit, 1), 100)
        max_pages: Optional[int] = 10 if limit > 100 else None
        parents = client.query_products_v1(limit=per_page, max_pages=max_pages)
    except Exception as e:
        log.exception("❌ Wix fetch parents failed")
        raise HTTPException(status_code=500, detail=str(e))

    created = updated = skipped_no_sku = inv_written = parents_processed = variants_seen = 0

    try:
        for p in parents:
            pid = p.get("id") or p.get("_id")
            if not pid:
                continue

            parents_processed += 1
            wix_product_id = str(pid).strip()

            variants = client.query_variants_v1(wix_product_id, limit=100) or []
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

                wix_id = (data.get("wix_id") or "").strip()
                wix_variant_id = (data.get("options") or {}).get("wix_variant_id")

                # -------------------------------------------------
                # 1) Trouver l'existant par (wix_id + wix_variant_id)
                # -------------------------------------------------
                existing: Optional[Product] = None
                if wix_id and wix_variant_id:
                    candidates = db.exec(select(Product).where(Product.wix_id == wix_id)).all()
                    for cand in candidates:
                        opts = cand.options or {}
                        if isinstance(opts, dict) and str(opts.get("wix_variant_id")) == str(wix_variant_id):
                            existing = cand
                            break

                # 2) fallback par sku
                if existing is None:
                    existing = db.exec(select(Product).where(Product.sku == sku)).first()

                # -------------------------------------------------
                # MERGE anti-doublon: si sku déjà pris, on fusionne
                # -------------------------------------------------
                sku_owner = db.exec(select(Product).where(Product.sku == sku)).first()
                if existing and sku_owner and sku_owner.id != existing.id:
                    # repointer l'inventaire vers sku_owner
                    inv_rows = db.exec(select(InventoryItem).where(InventoryItem.product_id == existing.id)).all()
                    for inv in inv_rows:
                        inv.product_id = sku_owner.id

                    # supprimer le produit fallback
                    db.delete(existing)
                    db.flush()

                    # continuer avec le produit "canonique"
                    existing = sku_owner

                # -------------------------------------------------
                # apply update / create
                # -------------------------------------------------
                if existing:
                    for field, value in data.items():
                        setattr(existing, field, value)
                    prod = existing
                    updated += 1
                else:
                    prod = Product(**data)
                    db.add(prod)
                    db.flush()
                    db.refresh(prod)
                    created += 1

                # -------------------------------------------------
                # 3) ENTREPOT inventory + vendor_sku (optionnel)
                # -------------------------------------------------
                if wix_variant_id:
                    key = f"{wix_product_id}:{str(wix_variant_id).strip()}"
                    it = inv_map.get(key)

                    if it:
                        vendor_sku = it.get("vendor_sku")
                        if vendor_sku:
                            opts = data.get("options") or {}
                            if not isinstance(opts, dict):
                                opts = {}
                            opts["vendor_sku"] = vendor_sku
                            data["options"] = opts
                            prod.options = data["options"]

                        track_qty = bool(it.get("track", False))
                        try:
                            qty = int(it.get("qty") or 0)
                        except Exception:
                            qty = 0

                        if track_qty:
                            upsert_inventory_entrepot(db, entrepot.id, prod.id, qty)
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
            "inventory_meta": inv_meta,
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
