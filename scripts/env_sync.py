#!/usr/bin/env python3
"""
🔐 LUXURA ENV SYNC - Synchronisation centralisée des variables d'environnement
=============================================================================

Ce script permet de :
1. Maintenir un fichier maître unique (.secrets.env)
2. Synchroniser automatiquement vers Render
3. Vérifier que toutes les variables sont présentes partout

Usage:
    python scripts/env_sync.py status     # Voir l'état des variables
    python scripts/env_sync.py sync       # Synchroniser vers Render
    python scripts/env_sync.py verify     # Vérifier la cohérence
    python scripts/env_sync.py export     # Exporter pour backup
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import dotenv_values

# Chemin vers le fichier maître
SECRETS_FILE = Path(__file__).parent.parent / ".secrets.env"
BACKUP_DIR = Path(__file__).parent.parent / "backups" / "env"

# Variables REQUISES pour chaque service
REQUIRED_VARS = {
    "supabase": ["DATABASE_URL", "SUPABASE_PROJECT_ID"],
    "wix": ["WIX_API_KEY", "WIX_SITE_ID", "WIX_CLIENT_ID", "WIX_CLIENT_SECRET"],
    "openai": ["OPENAI_API_KEY"],
    "facebook": ["FB_PAGE_ID", "FB_PAGE_ACCESS_TOKEN"],
    "email": ["LUXURA_EMAIL", "LUXURA_APP_PASSWORD"],
    "github": ["GITHUB_TOKEN"],
    "render": ["RENDER_API_KEY", "RENDER_SERVICE_URL"],
    "fal": ["FAL_KEY"],
}

# Variables à NE PAS synchroniser (sensibles ou spécifiques à l'environnement)
SKIP_SYNC = ["GOOGLE_SERVICE_ACCOUNT_JSON"]  # Trop long pour env vars standard


def load_secrets():
    """Charge les secrets depuis le fichier maître"""
    if not SECRETS_FILE.exists():
        print(f"❌ Fichier secrets non trouvé: {SECRETS_FILE}")
        sys.exit(1)
    return dotenv_values(SECRETS_FILE)


def get_render_env_vars():
    """Récupère les variables actuelles sur Render"""
    secrets = load_secrets()
    api_key = secrets.get("RENDER_API_KEY")
    
    if not api_key:
        print("❌ RENDER_API_KEY non trouvé dans .secrets.env")
        return None
    
    # Récupérer la liste des services
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # Lister les services
        resp = requests.get("https://api.render.com/v1/services", headers=headers)
        if resp.status_code != 200:
            print(f"❌ Erreur Render API: {resp.status_code}")
            return None
        
        services = resp.json()
        luxura_service = None
        
        for svc in services:
            if "luxura" in svc.get("service", {}).get("name", "").lower():
                luxura_service = svc.get("service", {})
                break
        
        if not luxura_service:
            print("❌ Service Luxura non trouvé sur Render")
            return None
        
        service_id = luxura_service.get("id")
        print(f"✅ Service trouvé: {luxura_service.get('name')} ({service_id})")
        
        # Récupérer les env vars
        resp = requests.get(f"https://api.render.com/v1/services/{service_id}/env-vars", headers=headers)
        if resp.status_code == 200:
            return {"service_id": service_id, "env_vars": resp.json()}
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    return None


def sync_to_render():
    """Synchronise les variables vers Render"""
    secrets = load_secrets()
    api_key = secrets.get("RENDER_API_KEY")
    
    if not api_key:
        print("❌ RENDER_API_KEY requis pour la synchronisation")
        return False
    
    render_data = get_render_env_vars()
    if not render_data:
        return False
    
    service_id = render_data["service_id"]
    current_vars = {v["envVar"]["key"]: v["envVar"]["value"] for v in render_data["env_vars"]}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    updates = []
    for key, value in secrets.items():
        if key in SKIP_SYNC:
            continue
        if key not in current_vars or current_vars[key] != value:
            updates.append({"key": key, "value": value})
    
    if not updates:
        print("✅ Toutes les variables sont déjà synchronisées!")
        return True
    
    print(f"\n📤 {len(updates)} variables à mettre à jour sur Render:")
    for u in updates:
        print(f"   - {u['key']}")
    
    confirm = input("\nConfirmer la synchronisation? (oui/non): ")
    if confirm.lower() != "oui":
        print("❌ Synchronisation annulée")
        return False
    
    # Mettre à jour chaque variable
    for update in updates:
        payload = [{"key": update["key"], "value": update["value"]}]
        resp = requests.put(
            f"https://api.render.com/v1/services/{service_id}/env-vars",
            headers=headers,
            json=payload
        )
        if resp.status_code in [200, 201]:
            print(f"   ✅ {update['key']}")
        else:
            print(f"   ❌ {update['key']} - Erreur {resp.status_code}")
    
    print("\n🔄 Redémarrage du service recommandé pour appliquer les changements")
    return True


def show_status():
    """Affiche l'état des variables"""
    secrets = load_secrets()
    
    print("\n" + "="*60)
    print("🔐 LUXURA ENV STATUS")
    print("="*60)
    
    for service, vars_list in REQUIRED_VARS.items():
        print(f"\n📦 {service.upper()}")
        for var in vars_list:
            value = secrets.get(var, "")
            if value:
                # Masquer les valeurs sensibles
                masked = value[:8] + "..." + value[-4:] if len(value) > 20 else "***"
                print(f"   ✅ {var} = {masked}")
            else:
                print(f"   ❌ {var} = MANQUANT")
    
    print("\n" + "="*60)
    print(f"📁 Fichier source: {SECRETS_FILE}")
    print(f"📊 Total variables: {len(secrets)}")


def verify_consistency():
    """Vérifie la cohérence entre local et Render"""
    secrets = load_secrets()
    render_data = get_render_env_vars()
    
    if not render_data:
        print("❌ Impossible de vérifier Render")
        return
    
    current_vars = {v["envVar"]["key"]: v["envVar"]["value"] for v in render_data["env_vars"]}
    
    print("\n🔍 VÉRIFICATION DE COHÉRENCE")
    print("="*60)
    
    missing_on_render = []
    different_values = []
    extra_on_render = []
    
    for key, value in secrets.items():
        if key in SKIP_SYNC:
            continue
        if key not in current_vars:
            missing_on_render.append(key)
        elif current_vars[key] != value:
            different_values.append(key)
    
    for key in current_vars:
        if key not in secrets:
            extra_on_render.append(key)
    
    if missing_on_render:
        print(f"\n❌ Manquantes sur Render ({len(missing_on_render)}):")
        for k in missing_on_render:
            print(f"   - {k}")
    
    if different_values:
        print(f"\n⚠️ Valeurs différentes ({len(different_values)}):")
        for k in different_values:
            print(f"   - {k}")
    
    if extra_on_render:
        print(f"\n📝 Seulement sur Render ({len(extra_on_render)}):")
        for k in extra_on_render:
            print(f"   - {k}")
    
    if not missing_on_render and not different_values:
        print("\n✅ Tout est synchronisé!")


def export_backup():
    """Exporte un backup des variables"""
    secrets = load_secrets()
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"env_backup_{timestamp}.json"
    
    # Ne pas inclure les valeurs complètes dans le backup JSON
    # (pour sécurité - utiliser .secrets.env directement)
    backup_data = {
        "timestamp": timestamp,
        "variables": list(secrets.keys()),
        "count": len(secrets),
        "source": str(SECRETS_FILE)
    }
    
    with open(backup_file, "w") as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Backup créé: {backup_file}")
    print(f"📝 {len(secrets)} variables enregistrées")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "sync":
        sync_to_render()
    elif command == "verify":
        verify_consistency()
    elif command == "export":
        export_backup()
    else:
        print(f"❌ Commande inconnue: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
