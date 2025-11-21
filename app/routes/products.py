# app/routes/products.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Product, ProductCreate, ProductRead, ProductUpdate

router = APIRouter()


# ─────────────────────────────────────────
# Routes CRUD Produits
# ─────────────────────────────────────────

@router.post(
    "/",
    response_model=ProductRead,
    summary="Créer un produit",
)
def create_product(
    product_in: ProductCreate,
    session: Session = Depends(get_session),
) -> ProductRead:
    """Créer un nouveau produit."""
    db_product = Product(**product_in.model_dump())
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


@router.get(
    "/",
    response_model=List[ProductRead],
    summary="Lister tous les produits",
)
def list_products(
    session: Session = Depends(get_session),
    only_active: bool = False,
) -> List[ProductRead]:
    """Lister tous les produits, avec option pour filtrer uniquement les actifs."""
    statement = select(Product)
    if only_active:
        statement = statement.where(Product.active == True)  # noqa: E712

    products = session.exec(statement).all()
    return products


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Récupérer un produit",
)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> ProductRead:
    """Récupérer un produit par son ID."""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return product


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Mettre à jour un produit",
)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    session: Session = Depends(get_session),
) -> ProductRead:
    """Mettre à jour un produit existant."""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    product_data = product_in.model_dump(exclude_unset=True)
    for key, value in product_data.items():
        setattr(product, key, value)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete(
    "/{product_id}",
    summary="Supprimer un produit",
)
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> dict:
    """Supprimer un produit par son ID."""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    session.delete(product)
    session.commit()
    return {"ok": True}
