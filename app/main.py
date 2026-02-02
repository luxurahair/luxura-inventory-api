# app/main.py
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlmodel import SQLModel

from app.db import engine

# Routes (routers)
from app.routes import inventory, products, salons, seo
from app.routes import wix as wix_routes
from app.routes.wix_oauth import router as wix_oauth_router
from app.routes.wix_webhooks import router as wix_webhooks_router
from app.routes.wix_token import router as wix_token_router
from app.routes.wix_seo_push import router as wix_seo_push_router

# from app.routes import movement  # décommente seulement si movement.py existe et compile


app = FastAPI(
    title="Luxura Inventory API",
    version="2.0.0",
)

@app.get("/cors/ping")
def cors_ping():
    return {"ok": True}

print("### LOADED app/main.py - Luxura Inventory API ###")


# ----------------------------
# CORS
# ----------------------------
origins_env = os.getenv("CORS_ORIGINS", "").strip()

if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    # ✅ valeurs par défaut sûres pour Wix + ton domaine + GitHub Pages
    allowed_origins = [
        "https://www.luxuradistribution.com",
        "https://luxuradistribution.com",
        "https://editor.wix.com",
        "https://manage.wix.com",
        "https://www.wix.com",
        "https://static.wixstatic.com",
        "https://static.parastorage.com",
        "https://luxurahair.github.io",  # ✅ GitHub Pages
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# OPTIONS "pare-chocs" (évite OPTIONS 400)
# ----------------------------
from fastapi import Request  # noqa: E402

@app.options("/{path:path}")
def options_handler(path: str, request: Request):
    origin = request.headers.get("origin")
    req_headers = request.headers.get("access-control-request-headers", "*")

    # Si origin non autorisée -> on répond 204 sans l'autoriser
    if origin and ("*" not in allowed_origins) and (origin not in allowed_origins):
        return Response(status_code=204)

    headers = {
        "Access-Control-Allow-Origin": origin or "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": req_headers,
        "Vary": "Origin",
    }
    return Response(status_code=204, headers=headers)


# ----------------------------
# ROUTES
# ----------------------------
# Core API
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(salons.router)
app.include_router(seo.router)

# Wix
app.include_router(wix_routes.router)
app.include_router(wix_oauth_router)
app.include_router(wix_webhooks_router)
app.include_router(wix_token_router)
app.include_router(wix_seo_push_router)

# app.include_router(movement.router)


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Luxura Inventory API",
        "docs": "/docs",
        "health": "/health",
    }


@app.head("/")
def root_head():
    return Response(status_code=200)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.head("/health")
def health_head():
    return Response(status_code=200)


# ----------------------------
# STARTUP
# ----------------------------
@app.on_event("startup")
def on_startup() -> None:
    SQLModel.metadata.create_all(engine)
