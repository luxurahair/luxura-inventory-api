# app/models.py
from typing import Optional

from sqlmodel import SQLModel, Field

# ─────────────────────────────────────────
# PRODUITS
# ─────────────────────────────────────────

class ProductBase(SQLModel):
    """Champs communs d'un produit Luxura."""
    sku: str                      # ex: "TAPE-18-60A"
    name: str                     # Nom du produit
    length: Optional[str] = None  # ex: "18", "20", "18-20"
    color: Optional[str] = None   # ex: "60A", "N8"
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
    sku: Optional[str] = None
    name: Optional[str] = None
    length: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    active: Optional[bool] = None


# ─────────────────────────────────────────
# SALONS
# ─────────────────────────────────────────

class SalonBase(SQLModel):
    name: str
    address: Optional[str] = None


class Salon(SalonBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class SalonCreate(SalonBase):
    pass


class SalonRead(SalonBase):
    id: int


class SalonUpdate(SQLModel):
    name: Optional[str] = None
    address: Optional[str] = None


# ─────────────────────────────────────────
# INVENTAIRE PAR SALON
# ─────────────────────────────────────────

class InventoryBase(SQLModel):
    salon_id: int
    product_id: int
    quantity: int = 0


class InventoryItem(InventoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class InventoryCreate(InventoryBase):
    pass


class InventoryRead(InventoryBase):
    id: int


class InventoryUpdate(SQLModel):
    salon_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
