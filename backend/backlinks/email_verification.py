# email_verification_engine.py
"""
Moteur de vérification email pour le système backlinks / citations Luxura.

Responsabilités:
- se connecter en IMAP
- lire les emails récents
- détecter les emails de validation / confirmation
- extraire les liens utiles
- cliquer les liens
- mettre à jour les BacklinkRecord

Ne gère PAS:
- la soumission annuaires
- l'orchestration complète du pipeline
"""

from __future__ import annotations

import os
import re
import imaplib
import email
import logging
import asyncio
import httpx
from typing import List, Optional, Dict, Tuple
from email.message import Message
from email.header import decode_header
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

from .backlink_models import BacklinkRecord

load_dotenv()
logger = logging.getLogger(__name__)

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FOLDER = os.getenv("EMAIL_FOLDER", "INBOX")

VERIFY_KEYWORDS = [
    "verify",
    "verification",
    "confirm",
    "confirmation",
    "activate",
    "activation",
    "validate",
    "validation",
    "complete registration",
    "confirm your email",
    "verify your email",
    "please confirm",
    "activate account",
]

URL_PATTERNS = [
    r'https?://[^\s"\'<>]+'
]

LINK_KEYWORDS = [
    "verify",
    "confirm",
    "activate",
    "validation",
    "approve",
    "complete-registration",
    "registration",
    "email-confirmation",
]


# -------------------------------------------------------------------
# Helpers généraux
# -------------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def decode_mime_words(value: Optional[str]) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded = []
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded.append(text.decode(charset or "utf-8", errors="ignore"))
        else:
            decoded.append(text)
    return "".join(decoded).strip()


def clean_text(value: Optional[str]) -> str:
    return (value or "").strip()


def normalize_subject(subject: Optional[str]) -> str:
    return decode_mime_words(subject).lower()


def extract_email_domain(value: str) -> str:
    match = re.search(r'@([A-Za-z0-9.-]+\.[A-Za-z]{2,})', value or "")
    return match.group(1).lower() if match else ""


def keyword_in_text(text: str, keywords: List[str]) -> bool:
    lowered = (text or "").lower()
    return any(k.lower() in lowered for k in keywords)


def safe_unique(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


# -------------------------------------------------------------------
# IMAP layer
# -------------------------------------------------------------------

class ImapClient:
    def __init__(
        self,
        host: str = IMAP_HOST,
        port: int = IMAP_PORT,
        username: str = EMAIL_USERNAME,
        password: str = EMAIL_PASSWORD,
        folder: str = EMAIL_FOLDER,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.folder = folder
        self.mail: Optional[imaplib.IMAP4_SSL] = None

    def connect(self):
        if not self.username or not self.password:
            raise RuntimeError("EMAIL_USERNAME / EMAIL_PASSWORD not configured")

        logger.info(f"📬 Connecting to IMAP {self.host}:{self.port} as {self.username}")
        self.mail = imaplib.IMAP4_SSL(self.host, self.port)
        self.mail.login(self.username, self.password)
        self.mail.select(self.folder)

    def close(self):
        try:
            if self.mail:
                self.mail.close()
        except Exception:
            pass
        try:
            if self.mail:
                self.mail.logout()
        except Exception:
            pass

    def search_recent_ids(self, days_back: int = 7) -> List[bytes]:
        if not self.mail:
            raise RuntimeError("IMAP not connected")

        since_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        status, data = self.mail.search(None, f'(SINCE "{since_date}")')
        if status != "OK":
            logger.warning(f"IMAP search failed: {status}")
            return []

        ids = data[0].split() if data and data[0] else []
        return ids

    def fetch_message(self, msg_id: bytes) -> Optional[Message]:
        if not self.mail:
            raise RuntimeError("IMAP not connected")

        status, data = self.mail.fetch(msg_id, "(RFC822)")
        if status != "OK" or not data or not data[0]:
            return None

        raw = data[0][1]
        return email.message_from_bytes(raw)


# -------------------------------------------------------------------
# Email parsing
# -------------------------------------------------------------------

def extract_message_bodies(msg: Message) -> Tuple[str, str]:
    """
    Retourne (text_body, html_body)
    """
    text_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition.lower():
                continue

            try:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="ignore") if payload else ""
            except Exception:
                decoded = ""

            if content_type == "text/plain" and not text_body:
                text_body = decoded
            elif content_type == "text/html" and not html_body:
                html_body = decoded
    else:
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="ignore") if payload else ""
        except Exception:
            decoded = ""

        if msg.get_content_type() == "text/html":
            html_body = decoded
        else:
            text_body = decoded

    return text_body, html_body


def strip_common_email_noise(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_urls_from_text(text: str) -> List[str]:
    if not text:
        return []
    urls = []
    for pattern in URL_PATTERNS:
        urls.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return safe_unique(urls)


def extract_verification_urls(text_body: str, html_body: str) -> List[str]:
    combined = "\n".join([text_body or "", html_body or ""])
    urls = extract_urls_from_text(combined)

    filtered = []
    for url in urls:
        lowered = url.lower()
        if any(keyword in lowered for keyword in LINK_KEYWORDS):
            filtered.append(url)

    # fallback: si aucun lien "keyword", on garde quand même les premiers liens https
    if not filtered:
        filtered = [u for u in urls if u.lower().startswith("http")]

    return safe_unique(filtered)


def message_matches_directory(msg: Message, record: BacklinkRecord) -> bool:
    subject = normalize_subject(msg.get("Subject", ""))
    from_header = decode_mime_words(msg.get("From", "")).lower()

    domain = (record.domain or "").lower()
    directory_name = (record.directory_name or "").lower()
    directory_key = (record.directory_key or "").lower()

    if domain and domain in from_header:
        return True
    if directory_name and directory_name in subject:
        return True
    if directory_key and directory_key in subject:
        return True

    if keyword_in_text(subject, VERIFY_KEYWORDS):
        # un peu permissif si sujet contient verify + nom du domaine tronqué
        short_domain = domain.split(".")[0] if domain else ""
        if short_domain and short_domain in subject:
            return True

    return False


# -------------------------------------------------------------------
# Link clicking
# -------------------------------------------------------------------

async def click_verification_link(url: str, timeout: float = 30.0) -> Tuple[bool, Optional[str], int]:
    """
    Clique via requête HTTP simple.
    Retourne:
    - success
    - final_url
    - status_code
    """
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0 Safari/537.36"
                )
            }
        ) as client:
            response = await client.get(url)
            final_url = str(response.url)
            status = response.status_code

            # On considère 2xx/3xx comme "probablement cliqué"
            success = 200 <= status < 400
            return success, final_url, status

    except Exception as e:
        logger.error(f"Error clicking verification link {url}: {e}")
        return False, None, 0


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

def find_verification_emails_for_record(
    imap_client: ImapClient,
    record: BacklinkRecord,
    days_back: int = 7
) -> List[Dict]:
    """
    Cherche les emails récents correspondant à un BacklinkRecord.
    """
    matches: List[Dict] = []
    msg_ids = imap_client.search_recent_ids(days_back=days_back)

    logger.info(
        f"🔎 Searching verification emails for {record.directory_name} "
        f"over {len(msg_ids)} recent emails"
    )

    for msg_id in reversed(msg_ids):
        msg = imap_client.fetch_message(msg_id)
        if not msg:
            continue

        if not message_matches_directory(msg, record):
            continue

        subject = decode_mime_words(msg.get("Subject", ""))
        from_header = decode_mime_words(msg.get("From", ""))
        text_body, html_body = extract_message_bodies(msg)

        subject_match = keyword_in_text(subject.lower(), VERIFY_KEYWORDS)
        body_match = keyword_in_text(
            strip_common_email_noise(text_body + " " + html_body).lower(),
            VERIFY_KEYWORDS
        )

        if not subject_match and not body_match:
            continue

        verification_urls = extract_verification_urls(text_body, html_body)

        matches.append({
            "subject": subject,
            "from": from_header,
            "message_id": msg.get("Message-ID", ""),
            "verification_urls": verification_urls,
            "text_body": text_body[:2000],
            "html_body": html_body[:2000],
        })

    return matches


async def process_record_email_verification(
    record: BacklinkRecord,
    days_back: int = 7,
    click_links: bool = True,
) -> BacklinkRecord:
    """
    Traite un BacklinkRecord:
    - cherche email
    - extrait liens
    - clique
    - met à jour le record
    """
    if not record.requires_email_verification:
        logger.info(f"ℹ️ {record.directory_name} does not require email verification")
        return record

    if record.status not in {"email_pending", "submitted", "email_found"}:
        logger.info(
            f"ℹ️ Skipping {record.directory_name}: status={record.status} not eligible for email verification"
        )
        return record

    client = ImapClient()
    try:
        client.connect()
        matches = find_verification_emails_for_record(client, record, days_back=days_back)

        if not matches:
            logger.info(f"📭 No verification email found for {record.directory_name}")
            return record

        logger.info(f"📨 Found {len(matches)} candidate email(s) for {record.directory_name}")

        for match in matches:
            urls = match.get("verification_urls", [])
            for url in urls:
                record.add_verification_link(
                    url=url,
                    source_email_subject=match.get("subject"),
                    source_email_from=match.get("from"),
                    notes="Link extracted from IMAP email"
                )

        if not click_links:
            return record

        clicked_any = False
        for link in record.verification_links:
            if link.clicked:
                continue

            success, final_url, status_code = await click_verification_link(link.url)
            if success:
                clicked_any = True
                link.clicked = True
                link.clicked_at = utcnow()
                if final_url:
                    link.notes = f"Clicked successfully -> {final_url} [{status_code}]"
                else:
                    link.notes = f"Clicked successfully [{status_code}]"

        if clicked_any:
            record.mark_verification_clicked()
            # On n'a pas encore prouvé que le lien est live; juste que le mail a été validé
            record.mark_verified()
        else:
            logger.warning(f"⚠️ Links found but none clicked successfully for {record.directory_name}")

        return record

    except Exception as e:
        logger.error(f"Email verification failed for {record.directory_name}: {e}")
        record.mark_failed(f"Email verification failed: {str(e)}")
        return record

    finally:
        client.close()


async def process_pending_verifications(
    records: List[BacklinkRecord],
    days_back: int = 7,
    click_links: bool = True,
) -> List[BacklinkRecord]:
    """
    Traite une liste de records en attente.
    """
    updated: List[BacklinkRecord] = []

    for record in records:
        if not record.requires_email_verification:
            updated.append(record)
            continue

        if record.status not in {"submitted", "email_pending", "email_found"}:
            updated.append(record)
            continue

        logger.info(f"🔁 Processing pending verification for {record.directory_name}")
        updated_record = await process_record_email_verification(
            record=record,
            days_back=days_back,
            click_links=click_links
        )
        updated.append(updated_record)

        # petit délai entre clics / boîtes
        await asyncio.sleep(1.2)

    return updated


def summarize_verification_results(records: List[BacklinkRecord]) -> Dict:
    summary = {
        "total": len(records),
        "email_pending": 0,
        "email_found": 0,
        "verification_clicked": 0,
        "verified": 0,
        "failed": 0,
        "live": 0,
        "details": []
    }

    for r in records:
        if r.status == "email_pending":
            summary["email_pending"] += 1
        elif r.status == "email_found":
            summary["email_found"] += 1
        elif r.status == "verification_clicked":
            summary["verification_clicked"] += 1
        elif r.status == "verified":
            summary["verified"] += 1
        elif r.status == "failed":
            summary["failed"] += 1
        elif r.status == "live":
            summary["live"] += 1

        summary["details"].append({
            "directory_key": r.directory_key,
            "directory_name": r.directory_name,
            "status": r.status,
            "verification_links_count": len(r.verification_links),
            "live_url": r.live_url,
            "last_error": r.last_error,
        })

    return summary
