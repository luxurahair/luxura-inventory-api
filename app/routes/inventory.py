# app/routes/inventory.py

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import InventoryItem, InventoryRead

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
)

SessionDep = Depends(get_session)


@router.get(
    "",
    response_model=List[InventoryRead],
    summary="Lister l’inventaire par salon & produit",
)
def list_inventory(
    session: Session = SessionDep,
    salon_id: Optional[int] = None,
    product_id: Optional[int] = None,
) -> List[InventoryRead]:
    """
    Retourne l’inventaire.

    - Sans paramètre : tous les enregistrements
    - Avec salon_id : filtre par salon
    - Avec product_id : filtre par produit
    """
    stmt = select(InventoryItem)
    if salon_id is not None:
        stmt = stmt.where(InventoryItem.salon_id == salon_id)
    if product_id is not None:
        stmt = stmt.where(InventoryItem.product_id == product_id)

    rows = session.exec(stmt).all()
    return rows
