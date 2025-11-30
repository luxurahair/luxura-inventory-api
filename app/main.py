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
#  STARTUP : synchro Wix → Luxura (une fois au boot)
# ------------------------------------------------
@app.on_event("startup")
def startup_event() -> None:
    print("--------------------------------------------------")
    print("[STARTUP] Démarrage de l'API Luxura Inventory")
    print("--------------------------------------------------")

    try:
        print("[WIX SYNC] Début synchro Wix → Luxura")
        summary = sync_wix_to_luxura()
        print(f"[WIX SYNC] Terminé : {summary}")
        print(f"[STARTUP] Résumé : {summary}")
    except Exception as e:
        # On ne casse pas l'API si Wix plante
        print("[WIX SYNC] ERREUR pendant la synchro :", repr(e))
        print("[STARTUP] Synchro Wix → Luxura : ÉCHEC (API quand même opérationnelle)")


# ------------------------------------------------
#  ROUTES
# ------------------------------------------------
app.include_router(salons.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(wix.router)
