# app/services/wix_sync.py

import os
from typing import Any, Dict, List, Optional, Tuple

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

WIX_API_KEY = os.getenv("WIX_API_KEY") or os.getenv("WIX_ACCESS_TOKEN")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

# Produits = v1, Inventaire = v2 (ton 404 venait de l’ancien v1)
WIX_PRODUCTS_URL = "https://www.wixapis.com/stores/v1/products/query"
WIX_INVENTORY_URL = "https://www.wixapis.com/stores/v2/inventoryItems/query"


# ----------------------------------------------------------
# OUTILS WIX ROBUSTES
# ----------------------------------------------------------

def _wix_headers() -> Optional[Dict[str, str]]:
    """
    Construit les en-têtes HTTP pour appeler l'API Wix.

    Si les variables d'environnement ne sont pas définies,
    la synchro est simplement ignorée (on ne plante pas l'API Luxura).
    """
    if not WIX_API_KEY or not WIX_SITE_ID:
        print("[WIX SYNC] WIX_API_KEY ou WIX_SITE_ID manquants → synchro désactivée.")
        return None

    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
    }


def _safe_post(url: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Appel POST vers Wix.

    - Ne lève jamais d'exception (catch complet)
    - Log les erreurs HTTP et JSON
    - Retourne None en cas de problème
    """
    headers = _wix_headers()
    if headers is None:
        return None

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=20)
    except Exception as e:
        print(f"[WIX SYNC] ERREUR réseau vers {url}: {e!r}")
        return None

    if resp.status_code != 200:
        print(f"[WIX SYNC] Statut HTTP {resp.status_code} pour {url}")
        txt = resp.text[:400].replace("\n", " ")
        print(f"[WIX SYNC] Réponse brute (début): {txt}")
        return None

    try:
        return resp.json()
    except Exception as e:
        print(f"[WIX SYNC] Réponse non-JSON depuis {url}: {e!r}")
        txt = resp.text[:400].replace("\n", " ")
        print(f"[WIX SYNC] Contenu brut (début): {txt}")
        return None


# ----------------------------------------------------------
# FETCH PRODUITS & INVENTAIRE AVEC PAGINATION
# ----------------------------------------------------------

def wix_fetch_products() -> List[Dict[str, Any]]:
    """
    Télécharge TOUS les produits Wix Stores, page par page.

    Par défaut l'API Wix renvoie 100 produits max par appel.
    On boucle donc avec offset tant qu'on reçoit des produits.
    """
    all_products: List[Dict[str, Any]] = []
    limit = 100
    offset = 0

    while True:
        body: Dict[str, Any] = {
            "query": {
                "paging": {
                    "limit": limit,
                    "offset": offset,
                }
            }
        }

        data = _safe_post(WIX_PRODUCTS_URL, body)
        if not data:
            break

        products = data.get("products") or []
        print(f"[WIX SYNC] Page produits Wix: offset={offset}, reçus={len(products)}")
        all_products.extend(products)

        # Si on reçoit moins que limit, c'est la dernière page
        if len(products) < limit:
            break

        offset += limit

    print(f"[WIX SYNC] Produits totaux reçus depuis Wix: {len(all_products)}")
    return all_products


def wix_fetch_inventory() -> List[Dict[str, Any]]:
    """
    Télécharge l'inventaire Wix.

    Si l'API retourne une erreur (404, 401, etc.), on log juste
    et on retourne une liste vide.
    """
    body: Dict[str, Any] = {"query": {}}
    data = _safe_post(WIX_INVENTORY_URL, body)
    if not data:
        print("[WIX SYNC] Aucun inventaire récupéré depuis Wix.")
        return []

    items = data.get("inventoryItems") or data.get("items") or []
    print(f"[WIX SYNC] Lignes d'inventaire Wix reçues: {len(items)}")
    return items


# ----------------------------------------------------------
# HELPERS PRODUITS / VARIANTES
# ----------------------------------------------------------

def _clean_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    return (
        value.replace("”", '"')
        .replace("“", '"')
        .replace("\u00a0", " ")
        .strip()
    )


def _guess_category_from_name(name: str) -> str:
    n = name.lower()
    if any(
        k in n
        for k in [
            "halo",
            "everly",
            "tape",
            "bande",
            "i-tip",
            "itip",
            "i tips",
            "extensions",
        ]
    ):
        return "Extensions"
    return "Wix"


def _build_variant_sku(
    base_sku: str, name: str, length: Optional[str], color: Optional[str]
) -> str:
    """
    Construit un SKU lisible si la variante n'a pas de SKU propre.
    Ex: base "NO-SKU", name "Halo Everly", length "18\"", color "60A"
         → "HaloEverly-18-60A"
    """
    base = base_sku if base_sku and base_sku != "NO-SKU" else name
    parts = [base]
    if length:
        parts.append(str(length))
    if color:
        parts.append(str(color))
    sku = "-".join(parts)
    return sku.replace(" ", "").replace('"', "").replace("′", "").replace("’", "")


def _extract_length_color_from_choices(choices: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Essaie de repérer la longueur et la couleur dans les choices Wix.
    Les clés sont souvent du genre "Longueur" / "Couleur" ou "Length" / "Color".
    """
    length: Optional[str] = None
    color: Optional[str] = None
    for opt_name, val in choices.items():
        on = (opt_name or "").lower()
        if "long" in on or "length" in on:
            length = _clean_text(str(val))
        if "coul" in on or "color" in on:
            color = _clean_text(str(val))
    return length, color


# ----------------------------------------------------------
# SYNC PRINCIPALE
# ----------------------------------------------------------

def sync_wix_to_luxura() -> Dict[str, Any]:
    """
    Synchro complète Wix → Luxura.

    - Produits :
        * produits "simples" → 1 Product
        * produits avec variantes → 1 Product par variante (utile pour les extensions)
    - Inventaire :
        * on synchronise l'inventaire Wix sur le salon "Luxura Online"
    """
    print("[WIX SYNC] Début synchro Wix → Luxura")

    created_products = 0
    updated_products = 0

    with Session(engine) as session:
        # ---------- 1) Créer / récupérer le salon central "Luxura Online" ----------
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

        # ---------- 2) Synchroniser les PRODUITS ----------
        wix_products = wix_fetch_products()

        for wp in wix_products:
            base_sku = wp.get("sku") or "NO-SKU"
            name = _clean_text(wp.get("name") or "Sans nom") or "Sans nom"
            desc = wp.get("description") or ""
            price_raw = (
                wp.get("priceData", {}).get("price")
                or wp.get("price", 0)
                or 0
            )

            try:
                base_price = float(price_raw)
            except Exception:
                base_price = 0.0

            category = _guess_category_from_name(name)

            # Variantes (extensions, etc.)
            variants = (
                wp.get("variants")
                or wp.get("productVariants")
                or []
            )

            if variants:
                # ----- Produit AVEC variantes : on crée un Product par variante -----
                for v in variants:
                    v_sku = v.get("sku") or None
                    choices = v.get("choices") or {}
                    length, color = _extract_length_color_from_choices(choices)

                    if not v_sku:
                        v_sku = _build_variant_sku(base_sku, name, length, color)

                    v_price_raw = (
                        v.get("priceData", {}).get("price", base_price)
                        or base_price
                    )
                    try:
                        v_price = float(v_price_raw)
                    except Exception:
                        v_price = base_price

                    db_product = session.exec(
                        select(Product).where(Product.sku == v_sku)
                    ).first()

                    if not db_product:
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
                # ----- Produit SANS variantes : shampoings, brosses, etc. -----
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

        # ---------- 3) Synchroniser l'INVENTAIRE sur "Luxura Online" ----------
        wix_stock = wix_fetch_inventory()
        for item in wix_stock:
            sku = item.get("sku")
            if not sku:
                continue

            quantity = item.get("quantity", 0) or 0
            try:
                quantity = int(quantity)
            except Exception:
                quantity = 0

            product = session.exec(
                select(Product).where(Product.sku == sku)
            ).first()
            if not product:
                # Il peut s'agir d'un SKU qu'on n'a pas créé (ou d'une variante spéciale)
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
