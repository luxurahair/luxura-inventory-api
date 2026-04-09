#!/usr/bin/env python3
"""
Cron Script v12 - Appel HTTP vers POST /wix/sync
- Plus de logique DB directe
- Utilise la route moderne qui gère tout
- Requiert SEO_SECRET
"""
import os
import sys
import requests

API_URL = (os.getenv("API_URL") or "https://luxura-inventory-api.onrender.com").rstrip("/")
SEO_SECRET = (os.getenv("SEO_SECRET") or "").strip()


def main():
    if not SEO_SECRET:
        print("[CRON] ❌ SEO_SECRET manquant dans les variables d'environnement")
        print("[CRON] Ajoutez SEO_SECRET dans Render Environment Variables")
        sys.exit(1)

    url = f"{API_URL}/wix/sync"
    headers = {
        "X-SEO-SECRET": SEO_SECRET,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    params = {
        "limit": 500,
        "dry_run": "false",
    }

    print(f"[CRON] Appel de {url}...")
    print(f"[CRON] SEO_SECRET configuré: {'✅ Oui' if SEO_SECRET else '❌ Non'}")

    try:
        resp = requests.post(url, headers=headers, params=params, timeout=300)

        if resp.status_code >= 400:
            print(f"[CRON] ❌ Erreur HTTP {resp.status_code}")
            print(resp.text[:2000])
            sys.exit(1)

        data = resp.json()
        print("[CRON] ✅ Sync terminé avec succès!")
        print(f"   - Créés: {data.get('created', 0)}")
        print(f"   - Mis à jour: {data.get('updated', 0)}")
        print(f"   - Fusionnés: {data.get('merged', 0)}")
        print(f"   - Ignorés (sans SKU): {data.get('skipped_no_sku', 0)}")
        print(f"   - Inventaire écrit: {data.get('inventory_written_entrepot', 0)}")
        print(f"   - Parents traités: {data.get('parents_processed', 0)}")
        print(f"   - Variants vus: {data.get('variants_seen', 0)}")

    except requests.exceptions.Timeout:
        print("[CRON] ❌ Timeout (5 min dépassées)")
        sys.exit(1)
    except Exception as e:
        print(f"[CRON] ❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
