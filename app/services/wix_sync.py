# app/services/wix_sync.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from sqlmodel import Session, select

from app.db import engine
from app.models import Product


WIX_BASE_URL = "https://www.wixapis.com"
WIX_API_KEY = os.getenv("WIX_API_KEY", "").strip()
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "").strip()


# ------------------------------------------------------------
# Helpers Wix
# ------------------------------------------------------------
def _wix_headers() -> Dict[str, str]:
    """
    Headers communs pour appeler l’API Wix.
    Nécessite WIX_API_KEY et WIX_SITE_ID dans les variables d’environnement.
    """
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
    }

    if WIX_API_KEY:
        headers["Authorization"] = f"Bearer {WIX_API_KEY}"

    if WIX_SITE_ID:
        headers["wix-site-id"] = WIX_SITE_ID

    return headers


def _extract_length_color_from_options(options: Any) -> tuple[Optional[str], Optional[str]]:
    """
    Essaie de deviner 'longueur' et 'couleur' à partir des options/choices Wix.
    Ça couvre plusieurs structures possibles (dict ou list de dicts).
    """
    length: Optional[str] = None
    color: Optional[str] = None

    if isinstance(options, dict):
        for k, v in options.items():
            key = str(k).lower()
            val = str(v)
            if "longueur" in key or "length" in key:
                length = val
            if "couleur" in key or "color" in key:
                color = val

    elif isinstance(options, list):
        for opt in options:
            if not isinstance(opt, dict):
                continue
            name = str(
                opt.get("name")
                or opt.get("optionType")
                or opt.get("title")
                or ""
            ).lower()
            value = str(
                opt.get("value")
                or opt.get("choice")
                or opt.get("option")
                or opt.get("description")
                or ""
            )
            if "longueur" in name or "length" in name:
                length = value
            if "couleur" in name or "color" in name:
                color = value

    return length, color


def _normalize_price(value: Any) -> float:
    """
    Convertit un champ price quelconque en float.
    Si ça ne marche pas → 0.0
    """
    if value is None:
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _fetch_all_wix_products_v1() -> List[Dict[str, Any]]:
    """
    Récupère tous les produits Wix (avec variantes) via /stores/v1/products/query
    en paginant si nécessaire.
    """
    url = f"{WIX_BASE_URL}/stores/v1/products/query"
    headers = _wix_headers()

    products: List[Dict[str, Any]] = []

    payload: Dict[str, Any] = {
        "query": {},  # pas de filtre : on veut tout
    }

    cursor: Optional[str] = None

    while True:
        body = dict(payload)
        if cursor:
            body["cursorPaging"] = {"cursor": cursor}

        resp = requests.post(url, headers=headers, json=body, timeout=30)

        try:
            resp.raise_for_status()
        except Exception as e:
            print("[WIX SYNC] ERREUR HTTP sur /stores/v1/products/query :", e)
            print("[WIX SYNC] Réponse brute (début) :")
            print(resp.text[:500])
            raise

        data = resp.json()
        # v1 : normalement "products"
        batch = data.get("products") or data.get("items") or []
        products.extend(batch)

        cursor = (
            data.get("nextCursor")
            or data.get("paging", {}).get("nextPageToken")
            or None
        )
        if not cursor:
            break

    print(f"[WIX SYNC] Produits reçus depuis Wix (v1) : {len(products)}")
    return products


# ------------------------------------------------------------
# Helpers DB : upsert produit
# ------------------------------------------------------------
def _upsert_product(
    session: Session,
    *,
    sku: str,
    name: str,
    length: Optional[str],
    color: Optional[str],
    category: Optional[str],
    description: Optional[str],
    price: float,
    active: bool,
) -> str:
    """
    Upsert d’un produit basé sur le SKU.
    Retourne "created" ou "updated".
    """
    existing: Optional[Product] = session.exec(
        select(Product).where(Product.sku == sku)
    ).first()

    if existing:
        existing.name = name
        existing.length = length
        existing.color = color
        existing.category = category
        existing.description = description
        existing.price = price
        existing.active = active
        session.add(existing)
        return "updated"

    obj = Product(
        sku=sku,
        name=name,
        length=length,
        color=color,
        category=category,
        description=description,
        price=price,
        active=active,
    )
    session.add(obj)
    return "created"


def _sync_products_from_wix(session: Session, wix_products: List[Dict[str, Any]]) -> tuple[int, int]:
    """
    Synchronise les produits Wix vers la table Product.

    Règles :
      - S’il y a des variantes → 1 ligne Product par variante (SKU de la variante ou fallback).
      - S’il n’y a PAS de variantes :
          → 1 ligne Product pour le produit lui-même.
      - Si aucun SKU n’est fourni (produit ou variante) :
          → on génère un SKU stable de type 'NO-SKU::<idWix>'.
    """
    created = 0
    updated = 0

    for p in wix_products:
        name = p.get("name") or "Sans nom"
        product_sku_raw = (p.get("sku") or "").strip() or None
        description = p.get("description") or None
        visible = p.get("visible")
        active = True if visible is None else bool(visible)

        # prix de base produit
        price_data = p.get("priceData") or {}
        base_price = _normalize_price(price_data.get("price") or p.get("price"))

        # options produit (utiles pour longueur / couleur)
        product_options = p.get("productOptions") or []

        # id Wix du produit (pour fabriquer un SKU stable si besoin)
        wix_id = p.get("id") or p.get("_id") or p.get("legacyId") or name.replace(" ", "-")
        wix_id_str = str(wix_id)

        variants = p.get("variants") or p.get("productVariants") or []

        # ─────────────────────────────────────────
        # CAS 1 : le produit a des variantes
        # ─────────────────────────────────────────
        if variants:
            for idx, v in enumerate(variants):
                # SKU de la variante ou fallback
                raw_sku = (v.get("sku") or product_sku_raw or "").strip()

                if not raw_sku:
                    # SKU synthétique mais stable
                    var_id = v.get("id") or v.get("_id") or f"var-{idx+1}"
                    raw_sku = f"NO-SKU::{wix_id_str}::{var_id}"

                sku = raw_sku

                # prix de la variante ou prix produit
                v_price_data = v.get("priceData") or {}
                v_price = _normalize_price(
                    v_price_data.get("price") or v.get("price") or base_price
                )

                # options de la variante (choices / options)
                var_opts = v.get("choices") or v.get("options") or {}
                length, color = _extract_length_color_from_options(var_opts)

                # si pas trouvé sur la variante, on tente les options produit
                if not length and not color and product_options:
                    length, color = _extract_length_color_from_options(product_options)

                category = str(p.get("productType") or "Wix")

                status = _upsert_product(
                    session,
                    sku=sku,
                    name=name,
                    length=length,
                    color=color,
                    category=category,
                    description=description,
                    price=v_price,
                    active=active,
                )
                if status == "created":
                    created += 1
                else:
                    updated += 1

        # ─────────────────────────────────────────
        # CAS 2 : AUCUNE variante → 1 ligne produit
        # ─────────────────────────────────────────
        else:
            raw_sku = (product_sku_raw or "").strip()
            if not raw_sku:
                # Avant : on ignorait ces produits.
                # Maintenant : on leur donne un SKU synthétique.
                raw_sku = f"NO-SKU::{wix_id_str}"
                print(
                    f"[WIX SYNC] Produit sans SKU ni variantes : '{name}' → "
                    f"créé avec SKU synthétique '{raw_sku}'."
                )

            sku = raw_sku
            length, color = _extract_length_color_from_options(product_options)
            category = str(p.get("productType") or "Wix")

            status = _upsert_product(
                session,
                sku=sku,
                name=name,
                length=length,
                color=color,
                category=category,
                description=description,
                price=base_price,
                active=active,
            )
            if status == "created":
                created += 1
            else:
                updated += 1

    return created, updated


# ------------------------------------------------------------
# Fonction principale appelée par /wix/sync et au startup
# ------------------------------------------------------------
def sync_wix_to_luxura(source: str = "startup") -> Dict[str, Any]:
    """
    Synchro complète Wix → Luxura (produits pour l’instant).

    - Appelée au démarrage (source="startup")
    - Appelée par POST /wix/sync (source="manual")
    """
    print("[WIX SYNC] Début synchro Wix → Luxura")

    summary: Dict[str, Any] = {
        "ok": False,
        "source": source,
        "created_products": 0,
        "updated_products": 0,
        "created_salons": 0,
        "updated_salons": 0,
    }

    if not WIX_API_KEY or not WIX_SITE_ID:
        print("[WIX SYNC] WIX_API_KEY ou WIX_SITE_ID manquant → synchro ignorée.")
        return summary

    try:
        wix_products = _fetch_all_wix_products_v1()

        with Session(engine) as session:
            created, updated = _sync_products_from_wix(session, wix_products)
            session.commit()

        summary["ok"] = True
        summary["created_products"] = created
        summary["updated_products"] = updated

        print(
            f"[WIX SYNC] Terminé : "
            f"{{'ok': True, 'source': '{source}', "
            f"'created_products': {created}, 'updated_products': {updated}, "
            f"'created_salons': 0, 'updated_salons': 0}}"
        )
        return summary

    except Exception as e:
        print("[WIX SYNC] ERREUR pendant la synchro :", repr(e))
        print("[STARTUP] Synchro Wix → Luxura : ÉCHEC (API quand même opérationnelle)")
        return summary
