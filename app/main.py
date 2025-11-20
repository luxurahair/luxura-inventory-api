# app/main.py
from contextlib import asynccontextmanager
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import DB init (création des tables) et, optionnellement, le moteur
from app.db import init_db

# ──────────────────────────────────────────────────────────────────────────────
# Lifespan: exécute init_db() au démarrage (recommandé avec FastAPI ≥0.95)
# ──────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Création des tables au boot
    init_db()
    yield
    # (optionnel) ajouter un teardown ici si nécessaire


# ──────────────────────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Luxura API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS (autorise ton site ou tout le monde par défaut)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins.split(",")] if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────────
# Inclusions conditionnelles de routeurs si présents
# (n'empêche pas l'appli de démarrer si un module manque)
# ──────────────────────────────────────────────────────────────────────────────
def try_include(router_path: str, prefix: str, tags: Optional[list[str]] = None):
    """
    Importe et inclut un router si le module existe. Évite un crash au boot
    quand un router est absent.
    """
    try:
        module_path, obj_name = router_path.rsplit(":", 1)
        module = __import__(module_path, fromlist=[obj_name])
        router = getattr(module, obj_name)
        app.include_router(router, prefix=prefix, tags=tags or [])
    except Exception:
        # Silencieux: l'API démarrera quand même sans ce router
        pass

# Exemple: si tu as app/routes/salons.py avec `router = APIRouter()`
try_include("app.routes.products:router", prefix="/products", tags=["products"])


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints de base
# ──────────────────────────────────────────────────────────────────────────────
@app.head("/")
def root_head():
    return {"status": "ok"}

@app.get("/", summary="Ping API")
def root():
    return {"status": "ok", "app": "Luxura API"}

@app.get("/healthz", summary="Health check")
def healthz():
    return {"ok": True}

@app.get("/version", summary="Version de l'API")
def version():
    return {"version": app.version}
