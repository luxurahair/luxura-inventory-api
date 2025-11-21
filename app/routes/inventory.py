# app/routes/inventory.py

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import func

from app.db import get_session
from app.models import (
    InventoryItem,
    InventoryCreate,
    InventoryRead,
    InventoryUpdate,
    Product,
    Salon,
)

router = APIRouter()

# ─────────────────────────────────────────
# Routes Inventaire par salon
# ─────────────────────────────────────────

@router.post(
    "/",
    response_model=InventoryRead,
    summary="Créer / définir un stock",
)
def create_inventory_item(
    item_in: InventoryCreate,
    session: Session = Depends(get_session),
) -> InventoryRead:
    """
    Crée une nouvelle ligne d'inventaire pour un salon et un produit.
    (Pas de logique de "upsert" ici : on crée une nouvelle ligne à chaque appel.)
    """
    item = InventoryItem(**item_in.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get(
    "/",
    response_model=List[InventoryRead],
    summary="Lister l'inventaire",
)
def list_inventory(
    session: Session = Depends(get_session),
    salon_id: Optional[int] = Query(default=None),
    product_id: Optional[int] = Query(default=None),
) -> List[InventoryRead]:
    """
    Liste les lignes d'inventaire, avec possibilité de filtrer
    par salon_id et/ou product_id.
    """
    statement = select(InventoryItem)

    if salon_id is not None:
        statement = statement.where(InventoryItem.salon_id == salon_id)

    if product_id is not None:
        statement = statement.where(InventoryItem.product_id == product_id)

    items = session.exec(statement).all()
    return items


@router.get(
    "/{item_id}",
    response_model=InventoryRead,
    summary="Récupérer une ligne d'inventaire",
)
def get_inventory_item(
    item_id: int,
    session: Session = Depends(get_session),
) -> InventoryRead:
    """
    Récupère une ligne d'inventaire par son ID.
    """
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ligne d'inventaire introuvable")
    return item


@router.put(
    "/{item_id}",
    response_model=InventoryRead,
    summary="Mettre à jour une ligne d'inventaire",
)
def update_inventory_item(
    item_id: int,
    item_in: InventoryUpdate,
    session: Session = Depends(get_session),
) -> InventoryRead:
    """
    Met à jour une ligne d'inventaire existante.
    """
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ligne d'inventaire introuvable")

    data = item_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(item, key, value)

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete(
    "/{item_id}",
    summary="Supprimer une ligne d'inventaire",
)
def delete_inventory_item(
    item_id: int,
    session: Session = Depends(get_session),
) -> dict:
    """
    Supprime une ligne d'inventaire par son ID.
    """
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ligne d'inventaire introuvable")

    session.delete(item)
    session.commit()
    return {"ok": True}


# ─────────────────────────────────────────
# Résumé global de l'inventaire
# ─────────────────────────────────────────

@router.get(
    "/summary",
    summary="Résumé d'inventaire par produit et par salon",
)
def inventory_summary(
    session: Session = Depends(get_session),
) -> List[Dict[str, Any]]:
    """
    Pour chaque produit (SKU), retourne :
    - la quantité totale (tous salons confondus)
    - la répartition de cette quantité par salon
    """

    # 1) Agrégation DB : Product + Salon + SUM(InventoryItem.quantity)
    stmt = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            Salon.id,
            Salon.name,
            func.sum(InventoryItem.quantity),
        )
        .join(Product, Product.id == InventoryItem.product_id)
        .join(Salon, Salon.id == InventoryItem.salon_id)
        .group_by(Product.id, Product.sku, Product.name, Salon.id, Salon.name)
    )

    rows = session.exec(stmt).all()

    # 2) Regroupement par produit côté Python
    summary: Dict[int, Dict[str, Any]] = {}

    for product_id, sku, product_name, salon_id, salon_name, qty in rows:
        qty = qty or 0

        if product_id not in summary:
            summary[product_id] = {
                "product_id": product_id,
                "sku": sku,
                "name": product_name,
                "total_quantity": 0,
                "by_salon": [],
            }

        summary[product_id]["total_quantity"] += qty
        summary[product_id]["by_salon"].append(
            {
                "salon_id": salon_id,
                "salon_name": salon_name,
                "quantity": qty,
            }
        )

    return list(summary.values())

