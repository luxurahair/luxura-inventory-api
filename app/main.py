import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.db.session import engine
from app.routes import wix as wix_routes
from app.routes import products

app = FastAPI(
    title="Luxura Inventory API",
    version="2.0.0",
)
print("### LOADED app/main.py - Luxura Inventory API ###")

# ----------------------------
#  CORS
# ----------------------------
origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()] if origins_env else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
#  ROUTES
# ----------------------------
app.include_router(wix_routes.router)
app.include_router(products.router)

# (On réactive après)
# from app.routes import inventory, salons, movement
# app.include_router(inventory.router)
# app.include_router(salons.router)
# app.include_router(movement.router)

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"ok": True, "service": "Luxura Inventory API", "docs": "/docs", "health": "/health"}

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}

# ----------------------------
#  STARTUP
# ----------------------------
@app.on_event("startup")
def on_startup() -> None:
    SQLModel.metadata.create_all(engine)
