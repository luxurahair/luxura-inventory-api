from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
import requests
import os

from app.db.session import get_session
from app.models.product import Product
from app.services.catalog_normalizer import normalize_product

router = APIRouter(prefix="/wix", tags=["wix"])
WIX_BASE_URL = "https://www.wixapis.com"

def _wix_headers():
    api_key = os.getenv("WIX_API_KEY") or os.getenv("WIX_API_TOKEN")
    site_id = os.getenv("WIX_SITE_ID")
    if not api_key or not site_id:
        raise RuntimeError("WIX_API_KEY (ou WIX_API_TOKEN) et WIX_SITE_ID manquants dans Render.")
    return {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "wix-site-id": site_id,
    }

@router.get("/debug-products")
def debug_wix_products():
    try:
        url = f"{WIX_BASE_URL}/stores/v1/products/query"
        payload = {"query": {"paging": {"limit": 20}}}
        resp = requests.post(url, headers=_wix_headers(), json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v1 products/query: {resp.status_code} {resp.text}")
        raw_products = (resp.json() or {}).get("products") or []
        normalized = [normalize_product(p, "CATALOG_V1") for p in raw_products]
        return {"catalog_version": "CATALOG_V1", "count": len(normalized), "products": normalized}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
def sync_wix_to_luxura(db: Session = Depends(get_session), limit: int = 500):
    try:
        url = f"{WIX_BASE_URL}/stores/v1/products/query"
        payload = {"query": {"paging": {"limit": limit}}}
        resp = requests.post(url, headers=_wix_headers(), json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v1 products/query: {resp.status_code} {resp.text}")
        raw_products = (resp.json() or {}).get("products") or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    synced = 0
    for wp in raw_products:
        data = normalize_product(wp, "CATALOG_V1")
        wix_id = data.get("wix_id")
        if not wix_id:
            continue

        existing = db.exec(select(Product).where(Product.wix_id == wix_id)).first()
        if existing:
            for field, value in data.items():
                setattr(existing, field, value)
        else:
            db.add(Product(**data))
        synced += 1

    db.commit()
    return {"catalog_version": "CATALOG_V1", "synced": synced}
