from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ----------------------------
# DB MODEL (table)
# ----------------------------
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # ID produit Wix (unique)
    wix_id: str = Field(index=True, unique=True)

    sku: Optional[str] = Field(default=None, index=True)
    name: str
    price: float = 0.0
    description: Optional[str] = None
    handle: Optional[str] = Field(default=None, index=True)

    is_in_stock: bool = True
    quantity: int = 0

    # options / variants en JSON
    options: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


# ----------------------------
# API SCHEMAS
# ----------------------------
class ProductCreate(SQLModel):
    wix_id: str
    sku: Optional[str] = None
    name: str
    price: float = 0.0
    description: Optional[str] = None
    handle: Optional[str] = None
    is_in_stock: bool = True
    quantity: int = 0
    options: Dict[str, Any] = Field(default_factory=dict)


c
