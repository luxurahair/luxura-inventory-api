from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.services.wix_sync import sync_wix_to_luxura

# Toutes les routes Wix auront le prefix /wix
router = APIRouter(prefix="/wix", tags=["wix"])


@router.post("/order-webhook")
async def wix_order_webhook(payload: Dict[str, Any]):
    """
    Webhook de commande Wix.
    Pour l'instant : on logge simplement et on renvoie {}.
    Plus tard, tu pourras décrémenter l'inventaire ici.
    """
    print("[WIX WEBHOOK] Payload reçu :", payload)
    return {}


@router.post("/sync", summary="Forcer une synchro Wix → Luxura")
def wix_sync_endpoint():
    """
    Synchro MANUELLE Wix → Luxura.
    (En plus de la synchro automatique au démarrage.)
    """
    try:
        summary = sync_wix_to_luxura()
        return {
            "ok": True,
            "source": "manual",
            **summary,
        }
    except Exception as e:
        # On renvoie une erreur claire à Swagger
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la synchro Wix → Luxura : {repr(e)}",
        )
