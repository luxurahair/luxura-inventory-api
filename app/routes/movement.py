# app/routes/movement.py

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import InventoryItem

router = APIRouter(
    tags=["movement"],
)

SessionDep = Depends(get_session)


@router.post(
    "/movement",
    summary="Enregistrer un mouvement et mettre à jour l’inventaire",
)
def record_movement(
    type: Literal["IN", "OUT", "SALE", "ADJUST"] = Query(..., description="Type de mouvement"),
    salon_id: int = Query(..., description="ID du salon"),
    product_id: int = Query(..., description="ID du produit"),
    qty: int = Query(..., gt=0, description="Quantité > 0"),
    note: Optional[str] = Query(None, description="Note optionnelle (non stockée pour l’instant)"),
    session: Session = SessionDep,
):
    """
    Applique un mouvement sur l’inventaire.

    - IN      : quantité += qty
    - OUT     : quantité -= qty (jamais < 0)
    - SALE    : quantité -= qty (jamais < 0)
    - ADJUST  : quantité = qty (ajustement absolu)

    Si aucune ligne d’inventaire n’existe pour (salon_id, product_id),
    elle est créée automatiquement avec quantity = 0 avant d’appliquer le mouvement.
    """
    # On cherche la ligne d'inventaire existante
    stmt = select(InventoryItem).where(
        InventoryItem.salon_id == salon_id,
        InventoryItem.product_id == product_id,
    )
    inv = session.exec(stmt).first()

    if inv is None:
        inv = InventoryItem(salon_id=salon_id, product_id=product_id, quantity=0)
        session.add(inv)
        session.flush()  # pour obtenir inv.id

    if type == "IN":
        inv.quantity += qty
    elif type in ("OUT", "SALE"):
        inv.quantity -= qty
        if inv.quantity < 0:
            inv.quantity = 0
    elif type == "ADJUST":
        inv.quantity = qty
    else:
        raise HTTPException(status_code=400, detail="Type de mouvement invalide")

    session.add(inv)
    session.commit()
    session.refresh(inv)

    return {
        "ok": True,
        "type": type,
        "salon_id": inv.salon_id,
        "product_id": inv.product_id,
        "quantity": inv.quantity,
        "inventory_id": inv.id,
    }
