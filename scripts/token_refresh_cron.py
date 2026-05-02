#!/usr/bin/env python3
"""
🔐 TOKEN REFRESH CRON - Renouvellement automatique des tokens
=============================================================

Ce script renouvelle les tokens Wix OAuth avant leur expiration.
À exécuter quotidiennement via un cron Render.

Render Cron Configuration:
  - Name: luxura-token-refresh
  - Schedule: 0 6 * * * (tous les jours à 6h UTC)
  - Start Command: python scripts/token_refresh_cron.py
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx
import asyncpg
from dotenv import load_dotenv

# Charger les variables
load_dotenv(Path(__file__).parent.parent / ".secrets.env")

# Configuration
API_URL = os.getenv("RENDER_SERVICE_URL", "https://luxura-inventory-api.onrender.com")
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def check_token_expiry():
    """Vérifie si le token Wix expire bientôt"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        row = await conn.fetchrow("SELECT * FROM wix_oauth WHERE id = 1")
        await conn.close()
        
        if not row:
            logger.error("❌ Aucun token trouvé dans wix_oauth")
            return None
        
        expires_at = row.get("expires_at")
        if not expires_at:
            logger.warning("⚠️ Pas de date d'expiration")
            return None
        
        now = datetime.now(timezone.utc)
        remaining = expires_at - now
        
        logger.info(f"📅 Token expire dans: {remaining}")
        return remaining
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification token: {e}")
        return None


async def refresh_wix_token():
    """Tente de rafraîchir le token Wix via l'API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Essayer le refresh endpoint
            response = await client.get(f"{API_URL}/api/wix/token/refresh")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    logger.info("✅ Token Wix rafraîchi avec succès!")
                    return True
                else:
                    logger.warning(f"⚠️ Refresh échoué: {data.get('error')}")
                    return False
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Erreur refresh: {e}")
        return False


async def send_alert_email(subject: str, body: str):
    """Envoie un email d'alerte"""
    import smtplib
    from email.mime.text import MIMEText
    
    email = os.getenv("LUXURA_EMAIL")
    password = os.getenv("LUXURA_APP_PASSWORD")
    
    if not email or not password:
        logger.warning("⚠️ Credentials email non configurés")
        return False
    
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = email
        msg['To'] = email
        msg['Subject'] = subject
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email, password)
            server.send_message(msg)
        
        logger.info(f"📧 Email envoyé: {subject}")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur envoi email: {e}")
        return False


async def main():
    logger.info("=" * 60)
    logger.info("🔐 TOKEN REFRESH CRON - Démarrage")
    logger.info("=" * 60)
    
    # Vérifier l'expiration
    remaining = await check_token_expiry()
    
    if remaining is None:
        await send_alert_email(
            "🚨 Luxura - Token Wix non trouvé",
            "Impossible de vérifier le token Wix. Vérifiez la configuration OAuth."
        )
        sys.exit(1)
    
    # Si le token expire dans moins de 3 jours, alerter et tenter refresh
    if remaining < timedelta(days=3):
        logger.warning(f"⚠️ Token expire bientôt: {remaining}")
        
        # Tenter le refresh
        success = await refresh_wix_token()
        
        if not success:
            await send_alert_email(
                f"🚨 Luxura - Token Wix expire dans {remaining.days} jours!",
                f"""Le token Wix va expirer bientôt et le refresh automatique a échoué.

Temps restant: {remaining}

ACTION REQUISE:
1. Aller sur: {API_URL}/wix/oauth/start
2. Autoriser l'application Wix
3. Le refresh_token sera sauvegardé automatiquement

Dashboard: {API_URL}/api/status/dashboard
"""
            )
            sys.exit(1)
    else:
        logger.info(f"✅ Token valide - expire dans {remaining.days} jours")
    
    logger.info("✅ Vérification terminée")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
