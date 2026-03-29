# backlink_routes.py
"""
Routes API pour piloter le pipeline backlinks / citations Luxura.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .backlink_orchestrator import (
    run_backlink_cycle,
    retry_pending_verifications_only,
    load_records_from_snapshot,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/backlinks", tags=["backlinks"])

DEFAULT_SNAPSHOT_PATH = os.getenv(
    "BACKLINK_RUN_OUTPUT_PATH",
    "/app/backend/data/backlink_run_latest.json"
)


# -------------------------------------------------------------------
# Request models
# -------------------------------------------------------------------

class RunBacklinkCycleRequest(BaseModel):
    business_overrides: Optional[Dict[str, Any]] = None
    headless: bool = True
    max_directories: Optional[int] = Field(default=3, ge=1, le=50)
    process_email_verification: bool = True
    verification_days_back: int = Field(default=7, ge=1, le=30)
    click_verification_links: bool = True
    save_snapshot: bool = True
    output_path: Optional[str] = None


class RetryPendingRequest(BaseModel):
    verification_days_back: int = Field(default=7, ge=1, le=30)
    click_verification_links: bool = True
    save_snapshot: bool = True
    output_path: Optional[str] = None


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def load_snapshot_json(path: str = DEFAULT_SNAPSHOT_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Snapshot not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@router.get("/status")
async def backlinks_status():
    """
    Retourne un résumé rapide du dernier snapshot.
    """
    try:
        payload = load_snapshot_json(DEFAULT_SNAPSHOT_PATH)
        return {
            "ok": True,
            "snapshot_path": DEFAULT_SNAPSHOT_PATH,
            "saved_at": payload.get("saved_at"),
            "metadata": payload.get("metadata", {}),
            "run_summary": payload.get("run_summary", {}),
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "message": "No backlink snapshot found yet",
            "snapshot_path": DEFAULT_SNAPSHOT_PATH,
        }
    except Exception as e:
        logger.error(f"Error loading backlinks status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest-run")
async def backlinks_latest_run():
    """
    Retourne le snapshot complet du dernier run.
    """
    try:
        payload = load_snapshot_json(DEFAULT_SNAPSHOT_PATH)
        return {
            "ok": True,
            "snapshot_path": DEFAULT_SNAPSHOT_PATH,
            "data": payload,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No backlink snapshot found")
    except Exception as e:
        logger.error(f"Error loading latest backlink run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records")
async def backlinks_records():
    """
    Retourne juste la liste des records du dernier snapshot.
    """
    try:
        payload = load_snapshot_json(DEFAULT_SNAPSHOT_PATH)
        return {
            "ok": True,
            "count": len(payload.get("records", [])),
            "records": payload.get("records", []),
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No backlink snapshot found")
    except Exception as e:
        logger.error(f"Error loading backlink records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_backlinks(request: RunBacklinkCycleRequest):
    """
    Lance un cycle backlinks complet.
    Conseil: commencer petit (2-3 annuaires max).
    """
    try:
        logger.info("🚀 API /api/backlinks/run called")

        result = await run_backlink_cycle(
            business_overrides=request.business_overrides,
            headless=request.headless,
            max_directories=request.max_directories,
            process_email_verification=request.process_email_verification,
            verification_days_back=request.verification_days_back,
            click_verification_links=request.click_verification_links,
            save_snapshot=request.save_snapshot,
            output_path=request.output_path,
        )

        return {
            "ok": True,
            "message": "Backlink cycle completed",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error running backlink cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry-pending")
async def retry_pending_backlinks(request: RetryPendingRequest):
    """
    Recharge le dernier snapshot et relance seulement les validations email en attente.
    """
    try:
        logger.info("🔁 API /api/backlinks/retry-pending called")

        snapshot_path = request.output_path or DEFAULT_SNAPSHOT_PATH
        records = load_records_from_snapshot(snapshot_path)

        result = await retry_pending_verifications_only(
            records=records,
            verification_days_back=request.verification_days_back,
            click_verification_links=request.click_verification_links,
            save_snapshot=request.save_snapshot,
            output_path=request.output_path,
        )

        return {
            "ok": True,
            "message": "Pending verifications retried",
            "result": result,
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No backlink snapshot found to retry")
    except Exception as e:
        logger.error(f"Error retrying pending verifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))
