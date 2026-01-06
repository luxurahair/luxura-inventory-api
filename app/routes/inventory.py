# app/routes/inventory.py

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.inventory import InventoryItem, InventoryRead
from app.models.product import Product

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get(
    "",
    response_model=List[InventoryRead],
    summary="Lister l’inventaire par salon & produit",
)
def list_inventory(
    salon_id: Optional[int] = None,
    product_id: Optional[int] = None,
    session: Session = Depends(get_session),
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

    return session.exec(stmt).all()


@router.get(
    "/view",
    summary="Vue lisible de l’inventaire (JOIN Product)",
)
def inventory_view(
    salon_id: Optional[int] = None,
    product_id: Optional[int] = None,
    session: Session = Depends(get_session),
) -> List[Dict[str, Any]]:
    """
    Vue lisible de l’inventaire (JOIN InventoryItem -> Product)
    Retourne: sku + name + quantity + options + price (si dispo).
    """
    stmt = select(InventoryItem, Product).join(Product, Product.id == InventoryItem.product_id)

    if salon_id is not None:
        stmt = stmt.where(InventoryItem.salon_id == salon_id)
    if product_id is not None:
        stmt = stmt.where(InventoryItem.product_id == product_id)

    rows = session.exec(stmt).all()

    out: List[Dict[str, Any]] = []
    for inv, prod in rows:
        out.append(
            {
                "inventory_id": inv.id,
                "salon_id": inv.salon_id,
                "product_id": inv.product_id,
                "quantity": inv.quantity,
                "sku": prod.sku,
                "name": prod.name,
                "price": getattr(prod, "price", None),
                "options": getattr(prod, "options", None),
                "wix_id": getattr(prod, "wix_id", None),
                "is_active": getattr(prod, "active", None),
            }
        )

    return out
