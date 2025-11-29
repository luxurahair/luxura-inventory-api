import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routes
from app.routes import products, salons, inventory, wix

# Service de synchro Wix → Luxura
from app.services.wix_sync import sync_wix_to_luxura


# ------------------------------------------------
#  INITIALISATION DE L'API
# ------------------------------------------------
app = FastAPI(
    title="Luxura Inventory API",
    version="1.0.0",
)


# ------------------------------------------------
#  CONFIGURATION CORS
# ------------------------------------------------
origins_env = os.getenv("CORS_ORIGINS", "")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    # ⭐ En développement : on permet tout
    # 💡 En production, mets tes vrais domaines :
    # ["https://luxurahair.github.io", "https://www.luxuradistribution.com"]
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
#  SYNCHRO AUTOMATIQUE AU DÉMARRAGE
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
        # ⚠️ On NE bloque PAS le démarrage si Wix plante.
        print("[STARTUP] ERREUR de synchro Wix → Luxura :", repr(e))


# ------------------------------------------------
#  INCLUSION DES ROUTES
# ------------------------------------------------
app.include_router(products.router)
app.include_router(salons.router)
app.include_router(inventory.router)
app.include_router(wix.router)


# ------------------------------------------------
#  ENDPOINT DE TEST RACINE
# ------------------------------------------------
@app.get("/", tags=["root"])
def root():
    return {"message": "Luxura Inventory API"}
