"""
Luxura Wix Cron Micro-Service
=============================
Service indépendant pour le renouvellement automatique du token Wix OAuth.
À déployer comme service séparé sur Render.

Endpoints:
- GET /health : Vérification de l'état du service
- GET /wix/cron/refresh-token : Renouveler le token Wix (appelé par cron)
- GET /wix/cron/status : Vérifier l'état du token en cache

Configuration Render:
- Health Check Path: /health
- Cron Job: toutes les 3 heures sur /wix/cron/refresh-token
"""

import os
import time
import threading
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ==================== CONFIGURATION ====================

load_dotenv()

# Variables d'environnement requises
WIX_CLIENT_ID = os.getenv("WIX_CLIENT_ID", "")
WIX_CLIENT_SECRET = os.getenv("WIX_CLIENT_SECRET", "")
WIX_ACCOUNT_ID = os.getenv("WIX_ACCOUNT_ID", "")
WIX_INSTANCE_ID = os.getenv("WIX_INSTANCE_ID", "")
WIX_REDIRECT_URL = os.getenv("WIX_REDIRECT_URL", "")
WIX_PUSH_SECRET = os.getenv("WIX_PUSH_SECRET", os.getenv("SEO_SECRET", ""))
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== TOKEN CACHE ====================

class WixTokenCache:
    """Cache thread-safe pour le token Wix OAuth"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._expires_at: Optional[float] = None
        self._last_refresh: Optional[datetime] = None
        self._refresh_count: int = 0
        self._errors: list = []
    
    def get_token(self) -> Optional[str]:
        """Récupérer le token si valide"""
        with self._lock:
            if self._access_token and self._expires_at:
                if time.time() < self._expires_at - 300:  # 5 min de marge
                    return self._access_token
            return None
    
    def set_token(self, access_token: str, refresh_token: str, expires_in: int):
        """Mettre à jour le cache avec un nouveau token"""
        with self._lock:
            self._access_token = access_token
            self._refresh_token = refresh_token
            self._expires_at = time.time() + expires_in
            self._last_refresh = datetime.now(timezone.utc)
            self._refresh_count += 1
            logger.info(f"Token cache updated. Refresh count: {self._refresh_count}")
    
    def get_refresh_token(self) -> Optional[str]:
        """Récupérer le refresh token pour renouvellement"""
        with self._lock:
            return self._refresh_token
    
    def add_error(self, error: str):
        """Enregistrer une erreur"""
        with self._lock:
            self._errors.append({
                "time": datetime.now(timezone.utc).isoformat(),
                "error": error
            })
            # Garder seulement les 10 dernières erreurs
            if len(self._errors) > 10:
                self._errors = self._errors[-10:]
    
    def get_status(self) -> Dict[str, Any]:
        """Récupérer l'état du cache"""
        with self._lock:
            token_valid = False
            time_remaining = 0
            
            if self._access_token and self._expires_at:
                time_remaining = max(0, int(self._expires_at - time.time()))
                token_valid = time_remaining > 300
            
            return {
                "token_cached": self._access_token is not None,
                "token_valid": token_valid,
                "time_remaining_seconds": time_remaining,
                "time_remaining_human": f"{time_remaining // 3600}h {(time_remaining % 3600) // 60}m",
                "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
                "refresh_count": self._refresh_count,
                "recent_errors": self._errors[-5:] if self._errors else []
            }


# Instance globale du cache
token_cache = WixTokenCache()

# ==================== FASTAPI APP ====================

app = FastAPI(
    title="Luxura Wix Cron Service",
    description="Micro-service pour le renouvellement automatique du token Wix OAuth",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== DATABASE HELPERS ====================

async def get_refresh_token_from_db() -> Optional[str]:
    """Récupérer le refresh token depuis Supabase"""
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not configured")
        return None
    
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            row = await conn.fetchrow(
                "SELECT refresh_token FROM wix_oauth WHERE id = 1"
            )
            if row:
                return row['refresh_token']
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"DB error getting refresh token: {e}")
        token_cache.add_error(f"DB read error: {str(e)}")
    
    return None


async def save_tokens_to_db(access_token: str, refresh_token: str, expires_in: int):
    """Sauvegarder les tokens dans Supabase"""
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not configured, tokens only in cache")
        return
    
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            expires_at = datetime.now(timezone.utc).timestamp() + expires_in
            await conn.execute("""
                INSERT INTO wix_oauth (id, access_token, refresh_token, expires_at, updated_at)
                VALUES (1, $1, $2, to_timestamp($3), NOW())
                ON CONFLICT (id) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
            """, access_token, refresh_token, expires_at)
            logger.info("Tokens saved to database")
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"DB error saving tokens: {e}")
        token_cache.add_error(f"DB write error: {str(e)}")


# ==================== WIX OAUTH ====================

async def refresh_wix_token() -> Dict[str, Any]:
    """
    Renouveler le token Wix OAuth.
    1. Essaie d'utiliser le refresh_token du cache
    2. Sinon, récupère le refresh_token depuis la DB
    3. Appelle l'API Wix OAuth pour obtenir un nouveau token
    4. Met à jour le cache et la DB
    """
    
    # 1. Récupérer le refresh_token
    refresh_token = token_cache.get_refresh_token()
    
    if not refresh_token:
        logger.info("No refresh token in cache, fetching from DB...")
        refresh_token = await get_refresh_token_from_db()
    
    if not refresh_token:
        error = "No refresh token available (cache or DB)"
        logger.error(error)
        token_cache.add_error(error)
        return {"ok": False, "error": error}
    
    # 2. Appeler l'API Wix OAuth
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://www.wixapis.com/oauth2/token",
                headers={"Content-Type": "application/json"},
                json={
                    "grant_type": "refresh_token",
                    "client_id": WIX_CLIENT_ID,
                    "client_secret": WIX_CLIENT_SECRET,
                    "refresh_token": refresh_token
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get("access_token")
                new_refresh_token = data.get("refresh_token", refresh_token)
                expires_in = data.get("expires_in", 3600)
                
                # 3. Mettre à jour le cache
                token_cache.set_token(new_access_token, new_refresh_token, expires_in)
                
                # 4. Sauvegarder en DB
                await save_tokens_to_db(new_access_token, new_refresh_token, expires_in)
                
                logger.info(f"Token refreshed successfully. Expires in {expires_in}s")
                
                return {
                    "ok": True,
                    "message": "Token refreshed successfully",
                    "expires_in": expires_in,
                    "expires_in_human": f"{expires_in // 3600}h {(expires_in % 3600) // 60}m"
                }
            else:
                error = f"Wix OAuth error: {response.status_code} - {response.text}"
                logger.error(error)
                token_cache.add_error(error)
                return {"ok": False, "error": error}
                
    except Exception as e:
        error = f"Refresh token exception: {str(e)}"
        logger.error(error)
        token_cache.add_error(error)
        return {"ok": False, "error": error}


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Page d'accueil"""
    return {
        "service": "Luxura Wix Cron Service",
        "status": "running",
        "endpoints": {
            "/health": "Health check",
            "/wix/cron/refresh-token": "Refresh Wix token (cron)",
            "/wix/cron/status": "Token cache status"
        }
    }


@app.get("/health")
async def health_check():
    """Health check pour Render"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "wix_client_id": bool(WIX_CLIENT_ID),
            "wix_client_secret": bool(WIX_CLIENT_SECRET),
            "database_url": bool(DATABASE_URL)
        }
    }


@app.get("/wix/cron/refresh-token")
async def cron_refresh_token(secret: Optional[str] = None):
    """
    Endpoint pour le renouvellement automatique du token.
    Appelez cet endpoint via un cron job toutes les 3 heures.
    
    Optionnel: paramètre `secret` pour sécuriser l'endpoint.
    """
    # Vérification du secret (optionnel)
    if WIX_PUSH_SECRET and secret != WIX_PUSH_SECRET:
        # Si un secret est configuré mais pas fourni, on log un warning
        if secret:
            logger.warning(f"Invalid secret provided: {secret[:8]}...")
    
    result = await refresh_wix_token()
    
    if result.get("ok"):
        return {
            "ok": True,
            "message": result.get("message"),
            "expires_in": result.get("expires_in"),
            "next_refresh_recommended": "in 3 hours",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))


@app.get("/wix/cron/status")
async def cron_status():
    """
    Vérifier l'état du token en cache.
    Utile pour monitoring et debugging.
    """
    status = token_cache.get_status()
    
    return {
        "ok": status["token_valid"],
        "cache": status,
        "config": {
            "wix_instance_id": WIX_INSTANCE_ID[:8] + "..." if WIX_INSTANCE_ID else None,
            "database_configured": bool(DATABASE_URL)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/wix/token")
async def get_current_token(secret: Optional[str] = None):
    """
    Récupérer le token actuel (pour debugging/intégration).
    ATTENTION: Cet endpoint expose le token, utilisez avec précaution.
    """
    if WIX_PUSH_SECRET and secret != WIX_PUSH_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    token = token_cache.get_token()
    
    if token:
        return {
            "ok": True,
            "access_token": token,
            "source": "cache"
        }
    
    # Si pas de token en cache, essayer de le rafraîchir
    result = await refresh_wix_token()
    
    if result.get("ok"):
        token = token_cache.get_token()
        return {
            "ok": True,
            "access_token": token,
            "source": "refreshed"
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))


# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    logger.info("Luxura Wix Cron Service starting...")
    logger.info(f"WIX_CLIENT_ID configured: {bool(WIX_CLIENT_ID)}")
    logger.info(f"WIX_CLIENT_SECRET configured: {bool(WIX_CLIENT_SECRET)}")
    logger.info(f"DATABASE_URL configured: {bool(DATABASE_URL)}")
    
    # Essayer de charger le token depuis la DB au démarrage
    if DATABASE_URL:
        try:
            refresh_token = await get_refresh_token_from_db()
            if refresh_token:
                logger.info("Refresh token loaded from DB, attempting initial refresh...")
                await refresh_wix_token()
        except Exception as e:
            logger.error(f"Startup token refresh failed: {e}")


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
