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

        # ... (tout ton code jusqu'à title/desc inchangé)

    if not title and not desc:
        raise HTTPException(400, "No SEO data on product (options.seo_parent.fr)")

    # ✅ Wix SEO v2/v3 style: seoData.tags (pas seoData.title/description)
    seo_payload = {
        "seoData": {
            "tags": [
                # <title>...</title>
                {"type": "title", "children": [{"text": title}]},
                # <meta name="description" content="...">
                {"type": "meta", "props": {"name": "description", "content": desc}},
            ],
            "settings": {
                "preventAutoRedirect": False,
                "keywords": [],
            },
        }
    }

    r = requests.patch(
        f"https://www.wixapis.com/stores/v1/products/{wix_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=seo_payload,
        timeout=30,
    )

    if not r.ok:
        raise HTTPException(502, f"Wix update failed: {r.status_code} {r.text}")

    return {"ok": True, "product_id": prod.id, "wix_id": wix_id, "title": title, "desc": desc}


@router.get("/seo/check_one_full")
def check_one_full(product_id: int, db: Session = Depends(get_session)):
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

    r = requests.get(
        f"https://www.wixapis.com/stores/v1/products/{wix_id}",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=30,
    )
    if not r.ok:
        raise HTTPException(502, f"Wix get failed: {r.status_code} {r.text}")

    data = r.json()

    # ✅ on essaie plusieurs formes possibles
    candidate = None
    if isinstance(data, dict):
        if isinstance(data.get("product"), dict):
            candidate = data["product"]
        elif isinstance(data.get("products"), list) and data["products"]:
            if isinstance(data["products"][0], dict):
                candidate = data["products"][0]
        else:
            candidate = data  # parfois l'objet produit est direct

    seo_data = candidate.get("seoData") if isinstance(candidate, dict) else None

    return {
        "ok": True,
        "product_id": prod.id,
        "wix_id": wix_id,
        "seoData": seo_data,
        # ✅ debug: montre les clés principales pour comprendre la structure
        "top_keys": list(data.keys()) if isinstance(data, dict) else None,
        "product_keys": list(candidate.keys()) if isinstance(candidate, dict) else None,
    }

