import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import products, salons, inventory, wix
from app.services.wix_sync import sync_wix_to_luxura


app = FastAPI(
    title="Luxura Inventory API",
    version="1.0.0",
)


# ------------------------------------------------
#  CORS
# ------------------------------------------------
allowed_origins = [
    # Frontend GitHub Pages
    "https://luxurahair.github.io",
    "https://luxurahair.github.io/luxura-inventory-frontend",
    "https://luxurahair.github.io/luxura-inventory-frontend/",
    # Ton site Wix (live)
    "https://www.luxuradistribution.com",
    "https://luxuradistribution.com",
    # Editeur Wix
    "https://editor.wix.com",
    "https://manage.wix.com",
    # certains assets Wix
    "https://static.parastorage.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # pas besoin de cookies/session
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
#  STARTUP : synchro automatique Wix → Luxura
# ------------------------------------------------
@app.on_event("startup")
def startup_event() -> None:
    print("--------------------------------------------------")
    print("[STARTUP] Démarrage de l'API Luxura Inventory")
    print("--------------------------------------------------")

    try:
        summary = sync_wix_to_luxura()
        print("[STARTUP] Synchro Wix → Luxura : OK")
        print("[STARTUP] Résumé :", summary)
    except Exception as e:
        # On log mais on ne fait pas crasher l'API si Wix foire
        print("[STARTUP] ERREUR de synchro Wix → Luxura :", repr(e))


# ------------------------------------------------
#  Routes système
# ------------------------------------------------
@app.get("/", tags=["default"])
def root():
    return "Luxura Inventory API"


@app.get("/healthz", tags=["default"])
def healthz():
    return "ok"


@app.get("/version", tags=["default"])
def version():
    return app.version


# ------------------------------------------------
#  Routers métier
# ------------------------------------------------
app.include_router(products.router)
app.include_router(salons.router)
app.include_router(inventory.router)
app.include_router(wix.router)
