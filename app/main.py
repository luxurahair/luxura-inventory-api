import os
import requests  # 👈 IMPORTANT

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import products, salons, inventory, wix
from scripts.sync_wix_to_luxura import sync_wix_products  # ⬅️ IMPORTANT


# --------- Variables d'environnement Wix --------- #
WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_ACCOUNT_ID = os.getenv("WIX_ACCOUNT_ID")


# --------- App FastAPI --------- #

app = FastAPI(
    title="Luxura Inventory API",
    version="1.0.0",
)


# --------- CORS --------- #

origins_env = os.getenv("CORS_ORIGINS", "")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    allowed_origins = ["*"]  # dev uniquement

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


from app.routes import products, salons, inventory, wix
# ...

# --------- Routers métier --------- #

# 1) D'ABORD le router Wix (routes fixes comme /wix-sites)
app.include_router(wix.router)

# 2) Ensuite les autres
app.include_router(products.router)
app.include_router(salons.router)
app.include_router(inventory.router)



# --------- DEBUG : lister les sites Wix --------- #

@app.get("/wix-sites", tags=["debug"])
def wix_sites():
    """
    Debug : liste les sites que Wix voit avec ta clé API,
    pour qu'on récupère le bon siteId / metaSiteId.
    """
    url = "https://www.wixapis.com/account/v1/sites"
    headers = {
        "Authorization": WIX_API_KEY,
        "wix-account-id": WIX_ACCOUNT_ID,
    }

    try:
        res = requests.get(url, headers=headers, timeout=20)
    except Exception as e:
        return {"status": "error", "error": str(e)}

    try:
        data = res.json()
    except Exception:
        data = {"raw": res.text}

    return {"status": res.status_code, "data": data}
