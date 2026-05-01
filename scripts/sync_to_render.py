#!/usr/bin/env python3
"""
🚀 SYNC TO RENDER - Push rapide des variables vers Render
=========================================================

Usage:
    python scripts/sync_to_render.py
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import dotenv_values

SECRETS_FILE = Path(__file__).parent.parent / ".secrets.env"

# Variables à synchroniser vers Render
RENDER_VARS = [
    "DATABASE_URL",
    "WIX_API_KEY",
    "WIX_SITE_ID",
    "WIX_INSTANCE_ID",
    "WIX_ACCOUNT_ID",
    "WIX_CLIENT_ID",
    "WIX_CLIENT_SECRET",
    "WIX_OAUTH_SCOPES",
    "WIX_REDIRECT_URL",
    "WIX_PUSH_SECRET",
    "SEO_SECRET",
    "OPENAI_API_KEY",
    "EMERGENT_LLM_KEY",
    "FB_PAGE_ID",
    "FB_PAGE_ACCESS_TOKEN",
    "FAL_KEY",
    "LUXURA_EMAIL",
    "LUXURA_APP_PASSWORD",
    "EMAIL_USERNAME",
    "EMAIL_PASSWORD",
    "IMAP_HOST",
    "IMAP_PORT",
    "GOOGLE_DRIVE_FOLDER_ID",
    "LUXURA_SALON_ID",
    "GITHUB_TOKEN",
    "XAI_API_KEY",  # Grok
]


def main():
    if not SECRETS_FILE.exists():
        print(f"❌ {SECRETS_FILE} non trouvé")
        sys.exit(1)
    
    secrets = dotenv_values(SECRETS_FILE)
    api_key = secrets.get("RENDER_API_KEY")
    
    if not api_key:
        print("❌ RENDER_API_KEY requis")
        sys.exit(1)
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Trouver le service
    print("🔍 Recherche du service Luxura sur Render...")
    resp = requests.get("https://api.render.com/v1/services", headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ Erreur API: {resp.status_code}")
        sys.exit(1)
    
    services = resp.json()
    service_id = None
    service_name = None
    
    for svc in services:
        name = svc.get("service", {}).get("name", "")
        if "luxura" in name.lower():
            service_id = svc.get("service", {}).get("id")
            service_name = name
            break
    
    if not service_id:
        print("❌ Service non trouvé")
        sys.exit(1)
    
    print(f"✅ Service: {service_name} ({service_id})")
    
    # Préparer les variables à envoyer
    env_vars = []
    for var in RENDER_VARS:
        if var in secrets and secrets[var]:
            env_vars.append({"key": var, "value": secrets[var]})
    
    print(f"\n📤 {len(env_vars)} variables à synchroniser:")
    for v in env_vars:
        print(f"   - {v['key']}")
    
    confirm = input("\n✅ Confirmer? (oui/non): ")
    if confirm.lower() != "oui":
        print("❌ Annulé")
        sys.exit(0)
    
    # Envoyer les variables
    headers["Content-Type"] = "application/json"
    
    for var in env_vars:
        resp = requests.put(
            f"https://api.render.com/v1/services/{service_id}/env-vars/{var['key']}",
            headers=headers,
            json={"value": var["value"]}
        )
        if resp.status_code in [200, 201]:
            print(f"   ✅ {var['key']}")
        else:
            # Essayer de créer si n'existe pas
            resp = requests.post(
                f"https://api.render.com/v1/services/{service_id}/env-vars",
                headers=headers,
                json={"key": var["key"], "value": var["value"]}
            )
            if resp.status_code in [200, 201]:
                print(f"   ✅ {var['key']} (créé)")
            else:
                print(f"   ❌ {var['key']} - {resp.status_code}")
    
    print("\n🎉 Synchronisation terminée!")
    print("💡 N'oubliez pas de redéployer le service sur Render")


if __name__ == "__main__":
    main()
