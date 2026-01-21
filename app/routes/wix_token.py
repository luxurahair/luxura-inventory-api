# app/routes/wix_token.py
import os
import requests
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/wix", tags=["wix-auth"])

@router.post("/token")
def wix_token(instance_id: str):
    client_id = os.getenv("WIX_CLIENT_ID")
    client_secret = os.getenv("WIX_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Missing env: WIX_CLIENT_ID / WIX_CLIENT_SECRET")

    r = requests.post(
        "https://www.wixapis.com/oauth2/token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "instance_id": instance_id,
        },
        timeout=30,
    )

    if not r.ok:
        raise HTTPException(status_code=502, detail=f"Wix token failed: {r.status_code} {r.text}")

    return r.json()
