from typing import Any, Dict

from fastapi import APIRouter

# Toutes les routes Wix auront le prefix /wix
router = APIRouter(prefix="/wix", tags=["wix"])


@router.post("/order-webhook")
async def wix_order_webhook(payload: Dict[str, Any]):
    """
    Webhook de commande Wix.
    Pour l'instant : on logge simplement et on renvoie {}.
    Tu pourras plus tard décrémenter l'inventaire ici.
    """
    print("[WIX WEBHOOK] Payload reçu :", payload)
    return {}
