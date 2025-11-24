import os
import sys
import time
import requests

# ─────────────────────────────────────────
# CONFIG VIA VARIABLES D'ENVIRONNEMENT
# ─────────────────────────────────────────

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")
LUXURA_API_BASE = os.getenv("LUXURA_API_BASE", "https://luxura-inventory-api.onrender.com")
LUXURA_SALON_ID = os.getenv("LUXURA_SALON_ID")  # ex: "3" (Luxura Online)

if not WIX_API_KEY:
    print("❌ WIX_API_KEY manquant dans les variables d'environnement", file=sys.stderr)
    sys.exit(1)

if not WIX_SITE_ID:
    print("❌ WIX_SITE_ID manquant dans les variables d'environnement", file=sys.stderr)
    sys.exit(1)

if not LUXURA_SALON_ID:
    print("❌ LUXURA_SALON_ID manquant dans les variables d'environnement", file=sys.stderr)
    sys.exit(1)

try:
    LUXURA_SALON_ID = int(LUXURA_SALON_ID)
except ValueError:
    print("❌ LUXURA_SALON_ID doit être un entier", file=sys.stderr)
    sys.exit(1)


def wix_headers() -> dict:
    """
    Headers corrects pour les appels REST avec API KEY (mode Admin).
    """
    return {
        "Authorization": WIX_API_KEY,      # API key brute, PAS 'Bearer ...'
        "wix-site-id": WIX_SITE_ID,        # très important pour les appels site-level
        "Content-Type": "application/json",
    }


# ─────────────────────────────────────────
# 1) Récupérer les produits Wix
# ─────────────────────────────────────────

def fetch_wix_products() -> list[dict]:
    """
    Appelle l'API officielle 'Query Products' (stores-reader/v1/products/query).
    Retourne une liste de produits Wix.
    """
    print("🔄 Téléchargement produits Wix…")

    url = "https://www.wixapis.com/stores-reader/v1/products/query"

    body = {
        # on peut ajuster plus tard (filtre, paging, etc.)
        "paging": {"limit": 100},
        "includeVariants": True,
    }

    resp = requests.post(url, headers=wix_headers(), json=body, timeout=30)

    # Log simple
    print(f"   → Status Wix: {resp.status_code}")
    if resp.status_code != 200:
        print(f"   → Réponse brute Wix: {resp.text[:500]}")
        if resp.status_code == 403 and "WIX_STORES.READ_PRODUCTS" in resp.text:
            print("❌ Erreur API Wix 403 : la clé n'a pas la permission 'Read Products' (Boutique Wix).")
            print("   ➜ Va dans 'Clés API' et vérifie que 'Boutique Wix' est bien coché pour cette clé.")
        resp.raise_for_status()

    data = resp.json()
    products = data.get("products", [])
    print(f"✅ Produits Wix récupérés : {len(products)}")
    return products


# ─────────────────────────────────────────
# 2) Récupérer les produits Luxura (API interne)
# ─────────────────────────────────────────

def fetch_luxura_products() -> list[dict]:
    url = f"{LUXURA_API_BASE}/products/"
    print("🔄 Téléchargement produits Luxura…")
    resp = requests.get(url, timeout=30)
    print(f"   → Status Luxura: {resp.status_code}")
    resp.raise_for_status()
    products = resp.json()
    print(f"✅ Produits Luxura récupérés : {len(products)}")
    return products


# ─────────────────────────────────────────
# 3) Exemple de mapping SKU → produit Luxura
# ─────────────────────────────────────────

def index_luxura_products_by_sku(products: list[dict]) -> dict[str, dict]:
    """
    Construit un index {sku -> produit Luxura}.
    """
    index: dict[str, dict] = {}
    for p in products:
        sku = p.get("sku")
        if sku:
            index[sku] = p
    print(f"ℹ️ Index Luxura par SKU : {len(index)} entrées")
    return index


# ─────────────────────────────────────────
# 4) Création / mise à jour des produits dans Luxura
# (pour l'instant on se contente de logguer, tu pourras
#  raffiner la logique selon ta stratégie d'inventaire)
# ─────────────────────────────────────────

def sync_wix_to_luxura():
    wix_products = fetch_wix_products()
    luxura_products = fetch_luxura_products()
    luxura_by_sku = index_luxura_products_by_sku(luxura_products)

    created = 0
    updated = 0
    ignored = 0

    for wp in wix_products:
        sku = wp.get("sku")
        name = wp.get("name")
        price = (wp.get("priceData") or {}).get("price") or 0.0

        if not sku:
            ignored += 1
            continue

        existing = luxura_by_sku.get(sku)

        if existing is None:
            # Création produit Luxura
            payload = {
                "sku": sku,
                "name": name or sku,
                "price": float(price),
                "category": None,
                "description": (wp.get("description") or "")[:500],
                "length": None,
                "color": None,
                "active": True,
            }
            print(f"➕ Création produit Luxura pour SKU {sku}…")
            resp = requests.post(
                f"{LUXURA_API_BASE}/products/",
                json=payload,
                timeout=30,
            )
            if resp.status_code not in (200, 201):
                print(f"   ⚠️ Erreur création produit Luxura {sku}: {resp.status_code} {resp.text[:200]}")
            else:
                created += 1
        else:
            # Mise à jour minimale (nom / prix)
            pid = existing["id"]
            payload = {
                "name": name or existing["name"],
                "price": float(price) or existing["price"],
            }
            print(f"♻️ Mise à jour produit Luxura {sku} (ID {pid})…")
            resp = requests.put(
                f"{LUXURA_API_BASE}/products/{pid}",
                json=payload,
                timeout=30,
            )
            if resp.status_code not in (200, 201):
                print(f"   ⚠️ Erreur update produit Luxura {sku}: {resp.status_code} {resp.text[:200]}")
            else:
                updated += 1

    print("✅ SYNC TERMINÉE")
    print(f"   Créés      : {created}")
    print(f"   Mises à jour : {updated}")
    print(f"   Ignorés    : {ignored}")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    start = time.time()
    try:
        sync_wix_to_luxura()
    except Exception as e:
        print(f"💥 Erreur fatale pendant la sync : {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        duration = time.time() - start
        print(f"⏱ Durée totale : {duration:.1f} s")
