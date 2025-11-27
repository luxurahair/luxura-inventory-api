import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import products, salons, inventory, wix

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
    # en dev seulement ; en prod, mets des domaines précis
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
#  STARTUP (aucune synchro Wix pour l’instant)
# ------------------------------------------------
@app.on_event("startup")
def startup_event() -> None:
    print("[STARTUP] Aucune synchro Wix au démarrage (désactivée).")


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
#  Route produits (liste simple pour l’instant)
# ------------------------------------------------
@app.get("/products/", tags=["products"])
def list_products_stub():
    """
    Stub temporaire : renvoie une liste vide de produits.
    On met ça pour que /products/ réponde proprement,
    sans se faire intercepter par une route dynamique /{product_id}.
    """
    return []


# ------------------------------------------------
#  Routers métier
# ------------------------------------------------
app.include_router(products.router)
app.include_router(salons.router)
app.include_router(inventory.router)
app.include_router(wix.router)
