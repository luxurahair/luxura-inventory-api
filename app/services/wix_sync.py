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

# ----------------------------------------------------------
# CONFIG WIX
# ----------------------------------------------------------

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

WIX_PRODUCTS_URL = "https://www.wixapis.com/stores/v1/products/query"
WIX_INVENTORY_URL = "https://www.wixapis.com/stores/v2/inventoryItems/query"


# ----------------------------------------------------------
# OUTILS WIX SÉCURISÉS
# ----------------------------------------------------------

def _wix_headers() -> Optional[Dict[str, str]]:
    """Construit les headers Wix. Si variables manquantes → synchro off."""
    if not WIX_API_KEY or not WIX_SITE_ID:
        print("[WIX SYNC] WIX_API_KEY ou WIX_SITE_ID manquants → synchro désactivée.")
        return None
    return {
        "Content-Type": "application/json",
        "Authorization": WIX_API_KEY,   # adapté à ton token Wix
        "wix-site-id": WIX_SITE_ID,
    }


def _safe_post(url: str, body: dict) -> Optional[dict]:
    """POST vers Wix, NE JAMAIS faire planter l’API Luxura."""
    headers = _wix_headers()
    if headers is None:
        return None

    try:
        r = requests.post(url, json=body, headers=headers, timeout=20)
    except Exception as e:
        print(f"[WIX SYNC] ERREUR réseau vers {url}: {e}")
        return None

    if r.status_code != 200:
        print(f"[WIX SYNC] Statut HTTP {r.status_code} pour {url}")
        print("[WIX SYNC] Réponse brute (début):", r.text[:300])
        return None

    try:
        return r.json()
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


# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------

def _clean_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    return value.replace("”", '"').replace("“", '"').strip()


def _guess_category_from_name(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ["halo", "everly", "tape", "bande", "i-tip", "itip", "i tips", "extensions"]):
        return "Extensions"
    return "Wix"


def _build_variant_sku(base_sku: str, name: str, length: Optional[str], color: Optional[str]) -> str:
    """Construit un SKU lisible si la variante n'a pas de SKU propre."""
    base = base_sku if base_sku and base_sku != "NO-SKU" else name
    parts = [base]
    if length:
        parts.append(str(length))
    if color:
        parts.append(str(color))
    sku = "-".join(parts)
    # On nettoie un peu
    return sku.replace(" ", "").replace('"', "").replace("′", "").replace("’", "")


# ----------------------------------------------------------
# SYNC PRINCIPALE
# ----------------------------------------------------------

def sync_wix_to_luxura() -> Dict[str, Any]:
    """
    Synchro complète Wix → Luxura.
    - 1 produit Wix "simple" → 1 Product
    - Produits avec variantes → 1 Product par variante (utile pour les extensions)
    En cas de problème Wix, on loggue mais on NE PLANTE PAS l'API.
    """
    print("[WIX SYNC] Début synchro Wix → Luxura")

    created_products = 0
    updated_products = 0

    with Session(engine) as session:
        # ---------- 1) Salon central "Luxura Online" ----------
        ONLINE_SALON_NAME = "Luxura Online"
        salon = session.exec(
            select(Salon).where(Salon.name == ONLINE_SALON_NAME)
        ).first()
        if not salon:
            salon = Salon(name=ONLINE_SALON_NAME, address="Entrepôt central")
            session.add(salon)
            session.commit()
            session.refresh(salon)

        online_salon_id = salon.id

        # ---------- 2) Produits Wix ----------
        wix_products = wix_fetch_products()

        for wp in wix_products:
            base_sku = wp.get("sku") or "NO-SKU"
            name = _clean_text(wp.get("name") or "Sans nom")
            desc = wp.get("description") or ""
            price_raw = wp.get("priceData", {}).get("price", 0) or 0
            try:
                base_price = float(price_raw)
            except Exception:
                base_price = 0.0

            # Catégorie : on essaie de repérer les extensions
            category = _guess_category_from_name(name)

            # Options globales (Longueur / Couleur)
            product_options = wp.get("productOptions", []) or []

            # Map des noms d’options → plus simple pour variants
            # ex: {"longueur": "18\"", "couleur": "60A"}
            def extract_length_color_from_choices(choices: Dict[str, Any]) -> (Optional[str], Optional[str]):
                length = None
                color = None
                for opt_name, val in choices.items():
                    on = (opt_name or "").lower()
                    if "long" in on or "length" in on:
                        length = _clean_text(str(val))
                    if "coul" in on or "color" in on:
                        color = _clean_text(str(val))
                return length, color

            # ---------- 2A) Cas AVEC variantes (extensions & co) ----------
            variants = wp.get("variants") or wp.get("productVariants") or []

            if variants:
                for v in variants:
                    v_sku = v.get("sku")
                    choices = v.get("choices") or {}
                    length, color = extract_length_color_from_choices(choices)

                    # si pas de SKU pour la variante → on en construit un
                    if not v_sku:
                        v_sku = _build_variant_sku(base_sku, name, length, color)

                    # prix de la variante, sinon prix de base
                    v_price_raw = v.get("priceData", {}).get("price", base_price)
                    try:
                        v_price = float(v_price_raw)
                    except Exception:
                        v_price = base_price

                    # Chercher si ce SKU existe déjà
                    db_product = session.exec(
                        select(Product).where(Product.sku == v_sku)
                    ).first()

                    if not db_product:
                        # CREATE
                        new = ProductCreate(
                            sku=v_sku,
                            name=name,
                            description=desc,
                            length=length,
                            color=color,
                            price=v_price,
                            category=category,
                            active=True,
                        )
                        session.add(Product(**new.dict()))
                        created_products += 1
                    else:
                        # UPDATE
                        upd = ProductUpdate(
                            name=name,
                            description=desc,
                            length=length,
                            color=color,
                            price=v_price,
                            category=category,
                        )
                        for k, vval in upd.dict(exclude_none=True).items():
                            setattr(db_product, k, vval)
                        updated_products += 1

            else:
                # ---------- 2B) Cas SANS variantes (shampoings, brosses…) ----------
                db_product = session.exec(
                    select(Product).where(Product.sku == base_sku)
                ).first()

                if not db_product:
                    new = ProductCreate(
                        sku=base_sku,
                        name=name,
                        description=desc,
                        length=None,
                        color=None,
                        price=base_price,
                        category=category,
                        active=True,
                    )
                    session.add(Product(**new.dict()))
                    created_products += 1
                else:
                    upd = ProductUpdate(
                        name=name,
                        description=desc,
                        price=base_price,
                        category=category,
                    )
                    for k, vval in upd.dict(exclude_none=True).items():
                        setattr(db_product, k, vval)
                    updated_products += 1

        session.commit()

        # ---------- 3) Inventaire Wix → Luxura Online ----------
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
        "ok": True,
        "source": "manual",
        "created_products": created_products,
        "updated_products": updated_products,
        "created_salons": 0,
        "updated_salons": 0,
    }

    print("[WIX SYNC] Terminé :", summary)
    return summary
