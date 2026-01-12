from typing import Optional, Dict, Any
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # ✅ Parent Wix (NON unique, car plusieurs variants partagent le même product_id Wix)
    wix_id: Optional[str] = Field(default=None, index=True)

    # ✅ SKU = clé logique d’un variant
    sku: Optional[str] = Field(default=None, index=True, unique=True)

    name: str
    price: float = 0.0
    description: Optional[str] = None
    handle: Optional[str] = Field(default=None, index=True)

    is_in_stock: bool = True
    quantity: int = 0

    # Options/choices (Longueur, Couleur, wix_variant_id, etc.)
    options: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    created_at: datetime = Field(default_factory=now_utc)

    # ✅ se met à jour automatiquement à chaque UPDATE
    updated_at: datetime = Field(default_factory=now_utc, sa_column_kwargs={"onupdate": now_utc})


class ProductCreate(SQLModel):
    wix_id: Optional[str] = None
    sku: Optional[str] = None

    name: str
    price: float = 0.0
    description: Optional[str] = None
    handle: Optional[str] = None
    is_in_stock: bool = True
    quantity: int = 0
    options: Dict[str, Any] = Field(default_factory=dict)


class ProductRead(SQLModel):
    id: int
    wix_id: Optional[str] = None
    sku: Optional[str] = None

    name: str
    price: float = 0.0
    description: Optional[str] = None
    handle: Optional[str] = None
    is_in_stock: bool
    quantity: int
    options: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ProductUpdate(SQLModel):
    wix_id: Optional[str] = None
    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    handle: Optional[str] = None
    is_in_stock: Optional[bool] = None
    quantity: Optional[int] = None
    options: Optional[Dict[str, Any]] = None
