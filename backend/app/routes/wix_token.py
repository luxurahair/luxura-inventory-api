"""
Luxura Wix Token Management - Auto-refresh system
Gère le token Wix OAuth avec cache et renouvellement automatique
"""

import os
import time
import logging
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException
import requests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wix", tags=["Wix Authentication"])

# ============ TOKEN CACHE ============

class WixTokenCache:
    """Cache pour le token Wix avec expiration automatique"""
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.expires_at: float = 0  # Unix timestamp
        self.refresh_token: Optional[str] = None
        
    def is_valid(self) -> bool:
        """Vérifie si le token est encore valide (avec 5 min de marge)"""
        if not self.access_token:
            return False
        return time.time() < (self.expires_at - 300)  # 5 min de marge
    
    def set_token(self, access_token: str, expires_in: int, refresh_token: str = None):
        """Enregistre un nouveau token"""
        self.access_token = access_token
        self.expires_at = time.time() + expires_in
        if refresh_token:
            self.refresh_token = refresh_token
        logger.info(f"Token cached, expires in {expires_in}s")
    
    def get_token(self) -> Optional[str]:
        """Retourne le token si valide, sinon None"""
        if self.is_valid():
            return self.access_token
        return None
    
    def clear(self):
        """Efface le cache"""
        self.access_token = None
        self.expires_at = 0
        self.refresh_token = None


# Instance globale du cache
token_cache = WixTokenCache()


# ============ HELPER FUNCTIONS ============

def get_wix_credentials() -> Dict[str, str]:
    """Récupère les credentials Wix depuis les variables d'environnement"""
    return {
        "client_id": os.getenv("WIX_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("WIX_CLIENT_SECRET", "").strip(),
        "instance_id": os.getenv("WIX_INSTANCE_ID", "ab8a5a88-69a5-4348-ad2e-06017de46f57").strip(),
    }


def fetch_new_token() -> Dict:
    """Obtient un nouveau token depuis l'API Wix"""
    creds = get_wix_credentials()
    
    if not creds["client_id"] or not creds["client_secret"]:
        raise HTTPException(
            status_code=500, 
            detail="Missing WIX_CLIENT_ID or WIX_CLIENT_SECRET"
        )
    
    try:
        response = requests.post(
            "https://www.wixapis.com/oauth2/token",
            json={
                "grant_type": "client_credentials",
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
                "instance_id": creds["instance_id"],
            },
            timeout=30,
        )
        
        if not response.ok:
            logger.error(f"Wix token error: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=502, 
                detail=f"Wix token failed: {response.status_code}"
            )
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Wix token request error: {e}")
        raise HTTPException(status_code=502, detail=str(e))


def get_valid_token() -> str:
    """
    Retourne un token valide, en le rafraîchissant si nécessaire.
    C'est LA fonction à utiliser pour obtenir un token Wix.
    """
    # Vérifier le cache d'abord
    cached_token = token_cache.get_token()
    if cached_token:
        return cached_token
    
    # Sinon, obtenir un nouveau token
    token_data = fetch_new_token()
    
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 3600)  # Default 1h
    refresh_token = token_data.get("refresh_token")
    
    if not access_token:
        raise HTTPException(status_code=502, detail="No access_token in response")
    
    # Mettre en cache
    token_cache.set_token(access_token, expires_in, refresh_token)
    
    return access_token


# ============ API ENDPOINTS ============

@router.get("/token/status")
async def token_status():
    """
    Vérifie le status du token Wix
    """
    creds = get_wix_credentials()
    
    return {
        "cached": token_cache.is_valid(),
        "expires_in_seconds": max(0, int(token_cache.expires_at - time.time())) if token_cache.is_valid() else 0,
        "has_client_id": bool(creds["client_id"]),
        "has_client_secret": bool(creds["client_secret"]),
        "instance_id": creds["instance_id"][:8] + "..." if creds["instance_id"] else None
    }


@router.post("/token")
async def get_token(instance_id: Optional[str] = None):
    """
    Obtient un token Wix (utilise le cache si disponible)
    
    Parameters:
    - instance_id: Override l'instance_id par défaut (optionnel)
    """
    try:
        # Si instance_id fourni, on force un nouveau fetch
        if instance_id and instance_id != get_wix_credentials()["instance_id"]:
            creds = get_wix_credentials()
            response = requests.post(
                "https://www.wixapis.com/oauth2/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": creds["client_id"],
                    "client_secret": creds["client_secret"],
                    "instance_id": instance_id,
                },
                timeout=30,
            )
            if not response.ok:
                raise HTTPException(502, f"Wix token failed: {response.status_code}")
            return response.json()
        
        # Sinon utiliser le système de cache
        token = get_valid_token()
        
        return {
            "access_token": token,
            "from_cache": token_cache.is_valid(),
            "expires_in_seconds": max(0, int(token_cache.expires_at - time.time()))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token error: {e}")
        raise HTTPException(500, str(e))


@router.post("/token/refresh")
async def refresh_token():
    """
    Force le renouvellement du token Wix (efface le cache)
    """
    # Effacer le cache
    token_cache.clear()
    
    try:
        # Obtenir un nouveau token
        token = get_valid_token()
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "expires_in_seconds": max(0, int(token_cache.expires_at - time.time()))
        }
        
    except HTTPException as e:
        return {
            "success": False,
            "error": e.detail
        }


@router.delete("/token/cache")
async def clear_token_cache():
    """
    Efface le cache du token (pour debug)
    """
    token_cache.clear()
    return {"success": True, "message": "Cache cleared"}


# ============ EXPORT HELPER ============

def get_wix_access_token() -> str:
    """
    Helper function pour les autres modules.
    Retourne un token valide ou lève une exception.
    
    Usage dans d'autres fichiers:
        from app.routes.wix_token import get_wix_access_token
        token = get_wix_access_token()
    """
    # D'abord vérifier si un token statique est configuré
    static_token = os.getenv("WIX_ACCESS_TOKEN", "").strip()
    if static_token:
        return static_token
    
    # Sinon utiliser le système OAuth avec cache
    return get_valid_token()
