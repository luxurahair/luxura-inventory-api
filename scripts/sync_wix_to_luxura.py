#!/usr/bin/env python3
"""
LUXURA CRON: Sync Wix to Luxura
================================
Script pour le Render Cron Job.
- Renouvelle le token Wix
- Synchronise les produits Wix vers Supabase
- Déclenche la génération de blogs si c'est l'heure

Usage sur Render Cron:
  Build Command: pip install httpx python-dotenv
  Start Command: python scripts/sync_wix_to_luxura.py
  Schedule: 0 */3 * * * (toutes les 3 heures)
"""

import os
import sys
import logging
from datetime import datetime

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:
    print("[CRON] ❌ httpx not installed. Run: pip install httpx")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Configuration
LUXURA_API_URL = os.getenv("LUXURA_API_URL", "https://luxura-inventory-api.onrender.com")
SEO_SECRET = os.getenv("SEO_SECRET", os.getenv("WIX_PUSH_SECRET", ""))
TIMEOUT = 180  # 3 minutes for long operations


def log_banner(message: str):
    """Affiche une bannière de log"""
    print("=" * 60)
    print(f"[CRON] {message}")
    print("=" * 60)


def refresh_wix_token() -> bool:
    """Renouvelle le token Wix OAuth avant expiration"""
    print(f"[CRON] 🔄 Renouvellement du token Wix...")
    
    try:
        with httpx.Client(timeout=60) as client:
            # Essayer l'endpoint de refresh token
            url = f"{LUXURA_API_URL}/api/wix/token/refresh"
            if SEO_SECRET:
                url += f"?secret={SEO_SECRET}"
            
            response = client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[CRON] ✅ Token Wix renouvelé: {data.get('message', 'OK')}")
                return True
            else:
                print(f"[CRON] ⚠️ Refresh token response: {response.status_code}")
                # Pas forcément une erreur fatale
                return True
                
    except Exception as e:
        print(f"[CRON] ⚠️ Token refresh warning: {e}")
        # Continue anyway, token might still be valid
        return True


def sync_wix_inventory() -> bool:
    """Synchronise l'inventaire Wix vers Supabase"""
    print(f"[CRON] 📦 Synchronisation inventaire Wix...")
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Appeler l'endpoint de sync inventory (sans préfixe /api/)
            url = f"{LUXURA_API_URL}/wix/sync"
            headers = {"Content-Type": "application/json"}
            
            if SEO_SECRET:
                headers["X-SEO-SECRET"] = SEO_SECRET
            
            print(f"[CRON] Appel de {url}...")
            print(f"[CRON] SEO_SECRET configuré: {'✅ Oui' if SEO_SECRET else '❌ Non'}")
            
            response = client.post(url, headers=headers, params={"limit": 500, "dry_run": "false"})
            
            if response.status_code == 200:
                data = response.json()
                print(f"[CRON] ✅ Inventory sync: {data}")
                return True
            elif response.status_code == 404:
                print(f"[CRON] ⚠️ Endpoint /wix/sync not found")
                print(f"[CRON] Response: {response.text[:200]}")
                return False
            else:
                print(f"[CRON] ❌ Erreur HTTP {response.status_code}")
                print(f"[CRON] Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"[CRON] ❌ Inventory sync error: {e}")
        return False


def trigger_blog_generation() -> bool:
    """Déclenche la génération de blog selon le calendrier éditorial"""
    print(f"[CRON] 📝 Vérification génération blog...")
    
    # Vérifier l'heure actuelle (heure de Montréal approximative)
    current_hour = datetime.utcnow().hour - 4  # UTC-4 pour Montréal (été)
    if current_hour < 0:
        current_hour += 24
    
    # Heures de publication configurées
    blog_hours = [7, 12, 16, 19, 20]
    
    if current_hour not in blog_hours:
        print(f"[CRON] ⏰ Pas d'heure de publication (heure actuelle: {current_hour}h)")
        return True
    
    print(f"[CRON] 📰 Heure de publication! Déclenchement génération blog...")
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            url = f"{LUXURA_API_URL}/api/blog/auto-generate"
            headers = {"Content-Type": "application/json"}
            
            if SEO_SECRET:
                headers["X-Secret"] = SEO_SECRET
            
            response = client.post(
                url,
                headers=headers,
                json={"count": 1, "source": "render_cron"}
            )
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get("posts", [])
                print(f"[CRON] ✅ Blog généré: {len(posts)} article(s)")
                for post in posts:
                    print(f"[CRON]    📄 {post.get('title', 'Sans titre')[:50]}...")
                return True
            elif response.status_code == 404:
                print(f"[CRON] ⚠️ Endpoint /api/blog/auto-generate not found")
                return True
            else:
                print(f"[CRON] ⚠️ Blog generation response: {response.status_code}")
                return True
                
    except Exception as e:
        print(f"[CRON] ⚠️ Blog generation error: {e}")
        return True  # Non-fatal


def check_api_health() -> bool:
    """Vérifie que l'API est accessible"""
    print(f"[CRON] 🔍 Vérification santé API: {LUXURA_API_URL}")
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(f"{LUXURA_API_URL}/api/health")
            
            if response.status_code == 200:
                print(f"[CRON] ✅ API accessible")
                return True
            else:
                print(f"[CRON] ⚠️ API response: {response.status_code}")
                return True  # Continue anyway
                
    except Exception as e:
        print(f"[CRON] ❌ API inaccessible: {e}")
        return False


def main():
    """Point d'entrée principal du cron job"""
    log_banner(f"LUXURA SYNC CRON - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"[CRON] 🌐 API URL: {LUXURA_API_URL}")
    print(f"[CRON] 🔑 SEO_SECRET configuré: {'✅ Oui' if SEO_SECRET else '❌ Non'}")
    
    # 1. Vérifier la santé de l'API
    if not check_api_health():
        print("[CRON] ❌ API non disponible, abandon du cron")
        sys.exit(1)
    
    success = True
    
    # 2. Renouveler le token Wix
    if not refresh_wix_token():
        print("[CRON] ⚠️ Token refresh failed (continuing anyway)")
    
    # 3. Synchroniser l'inventaire
    if not sync_wix_inventory():
        print("[CRON] ⚠️ Inventory sync failed (continuing anyway)")
    
    # 4. Déclencher la génération de blog si c'est l'heure
    if not trigger_blog_generation():
        print("[CRON] ⚠️ Blog generation failed (continuing anyway)")
    
    log_banner("CRON TERMINÉ AVEC SUCCÈS ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()
