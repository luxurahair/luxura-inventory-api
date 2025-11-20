# app/routes/products.py

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, Field, Session, select

from app.db import engine

router = APIRouter()


# ─────────────────────────────────────────────────────────
# Modèles SQLModel
# ─────────────────────────────────────────────────────────

class ProductBase(SQLModel):
    """Champs communs d'un produit."""
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    price: float
    active: bool = True


class Product(ProductBase, table=True):
    """Table products dans la DB."""
    id: Optional[int] = Field(default=None, primary_key=True)


class ProductCreate(ProductBase):
    """Payload pour créer un produit."""
    pass


class ProductRead(ProductBase):
    """Réponse retournée à l'API."""
    id: int


class ProductUpdate(SQLModel):
    """Payload partiel pour mise à jour."""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    active: Optional[bool] = None


# ─────────────────────────────────────────────────────────
# Session DB
# ─────────────────────────────────────────────────────────

def get_session():
    with Session(engine) as session:
        yield session


# ─────────────────────────────────────────────────────────
# Routes CRUD
# ─────────────────────────────────────────────────────────

@router.post("/", response_model=ProductRead, summary="Créer un produit")
def create_product(
    product_in: ProductCreate,
    session: Session = Depends(get_session),
):
    db_product = Product(**product_in.model_dump())
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


@router.get("/", response_model=List[ProductRead], summary="Lister tous les produits")
def list_products(
    session: Session = Depends(get_session),
    only_active: bool = False,
):
    statement = select(Product)
    if only_active:
        statement = statement.where(Product.active == True)  # noqa: E712

    products = session.exec(statement).all()
    return products


@router.get("/{product_id}", response_model=ProductRead, summary="Récupérer un produit")
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return product


@router.put("/{product_id}", response_model=ProductRead, summary="Mettre à jour un produit")
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    session: Session = Depends(get_session),
):
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


@router.delete("/{product_id}", summary="Supprimer un produit")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    session.delete(product)
    session.commit()
    return {"ok": True}
