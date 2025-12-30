# app/routes/wix.py

print("### LOADED app/routes/wix.py (v1 sync + db error details) ###")

import logging
import os
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, DataError
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.product import Product
from services.catalog_normalizer import normalize_product


router = APIRouter(prefix="/wix", tags=["wix"])
log = logging.getLogger("uvicorn.error")

WIX_BASE_URL = "https://www.wixapis.com"


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
    return data.get("products") or []


@router.get("/debug-products")
def debug_wix_products() -> Dict[str, Any]:
    try:
        raw_products = _fetch_products_v1(limit=20)
        normalized = [normalize_product(p, "CATALOG_V1") for p in raw_products]
        return {"catalog_version": "CATALOG_V1", "count": len(normalized), "products": normalized}
    except Exception as e:
        log.exception("❌ /wix/debug-products failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
def sync_wix_to_luxura(db: Session = Depends(get_session), limit: int = 500) -> Dict[str, Any]:
    try:
        raw_products = _fetch_products_v1(limit=limit)
    except Exception as e:
        log.exception("❌ Wix fetch failed")
        raise HTTPException(status_code=500, detail=str(e))

    synced = 0
    skipped = 0

    try:
        for wp in raw_products:
            data = normalize_product(wp, "CATALOG_V1")
            wix_id = data.get("wix_id")
            name = data.get("name")

            if not wix_id or not name:
                skipped += 1
                continue

            wix_id = str(wix_id).strip()
            data["wix_id"] = wix_id
            data["name"] = str(name)

            if data.get("options") is None:
                data["options"] = {}

            existing = db.exec(select(Product).where(Product.wix_id == wix_id)).first()
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
            else:
                db.add(Product(**data))

            synced += 1

        db.commit()
        return {"catalog_version": "CATALOG_V1", "synced": synced, "skipped": skipped}

    except IntegrityError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e))[:1500]
        log.exception("❌ DB IntegrityError on /wix/sync")
        raise HTTPException(status_code=500, detail=f"DB IntegrityError: {msg}")

    except DataError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e))[:1500]
        log.exception("❌ DB DataError on /wix/sync")
        raise HTTPException(status_code=500, detail=f"DB DataError: {msg}")

    except Exception as e:
        db.rollback()
        msg = str(e)[:1500]
        log.exception("❌ DB Error on /wix/sync")
        raise HTTPException(status_code=500, detail=f"DB Error: {msg}")
