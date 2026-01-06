# app/routes/wix.py

print("### LOADED app/routes/wix.py (v2 variants + entrepot inventory, CATALOG_V1) ###")

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

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
from typing import Any, Dict, Tuple

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
    Retourne:
      inv_map: key "<productId>:<variantId>" -> {
        "track": bool,
        "qty": int,
        "inStock": bool,
        "vendor_sku": Optional[str]
      }
      meta: infos debug (pages/items)
    """
    inv_map: Dict[str, Dict[str, Any]] = {}
    pages = 0
    total_items = 0

    offset = 0
    page_limit = min(max(int(page_limit), 1), 100)

    while pages < max_pages:
        resp = client.query_inventory_items_v1(limit=page_limit, offset=offset)

        # Wix peut renvoyer "inventoryItems" ou "items"
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

                # quantité (safe)
                try:
                    qty = int(v.get("quantity") or 0)
                except Exception:
                    qty = 0

                # inStock (safe)
                in_stock_val = v.get("inStock")
                instock = bool(in_stock_val) if isinstance(in_stock_val, bool) else (qty > 0)

                # SKU humain (vendor_sku) — Wix varie selon payload
                # On tente plusieurs champs possibles. Si rien -> None.
                vendor_sku = (
                    _clean_str(v.get("sku"))  # parfois existe
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

        # stop si dernière page
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
    Debug: affiche, pour chaque variante, où Wix met le SKU (selon structure réelle).
    """
    try:
        client = WixClient()
        variants = client.query_variants_v1(product_id, limit=100)

        def pick(*vals: Any) -> Optional[str]:
            for x in vals:
                if isinstance(x, str) and x.strip():
                    return x.strip()
            return None

        debug: List[Dict[str, Any]] = []
        for v in variants:
            # chemins fréquents (Wix varie selon payload)
            sku_a = v.get("sku")  # parfois string, parfois dict, parfois vide
            sku_b = (v.get("variant") or {}).get("sku")
            sku_c = (sku_a or {}).get("value") if isinstance(sku_a, dict) else None
            sku_d = v.get("stockKeepingUnit")
            sku_e = (v.get("skuData") or {}).get("sku")

            chosen = pick(
                sku_a if isinstance(sku_a, str) else None,
                sku_b,
                sku_c,
                sku_d,
                sku_e,
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
                    },
                    "raw_sku_chosen": chosen,
                }
            )

        return {
            "product_id": product_id,
            "count": len(variants),
            "debug": debug[:20],  # on coupe pour pas spammer swagger
            "note": "Si raw_sku_chosen est vide alors Wix n'a pas de SKU pour cette variante → fallback requis.",
        }

    except Exception as e:
        log.exception("❌ /wix/debug-variants failed")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# Sync V2: 1 variant = 1 Product, stock -> ENTREPOT (V1 inventory)
# ---------------------------------------------------------
@router.post("/sync")
def sync_wix_to_luxura(db: Session = Depends(get_session), limit: int = 200) -> Dict[str, Any]:
    """
    Sync Wix -> Luxura (V2):
    - Fetch products parents (CATALOG_V1)
    - Pour chaque parent: fetch variants
    - 1 variant = 1 Product (clé = SKU)
    - Inventory Wix écrit UNIQUEMENT dans ENTREPOT (InventoryItem) via stores-reader/v2 (CATALOG_V1 compatible)
    """
    client = WixClient()
    entrepot = get_or_create_entrepot(db)

    # 1) Charger inventaire V1 et construire map
    try:
        inv_map, inv_meta = _build_inventory_map_v1(client, page_limit=100, max_pages=50)
        # debug léger (pas 2000 lignes)
        print("[INV META]", inv_meta)
    except Exception as e:
        # On ne bloque pas la sync produits/variants si l'inventaire plante.
        inv_map = {}
        inv_meta = {"error": str(e)[:500]}

    # 2) Fetch parents (avec garde-fous)
    try:
        limit = int(limit or 200)
        per_page = min(max(limit, 1), 100)

        max_pages: Optional[int] = None
        if limit > 100:
            max_pages = 10  # max 1000 parents en une sync

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
            wix_product_id = str(pid).strip()

            variants = client.query_variants_v1(wix_product_id, limit=100)
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
                    db.flush()        # ✅ évite commit à chaque insert
                    db.refresh(prod)
                    created += 1

                # 3) Écrire inventaire ENTREPOT via inv_map V1
                wix_variant_id = (data.get("options") or {}).get("wix_variant_id")
                if wix_variant_id:
                    key = f"{wix_product_id}:{str(wix_variant_id).strip()}"
                    it = inv_map.get(key)

                    if it:
                        track_qty = bool(it.get("track", False))
                        qty = int(it.get("qty", 0) or 0)

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
