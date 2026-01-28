import os
from typing import Any, Dict, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.product import Product

router = APIRouter(prefix="/wix", tags=["wix-push"])

WIX_API_BASE = "https://www.wixapis.com"
DEFAULT_PUBLIC_BASE = "https://luxura-inventory-api.onrender.com"


def _get_instance_id() -> str:
    instance_id = (os.getenv("WIX_INSTANCE_ID") or "").strip()
    if not instance_id:
        raise HTTPException(500, "Missing env: WIX_INSTANCE_ID")
    return instance_id


def _get_public_base_url() -> str:
    return (os.getenv("PUBLIC_BASE_URL") or DEFAULT_PUBLIC_BASE).strip().rstrip("/")


def _fetch_access_token(instance_id: str) -> str:
    base = _get_public_base_url()
    try:
        token_res = requests.post(
            f"{base}/wix/token",
            params={"instance_id": instance_id},
            timeout=30,
        )
    except requests.RequestException as e:
        raise HTTPException(502, f"Token fetch network error: {e}")

    if not token_res.ok:
        raise HTTPException(502, f"Token fetch failed: {token_res.status_code} {token_res.text}")

    try:
        data = token_res.json()
    except ValueError:
        raise HTTPException(502, f"Token fetch invalid JSON: {token_res.text[:500]}")

    access_token = (data.get("access_token") or "").strip()
    if not access_token:
        raise HTTPException(502, "No access_token returned by /wix/token")

    return access_token


def _load_product_or_404(product_id: int, db: Session) -> Product:
    prod = db.exec(select(Product).where(Product.id == product_id)).first()
    if not prod:
        raise HTTPException(404, "Product not found")
    return prod


def _get_wix_id_or_400(prod: Product) -> str:
    wix_id = (prod.wix_id or "").strip()
    if not wix_id:
        raise HTTPException(400, "Missing wix_id on product")
    return wix_id


def _get_seo_fr_from_product(prod: Product) -> Dict[str, str]:
    opts = prod.options if isinstance(prod.options, dict) else {}
    seo_parent = opts.get("seo_parent") or {}
    seo_fr = seo_parent.get("fr") or {}

    title = (seo_fr.get("title") or "").strip()
    desc = (seo_fr.get("meta") or "").strip()

    return {"title": title, "description": desc}


def _wix_patch_description_with_luxura_seo(wix_id: str, access_token: str, title: str, desc: str) -> Dict[str, Any]:
    """
    Persiste le SEO Luxura dans le champ description via un commentaire HTML.
    - invisible sur la page (commentaire)
    - persistant
    - vérifiable via GET
    """
    # 1) Get produit actuel pour ne pas écraser la description
    try:
        g = requests.get(
            f"{WIX_API_BASE}/stores/v1/products/{wix_id}",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            timeout=30,
        )
    except requests.RequestException as e:
        raise HTTPException(502, f"Wix GET network error: {e}")

    if not g.ok:
        raise HTTPException(502, f"Wix get failed: {g.status_code} {g.text}")

    data = g.json()
    prod = data.get("product") if isinstance(data, dict) else None
    if not isinstance(prod, dict):
        raise HTTPException(502, f"Wix get unexpected format: top_keys={list(data.keys()) if isinstance(data, dict) else None}")

    current_desc = prod.get("description") or ""
    if not isinstance(current_desc, str):
        current_desc = str(current_desc)

    # 2) Construire bloc commentaire (on remplace l'ancien si déjà présent)
    marker_start = "<!-- LUXURA_SEO_START -->"
    marker_end = "<!-- LUXURA_SEO_END -->"

    seo_block = (
        f"{marker_start}\n"
        f'{{"title_fr": {title!r}, "desc_fr": {desc!r}}}\n'
        f"{marker_end}"
    )

    # enlever ancien bloc
    if marker_start in current_desc and marker_end in current_desc:
        before = current_desc.split(marker_start)[0]
        after = current_desc.split(marker_end, 1)[1]
        new_desc = (before + seo_block + after).strip()
    else:
        # on l'ajoute à la fin proprement
        new_desc = (current_desc.strip() + "\n\n" + seo_block).strip()

    payload = {"description": new_desc}

    # 3) PATCH
    try:
        r = requests.patch(
            f"{WIX_API_BASE}/stores/v1/products/{wix_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=30,
        )
    except requests.RequestException as e:
        raise HTTPException(502, f"Wix PATCH network error: {e}")

    if not r.ok:
        raise HTTPException(502, f"Wix update failed: {r.status_code} {r.text}")

    try:
        return r.json()
    except ValueError:
        return {"raw": r.text}


def _wix_get_product(wix_id: str, access_token: str) -> Dict[str, Any]:
    try:
        r = requests.get(
            f"{WIX_API_BASE}/stores/v1/products/{wix_id}",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            timeout=30,
        )
    except requests.RequestException as e:
        raise HTTPException(502, f"Wix GET network error: {e}")

    if not r.ok:
        raise HTTPException(502, f"Wix get failed: {r.status_code} {r.text}")

    try:
        return r.json()
    except ValueError:
        raise HTTPException(502, f"Wix get invalid JSON: {r.text[:500]}")


def _extract_product_candidate(data: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(data, dict):
        return None
    if isinstance(data.get("product"), dict):
        return data["product"]
    if isinstance(data.get("products"), list) and data["products"]:
        if isinstance(data["products"][0], dict):
            return data["products"][0]
    return data


@router.post("/seo/push_one")
def push_one(product_id: int, db: Session = Depends(get_session)):
    prod = _load_product_or_404(product_id, db)
    wix_id = _get_wix_id_or_400(prod)

    instance_id = _get_instance_id()
    access_token = _fetch_access_token(instance_id)

    seo = _get_seo_fr_from_product(prod)
    title = seo["title"]
    desc = seo["description"]

    if not title and not desc:
        raise HTTPException(400, "No SEO data on product (options.seo_parent.fr)")

    wix_resp = _wix_patch_custom_text_fields(wix_id, access_token, title, desc)

    return {
        "ok": True,
        "product_id": prod.id,
        "wix_id": wix_id,
        "stored_in_wix": {
            "luxura_seo_title_fr": title,
            "luxura_seo_desc_fr": desc,
        },
        "wix_response": wix_resp,
    }


@router.get("/seo/check_one_full")
def check_one_full(product_id: int, db: Session = Depends(get_session)):
    prod = _load_product_or_404(product_id, db)
    wix_id = _get_wix_id_or_400(prod)

    instance_id = _get_instance_id()
    access_token = _fetch_access_token(instance_id)

    data = _wix_get_product(wix_id, access_token)
    candidate = _extract_product_candidate(data)

    custom = None
    product_keys = None
    if isinstance(candidate, dict):
        custom = candidate.get("customTextFields")
        product_keys = list(candidate.keys())

    return {
        "ok": True,
        "product_id": prod.id,
        "wix_id": wix_id,
        "customTextFields": custom,
        "top_keys": list(data.keys()) if isinstance(data, dict) else None,
        "product_keys": product_keys,
    }
