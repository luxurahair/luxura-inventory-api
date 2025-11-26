import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import products, salons, inventory, wix
from scripts.sync_wix_to_luxura import sync_wix_products  # ⬅️ IMPORTANT


app = FastAPI(
    title="Luxura Inventory API",
    version="1.0.0",
)


# --------- CORS --------- #

origins_env = os.getenv("CORS_ORIGINS", "")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    allowed_origins = ["*"]  # dev seulement

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------- STARTUP : sync Wix -> DB --------- #

@app.on_event("startup")
def startup_event() -> None:
    """
    Au démarrage de l'API :
      - on lance une synchro Wix -> base Luxura
    """
    print("[STARTUP] Lancement de la synchro Wix -> Luxura…")
    try:
        sync_wix_products()
        print("[STARTUP] Synchro Wix -> Luxura TERMINÉE ✅")
    except Exception as e:
        print("[STARTUP] Erreur pendant la synchro Wix :", repr(e))


# --------- Routes système --------- #

@app.get("/", tags=["default"])
def root():
    return "Luxura Inventory API"


@app.get("/healthz", tags=["default"])
def healthz():
    return "ok"


@app.get("/version", tags=["default"])
def version():
    return app.version


# --------- Routers métier --------- #

app.include_router(products.router)
app.include_router(salons.router)
app.include_router(inventory.router)
app.include_router(wix.router)
