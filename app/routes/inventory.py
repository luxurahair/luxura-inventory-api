# app/routes/inventory.py

from typing import List, Dict, Any

from fastapi import APIRouter

# 🔹 C'EST ÇA que FastAPI cherche : "router"
router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
)


@router.get(
    "",
    summary="Lister l’inventaire (placeholder simple)",
)
def list_inventory() -> List[Dict[str, Any]]:
    """
    Endpoint d’inventaire simplifié.

    Pour l’instant :
    - pas de dépendance à app.models (pas d’ImportError)
    - aucun paramètre requis (pas de 422 sur GET /inventory)
    - renvoie simplement une liste vide.

    On branchera la vraie logique plus tard.
    """
    return []
