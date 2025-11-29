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
origins_env = os.getenv("CORS_ORIGINS", "")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    # 💡 En dev seulement ; en prod mets tes vrais domaines
    # ex: ["https://luxurahair.github.io", "https://www.luxuradistribution.com"]
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
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
