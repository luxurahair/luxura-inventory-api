#!/usr/bin/env python3
"""
Cron Script: Appelle POST /wix/sync qui a la logique intelligente:
- Lookup par wix_variant_id, puis sku
- Merge anti-doublon SKU
- Gestion inventaire entrepôt
"""
import os
import sys
import requests

# Permet d'importer "app.*" si besoin
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def main():
    # URL de l'API Render (ou localhost en dev)
    api_url = os.getenv("API_URL", "https://luxura-inventory-api.onrender.com")
    seo_secret = os.getenv("SEO_SECRET", "")
    
    sync_endpoint = f"{api_url}/wix/sync"
    
    print(f"[CRON] Appel de {sync_endpoint}...")
    
    headers = {
        "Content-Type": "application/json",
        "x-seo-secret": seo_secret,
    }
    
    params = {
        "limit": 500,
        "dry_run": False,
    }
    
    try:
        resp = requests.post(
            sync_endpoint,
            headers=headers,
            params=params,
            timeout=300,  # 5 minutes max
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"[CRON] ✅ Sync réussi!")
            print(f"   - Créés: {data.get('created', 0)}")
            print(f"   - Mis à jour: {data.get('updated', 0)}")
            print(f"   - Fusionnés: {data.get('merged', 0)}")
            print(f"   - Sans SKU (ignorés): {data.get('skipped_no_sku', 0)}")
            print(f"   - Inventaire écrit: {data.get('inventory_written_entrepot', 0)}")
            print(f"   - Parents traités: {data.get('parents_processed', 0)}")
            print(f"   - Variantes vues: {data.get('variants_seen', 0)}")
        else:
            print(f"[CRON] ❌ Erreur HTTP {resp.status_code}")
            print(f"   {resp.text[:500]}")
            sys.exit(1)
            
    except requests.exceptions.Timeout:
        print("[CRON] ❌ Timeout (5 min dépassées)")
        sys.exit(1)
    except Exception as e:
        print(f"[CRON] ❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
