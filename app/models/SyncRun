from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class SyncRun(SQLModel, table=True):
    __tablename__ = "sync_runs"

    id: Optional[int] = Field(default=None, primary_key=True)

    job: str = Field(default="wix_sync", index=True)
    status: str = Field(default="running")  # running | success | error

    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

    limit: Optional[int] = None
    dry_run: bool = False

    created: int = 0
    updated: int = 0
    inventory_written: int = 0
    parents_processed: Optional[int] = None
    variants_seen: Optional[int] = None

    error: Optional[str] = None
