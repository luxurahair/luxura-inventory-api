import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ⬇️ Adapte ces imports si tes modules ne sont pas exactement à ces chemins
from app.routes import products, salons, inventory, wix
# Dans ton script de sync, si la fonction s'appelle autrement,
# change "main" par le bon nom.
try:
    from scripts.sync_wix_to_luxura import main as sync_wix_to_luxura
except ImportError:
    sync_wix_to_luxura = None


app = FastAPI(
    title="Luxura Inventory API",
    version="1.0.0",
)


# ---------------- CORS ---------------- #

origins_env = os.getenv("CORS_ORIGINS", "")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    # En dev seulement. En prod, mets ta variable CORS_ORIGINS sur Render.
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- Startup : sync Wix -> DB ---------------- #

@app.on_event("startup")
def startup_event() -> None:
    """
    Au démarrage de l'API :
      - on lance une synchro Wix -> base Luxura (si le script est dispo)
    """
    if sync_wix_to_luxura is None:
        print("[STARTUP] Pas de sync_wix_to_luxura importée (ok pour l’instant).")
        return

    try:
        print("[STARTUP] Lancement de la synchro Wix -> Luxura…")
        sync_wix_to_luxura()
        print("[STARTUP] Synchro Wix -> Luxura TERMINÉE ✅")
    except Exception as e:
        # On log juste, on ne bloque pas le démarrage de l’API
        print("[STARTUP] Erreur pendant la synchro Wix :", repr(e))


# ---------------- Routes système ---------------- #

@app.get("/", tags=["default"])
def root():
    return "Luxura Inventory API"


@app.get("/healthz", tags=["default"])
def healthz():
    return "ok"


@app.get("/version", tags=["default"])
def version():
    return app.version


# ---------------- Routers métier ---------------- #

# Chaque router définit déjà son propre prefix (ex: "/products", "/salons", etc.)
app.include_router(products.router)
app.include_router(salons.router)
app.include_router(inventory.router)
app.include_router(wix.router)
