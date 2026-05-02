# app/routes/wix_oauth.py
"""
🔐 WIX OAUTH ROUTER - Gestion automatique du token Wix
=====================================================
Endpoints pour OAuth Wix avec échange de code et refresh automatique.
"""
import os
import logging
from urllib.parse import urlencode
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter(prefix="/wix/oauth", tags=["wix-oauth"])
logger = logging.getLogger(__name__)

WIX_AUTH_URL = "https://www.wix.com/oauth/authorize"
WIX_TOKEN_URL = "https://www.wixapis.com/oauth2/token"


@router.get("/start")
def wix_oauth_start():
    """
    Démarre le flux OAuth Wix.
    Redirige vers la page d'autorisation Wix.
    """
    client_id = os.getenv("WIX_CLIENT_ID")
    redirect_uri = os.getenv("WIX_REDIRECT_URL")
    scope = os.getenv("WIX_OAUTH_SCOPES", "").strip()

    if not client_id or not redirect_uri or not scope:
        raise HTTPException(
            status_code=500,
            detail="Missing env: WIX_CLIENT_ID / WIX_REDIRECT_URL / WIX_OAUTH_SCOPES"
        )

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope,
    }

    return RedirectResponse(WIX_AUTH_URL + "?" + urlencode(params))


@router.get("/callback")
async def wix_oauth_callback(request: Request):
    """
    Callback OAuth Wix - échange le code contre access_token + refresh_token.
    Sauvegarde automatiquement les tokens dans la DB pour renouvellement automatique.
    """
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    desc = request.query_params.get("error_description")

    if error:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": error, "error_description": desc}
        )

    if not code:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "No authorization code received"}
        )

    # Échanger le code contre des tokens
    client_id = os.getenv("WIX_CLIENT_ID", "")
    client_secret = os.getenv("WIX_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "WIX_CLIENT_ID or WIX_CLIENT_SECRET not configured"}
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                WIX_TOKEN_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code
                }
            )

            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token")
                expires_in = data.get("expires_in", 3600)

                logger.info(f"OAuth tokens received - expires_in: {expires_in}")

                # Sauvegarder dans la DB
                try:
                    from wix_cron_service import save_tokens_to_db, token_cache
                    await save_tokens_to_db(access_token, refresh_token, expires_in)
                    token_cache.set_token(access_token, refresh_token, expires_in)
                    logger.info("Tokens saved to DB and cache")
                except Exception as e:
                    logger.warning(f"Could not save tokens to DB: {e}")

                return {
                    "ok": True,
                    "message": "✅ Wix OAuth configuré avec succès!",
                    "has_access_token": bool(access_token),
                    "has_refresh_token": bool(refresh_token),
                    "expires_in_hours": expires_in // 3600,
                    "auto_renewal": "Le token sera renouvelé automatiquement via le cron"
                }
            else:
                error_msg = f"Wix OAuth token exchange failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "error": error_msg}
                )

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/status")
async def wix_oauth_status():
    """
    Vérifie le statut du token Wix OAuth.
    """
    import asyncpg

    try:
        db_url = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")
        conn = await asyncpg.connect(db_url)

        row = await conn.fetchrow("SELECT * FROM wix_oauth WHERE id = 1")
        await conn.close()

        if row:
            expires_at = row['expires_at']
            now = datetime.now(timezone.utc)

            if expires_at:
                is_valid = expires_at > now
                time_remaining = expires_at - now if is_valid else None
            else:
                is_valid = False
                time_remaining = None

            return {
                "ok": True,
                "has_access_token": bool(row['access_token']),
                "has_refresh_token": bool(row['refresh_token']),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "is_valid": is_valid,
                "time_remaining": str(time_remaining) if time_remaining else "EXPIRÉ",
                "can_auto_renew": bool(row['refresh_token']),
            }
        else:
            return {"ok": False, "error": "Aucun token configuré"}

    except Exception as e:
        logger.error(f"OAuth status error: {e}")
        return {"ok": False, "error": str(e)}
