# app/routes/inventory.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import (
    InventoryItem,
    InventoryCreate,
    InventoryRead,
    InventoryUpdate,
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
