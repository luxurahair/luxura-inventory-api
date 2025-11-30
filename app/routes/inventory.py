# app/routes/inventory.py
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Inventory, InventoryRead  # adapte ces noms si besoin

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
)

SessionDep = Depends(get_session)


@router.get(
    "",
    response_model=List[InventoryRead],
    summary="Lister l’inventaire consolidé",
)
def list_inventory(
    session: Session = SessionDep,
    salon_id: Optional[int] = None,
    product_id: Optional[int] = None,
) -> List[InventoryRead]:
    """
    Retourne l’inventaire.
    - Sans paramètre → tous les enregistrements
    - Avec salon_id → filtre par salon
    - Avec product_id → filtre par produit
    Aucun paramètre n’est obligatoire → pas de 422 sur GET /inventory.
    """
    stmt = select(Inventory)

    if salon_id is not None:
        stmt = stmt.where(Inventory.salon_id == salon_id)
    if product_id is not None:
        stmt = stmt.where(Inventory.product_id == product_id)

    return session.exec(stmt).all()

