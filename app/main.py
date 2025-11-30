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
from fastapi.middleware.cors import CORSMiddleware
import os

origins_env = os.getenv("CORS_ORIGINS", "").strip()

if origins_env:
    # Exemple de valeur dans Render :
    #   https://luxurahair.github.io,https://www.luxuradistribution.com,https://luxuradistribution.com
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    # ⚠️ Ici on met tes vrais domaines front
    allowed_origins = [
        "https://luxurahair.github.io",
        "https://luxurahair.github.io/luxura-inventory-frontend",
        "https://luxurahair.github.io/luxura-inventory-frontend/",
        "https://www.luxuradistribution.com",
        "https://luxuradistribution.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # tu n'utilises pas de cookies → on met False
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
