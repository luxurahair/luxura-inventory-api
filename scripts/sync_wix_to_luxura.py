import os
import requests
from time import perf_counter

def sync_wix_products():
    print("🔄 Téléchargement produits Wix…")
    t0 = perf_counter()

    api_key = os.environ.get("WIX_API_KEY")
    site_id = os.environ.get("WIX_SITE_ID")

    if not api_key:
        print("❌ WIX_API_KEY manquant")
        return
    if not site_id:
        print("❌ WIX_SITE_ID manquant")
        return

    # ✔️ URL officielle pour l’API produits Wix Stores
    url = "https://www.wixapis.com/stores/v1/products/query"

    # ✔️ Headers obligatoires
    headers = {
        "Authorization": api_key,
        "wix-site-id": site_id,
        "Content-Type": "application/json"
    }

    # ✔️ Filtre vide = retourne tous les produits
    body = {
        "query": {}
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
    except Exception as e:
        print("❌ Erreur réseau :", str(e))
        return

    print(f"   → Status Wix: {resp.status_code}")
    print("   → Réponse brute Wix:", resp.text[:500])

    if resp.status_code != 200:
        print("⚠️  Wix renvoie une erreur, sync annulée.")
        return

    data = resp.json()

    # Wix varie : parfois "products", parfois "items"
    items = data.get("products") or data.get("items") or []

    print(f"✅ Produits reçus depuis Wix : {len(items)}")

    # 👉 Ici : tu continues ton insertion en base Supabase
    # Exemple :
    # for item in items:
    #     create_or_update_product(item)

    print(f"⏱ Durée totale : {perf_counter() - t0:.1f} s")

