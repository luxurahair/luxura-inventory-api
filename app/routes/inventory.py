# app/routes/inventory.py
from typing import List, Dict, Any

from fastapi import APIRouter

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
    Version simplifiée de l’endpoint d’inventaire.

    Pour l’instant :
    - ne dépend d’aucun modèle (pas d'ImportError)
    - n’attend aucun paramètre (pas de 422)
    - renvoie simplement une liste vide.

    On branchera la vraie logique plus tard (agrégation des mouvements).
    """
    return []
