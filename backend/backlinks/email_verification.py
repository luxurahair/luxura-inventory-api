"""
EMAIL VERIFICATION ENGINE - Moteur de vérification email
Version: 1.0
Date: 2026-03-29

Consolide la logique de:
- gmail_imap_checker.py
- auto_verification_loop.py

Rôle:
- Scanner la boîte mail IMAP
- Trouver les emails de vérification
- Extraire les liens
- Cliquer sur les liens via Playwright
- Mettre à jour les statuts
"""

import imaplib
import email
from email.header import decode_header
import os
import re
import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv

from .directory_registry import DIRECTORY_REGISTRY, get_email_verification_directories
from .backlink_models import (
    BacklinkRecord, 
    BacklinkStatus, 
    EmailVerificationResult,
    VerificationClickResult
)

load_dotenv("/app/backend/.env")

logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION
# =====================================================

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

EMAIL_ADDRESS = os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com")
APP_PASSWORD = os.getenv("LUXURA_APP_PASSWORD", "")
PASSWORD_FALLBACK = os.getenv("LUXURA_PASSWORD", "")

SCREENSHOTS_DIR = "/tmp/backlinks"
STATUS_FILE = "/tmp/backlinks/verification_status.json"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Mots-clés de vérification par annuaire
DIRECTORY_KEYWORDS = {
    "hotfrog": ["hotfrog"],
    "cylex": ["cylex"],
    "yelp": ["yelp"],
    "canpages": ["canpages", "canpage"],
    "411": ["411"],
    "iglobal": ["iglobal", "i-global"],
    "pagesjaunes": ["pages jaunes", "yellow pages", "pagesjaunes", "yellowpages"],
    "indexbeaute": ["indexbeaute", "index beauté", "indexbeauté"],
    "indexquebec": ["indexquebec", "index québec"],
}

# Domaines à exclure des liens
EXCLUDE_DOMAINS = [
    'google.com', 'gstatic.com', 'googleapis.com',
    'facebook.com', 'twitter.com', 'linkedin.com',
    'unsubscribe', 'mailto:', 'tel:'
]

# Mots-clés de lien de vérification
VERIFICATION_KEYWORDS = [
    'verify', 'confirm', 'activate', 'validate', 
    'click', 'registration', 'account', 'subscribe'
]


# =====================================================
# HELPERS EMAIL
# =====================================================

def decode_mime_header(header: str) -> str:
    """Décode un header email MIME"""
    if not header:
        return ""
    try:
        parts = decode_header(header)
        result = ""
        for part, enc in parts:
            if isinstance(part, bytes):
                result += part.decode(enc or 'utf-8', errors='ignore')
            else:
                result += str(part)
        return result
    except:
        return str(header)


def extract_links_from_email(msg) -> List[str]:
    """Extrait tous les liens d'un email"""
    links = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ["text/html", "text/plain"]:
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    # Pattern URL
                    found = re.findall(r'https?://[^\s<>"\']+', body)
                    links.extend(found)
                    # Pattern href
                    if content_type == "text/html":
                        href_found = re.findall(r'href=["\']([^"\']+)["\']', body, re.IGNORECASE)
                        links.extend([l for l in href_found if l.startswith('http')])
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            links = re.findall(r'https?://[^\s<>"\']+', body)
        except:
            pass
    
    # Nettoyer et filtrer
    clean_links = []
    for link in links:
        # Nettoyer caractères de fin
        link = link.rstrip('.,;:)>]')
        
        # Exclure domaines non pertinents
        if any(domain in link.lower() for domain in EXCLUDE_DOMAINS):
            continue
        
        clean_links.append(link)
    
    return list(dict.fromkeys(clean_links))  # Déduplique en gardant l'ordre


def filter_verification_links(links: List[str]) -> List[str]:
    """Filtre les liens pour garder seulement ceux de vérification"""
    verification_links = []
    other_links = []
    
    for link in links:
        link_lower = link.lower()
        if any(keyword in link_lower for keyword in VERIFICATION_KEYWORDS):
            verification_links.append(link)
        else:
            other_links.append(link)
    
    # Priorité aux liens de vérification
    return verification_links + other_links[:5]


def identify_directory_from_email(sender: str, subject: str) -> Optional[str]:
    """Identifie l'annuaire source d'un email"""
    combined = f"{sender} {subject}".lower()
    
    for directory_key, keywords in DIRECTORY_KEYWORDS.items():
        if any(keyword in combined for keyword in keywords):
            return directory_key
    
    return None


# =====================================================
# CONNEXION IMAP
# =====================================================

def connect_gmail() -> Optional[imaplib.IMAP4_SSL]:
    """Connecte à Gmail via IMAP"""
    password = APP_PASSWORD or PASSWORD_FALLBACK
    
    if not password:
        logger.error("❌ Pas de mot de passe Gmail configuré")
        logger.info("💡 Configure LUXURA_APP_PASSWORD dans .env")
        return None
    
    logger.info(f"📧 Connexion IMAP à {EMAIL_ADDRESS}...")
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ADDRESS, password)
        logger.info("✅ Connexion IMAP réussie")
        return mail
        
    except imaplib.IMAP4.error as e:
        error_msg = str(e)
        if "AUTHENTICATIONFAILED" in error_msg:
            logger.error("❌ Authentification échouée")
            logger.info("💡 Si 2FA activé, utilise un App Password:")
            logger.info("   https://myaccount.google.com/apppasswords")
        else:
            logger.error(f"❌ Erreur IMAP: {error_msg}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Erreur connexion: {e}")
        return None


# =====================================================
# RECHERCHE D'EMAILS
# =====================================================

def search_verification_emails(
    mail: imaplib.IMAP4_SSL,
    days_back: int = 7,
    limit: int = 50
) -> List[EmailVerificationResult]:
    """
    Recherche les emails de vérification dans la boîte mail.
    
    Args:
        mail: Connexion IMAP
        days_back: Nombre de jours en arrière
        limit: Nombre max d'emails à analyser
    
    Returns:
        Liste d'EmailVerificationResult
    """
    results = []
    
    try:
        mail.select("INBOX")
        
        # Date de recherche
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        
        # Rechercher les emails récents
        status, messages = mail.search(None, f'(SINCE "{since_date}")')
        
        if status != "OK":
            logger.error("❌ Erreur recherche emails")
            return results
        
        email_ids = messages[0].split()
        logger.info(f"📬 {len(email_ids)} emails des {days_back} derniers jours")
        
        # Analyser les emails (du plus récent au plus ancien)
        for email_id in reversed(email_ids[-limit:]):
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                if status != "OK":
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                subject = decode_mime_header(msg.get("Subject", ""))
                sender = decode_mime_header(msg.get("From", ""))
                date_str = msg.get("Date", "")
                
                # Identifier l'annuaire
                directory_key = identify_directory_from_email(sender, subject)
                
                if not directory_key:
                    # Vérifier si c'est quand même un email de vérification
                    combined = f"{sender} {subject}".lower()
                    is_verification = any(w in combined for w in ["verify", "confirm", "activate", "welcome"])
                    if not is_verification:
                        continue
                
                # Extraire les liens
                all_links = extract_links_from_email(msg)
                verification_links = filter_verification_links(all_links)
                
                if verification_links:
                    result = EmailVerificationResult(
                        directory_key=directory_key or "unknown",
                        found=True,
                        email_subject=subject[:100],
                        email_from=sender[:100],
                        verification_link=verification_links[0] if verification_links else None,
                        raw_body_preview=f"{len(all_links)} liens trouvés"
                    )
                    results.append(result)
                    
                    logger.info(f"📬 {directory_key or 'unknown'}: {subject[:50]}...")
                    logger.info(f"   🔗 {len(verification_links)} liens de vérification")
                    
            except Exception as e:
                logger.debug(f"Erreur email {email_id}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"❌ Erreur recherche: {e}")
    
    return results


# =====================================================
# CLIC SUR LIENS DE VÉRIFICATION
# =====================================================

async def click_verification_link(
    link: str,
    directory_key: str
) -> VerificationClickResult:
    """
    Clique sur un lien de vérification via Playwright.
    
    Args:
        link: URL du lien de vérification
        directory_key: Clé de l'annuaire
    
    Returns:
        VerificationClickResult
    """
    logger.info(f"🔗 Clic sur lien de vérification: {directory_key}")
    logger.info(f"   URL: {link[:80]}...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Naviguer vers le lien
            await page.goto(link, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            # Screenshot
            screenshot_path = f"{SCREENSHOTS_DIR}/verify_{directory_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            
            final_url = page.url
            
            await browser.close()
            
            logger.info(f"✅ Lien cliqué avec succès")
            logger.info(f"   URL finale: {final_url[:80]}...")
            
            return VerificationClickResult(
                directory_key=directory_key,
                link=link,
                success=True,
                final_url=final_url,
                screenshot_path=screenshot_path
            )
            
    except Exception as e:
        logger.error(f"❌ Erreur clic: {e}")
        return VerificationClickResult(
            directory_key=directory_key,
            link=link,
            success=False,
            error_message=str(e)[:100]
        )


# =====================================================
# GESTION DES STATUTS
# =====================================================

def load_verification_status() -> Dict:
    """Charge le statut de vérification depuis le fichier"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    
    # Statut initial
    return {
        key: {
            "status": "pending",
            "email_found": False,
            "link_clicked": False,
            "verified": False,
            "last_check": None
        }
        for key in DIRECTORY_KEYWORDS.keys()
    }


def save_verification_status(status: Dict):
    """Sauvegarde le statut de vérification"""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2, default=str)
        logger.debug(f"💾 Statut sauvegardé: {STATUS_FILE}")
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde: {e}")


def update_status_from_result(
    status: Dict,
    result: EmailVerificationResult,
    click_result: VerificationClickResult = None
) -> Dict:
    """Met à jour le statut depuis un résultat"""
    key = result.directory_key
    
    if key not in status:
        status[key] = {
            "status": "pending",
            "email_found": False,
            "link_clicked": False,
            "verified": False
        }
    
    if result.found:
        status[key]["email_found"] = True
        status[key]["email_subject"] = result.email_subject
        status[key]["verification_link"] = result.verification_link
        status[key]["status"] = "email_found"
    
    if click_result and click_result.success:
        status[key]["link_clicked"] = True
        status[key]["final_url"] = click_result.final_url
        status[key]["status"] = "verification_clicked"
        status[key]["clicked_at"] = datetime.now(timezone.utc).isoformat()
    
    status[key]["last_check"] = datetime.now(timezone.utc).isoformat()
    
    return status


# =====================================================
# FONCTIONS PRINCIPALES
# =====================================================

async def process_pending_verifications() -> Dict:
    """
    Traite toutes les vérifications en attente.
    
    1. Charge le statut actuel
    2. Connecte à Gmail
    3. Cherche les emails de vérification
    4. Clique sur les liens trouvés
    5. Met à jour les statuts
    
    Returns:
        Rapport de traitement
    """
    logger.info("=" * 60)
    logger.info("📧 TRAITEMENT DES VÉRIFICATIONS")
    logger.info("=" * 60)
    
    report = {
        "emails_found": 0,
        "links_clicked": 0,
        "errors": [],
        "results": []
    }
    
    # Charger statut
    status = load_verification_status()
    
    # Connecter à Gmail
    mail = connect_gmail()
    if not mail:
        report["errors"].append("Connexion Gmail échouée")
        return report
    
    try:
        # Chercher les emails
        email_results = search_verification_emails(mail, days_back=7, limit=50)
        report["emails_found"] = len(email_results)
        
        logger.info(f"\n📬 {len(email_results)} emails de vérification trouvés")
        
        # Traiter chaque email
        for email_result in email_results:
            directory_key = email_result.directory_key
            
            # Vérifier si déjà cliqué
            if status.get(directory_key, {}).get("link_clicked", False):
                logger.info(f"⏭️ {directory_key}: déjà vérifié, skip")
                continue
            
            # Cliquer sur le lien
            if email_result.verification_link:
                click_result = await click_verification_link(
                    email_result.verification_link,
                    directory_key
                )
                
                if click_result.success:
                    report["links_clicked"] += 1
                    status = update_status_from_result(status, email_result, click_result)
                else:
                    report["errors"].append(f"{directory_key}: {click_result.error_message}")
                
                report["results"].append({
                    "directory": directory_key,
                    "email_found": True,
                    "link_clicked": click_result.success,
                    "final_url": click_result.final_url if click_result.success else None
                })
                
                # Délai entre clics
                await asyncio.sleep(2)
        
        # Sauvegarder statut
        save_verification_status(status)
        
    finally:
        mail.logout()
    
    # Résumé
    logger.info("=" * 60)
    logger.info(f"📊 RÉSUMÉ:")
    logger.info(f"   Emails trouvés: {report['emails_found']}")
    logger.info(f"   Liens cliqués: {report['links_clicked']}")
    logger.info(f"   Erreurs: {len(report['errors'])}")
    logger.info("=" * 60)
    
    return report


def get_verification_summary() -> Dict:
    """Retourne un résumé du statut de vérification"""
    status = load_verification_status()
    
    summary = {
        "total": len(status),
        "verified": 0,
        "pending": 0,
        "failed": 0,
        "directories": {}
    }
    
    for key, data in status.items():
        summary["directories"][key] = {
            "status": data.get("status", "pending"),
            "email_found": data.get("email_found", False),
            "link_clicked": data.get("link_clicked", False)
        }
        
        if data.get("link_clicked"):
            summary["verified"] += 1
        elif data.get("status") == "pending":
            summary["pending"] += 1
        else:
            summary["failed"] += 1
    
    return summary


# =====================================================
# FONCTION CLI
# =====================================================

async def run_verification_cycle():
    """
    Lance un cycle de vérification complet.
    Utilisable depuis CLI ou CRON.
    """
    report = await process_pending_verifications()
    
    print("\n" + "=" * 60)
    print("📊 RAPPORT DE VÉRIFICATION")
    print("=" * 60)
    print(f"   Emails trouvés: {report['emails_found']}")
    print(f"   Liens cliqués: {report['links_clicked']}")
    print(f"   Erreurs: {len(report['errors'])}")
    
    if report['errors']:
        print("\n⚠️ Erreurs:")
        for error in report['errors']:
            print(f"   - {error}")
    
    return report


if __name__ == "__main__":
    asyncio.run(run_verification_cycle())
