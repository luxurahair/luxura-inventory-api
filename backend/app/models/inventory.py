from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class InventoryItem(SQLModel, table=True):
    __tablename__ = "inventory_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    salon_id: int = Field(index=True, foreign_key="salon.id")
    product_id: int = Field(index=True, foreign_key="product.id")
    quantity: int = Field(default=0)

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class InventoryRead(SQLModel):
    id: int
    salon_id: int
    product_id: int
    quantity: int
