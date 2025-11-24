import os
import sys
import time
from typing import Dict, List, Any

import requests

# ─────────────────────────────────────────
# CONFIG VIA VARIABLES D'ENVIRONNEMENT
# ─────────────────────────────────────────

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")
LUXURA_API_BASE = os.getenv("LUXURA_API_BASE", "https://luxura-inventory-api.onrender.com")
LUXURA_SALON_ID = os.getenv("LUXURA_SALON_ID")  # pas encore utilisé, mais prêt pour l'inventaire


def _fatal(msg: str) -> None:
    print(f"❌ {msg}", file=sys.stderr, flush=True)


def _check_env() -> bool:
    ok = True
    if not WIX_API_KEY:
        _fatal("WIX_API_KEY manquant dans les variables d'environnement")
        ok = False
    if not WIX_SITE_ID:
        _fatal("WIX_SITE_ID manquant dans les variables d'environnement")
        ok = False
    if not LUXURA_API_BASE:
        _fatal("LUXURA_API_BASE manquant dans les variables d'environnement")
        ok = False
    if not LUXURA_SALON_ID:
        _fatal("LUXURA_SALON_ID manquant dans les variables d'environnement (id du salon 'Luxura Online')")
        ok = False
    return ok


def wix_headers() -> Dict[str, str]:
    """
    Headers pour l'API Wix avec API Key.
    ATTENTION: ici Wix attend l'API key brute dans Authorization, pas "Bearer ...".
    """
    return {
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json",
    }


# ─────────────────────────────────────────
# 1) Récupérer les produits Wix
# ─────────────────────────────────────────

WIX_PRODUCTS_URL = "https://www.wixapis.com/stores-reader/v1/products/query"


def fetch_wix_products() -> List[Dict[str, Any]]:
    """
    Récupère les produits depuis Wix Stores Reader.
    Si Wix renvoie une erreur 5xx, on log et on retourne une liste vide.
    """
    print("🔄 Téléchargement produits Wix…", flush=True)

    body = {
        "query": {},               # pas de filtre = tous les produits
        "paging": {"limit": 100},  # on pourra gérer la pagination plus tard si besoin
        "includeVariants": True,
    }

    try:
        resp = requests.post(
            WIX_PRODUCTS_URL,
            headers=wix_headers(),
            json=body,
            timeout=15,
        )
    except Exception as e:
        _fatal(f"Erreur réseau en appelant Wix: {e}")
        return []

    print(f"   → Status Wix: {resp.status_code}", flush=True)
    print(f"   → Réponse brute Wix: {resp.text[:400]}", flush=True)

    # Erreurs serveurs Wix (5xx)
    if 500 <= resp.status_code <= 599:
        print("⚠️  Wix renvoie une erreur serveur (5xx). Impossible de récupérer les produits pour l'instant.", flush=True)
        return []

    # Erreurs d'auth / permissions
    if resp.status_code == 403:
        if "WIX_STORES.READ_PRODUCTS" in resp.text:
            _fatal(
                "La clé API Wix n'a pas la permission 'Boutique Wix / Read Products'. "
                "Vérifie dans Paramètres du compte → Clés API que 'Boutique Wix' est bien cochée."
            )
        else:
            _fatal("403 Forbidden de Wix. Vérifie API key, site, et permissions.")
        return []

    if not resp.ok:
        _fatal(f"Erreur API Wix: {resp.status_code} {resp.text[:400]}")
        return []

    data = resp.json()
    # Selon la version, les produits peuvent être dans "items" ou "products"
    products = data.get("items") or data.get("products") or []
    print(f"✅ Produits Wix récupérés : {len(products)}", flush=True)
    return products


# ─────────────────────────────────────────
# 2) Récupérer les produits Luxura
# ─────────────────────────────────────────

def fetch_luxura_products() -> List[Dict[str, Any]]:
    url = f"{LUXURA_API_BASE}/products/"
    print("🔄 Téléchargement produits Luxura…", flush=True)

    try:
        resp = requests.get(url, timeout=15)
    except Exception as e:
        _fatal(f"Erreur réseau en appelant Luxura API /products/: {e}")
        return []

    print(f"   → Status Luxura: {resp.status_code}", flush=True)

    if not resp.ok:
        _fatal(f"Erreur API Luxura /products/: {resp.status_code} {resp.text[:400]}")
        return []

    try:
        products = resp.json()
    except Exception as e:
        _fatal(f"Impossible de parser la réponse JSON de Luxura /products/: {e}")
        return []

    print(f"✅ Produits Luxura récupérés : {len(products)}", flush=True)
    return products


def index_luxura_products_by_sku(products: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Construit un index {sku -> produit Luxura}.
    """
    index: Dict[str, Dict[str, Any]] = {}
    for p in products:
        sku = p.get("sku")
        if sku:
            index[sku] = p
    print(f"ℹ️ Index Luxura par SKU : {len(index)} entrées", flush=True)
    return index


# ─────────────────────────────────────────
# 3) Sync: Wix → Luxura (produits seulement)
# ─────────────────────────────────────────

def sync_wix_to_luxura() -> None:
    wix_products = fetch_wix_products()

    if not wix_products:
        print("⚠️ Aucun produit Wix récupéré. Sync interrompue gentiment.", flush=True)
        return

    luxura_products = fetch_luxura_products()
    luxura_by_sku = index_luxura_products_by_sku(luxura_products)

    created = 0
    updated = 0
    ignored = 0

    for wp in wix_products:
        sku = wp.get("sku")
        if not sku:
            ignored += 1
            continue

        name = wp.get("name") or sku
        price = 0.0
        price_data = wp.get("priceData") or {}
        if isinstance(price_data, dict):
            price = float(price_data.get("price") or 0.0)

        # On pourrait mapper length/color à partir de champs custom si tu les utilises.
        payload_base = {
            "sku": sku,
            "name": name,
            "price": price,
            "category": None,
            "description": (wp.get("description") or "")[:500],
            "length": None,
            "color": None,
            "active": True,
        }

        existing = luxura_by_sku.get(sku)

        if existing is None:
            # Création produit Luxura
            print(f"➕ Création produit Luxura pour SKU {sku}…", flush=True)
            resp = requests.post(
                f"{LUXURA_API_BASE}/products/",
                json=payload_base,
                timeout=15,
            )
            if not resp.ok:
                _fatal(f"   ⚠️ Erreur création produit Luxura {sku}: {resp.status_code} {resp.text[:200]}")
                ignored += 1
                continue
            created += 1
        else:
            # Mise à jour minimale (nom + prix)
            pid = existing.get("id")
            if not pid:
                ignored += 1
                continue

            payload_update = {
                "name": name,
                "price": price or existing.get("price") or 0.0,
            }
            print(f"♻️ Mise à jour produit Luxura {sku} (ID {pid})…", flush=True)
            resp = requests.put(
                f"{LUXURA_API_BASE}/products/{pid}",
                json=payload_update,
                timeout=15,
            )
            if not resp.ok:
                _fatal(f"   ⚠️ Erreur update produit Luxura {sku}: {resp.status_code} {resp.text[:200]}")
                ignored += 1
                continue
            updated += 1

    print("✅ SYNC PRODUITS TERMINÉE", flush=True)
    print(f"   Créés       : {created}", flush=True)
    print(f"   Mises à jour: {updated}", flush=True)
    print(f"   Ignorés     : {ignored}", flush=True)


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main() -> None:
    if not _check_env():
        print("⛔ Variables d'environnement incomplètes. Sync annulée.", flush=True)
        return

    start = time.time()
    try:
        sync_wix_to_luxura()
    except Exception as e:
        _fatal(f"💥 Erreur inattendue pendant la sync : {e}")
    finally:
        duration = time.time() - start
        print(f"⏱ Durée totale : {duration:.1f} s", flush=True)


if __name__ == "__main__":
    # Mode "une sync, puis exit" : parfait pour Render Background Worker
    main()
