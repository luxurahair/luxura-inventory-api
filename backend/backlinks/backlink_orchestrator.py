# backlink_orchestrator.py
"""
Orchestrateur principal du pipeline backlinks / citations Luxura.

Responsabilités:
- lancer la soumission annuaires via citation_engine.py
- traiter les emails de validation via email_verification.py
- consolider les résultats
- sauvegarder un snapshot JSON si demandé

Ne gère PAS:
- les routes API
- le dashboard admin
- les guest posts / outreach avancé
"""

from __future__ import annotations

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

from dotenv import load_dotenv

from .citation_engine import (
    submit_submission_queue,
    summarize_submission_results,
)
from .email_verification import (
    process_pending_verifications,
    summarize_verification_results,
)
from .backlink_models import BacklinkRecord, BacklinkRunSummary

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_PATH = os.getenv(
    "BACKLINK_RUN_OUTPUT_PATH",
    "/app/backend/data/backlink_run_latest.json"
)


# -------------------------------------------------------------------
# Helpers JSON / serialization
# -------------------------------------------------------------------

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_parent_dir(path: str):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def record_to_dict(record: BacklinkRecord) -> Dict:
    return record.model_dump(mode="json")


def records_to_dicts(records: List[BacklinkRecord]) -> List[Dict]:
    return [record_to_dict(r) for r in records]


def save_run_snapshot(
    path: str,
    run_summary: Dict,
    records: List[BacklinkRecord],
    metadata: Optional[Dict] = None,
):
    ensure_parent_dir(path)
    payload = {
        "saved_at": utcnow_iso(),
        "metadata": metadata or {},
        "run_summary": run_summary,
        "records": records_to_dicts(records),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# -------------------------------------------------------------------
# Consolidation helpers
# -------------------------------------------------------------------

def merge_summaries(
    submission_summary: Dict,
    verification_summary: Dict,
    records: List[BacklinkRecord]
) -> Dict:
    """
    Produit un résumé consolidé du cycle.
    """
    counts = {
        "total": len(records),
        "new": 0,
        "queued": 0,
        "submitted": 0,
        "email_pending": 0,
        "email_found": 0,
        "verification_clicked": 0,
        "verified": 0,
        "live": 0,
        "failed": 0,
        "skipped": 0,
    }

    for r in records:
        if r.status in counts:
            counts[r.status] += 1

    return {
        "submission_summary": submission_summary,
        "verification_summary": verification_summary,
        "final_counts": counts,
    }


def split_records_for_verification(records: List[BacklinkRecord]) -> List[BacklinkRecord]:
    return [
        r for r in records
        if r.requires_email_verification and r.status in {"submitted", "email_pending", "email_found"}
    ]


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

async def run_backlink_cycle(
    business_overrides: Optional[Dict] = None,
    headless: bool = True,
    max_directories: Optional[int] = None,
    process_email_verification: bool = True,
    verification_days_back: int = 7,
    click_verification_links: bool = True,
    save_snapshot: bool = True,
    output_path: Optional[str] = None,
) -> Dict:
    """
    Lance un cycle complet:
    1) soumission annuaires
    2) vérification email
    3) consolidation
    4) sauvegarde JSON optionnelle
    """
    logger.info("🚀 Starting backlink cycle")

    run_summary = BacklinkRunSummary(
        total_directories=max_directories or 0,
        notes="Luxura backlinks pipeline run"
    )

    # 1) SOUMISSION
    submitted_records: List[BacklinkRecord] = await submit_submission_queue(
        business_overrides=business_overrides,
        headless=headless,
        max_directories=max_directories,
    )

    submission_summary = summarize_submission_results(submitted_records)

    # 2) EMAIL VERIFICATION
    updated_records = submitted_records
    verification_summary = {
        "total": 0,
        "email_pending": 0,
        "email_found": 0,
        "verification_clicked": 0,
        "verified": 0,
        "failed": 0,
        "live": 0,
        "details": [],
    }

    if process_email_verification:
        pending_records = split_records_for_verification(submitted_records)

        logger.info(f"📬 Processing email verification for {len(pending_records)} record(s)")

        if pending_records:
            verified_records = await process_pending_verifications(
                records=pending_records,
                days_back=verification_days_back,
                click_links=click_verification_links,
            )

            verified_map = {
                (r.directory_key, r.domain): r
                for r in verified_records
            }

            merged_records: List[BacklinkRecord] = []
            for original in submitted_records:
                key = (original.directory_key, original.domain)
                merged_records.append(verified_map.get(key, original))

            updated_records = merged_records
            verification_summary = summarize_verification_results(updated_records)

    # 3) CONSOLIDATION
    consolidated_summary = merge_summaries(
        submission_summary=submission_summary,
        verification_summary=verification_summary,
        records=updated_records,
    )

    run_summary.total_directories = len(updated_records)
    run_summary.submitted = consolidated_summary["final_counts"]["submitted"]
    run_summary.email_pending = consolidated_summary["final_counts"]["email_pending"]
    run_summary.email_found = consolidated_summary["final_counts"]["email_found"]
    run_summary.verification_clicked = consolidated_summary["final_counts"]["verification_clicked"]
    run_summary.verified = consolidated_summary["final_counts"]["verified"]
    run_summary.live = consolidated_summary["final_counts"]["live"]
    run_summary.failed = consolidated_summary["final_counts"]["failed"]
    run_summary.skipped = consolidated_summary["final_counts"]["skipped"]
    run_summary.finish()

    final_result = {
        "run_summary": run_summary.model_dump(mode="json"),
        "submission_summary": submission_summary,
        "verification_summary": verification_summary,
        "consolidated_summary": consolidated_summary,
        "records": records_to_dicts(updated_records),
    }

    # 4) SAUVEGARDE JSON
    if save_snapshot:
        save_path = output_path or DEFAULT_OUTPUT_PATH
        save_run_snapshot(
            path=save_path,
            run_summary=final_result,
            records=updated_records,
            metadata={
                "pipeline_version": "backlinks_v1",
                "headless": headless,
                "max_directories": max_directories,
                "process_email_verification": process_email_verification,
                "verification_days_back": verification_days_back,
                "click_verification_links": click_verification_links,
            }
        )
        logger.info(f"💾 Backlink run snapshot saved: {save_path}")

    logger.info("✅ Backlink cycle completed")
    logger.info(
        f"submitted={run_summary.submitted} | "
        f"email_pending={run_summary.email_pending} | "
        f"verified={run_summary.verified} | "
        f"failed={run_summary.failed} | "
        f"skipped={run_summary.skipped}"
    )

    return final_result


async def retry_pending_verifications_only(
    records: List[BacklinkRecord],
    verification_days_back: int = 7,
    click_verification_links: bool = True,
    save_snapshot: bool = False,
    output_path: Optional[str] = None,
) -> Dict:
    """
    Relance uniquement les validations email pour les records déjà existants.
    """
    logger.info("🔁 Retrying pending email verifications only")

    eligible = split_records_for_verification(records)
    logger.info(f"Eligible records: {len(eligible)}")

    updated = await process_pending_verifications(
        records=eligible,
        days_back=verification_days_back,
        click_links=click_verification_links,
    )

    updated_map = {(r.directory_key, r.domain): r for r in updated}
    merged_records: List[BacklinkRecord] = []

    for original in records:
        key = (original.directory_key, original.domain)
        merged_records.append(updated_map.get(key, original))

    verification_summary = summarize_verification_results(merged_records)

    result = {
        "retried": len(eligible),
        "verification_summary": verification_summary,
        "records": records_to_dicts(merged_records),
    }

    if save_snapshot:
        save_path = output_path or DEFAULT_OUTPUT_PATH
        save_run_snapshot(
            path=save_path,
            run_summary=result,
            records=merged_records,
            metadata={
                "pipeline_version": "backlinks_v1",
                "mode": "retry_pending_verifications_only",
                "verification_days_back": verification_days_back,
                "click_verification_links": click_verification_links,
            }
        )
        logger.info(f"💾 Retry snapshot saved: {save_path}")

    return result


def load_records_from_snapshot(path: str) -> List[BacklinkRecord]:
    """
    Recharge les records depuis un snapshot JSON.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Snapshot not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    raw_records = payload.get("records", [])
    return [BacklinkRecord(**item) for item in raw_records]
