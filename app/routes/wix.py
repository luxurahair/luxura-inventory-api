# app/routes/wix.py

from fastapi import APIRouter, HTTPException
from app.services.wix_sync import sync_wix_to_luxura

router = APIRouter(prefix="/wix", tags=["wix"])


@router.get("/debug-products")
def debug_wix_products():
    """
    Debug: exécute une mini-sync "dry run" et retourne un échantillon normalisé.
    IMPORTANT: ne touche pas à la DB.
    """
    try:
        # On appelle la sync en mode "limit petit", mais sans commit DB
        # => Pour garder ça simple, on fait plutôt une vraie sync limit=20 ?
        # Non: debug doit éviter d'écrire. Donc on lève si tu veux du dry-run.
        # Ici: on te donne juste un message clair.
        raise HTTPException(
            status_code=501,
            detail="debug-products a été désactivé. Utilise POST /wix/sync?limit=20 puis GET /products."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
def wix_sync(limit: int = 500):
    """
    Sync complète des produits Wix (Stores v1) vers la DB Luxura.
    1 produit Wix = 1 ligne Product (wix_id unique).
    Variantes stockées dans Product.options (JSONB).
    """
    try:
        return sync_wix_to_luxura(limit=limit)
    except Exception as e:
        # On renvoie un 500 JSON lisible (pas "Internal Server Error" opaque)
        raise HTTPException(status_code=500, detail=str(e))
