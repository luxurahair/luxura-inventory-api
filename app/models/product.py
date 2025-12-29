from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=List[ProductRead], summary="Lister tous les produits")
def list_products(session: Session = Depends(get_session)) -> List[ProductRead]:
    return session.exec(select(Product)).all()


@router.get("/{product_id}", response_model=ProductRead, summary="Récupérer un produit")
def get_product(product_id: int, session: Session = Depends(get_session)) -> ProductRead:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return product


@router.post("", response_model=ProductRead, summary="Créer un produit")
def create_product(payload: ProductCreate, session: Session = Depends(get_session)) -> ProductRead:
    product = Product.from_orm(payload)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.post("/wix-sync", response_model=ProductRead, summary="Créer ou mettre à jour un produit depuis Wix")
def upsert_product_from_wix(payload: ProductCreate, session: Session = Depends(get_session)) -> ProductRead:
    product = session.exec(select(Product).where(Product.wix_id == payload.wix_id)).first()
    data = payload.dict(exclude_unset=True)

    if product:
        for key, value in data.items():
            setattr(product, key, value)
    else:
        product = Product.from_orm(payload)
        session.add(product)

    product.updated_at = datetime.now(timezone.utc)  # ✅ ICI
    session.commit()
    session.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductRead, summary="Mettre à jour un produit")
def update_product(product_id: int, payload: ProductUpdate, session: Session = Depends(get_session)) -> ProductRead:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(product, key, value)

    product.updated_at = datetime.now(timezone.utc)  # ✅ ICI
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204, summary="Supprimer un produit")
def delete_product(product_id: int, session: Session = Depends(get_session)) -> None:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    session.delete(product)
    session.commit()
