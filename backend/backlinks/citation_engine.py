# citation_engine.py
"""
Moteur de soumission citations / annuaires Luxura.

Responsabilités:
- charger les annuaires actifs depuis directory_registry.py
- soumettre vers les annuaires supportés
- retourner des résultats standardisés
- ne PAS gérer le mail ici
- ne PAS gérer l'orchestration globale ici
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Dict, List, Optional, Callable, Awaitable

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError

from .directory_registry import (
    get_submission_queue,
    get_directory,
    build_business_payload,
)
from .backlink_models import BacklinkRecord, SubmissionResult

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Helpers Playwright
# -------------------------------------------------------------------

async def human_delay(min_ms: int = 600, max_ms: int = 1800):
    await asyncio.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


async def safe_goto(page: Page, url: str, timeout: int = 45000) -> bool:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        await human_delay()
        return True
    except Exception as e:
        logger.error(f"safe_goto failed for {url}: {e}")
        return False


async def safe_fill(page: Page, selectors: List[str], value: str) -> bool:
    if not value:
        return False

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0:
                await locator.fill(value)
                await human_delay()
                return True
        except Exception:
            continue
    return False


async def safe_click(page: Page, selectors: List[str]) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0:
                await locator.click()
                await human_delay()
                return True
        except Exception:
            continue
    return False


async def safe_select(page: Page, selectors: List[str], value: str) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0:
                await locator.select_option(value=value)
                await human_delay()
                return True
        except Exception:
            continue
    return False


async def try_checkbox_captcha(page: Page) -> bool:
    """
    Essaie seulement les checkbox simples.
    On ne contourne pas les captchas complexes.
    """
    candidates = [
        'iframe[title*="reCAPTCHA"]',
        'iframe[src*="recaptcha"]',
        'input[type="checkbox"]',
        '.recaptcha-checkbox-border',
    ]

    try:
        for selector in candidates:
            elements = page.locator(selector)
            if await elements.count() > 0:
                logger.info(f"Captcha/simple checkbox detected via {selector}")
                return False
    except Exception:
        pass

    return False


def now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# -------------------------------------------------------------------
# Standard mapping helpers
# -------------------------------------------------------------------

def build_record_from_directory(directory: Dict) -> BacklinkRecord:
    return BacklinkRecord(
        directory_key=directory["key"],
        directory_name=directory["name"],
        domain=directory["domain"],
        category=directory.get("category", "directory"),
        country=directory.get("country", "CA"),
        language=directory.get("language", ["fr", "en"]),
        niche=directory.get("niche", []),
        priority=directory.get("priority", 1),
        requires_email_verification=directory.get("requires_email_verification", False),
        status="queued",
        notes=directory.get("notes", None),
    )


def build_submission_result(
    directory: Dict,
    status: str,
    submission_url: Optional[str] = None,
    notes: Optional[str] = None,
    raw_data: Optional[Dict] = None,
) -> SubmissionResult:
    return SubmissionResult(
        directory_key=directory["key"],
        directory_name=directory["name"],
        domain=directory["domain"],
        status=status,
        requires_email_verification=directory.get("requires_email_verification", False),
        submission_url=submission_url,
        notes=notes,
        raw_data=raw_data or {},
    )


# -------------------------------------------------------------------
# Per-directory submitters
# -------------------------------------------------------------------

async def submit_hotfrog(page: Page, business_data: Dict, directory: Dict) -> SubmissionResult:
    ok = await safe_goto(page, directory["submission_url"])
    if not ok:
        return build_submission_result(directory, "failed", notes="Navigation failed")

    await safe_fill(page, ['input[name="name"]', 'input[name="businessName"]', '#businessName'], business_data["business_name"])
    await safe_fill(page, ['input[name="email"]', '#email'], business_data["email"])
    await safe_fill(page, ['input[name="phone"]', '#phone'], business_data.get("phone", ""))
    await safe_fill(page, ['input[name="website"]', '#website'], business_data["website"])
    await safe_fill(page, ['textarea[name="description"]', '#description'], business_data["description_long"])
    await safe_fill(page, ['input[name="address1"]', '#address1'], business_data.get("address_line_1", ""))
    await safe_fill(page, ['input[name="city"]', '#city'], business_data.get("city", ""))
    await safe_fill(page, ['input[name="postalCode"]', '#postalCode'], business_data.get("postal_code", ""))

    await try_checkbox_captcha(page)

    clicked = await safe_click(page, [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Add Business")'
    ])

    if not clicked:
        return build_submission_result(directory, "failed", notes="Submit button not found")

    return build_submission_result(
        directory,
        "submitted",
        submission_url=page.url,
        notes="Submitted to Hotfrog; email verification may be required",
    )


async def submit_cylex(page: Page, business_data: Dict, directory: Dict) -> SubmissionResult:
    ok = await safe_goto(page, directory["submission_url"])
    if not ok:
        return build_submission_result(directory, "failed", notes="Navigation failed")

    await safe_fill(page, ['input[name="companyName"]', '#companyName', 'input[name="name"]'], business_data["business_name"])
    await safe_fill(page, ['input[name="email"]', '#email'], business_data["email"])
    await safe_fill(page, ['input[name="phone"]', '#phone'], business_data.get("phone", ""))
    await safe_fill(page, ['input[name="website"]', '#website'], business_data["website"])
    await safe_fill(page, ['textarea[name="description"]', '#description'], business_data["description_long"])
    await safe_fill(page, ['input[name="street"]', '#street'], business_data.get("address_line_1", ""))
    await safe_fill(page, ['input[name="city"]', '#city'], business_data.get("city", ""))
    await safe_fill(page, ['input[name="zip"]', '#zip'], business_data.get("postal_code", ""))

    clicked = await safe_click(page, [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Continue")',
        'button:has-text("Submit")'
    ])

    if not clicked:
        return build_submission_result(directory, "failed", notes="Submit button not found")

    return build_submission_result(
        directory,
        "submitted",
        submission_url=page.url,
        notes="Submitted to Cylex; verification may be required",
    )


async def submit_canpages(page: Page, business_data: Dict, directory: Dict) -> SubmissionResult:
    ok = await safe_goto(page, directory["submission_url"])
    if not ok:
        return build_submission_result(directory, "failed", notes="Navigation failed")

    await safe_fill(page, ['input[name="businessName"]', '#businessName', 'input[name="name"]'], business_data["business_name"])
    await safe_fill(page, ['input[name="email"]', '#email'], business_data["email"])
    await safe_fill(page, ['input[name="phone"]', '#phone'], business_data.get("phone", ""))
    await safe_fill(page, ['input[name="website"]', '#website'], business_data["website"])
    await safe_fill(page, ['textarea[name="description"]', '#description'], business_data["description_long"])
    await safe_fill(page, ['input[name="address"]', '#address'], business_data.get("address_line_1", ""))
    await safe_fill(page, ['input[name="city"]', '#city'], business_data.get("city", ""))
    await safe_fill(page, ['input[name="postalCode"]', '#postalCode'], business_data.get("postal_code", ""))

    clicked = await safe_click(page, [
        'button[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Add")',
        'input[type="submit"]'
    ])

    if not clicked:
        return build_submission_result(directory, "failed", notes="Submit button not found")

    return build_submission_result(
        directory,
        "submitted",
        submission_url=page.url,
        notes="Submitted to Canpages",
    )


async def submit_411(page: Page, business_data: Dict, directory: Dict) -> SubmissionResult:
    ok = await safe_goto(page, directory["submission_url"])
    if not ok:
        return build_submission_result(directory, "failed", notes="Navigation failed")

    await safe_fill(page, ['input[name="businessName"]', '#businessName', 'input[name="name"]'], business_data["business_name"])
    await safe_fill(page, ['input[name="email"]', '#email'], business_data["email"])
    await safe_fill(page, ['input[name="phone"]', '#phone'], business_data.get("phone", ""))
    await safe_fill(page, ['input[name="website"]', '#website'], business_data["website"])
    await safe_fill(page, ['textarea[name="description"]', '#description'], business_data["description_long"])
    await safe_fill(page, ['input[name="address"]', '#address'], business_data.get("address_line_1", ""))
    await safe_fill(page, ['input[name="city"]', '#city'], business_data.get("city", ""))
    await safe_fill(page, ['input[name="postalCode"]', '#postalCode'], business_data.get("postal_code", ""))

    clicked = await safe_click(page, [
        'button[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Add Business")',
        'input[type="submit"]'
    ])

    if not clicked:
        return build_submission_result(directory, "failed", notes="Submit button not found")

    return build_submission_result(
        directory,
        "submitted",
        submission_url=page.url,
        notes="Submitted to 411",
    )


async def submit_iglobal(page: Page, business_data: Dict, directory: Dict) -> SubmissionResult:
    ok = await safe_goto(page, directory["submission_url"])
    if not ok:
        return build_submission_result(directory, "failed", notes="Navigation failed")

    await safe_fill(page, ['input[name="title"]', '#title', 'input[name="businessName"]'], business_data["business_name"])
    await safe_fill(page, ['input[name="email"]', '#email'], business_data["email"])
    await safe_fill(page, ['input[name="phone"]', '#phone'], business_data.get("phone", ""))
    await safe_fill(page, ['input[name="website"]', '#website'], business_data["website"])
    await safe_fill(page, ['textarea[name="description"]', '#description'], business_data["description_long"])
    await safe_fill(page, ['input[name="address"]', '#address'], business_data.get("address_line_1", ""))
    await safe_fill(page, ['input[name="city"]', '#city'], business_data.get("city", ""))
    await safe_fill(page, ['input[name="zip"]', '#zip'], business_data.get("postal_code", ""))

    clicked = await safe_click(page, [
        'button[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Add Business")',
        'input[type="submit"]'
    ])

    if not clicked:
        return build_submission_result(directory, "failed", notes="Submit button not found")

    return build_submission_result(
        directory,
        "submitted",
        submission_url=page.url,
        notes="Submitted to iGlobal",
    )


async def submit_indexbeaute(page: Page, business_data: Dict, directory: Dict) -> SubmissionResult:
    if not directory.get("submission_url"):
        return build_submission_result(directory, "skipped", notes="No submission URL configured")

    ok = await safe_goto(page, directory["submission_url"])
    if not ok:
        return build_submission_result(directory, "failed", notes="Navigation failed")

    await safe_fill(page, ['input[name="name"]', '#name', 'input[name="businessName"]'], business_data["business_name"])
    await safe_fill(page, ['input[name="email"]', '#email'], business_data["email"])
    await safe_fill(page, ['input[name="phone"]', '#phone'], business_data.get("phone", ""))
    await safe_fill(page, ['input[name="website"]', '#website'], business_data["website"])
    await safe_fill(page, ['textarea[name="description"]', '#description'], business_data["description_long"])
    await safe_fill(page, ['input[name="address"]', '#address'], business_data.get("address_line_1", ""))
    await safe_fill(page, ['input[name="city"]', '#city'], business_data.get("city", ""))

    clicked = await safe_click(page, [
        'button[type="submit"]',
        'button:has-text("Envoyer")',
        'button:has-text("Soumettre")',
        'input[type="submit"]'
    ])

    if not clicked:
        return build_submission_result(directory, "failed", notes="Submit button not found")

    return build_submission_result(
        directory,
        "submitted",
        submission_url=page.url,
        notes="Submitted to Index Beauté",
    )


async def submit_manual_or_skipped(page: Page, business_data: Dict, directory: Dict) -> SubmissionResult:
    return build_submission_result(
        directory,
        "skipped",
        notes=f"Directory {directory['name']} is marked manual or disabled for safe automation"
    )


# -------------------------------------------------------------------
# Registry of submitter functions
# -------------------------------------------------------------------

SUBMITTERS: Dict[str, Callable[[Page, Dict, Dict], Awaitable[SubmissionResult]]] = {
    "hotfrog": submit_hotfrog,
    "cylex": submit_cylex,
    "canpages": submit_canpages,
    "411": submit_411,
    "iglobal": submit_iglobal,
    "indexbeaute": submit_indexbeaute,
    "yelp": submit_manual_or_skipped,
    "yellowpages": submit_manual_or_skipped,
    "google_business_profile": submit_manual_or_skipped,
}


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

async def submit_to_directory(
    page: Page,
    directory_key: str,
    business_overrides: Optional[Dict] = None,
) -> SubmissionResult:
    directory = get_directory(directory_key)
    if not directory:
        raise ValueError(f"Unknown directory key: {directory_key}")

    if not directory.get("active", False):
        return build_submission_result(directory, "skipped", notes="Directory inactive")

    business_data = build_business_payload(business_overrides or {})
    submitter = SUBMITTERS.get(directory_key)

    if not submitter:
        return build_submission_result(directory, "skipped", notes="No submitter implemented")

    logger.info(f"📨 Submitting to {directory['name']} ({directory_key})")
    result = await submitter(page, business_data, directory)
    return result


async def submit_directory_record(
    page: Page,
    directory_key: str,
    business_overrides: Optional[Dict] = None,
) -> BacklinkRecord:
    directory = get_directory(directory_key)
    if not directory:
        raise ValueError(f"Unknown directory key: {directory_key}")

    record = build_record_from_directory(directory)

    result = await submit_to_directory(page, directory_key, business_overrides)

    if result.status == "submitted":
        record.mark_submitted(submission_url=result.submission_url, notes=result.notes)
        if record.requires_email_verification:
            record.mark_email_pending()
    elif result.status == "skipped":
        record.status = "skipped"
        record.notes = result.notes
    else:
        record.mark_failed(result.notes or "Submission failed")

    return record


async def submit_submission_queue(
    business_overrides: Optional[Dict] = None,
    headless: bool = True,
    max_directories: Optional[int] = None,
) -> List[BacklinkRecord]:
    """
    Soumet tous les annuaires actifs selon la queue triée.
    """
    queue = get_submission_queue()
    if max_directories:
        queue = queue[:max_directories]

    results: List[BacklinkRecord] = []

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        for directory in queue:
            try:
                record = await submit_directory_record(
                    page=page,
                    directory_key=directory["key"],
                    business_overrides=business_overrides,
                )
                results.append(record)

                logger.info(
                    f"✅ {record.directory_name}: status={record.status} "
                    f"email_required={record.requires_email_verification}"
                )

                await human_delay(1200, 2600)

            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout on {directory['key']}: {e}")
                failed_record = build_record_from_directory(directory)
                failed_record.mark_failed(f"Timeout: {str(e)}")
                results.append(failed_record)

            except Exception as e:
                logger.error(f"Error on {directory['key']}: {e}")
                failed_record = build_record_from_directory(directory)
                failed_record.mark_failed(str(e))
                results.append(failed_record)

        await browser.close()

    return results


def summarize_submission_results(records: List[BacklinkRecord]) -> Dict:
    summary = {
        "total": len(records),
        "submitted": 0,
        "email_pending": 0,
        "skipped": 0,
        "failed": 0,
        "live": 0,
        "directories": []
    }

    for r in records:
        if r.status == "submitted":
            summary["submitted"] += 1
        elif r.status == "email_pending":
            summary["email_pending"] += 1
        elif r.status == "skipped":
            summary["skipped"] += 1
        elif r.status == "failed":
            summary["failed"] += 1
        elif r.status == "live":
            summary["live"] += 1

        summary["directories"].append({
            "directory_key": r.directory_key,
            "directory_name": r.directory_name,
            "status": r.status,
            "submission_url": r.submission_url,
            "requires_email_verification": r.requires_email_verification,
            "notes": r.notes,
            "last_error": r.last_error,
        })

    return summary
