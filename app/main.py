# app/main.py
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routes.products import router as products_router
from app.routes.salons import router as salons_router
from app.routes.inventory import router as inventory_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Création des tables au démarrage
    init_db()
    yield
    # teardown éventuel plus tard si besoin


app = FastAPI(
    title="Luxura API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─────────────────────────────────────────
# CORS
# ─────────────────────────────────────────
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins.split(",")] if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# Routers
# ─────────────────────────────────────────
app.include_router(products_router, prefix="/products", tags=["products"])
app.include_router(salons_router, prefix="/salons", tags=["salons"])
app.include_router(inventory_router, prefix="/inventory", tags=["inventory"])


# ─────────────────────────────────────────
# Endpoints de base
# ─────────────────────────────────────────
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

