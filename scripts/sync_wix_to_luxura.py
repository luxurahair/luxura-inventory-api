import os
import time
import requests

# ─────────────────────────────────────────
# Variables d’environnement Render
# ─────────────────────────────────────────
WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")
LUXURA_API_BASE = os.getenv("LUXURA_API_BASE", "https://luxura-inventory-api.onrender.com")
LUXURA_SALON_ID = int(os.getenv("LUXURA_SALON_ID", "3"))

if not WIX_API_KEY or not WIX_SITE_ID:
    print("❌ ERREUR : variables d’environnement WIX_API_KEY ou WIX_SITE_ID manquantes.")
    exit(1)

WIX_HEADERS = {
    "Authorization": WIX_API_KEY,
    "wix-site-id": WIX_SITE_ID,
    "Content-Type": "application/json",
}

# ─────────────────────────────────────────
# 1. RÉCUPÉRER LES PRODUITS WIX
# ─────────────────────────────────────────
def fetch_wix_products():
    url = "https://www.wixapis.com/stores/v1/products/query"
    items = []
    limit = 100
    offset = 0

    while True:
        payload = {
            "includeVariants": True,
            "paging": { "limit": limit, "offset": offset }
        }
        resp = requests.post(url, headers=WIX_HEADERS, json=payload)
        if resp.status_code != 200:
            print("❌ Erreur API Wix:", resp.status_code, resp.text)
            break

        data = resp.json()
        batch = data.get("items") or data.get("products") or []
        items.extend(batch)

        if len(batch) < limit:
            break
        offset += limit
        time.sleep(0.1)

    return items


def wix_sku_quantities(products):
    sku_qty = {}

    for p in products:
        if not p.get("manageVariants", False):
            sku = (p.get("sku") or "").strip()
            stock = p.get("stock") or {}
            q = stock.get("quantity")
            if sku and isinstance(q, int):
                sku_qty[sku] = q
            continue

        for v in p.get("variants", []):
            sku = (v.get("sku") or "").strip()
            stock = v.get("stock") or {}
            q = stock.get("quantity")
            if sku and isinstance(q, int):
                sku_qty[sku] = q
    
    return sku_qty


# ─────────────────────────────────────────
# 2. RÉCUPÉRER PRODUITS LUXURA
# ─────────────────────────────────────────
def fetch_luxura_products():
    resp = requests.get(f"{LUXURA_API_BASE}/products/")
    if resp.status_code != 200:
        print("❌ Erreur Luxura API /products:", resp.text)
        exit(1)
    return resp.json()


# ─────────────────────────────────────────
# 3. GESTION INVENTAIRE LUXURA
# ─────────────────────────────────────────
def inventory_get(salon_id, product_id):
    resp = requests.get(f"{LUXURA_API_BASE}/inventory/", params={
        "salon_id": salon_id,
        "product_id": product_id
    })
    if resp.status_code != 200:
        return []
    return resp.json()


def inventory_create(salon_id, product_id, quantity):
    resp = requests.post(f"{LUXURA_API_BASE}/inventory/", json={
        "salon_id": salon_id,
        "product_id": product_id,
        "quantity": quantity
    })
    return resp.json()


def inventory_update(item_id, quantity):
    resp = requests.put(f"{LUXURA_API_BASE}/inventory/{item_id}", json={
        "quantity": quantity
    })
    return resp.json()


# ─────────────────────────────────────────
# 4. SYNC PRINCIPALE
# ─────────────────────────────────────────
def sync_inventory():
    print("🔄 Téléchargement produits Wix…")
    wix_products = fetch_wix_products()

    print("🔄 Extraction SKUs Wix…")
    wix_skus = wix_sku_quantities(wix_products)

    print("🔄 Téléchargement produits Luxura…")
    lux_products = fetch_luxura_products()
    lux_map = { p["sku"]: p["id"] for p in lux_products }

    created, updated, skipped = 0, 0, 0

    for sku, qty in wix_skus.items():
        if sku not in lux_map:
            print(f"⚠️ SKU Wix inconnu dans Luxura: {sku}")
            skipped += 1
            continue

        product_id = lux_map[sku]
        existing = inventory_get(LUXURA_SALON_ID, product_id)

        if not existing:
            print(f"➕ Création inventaire {sku} = {qty}")
            inventory_create(LUXURA_SALON_ID, product_id, qty)
            created += 1
            continue

        item = existing[0]
        if item["quantity"] != qty:
            print(f"✏️ MAJ {sku}: {item['quantity']} → {qty}")
            inventory_update(item["id"], qty)
            updated += 1

    print("\n✅ SYNC TERMINÉE")
    print(f"Créés : {created}")
    print(f"Mises à jour : {updated}")
    print(f"Ignorés : {skipped}")


if __name__ == "__main__":
    sync_inventory()

