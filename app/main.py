# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlmodel import SQLModel

from app.db import engine

# Routers
from app.routes import inventory, products, salons, seo
from app.routes import wix as wix_routes
from app.routes.wix_oauth import router as wix_oauth_router
from app.routes.wix_webhooks import router as wix_webhooks_router
from app.routes.wix_token import router as wix_token_router
from app.routes.wix_seo_push import router as wix_seo_push_router

print("### LOADING Luxura Inventory API ###")

app = FastAPI(
    title="Luxura Inventory API",
    version="2.0.0",
)

# ----------------------------
# CORS — DOIT ÊTRE AVANT LES ROUTES
# ----------------------------
origins_env = os.getenv("CORS_ORIGINS", "").strip()

if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "https://editor.wix.com",
        "https://www.wix.com",
        "https://manage.wix.com",
        "https://static.wixstatic.com",
        "https://www.luxuradistribution.com",
        "https://luxuradistribution.com",
        "https://luxurahair.github.io",  # GitHub Pages UI
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# ROUTES
# ----------------------------
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(salons.router)
app.include_router(seo.router)

app.include_router(wix_routes.router)
app.include_router(wix_oauth_router)
app.include_router(wix_webhooks_router)
app.include_router(wix_token_router)
app.include_router(wix_seo_push_router)

# ----------------------------
# ROOT / HEALTH
# ----------------------------
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

@app.get("/cors/ping")
def cors_ping():
    return {"ok": True}

# ----------------------------
# STARTUP
# ----------------------------
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
