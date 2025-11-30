# app/services/wix_sync.py

import os
from typing import Any, Dict, List

import requests
from sqlmodel import Session, select

from app.db import engine
from app.models import (
    Product,
    ProductCreate,
    ProductUpdate,
    Salon,
    SalonCreate,
    SalonUpdate,
    InventoryItem,
    InventoryCreate,
    InventoryUpdate,
)

# ----------------------------------------------------------
# CONFIG WIX
# ----------------------------------------------------------

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

WIX_PRODUCTS_URL = "https://www.wixapis.com/stores/v1/products/query"
WIX_ORDERS_URL = "https://www.wixapis.com/stores/v1/inventoryItems/query"


HEADERS = {
    "Content-Type": "application/json",
    "Authorization": WIX_API_KEY,
    "wix-site-id": WIX_SITE_ID,
}


# ----------------------------------------------------------
# FONCTIONS WIX
# ----------------------------------------------------------

def wix_fetch_products() -> List[dict]:
    """Télécharge tous les produits Wix Stores."""
    body = { "query": {} }

    r = requests.post(WIX_PRODUCTS_URL, json=body, headers=HEADERS)
    data = r.json()

    if "products" not in data:
        print("[WIX] ERREUR produits:", data)
        return []

    return data["products"]


def wix_fetch_inventory() -> List[dict]:
    """Télécharge le stock Wix (stock global)."""
    body = { "query": {} }

    r = requests.post(WIX_ORDERS_URL, json=body, headers=HEADERS)
    data = r.json()

    if "inventoryItems" not in data:
        print("[WIX] ERREUR inventaire:", data)
        return []

    return data["inventoryItems"]


# ----------------------------------------------------------
# FONCTION PRINCIPALE
# ----------------------------------------------------------

def sync_wix_to_luxura() -> Dict[str, Any]:
    print("[WIX SYNC] Début synchro Wix → Luxura")

    created_products = 0
    updated_products = 0

    # Le salon “Luxura Online” recevra l’inventaire global venant de Wix
    ONLINE_SALON_NAME = "Luxura Online"

    with Session(engine) as session:

        # ------------------------------------------------------
        # 1. S’assurer que le salon “Luxura Online” existe
        # ------------------------------------------------------
        salon = session.exec(
            select(Salon).where(Salon.name == ONLINE_SALON_NAME)
        ).first()

        if not salon:
            salon = Salon(name=ONLINE_SALON_NAME, address="Entrepôt")
            session.add(salon)
            session.commit()
            session.refresh(salon)

        online_salon_id = salon.id

        # ------------------------------------------------------
        # 2. Télécharger produits Wix
        # ------------------------------------------------------
        wix_products = wix_fetch_products()

        for wp in wix_products:

            sku = wp.get("sku", "NO-SKU")
            name = wp.get("name", "Sans nom")
            desc = wp.get("description", "")
            price = float(wp.get("priceData", {}).get("price", 0))

            # On découpe les options Wix pour trouver longueur/couleur
            length = None
            color = None

            if "productOptions" in wp:
                for opt in wp["productOptions"]:
                    if opt["name"].lower() == "longueur":
                        length = opt["choices"][0].get("description")
                    if opt["name"].lower() == "couleur":
                        color = opt["choices"][0].get("description")

            # Vérifier si le produit existe
            db_product = session.exec(
                select(Product).where(Product.sku == sku)
            ).first()

            if not db_product:
                # CREATE
                new = ProductCreate(
                    sku=sku,
                    name=name,
                    description=desc,
                    length=length,
                    color=color,
                    price=price,
                    category="Wix",
                    active=True
                )

                obj = Product(**new.dict())
                session.add(obj)
                created_products += 1

            else:
                # UPDATE
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

        # ------------------------------------------------------
        # 3. Télécharger inventaire Wix et le mettre sur “Luxura Online”
        # ------------------------------------------------------
        wix_stock = wix_fetch_inventory()

        for item in wix_stock:
            sku = item.get("sku")
            quantity = item.get("quantity", 0)

            # trouver le produit DB
            product = session.exec(
                select(Product).where(Product.sku == sku)
            ).first()

            if not product:
                continue

            # Vérifier si inventaire existe
            inv = session.exec(
                select(InventoryItem).where(
                    InventoryItem.salon_id == online_salon_id,
                    InventoryItem.product_id == product.id,
                )
            ).first()

            if not inv:
                new_inv = InventoryItem(
                    salon_id=online_salon_id,
                    product_id=product.id,
                    quantity=quantity
                )
                session.add(new_inv)

            else:
                inv.quantity = quantity

        session.commit()

    summary = {
        "ok": True,
        "source": "manual",
        "created_products": created_products,
        "updated_products": updated_products,
        "created_salons": 0,
        "updated_salons": 0,
    }

    print("[WIX SYNC] Terminé :", summary)
    return summary
