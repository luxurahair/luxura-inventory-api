# app/routes/wix_oauth.py
import os
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter(prefix="/wix/oauth", tags=["wix-oauth"])

WIX_AUTH_URL = "https://www.wix.com/oauth/authorize"

@router.get("/start")
def wix_oauth_start():
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
def wix_oauth_callback(request: Request):
    # pour l'instant: on valide juste qu'on reçoit le code
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    desc = request.query_params.get("error_description")

    if error:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": error, "error_description": desc}
        )

    return {"ok": True, "code_received": bool(code), "code_preview": (code[:8] + "...") if code else None}
