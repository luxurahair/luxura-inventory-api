# app/services/wix_sync.py

import os
from typing import Any, Dict, List, Optional

import requests
from sqlmodel import Session, select

from app.db import engine
from app import models


# -------------------------------------------------------------------
#  Config Wix
# -------------------------------------------------------------------

WIX_BASE_URL = "https://www.wixapis.com"


def _wix_headers() -> Dict[str, str]:
    """
    Construit les en-têtes pour appeler l’API Wix Catalog.
    On utilise :
      - WIX_API_KEY  (token backend)
      - WIX_SITE_ID  (id du site)
    """
    api_key = os.getenv("WIX_API_KEY")
    site_id = os.getenv("WIX_SITE_ID")

    if not api_key:
        raise RuntimeError("WIX_API_KEY manquant dans les variables d’environnement.")
    if not site_id:
        raise RuntimeError("WIX_SITE_ID manquant dans les variables d’environnement.")

    if not api_key.startswith("Bearer "):
        api_key = f"Bearer {api_key}"

    return {
        "Authorization": api_key,
        "wix-site-id": site_id,
        "Content-Type": "application/json",
    }


# -------------------------------------------------------------------
#  Récupération des items Catalog (avec variantes)
# -------------------------------------------------------------------

def _fetch_all_catalog_items() -> List[Dict[str, Any]]:
    """
    Récupère tous les items Catalog (avec variantes) via
    POST https://www.wixapis.com/catalog/v1/items/query
    avec pagination si nécessaire.
    """
    url = f"{WIX_BASE_URL}/catalog/v1/items/query"
    headers = _wix_headers()

    items: List[Dict[str, Any]] = []
    cursor: Optional[str] = None

    while True:
        body: Dict[str, Any] = {"query": {}}
        if cursor:
            body["cursorPaging"] = {"cursor": cursor}

        resp = requests.post(url, headers=headers, json=body, timeout=30)

        try:
            resp.raise_for_status()
        except Exception as e:
            print("[WIX SYNC] ERREUR HTTP sur /catalog/v1/items/query :", repr(e))
            print("[WIX SYNC] Réponse brute (début) :")
            print(resp.text[:500])
            raise

        data = resp.json()

        # Normalement c’est "items"
        batch = data.get("items") or data.get("products") or []
        items.extend(batch)

        # Pagination : plusieurs conventions possibles, on les teste.
        cursor = (
            data.get("nextCursor")
            or data.get("paging", {}).get("nextCursor")
            or data.get("cursorPaging", {}).get("nextCursor")
        )

        if not cursor:
            break

    print(f"[WIX SYNC] Items reçus depuis Wix Catalog : {len(items)}")
    return items


# -------------------------------------------------------------------
#  Upsert Product (dans ta DB Luxura)
# -------------------------------------------------------------------

def _upsert_product(
    session: Session,
    *,
    sku: str,
    name: str,
    length: Optional[str],
    color: Optional[str],
    price: float,
    category: Optional[str],
    active: bool = True,
) -> bool:
    """
    Crée ou met à jour un Product.
    Retourne True si créé, False si mis à jour.
    """
    existing = session.exec(
        select(models.Product).where(models.Product.sku == sku)
    ).first()

    if existing:
        # Mise à jour minimale
        existing.name = name
        existing.length = length
        existing.color = color
        existing.category = category
        existing.price = price
        existing.active = active
        return False

    product = models.Product(
        sku=sku,
        name=name,
        length=length,
        color=color,
        category=category or "Wix Catalog",
        description=None,
        price=price,
        active=active,
    )
    session.add(product)
    return True


def _extract_length_color_from_choices(choices: Dict[str, Any]) -> (Optional[str], Optional[str]):
    """
    Essaie de deviner length / color à partir des "choices" de variante.
    Ex. {"Longueur": "18\" 60 grammes"} -> length = "18\" 60 grammes"
    """
    length: Optional[str] = None
    color: Optional[str] = None

    if not isinstance(choices, dict):
        return None, None

    # Si l’API nous donne des clés du style "Length", "Longueur", "Couleur", "Color"
    for key, value in choices.items():
        key_l = str(key).lower()
        val_s = str(value)

        if "longueur" in key_l or "length" in key_l:
            length = val_s
        elif "couleur" in key_l or "color" in key_l:
            color = val_s

    # Si on n’a qu’un seul choix et rien mis, on met tout en "length"
    if length is None and color is None and len(choices) == 1:
        only_val = list(choices.values())[0]
        length = str(only_val)

    return length, color


# -------------------------------------------------------------------
#  Synchro principale Wix → Luxura
# -------------------------------------------------------------------

def sync_wix_to_luxura(source: str = "manual") -> Dict[str, Any]:
    """
    Synchro complète Wix Catalog → DB Luxura.
    - Import des produits + variantes dans la table products.
    - Salons / inventaire : à brancher plus tard au besoin.

    `source` est juste un label ("startup" ou "manual") pour les logs.
    """
    print("[WIX SYNC] Début synchro Wix → Luxura")

    created_products = 0
    updated_products = 0
    created_salons = 0  # pour l’instant : 0
    updated_salons = 0  # pour l’instant : 0

    try:
        items = _fetch_all_catalog_items()
    except Exception as e:
        # On log, mais on n’empêche pas l’API de fonctionner.
        print("[WIX SYNC] ERREUR pendant la récupération Catalog :", repr(e))
        summary_err = {
            "ok": False,
            "source": source,
            "created_products": 0,
            "updated_products": 0,
            "created_salons": 0,
            "updated_salons": 0,
        }
        print(f"[WIX SYNC] Terminé (erreur) : {summary_err}")
        return summary_err

    with Session(engine) as session:
        for item in items:
            item_name = item.get("name") or item.get("productName") or "Sans nom"
            category = "Wix Catalog"

            price_data = item.get("priceData") or {}
            base_price_raw = price_data.get("price") or 0
            try:
                base_price = float(base_price_raw)
            except (TypeError, ValueError):
                base_price = 0.0

            variants = item.get("variants") or []

            # Cas 1 : pas de variante → on utilise le SKU de l’item (si présent)
            if not variants:
                sku_item = item.get("sku") or ""
                if not sku_item:
                    # On ignore les items sans aucun SKU exploitable.
                    print(
                        f"[WIX SYNC] Item Catalog sans SKU ni variantes : "
                        f"'{item_name}' → ignoré."
                    )
                    continue

                created = _upsert_product(
                    session,
                    sku=sku_item,
                    name=item_name,
                    length=None,
                    color=None,
                    price=base_price,
                    category=category,
                )
                if created:
                    created_products += 1
                else:
                    updated_products += 1
                continue

            # Cas 2 : item avec variantes (cas de tes extensions / longueurs)
            for variant in variants:
                sku_variant = (
                    variant.get("sku")
                    or variant.get("variantSku")
                    or ""
                )
                if not sku_variant:
                    print(
                        f"[WIX SYNC] Variante sans SKU pour '{item_name}' → ignorée."
                    )
                    continue

                v_price_data = variant.get("priceData") or {}
                v_price_raw = v_price_data.get("price", base_price)
                try:
                    v_price = float(v_price_raw)
                except (TypeError, ValueError):
                    v_price = base_price

                choices = variant.get("choices") or {}
                length, color = _extract_length_color_from_choices(choices)

                active = bool(variant.get("visible", True))

                created = _upsert_product(
                    session,
                    sku=sku_variant,
                    name=item_name,
                    length=length,
                    color=color,
                    price=v_price,
                    category=category,
                    active=active,
                )
                if created:
                    created_products += 1
                else:
                    updated_products += 1

        session.commit()

    summary_ok = {
        "ok": True,
        "source": source,
        "created_products": created_products,
        "updated_products": updated_products,
        "created_salons": created_salons,
        "updated_salons": updated_salons,
    }
    print(f"[WIX SYNC] Terminé : {summary_ok}")
    return summary_ok
