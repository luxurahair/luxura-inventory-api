import os
import requests
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.product import Product

router = APIRouter(prefix="/wix", tags=["wix-push"])

@router.post("/seo/push_one")
def push_one(product_id: int, db: Session = Depends(get_session)):
    prod = db.exec(select(Product).where(Product.id == product_id)).first()
    if not prod:
        raise HTTPException(404, "Product not found")

    wix_id = (prod.wix_id or "").strip()
    if not wix_id:
        raise HTTPException(400, "Missing wix_id on product")

    instance_id = os.getenv("WIX_INSTANCE_ID")
    if not instance_id:
        raise HTTPException(500, "Missing env: WIX_INSTANCE_ID")

    base = os.getenv("PUBLIC_BASE_URL", "https://luxura-inventory-api.onrender.com")
    token_res = requests.post(f"{base}/wix/token", params={"instance_id": instance_id}, timeout=30)
    if not token_res.ok:
        raise HTTPException(502, f"Token fetch failed: {token_res.status_code} {token_res.text}")

    access_token = token_res.json().get("access_token")
    if not access_token:
        raise HTTPException(502, "No access_token returned")

    opts = prod.options if isinstance(prod.options, dict) else {}
    seo_parent = (opts.get("seo_parent") or {})
    seo_fr = (seo_parent.get("fr") or {})

    title = (seo_fr.get("title") or "").strip()
    desc = (seo_fr.get("meta") or "").strip()

    if not title and not desc:
        raise HTTPException(400, "No SEO data on product (options.seo_parent.fr)")

    r = requests.patch(
        f"https://www.wixapis.com/stores/v1/products/{wix_id}",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"seoData": {"title": title, "description": desc}},
        timeout=30,
    )

    if not r.ok:
        raise HTTPException(502, f"Wix update failed: {r.status_code} {r.text}")

    return {"ok": True, "product_id": prod.id, "wix_id": wix_id, "title": title}
