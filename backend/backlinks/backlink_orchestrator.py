"""
BACKLINK ORCHESTRATOR - Cerveau de coordination
Version: 1.0
Date: 2026-03-29

Remplace complete_backlink_system.py

Rôle:
- Orchestrer le cycle complet de backlinks
- Coordonner citation_engine + email_verification
- Gérer les statuts et rapports
- Exposer une interface simple
"""

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .directory_registry import (
    get_active_directories,
    get_playwright_directories,
    get_business_data,
    get_registry_stats
)
from .citation_engine import (
    submit_to_directory,
    submit_to_all_directories,
    SUBMISSION_FUNCTIONS
)
from .email_verification import (
    process_pending_verifications,
    get_verification_summary,
    load_verification_status,
    save_verification_status
)
from .backlink_models import (
    BacklinkRecord,
    BacklinkStatus,
    SubmissionResult,
    BacklinkCycleReport
)

logger = logging.getLogger(__name__)


# =====================================================
# ORCHESTRATION PRINCIPALE
# =====================================================

async def run_full_backlink_cycle(
    directories: List[str] = None,
    verify_emails: bool = True,
    delay_between_submissions: tuple = (3, 6)
) -> BacklinkCycleReport:
    """
    Lance un cycle complet de backlinks:
    1. Soumettre aux annuaires
    2. Vérifier les emails
    3. Cliquer sur les liens de vérification
    4. Générer un rapport
    
    Args:
        directories: Liste des annuaires à soumettre (tous par défaut)
        verify_emails: Lancer la vérification email après soumission
        delay_between_submissions: Délai entre soumissions (min, max secondes)
    
    Returns:
        BacklinkCycleReport avec tous les résultats
    """
    cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    report = BacklinkCycleReport(cycle_id=cycle_id)
    
    logger.info("=" * 70)
    logger.info(f"🚀 CYCLE BACKLINKS: {cycle_id}")
    logger.info("=" * 70)
    
    try:
        # Phase 1: Soumissions
        logger.info("\n📤 PHASE 1: SOUMISSIONS AUX ANNUAIRES")
        logger.info("-" * 50)
        
        if directories is None:
            directories = list(SUBMISSION_FUNCTIONS.keys())
        
        submission_results = await submit_to_all_directories(
            directory_keys=directories,
            delay_between=delay_between_submissions
        )
        
        for result in submission_results:
            report.add_result(result)
        
        # Phase 2: Vérification emails
        if verify_emails:
            logger.info("\n📧 PHASE 2: VÉRIFICATION EMAILS")
            logger.info("-" * 50)
            
            # Attendre un peu pour que les emails arrivent
            logger.info("⏳ Attente 30 secondes pour les emails...")
            await asyncio.sleep(30)
            
            email_report = await process_pending_verifications()
            report.emails_found = email_report.get("emails_found", 0)
            report.verifications_clicked = email_report.get("links_clicked", 0)
            
            if email_report.get("errors"):
                report.errors.extend(email_report["errors"])
        
        report.complete()
        
    except Exception as e:
        logger.error(f"❌ Erreur cycle: {e}")
        report.errors.append(str(e))
        report.complete()
    
    # Résumé final
    summary = report.get_summary()
    
    logger.info("\n" + "=" * 70)
    logger.info("📊 RAPPORT FINAL")
    logger.info("=" * 70)
    logger.info(f"   Cycle ID: {summary['cycle_id']}")
    logger.info(f"   Durée: {summary.get('duration_seconds', 'N/A')} secondes")
    logger.info(f"   Annuaires tentés: {summary['directories_attempted']}")
    logger.info(f"   Taux de succès: {summary['success_rate']}%")
    logger.info(f"   Emails trouvés: {summary['emails_found']}")
    logger.info(f"   Vérifications cliquées: {summary['verifications_clicked']}")
    logger.info(f"   Erreurs: {summary['errors_count']}")
    logger.info("=" * 70)
    
    return report


async def run_submission_only(
    directories: List[str] = None
) -> List[SubmissionResult]:
    """
    Lance seulement les soumissions, sans vérification email.
    Utile pour soumettre rapidement et vérifier les emails plus tard.
    """
    logger.info("📤 SOUMISSIONS SEULEMENT (pas de vérification email)")
    
    if directories is None:
        directories = list(SUBMISSION_FUNCTIONS.keys())
    
    return await submit_to_all_directories(directory_keys=directories)


async def run_verification_only() -> Dict:
    """
    Lance seulement la vérification email.
    Utile pour re-vérifier après un délai.
    """
    logger.info("📧 VÉRIFICATION EMAILS SEULEMENT")
    return await process_pending_verifications()


# =====================================================
# GESTION DES STATUTS
# =====================================================

def get_backlink_status() -> Dict:
    """
    Retourne le statut global du système de backlinks.
    """
    registry_stats = get_registry_stats()
    verification_summary = get_verification_summary()
    
    return {
        "registry": registry_stats,
        "verification": verification_summary,
        "available_directories": list(SUBMISSION_FUNCTIONS.keys()),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


def get_pending_directories() -> List[str]:
    """
    Retourne les annuaires qui n'ont pas encore été vérifiés.
    """
    status = load_verification_status()
    
    pending = []
    for key, data in status.items():
        if not data.get("link_clicked", False):
            pending.append(key)
    
    return pending


def reset_directory_status(directory_key: str) -> bool:
    """
    Réinitialise le statut d'un annuaire pour permettre une nouvelle soumission.
    """
    status = load_verification_status()
    
    if directory_key in status:
        status[directory_key] = {
            "status": "pending",
            "email_found": False,
            "link_clicked": False,
            "verified": False,
            "reset_at": datetime.now(timezone.utc).isoformat()
        }
        save_verification_status(status)
        logger.info(f"🔄 Statut réinitialisé: {directory_key}")
        return True
    
    return False


# =====================================================
# UTILITAIRES
# =====================================================

def list_available_directories() -> List[Dict]:
    """
    Liste tous les annuaires disponibles avec leurs infos.
    """
    directories = get_playwright_directories()
    
    return [
        {
            "key": d["key"],
            "name": d["name"],
            "category": d.get("category", "general"),
            "priority": d.get("priority", 5),
            "requires_email": d.get("requires_email_verification", False),
            "difficulty": d.get("difficulty", "medium"),
            "estimated_time": d.get("estimated_time_minutes", 10)
        }
        for d in directories
    ]


def get_business_info() -> Dict:
    """
    Retourne les informations business utilisées pour les soumissions.
    """
    return get_business_data()


# =====================================================
# SCRIPTS CLI
# =====================================================

async def cli_run_full_cycle():
    """Point d'entrée CLI pour cycle complet"""
    report = await run_full_backlink_cycle()
    return report.get_summary()


async def cli_run_submissions():
    """Point d'entrée CLI pour soumissions seulement"""
    results = await run_submission_only()
    return [
        {"directory": r.directory_name, "status": r.status, "fields": r.fields_filled}
        for r in results
    ]


async def cli_run_verifications():
    """Point d'entrée CLI pour vérifications seulement"""
    return await run_verification_only()
