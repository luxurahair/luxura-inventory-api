# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlmodel import SQLModel

from app.db import engine

# Routes
from app.routes import inventory, products, salons, seo
from app.routes import wix as wix_routes
from app.routes.wix_oauth import router as wix_oauth_router
from app.routes.wix_webhooks import router as wix_webhooks_router
from app.routes.wix_token import router as wix_token_router
from app.routes.wix_seo_push import router as wix_seo_push_router

app = FastAPI(
    title="Luxura Inventory API",
    version="2.0.0",
)

print("### LOADED Luxura Inventory API ###")

# -------------------------------------------------
# CORS — VERSION STABLE (COMME LE 19 JANVIER)
# -------------------------------------------------

origins = [
    "https://editor.wix.com",
    "https://www.wix.com",
    "https://manage.wix.com",
    "https://static.wixstatic.com",
    "https://www.luxuradistribution.com",
    "https://luxuradistribution.com",
    "https://luxurahair.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,      # 🔥 OBLIGATOIRE POUR WIX / IFRAme
    allow_methods=["*"],          # inclut OPTIONS
    allow_headers=["*"],
)

# -------------------------------------------------
# ROUTES
# -------------------------------------------------
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(salons.router)
app.include_router(seo.router)

app.include_router(wix_routes.router)
app.include_router(wix_oauth_router)
app.include_router(wix_webhooks_router)
app.include_router(wix_token_router)
app.include_router(wix_seo_push_router)

# -------------------------------------------------
# ROOT / HEALTH
# -------------------------------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Luxura Inventory API",
        "docs": "/docs",
        "health": "/health",
    }

@app.options("/{path:path}")
def options_handler(path: str):
    return Response(status_code=200)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
