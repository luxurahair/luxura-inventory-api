import os
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.routes import products, salons, inventory, wix


app = FastAPI(
    title="Luxura Inventory API",
    version="1.0.0",
)


# ------------------------------------------------
#  CORS
# ------------------------------------------------
origins_env = os.getenv("CORS_ORIGINS", "")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    # en dev seulement ; en prod, mets des domaines précis
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
#  STARTUP (aucune synchro Wix pour l’instant)
# ------------------------------------------------
@app.on_event("startup")
def startup_event() -> None:
    print("[STARTUP] Aucune synchro Wix au démarrage (désactivée).")


# ------------------------------------------------
#  Routes système
# ------------------------------------------------
@app.get("/", tags=["default"])
def root():
    return "Luxura Inventory API"


@app.get("/healthz", tags=["default"])
def healthz():
    return {"status": "ok"}


@app.get("/version", tags=["default"])
def version():
    return app.version


# ------------------------------------------------
#  Route produits (liste simple pour l’instant)
# ------------------------------------------------
@app.get("/products/", tags=["products"])
def list_products_stub():
    """
    Stub temporaire : renvoie une liste vide de produits.
    On met ça pour que /products/ réponde proprement,
    sans se faire intercepter par une route dynamique /{product_id}.
    """
    return []


# ------------------------------------------------
#  Synchro manuelle Wix -> Debug
# ------------------------------------------------
@app.post("/wix-sync", tags=["wix"])
def wix_sync_debug() -> Dict[str, Any]:
    """
    Appelle l’API Wix et retourne brut ce que Wix répond.
    On s’en sert pour vérifier les droits / structure de réponse.
    """

    api_key = os.getenv("WIX_API_KEY")
    account_id = os.getenv("WIX_ACCOUNT_ID")
    site_id = os.getenv("WIX_SITE_ID")

    if not api_key or not account_id or not site_id:
        raise HTTPException(
            status_code=500,
            detail="Variables WIX_API_KEY, WIX_ACCOUNT_ID ou WIX_SITE_ID manquantes dans l'environnement.",
        )

    url = "https://www.wixapis.com/stores/v1/products/query"

    headers = {
        "Authorization": api_key,
        "wix-account-id": account_id,
        "wix-site-id": site_id,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, headers=headers, json={"query": {}})
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur réseau en appelant l'API Wix: {repr(e)}",
        )

    # On essaie de décoder en JSON, sinon on renvoie le texte brut
    try:
        body = resp.json()
    except Exception:
        body = resp.text

    return {
        "status_code": resp.status_code,
        "body": body,
    }


# ------------------------------------------------
#  Routers métier
# ------------------------------------------------
app.include_router(products.router)
app.include_router(salons.router)
app.include_router(inventory.router)
app.include_router(wix.router)
