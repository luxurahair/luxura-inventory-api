# app/services/wix_sync.py

import os
from typing import Any, Dict, List, Optional

import requests
from sqlmodel import Session, select

from app.db import engine
from app.models import (
    Product,
    ProductCreate,
    ProductUpdate,
    Salon,
    InventoryItem,
)

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

WIX_PRODUCTS_URL = "https://www.wixapis.com/stores/v1/products/query"
WIX_INVENTORY_URL = "https://www.wixapis.com/stores/v1/inventoryItems/query"


def _wix_headers() -> Optional[Dict[str, str]]:
    """
    Construit les headers Wix.
    Si une variable manque, on désactive juste la synchro proprement.
    """
    if not WIX_API_KEY or not WIX_SITE_ID:
        print("[WIX SYNC] WIX_API_KEY ou WIX_SITE_ID manquants → synchro désactivée.")
        return None

    return {
        "Content-Type": "application/json",
        "Authorization": WIX_API_KEY,  # à adapter à ton type de clé si nécessaire
        "wix-site-id": WIX_SITE_ID,
    }


def _safe_post(url: str, body: dict) -> Optional[dict]:
    """
    POST vers Wix avec gestion d'erreur : ne lève jamais d'exception vers l'extérieur.
    Retourne un dict ou None.
    """
    headers = _wix_headers()
    if headers is None:
        return None

    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
    except Exception as e:
        print(f"[WIX SYNC] ERREUR réseau vers {url}: {e}")
        return None

    # Log basique si statut HTTP pas 200
    if r.status_code != 200:
        print(f"[WIX SYNC] Statut HTTP {r.status_code} pour {url}")
        # On essaie quand même de print un bout de texte pour debug
        print("[WIX SYNC] Réponse brute (début):", r.text[:300])
        return None

    try:
        data = r.json()
        return data
    except Exception as e:
        print(f"[WIX SYNC] Réponse non-JSON depuis {url}: {e}")
        print("[WIX SYNC] Contenu brut (début):", r.text[:300])
        return None


def wix_fetch_products() -> List[dict]:
    """Télécharge tous les produits Wix Stores (ou [] en cas d'erreur)."""
    body = {"query": {}}
    data = _safe_post(WIX_PRODUCTS_URL, body)
    if not data or "products" not in data:
        print("[WIX SYNC] Aucun produit récupéré depuis Wix.")
        return []
    return data["products"]


def wix_fetch_inventory() -> List[dict]:
    """Télécharge l'inventaire Wix (ou [] en cas d'erreur)."""
    body = {"query": {}}
    data = _safe_post(WIX_INVENTORY_URL, body)
    if not data or "inventoryItems" not in data:
        print("[WIX SYNC] Aucun inventaire récupéré depuis Wix.")
        return []
    return data["inventoryItems"]


def sync_wix_to_luxura() -> Dict[str, Any]:
    """
    Synchro complète Wix → Luxura.
    En cas de bug Wix, on log, mais on NE FAIT PAS planter l'API.
    """
    print("[WIX SYNC] Début synchro Wix → Luxura")

    created_products = 0
    updated_products = 0

    with Session(engine) as session:
        # Vérifier ou créer le salon "Luxura Online"
        ONLINE_SALON_NAME = "Luxura Online"
        salon = session.exec(
            select(Salon).where(Salon.name == ONLINE_SALON_NAME)
        ).first()
        if not salon:
            salon = Salon(name=ONLINE_SALON_NAME, address="Entrepôt")
            session.add(salon)
            session.commit()
            session.refresh(salon)

        online_salon_id = salon.id

        # 1) Produits Wix
        wix_products = wix_fetch_products()
        for wp in wix_products:
            sku = wp.get("sku") or "NO-SKU"
            name = wp.get("name") or "Sans nom"
            desc = wp.get("description") or ""
            price_raw = wp.get("priceData", {}).get("price", 0) or 0
            try:
                price = float(price_raw)
            except Exception:
                price = 0.0

            length = None
            color = None

            for opt in wp.get("productOptions", []):
                oname = (opt.get("name") or "").lower()
                if oname == "longueur" and opt.get("choices"):
                    length = opt["choices"][0].get("description")
                if oname == "couleur" and opt.get("choices"):
                    color = opt["choices"][0].get("description")

            db_product = session.exec(
                select(Product).where(Product.sku == sku)
            ).first()

            if not db_product:
                new = ProductCreate(
                    sku=sku,
                    name=name,
                    description=desc,
                    length=length,
                    color=color,
                    price=price,
                    category="Wix",
                    active=True,
                )
                session.add(Product(**new.dict()))
                created_products += 1
            else:
                upd = ProductUpdate(
                    name=name,
                    description=desc,
                    length=length,
                    color=color,
                    price=price,
                )
                for k, v in upd.dict(exclude_none=True).items():
                    setattr(db_product, k, v)
                updated_products += 1

        session.commit()

        # 2) Inventaire Wix → Luxura Online
        wix_stock = wix_fetch_inventory()
        for item in wix_stock:
            sku = item.get("sku")
            quantity = item.get("quantity", 0) or 0

            if not sku:
                continue

            product = session.exec(
                select(Product).where(Product.sku == sku)
            ).first()
            if not product:
                continue

            inv = session.exec(
                select(InventoryItem).where(
                    InventoryItem.salon_id == online_salon_id,
                    InventoryItem.product_id == product.id,
                )
            ).first()

            if not inv:
                inv = InventoryItem(
                    salon_id=online_salon_id,
                    product_id=product.id,
                    quantity=quantity,
                )
                session.add(inv)
            else:
                inv.quantity = quantity

        session.commit()

    summary: Dict[str, Any] = {
        "created_products": created_products,
        "updated_products": updated_products,
        "created_salons": 0,
        "updated_salons": 0,
    }

    print("[WIX SYNC] Terminé :", summary)
    return summary
