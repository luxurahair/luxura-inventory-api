import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.db import SessionLocal
from app.models import Product

# Toutes les routes Wix auront le prefix /wix
router = APIRouter(prefix="/wix", tags=["wix"])


# ------------------------------------------------
#  Webhook commande Wix
# ------------------------------------------------
@router.post("/order-webhook")
async def wix_order_webhook(payload: Dict[str, Any]):
    """
    Webhook de commande Wix.
    Pour l'instant : on logge simplement et on renvoie {}.
    Tu pourras plus tard décrémenter l'inventaire ici.
    """
    print("[WIX WEBHOOK] Payload reçu :", payload)
    # TODO plus tard: décrémenter l'inventaire en fonction des lineItems
    return {}


# ------------------------------------------------
#  Synchro manuelle Wix -> Luxura
# ------------------------------------------------
@router.post("/sync")
def sync_wix_products_manual():
    """
    Endpoint manuel pour synchroniser les produits Wix vers la base Luxura.

    À appeler via /docs (POST /wix/sync) ou directement en HTTP.
    """

    api_key = os.getenv("WIX_API_KEY")
    account_id = os.getenv("WIX_ACCOUNT_ID")
    site_id = os.getenv("WIX_SITE_ID")

    if not api_key or not account_id or not site_id:
        raise HTTPException(
            status_code=500,
            detail="Variables WIX_API_KEY, WIX_ACCOUNT_ID ou WIX_SITE_ID manquantes dans l'environnement.",
        )

    # URL API produits Wix – à ajuster si besoin
    url = "https://www.wixapis.com/stores/v1/products/query"

    headers = {
        "Authorization": api_key,
        "wix-account-id": account_id,
        "wix-site-id": site_id,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, headers=headers, json={"query": {}})
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur réseau en appelant l'API Wix: {repr(e)}",
        )

    if resp.status_code != 200:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise HTTPException(
            status_code=resp.status_code,
            detail={"message": "Erreur renvoyée par Wix", "body": body},
        )

    data = resp.json()
    wix_products: List[Dict[str, Any]] = data.get("products") or data.get("items") or []

    created = 0
    updated = 0

    with SessionLocal() as session:
        for wp in wix_products:
            sku: Optional[str] = wp.get("sku")
            if not sku:
                # On ignore les produits sans SKU
                continue

            name = wp.get("name") or wp.get("productName") or ""
            description = wp.get("description") or ""

            price_value = 0
            price_obj = wp.get("price") or wp.get("priceData") or {}
            if isinstance(price_obj, dict):
                price_value = (
                    price_obj.get("price")
                    or price_obj.get("basePrice")
                    or price_obj.get("amount")
                    or 0
                )

            length = ""
            color = ""
            category = ""

            existing: Optional[Product] = session.exec(
                select(Product).where(Product.sku == sku)
            ).first()

            if existing:
                existing.name = name
                existing.description = description
                existing.price = price_value
                existing.length = length
                existing.color = color
                existing.category = category
                existing.active = True
                updated += 1
            else:
                prod = Product(
                    sku=sku,
                    name=name,
                    description=description,
                    price=price_value,
                    length=length,
                    color=color,
                    category=category,
                    active=True,
                )
                session.add(prod)
                created += 1

        session.commit()

    return {
        "status": "ok",
        "wix_products_received": len(wix_products),
        "created": created,
        "updated": updated,
    }
