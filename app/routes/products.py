from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Product, ProductCreate, ProductRead, ProductUpdate

router = APIRouter(
    prefix="/products",
    tags=["products"],
)

SessionDep = Depends(get_session)


@router.get(
    "",
    response_model=List[ProductRead],
    summary="Lister tous les produits",
)
def list_products(
    session: Session = SessionDep,
) -> List[ProductRead]:
    """
    Retourne la liste complète des produits.
    Aucun paramètre requis -> ne peut PAS renvoyer 422.
    """
    products = session.exec(select(Product)).all()
    return products


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Récupérer un produit",
)
def get_product(
    product_id: int,
    session: Session = SessionDep,
) -> ProductRead:
    """Récupérer un produit par son ID."""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return product


@router.post(
    "/wix-sync",
    response_model=ProductRead,
    summary="Créer ou mettre à jour un produit depuis Wix",
)
def upsert_product_from_wix(
    payload: ProductCreate,
    session: Session = SessionDep,
) -> ProductRead:

    product = session.exec(
        select(Product).where(Product.wix_id == payload.wix_id)
    ).first()

    if product:
        # UPDATE
        data = payload.dict(exclude_unset=True)
        for key, value in data.items():
            setattr(product, key, value)
    else:
        # CREATE
        product = Product.from_orm(payload)
        session.add(product)

    session.commit()
    session.refresh(product)
    return product

def create_product(
    payload: ProductCreate,
    session: Session = SessionDep,
) -> ProductRead:
    """Créer un nouveau produit."""
    product = Product.from_orm(payload)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Mettre à jour un produit",
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    session: Session = SessionDep,
) -> ProductRead:
    """Mettre à jour un produit existant."""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(product, key, value)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete(
    "/{product_id}",
    status_code=204,
    summary="Supprimer un produit",
)
def delete_product(
    product_id: int,
    session: Session = SessionDep,
) -> None:
    """Supprimer un produit."""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    session.delete(product)
    session.commit()
