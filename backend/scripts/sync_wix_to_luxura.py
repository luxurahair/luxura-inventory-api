#!/usr/bin/env python3
"""
Script de synchronisation Wix vers Luxura
Appelé par le cron job Render pour synchroniser les produits Wix
"""

import os
import sys
import asyncio
import logging
import httpx
from datetime import datetime

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URLs API
RENDER_API_URL = os.getenv("RENDER_API_URL", "https://luxura-inventory-api.onrender.com")
WIX_SYNC_SECRET = os.getenv("SEO_SECRET_KEY", os.getenv("WIX_SYNC_SECRET", ""))


async def sync_wix_products():
    """
    Déclenche la synchronisation Wix via l'API
    """
    logger.info("=" * 60)
    logger.info("🔄 DÉMARRAGE SYNC WIX → LUXURA")
    logger.info(f"📅 {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    # Endpoint de sync
    sync_url = f"{RENDER_API_URL}/wix/sync"
    
    headers = {
        "Content-Type": "application/json",
        "X-SEO-SECRET": WIX_SYNC_SECRET
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            logger.info(f"📡 Appel API: {sync_url}")
            
            response = await client.post(
                sync_url,
                headers=headers,
                json={"force": False}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Sync réussie!")
                logger.info(f"   Produits traités: {result.get('products_synced', 'N/A')}")
                logger.info(f"   Variants traités: {result.get('variants_synced', 'N/A')}")
                logger.info(f"   Durée: {result.get('duration', 'N/A')}s")
                return True
            else:
                logger.error(f"❌ Erreur sync: HTTP {response.status_code}")
                logger.error(f"   Réponse: {response.text[:500]}")
                return False
                
    except httpx.TimeoutException:
        logger.error("❌ Timeout - la sync prend trop de temps")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False


async def health_check():
    """
    Vérifie que l'API est accessible
    """
    health_url = f"{RENDER_API_URL}/api/health"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(health_url)
            if response.status_code == 200:
                logger.info("✅ API Health: OK")
                return True
            else:
                logger.warning(f"⚠️ API Health: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ API inaccessible: {e}")
        return False


async def main():
    """
    Point d'entrée principal
    """
    # Vérifier la santé de l'API d'abord
    if not await health_check():
        logger.warning("⚠️ API non disponible, tentative de sync quand même...")
    
    # Lancer la sync
    success = await sync_wix_products()
    
    logger.info("=" * 60)
    if success:
        logger.info("✅ SYNC TERMINÉE AVEC SUCCÈS")
    else:
        logger.info("❌ SYNC ÉCHOUÉE")
    logger.info("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
