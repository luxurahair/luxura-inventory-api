"""
BACKLINK MODELS - Structures de données centralisées
Version: 1.0
Date: 2026-03-29

Modèles Pydantic pour la gestion des backlinks/citations.
Fini les JSON bancals différents d'un fichier à l'autre.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class BacklinkStatus(str, Enum):
    """Statuts possibles d'un backlink"""
    NEW = "new"                           # Pas encore soumis
    SUBMITTED = "submitted"               # Formulaire soumis
    EMAIL_PENDING = "email_pending"       # En attente d'email de vérification
    EMAIL_FOUND = "email_found"           # Email de vérification trouvé
    VERIFICATION_CLICKED = "verification_clicked"  # Lien de vérification cliqué
    VERIFIED = "verified"                 # Vérification complète
    LIVE = "live"                         # Listing actif et visible
    FAILED = "failed"                     # Échec de soumission
    REJECTED = "rejected"                 # Rejeté par l'annuaire
    EXPIRED = "expired"                   # Listing expiré


class SubmissionResult(BaseModel):
    """Résultat d'une soumission à un annuaire"""
    directory_key: str
    directory_name: str
    status: BacklinkStatus
    requires_email_verification: bool = False
    fields_filled: int = 0
    submission_url: Optional[str] = None
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    notes: Optional[str] = None
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        use_enum_values = True


class BacklinkRecord(BaseModel):
    """Enregistrement complet d'un backlink/citation"""
    id: Optional[str] = None
    domain: str                           # luxuradistribution.com
    directory_key: str                    # hotfrog, cylex, etc.
    directory_name: str                   # Nom lisible
    status: BacklinkStatus = BacklinkStatus.NEW
    
    # Soumission
    submission_url: Optional[str] = None
    fields_filled: int = 0
    submitted_at: Optional[datetime] = None
    
    # Vérification email
    email_required: bool = False
    verification_email_subject: Optional[str] = None
    verification_link: Optional[str] = None
    verification_link_found_at: Optional[datetime] = None
    verification_clicked_at: Optional[datetime] = None
    
    # Résultat
    live_url: Optional[str] = None
    verified_at: Optional[datetime] = None
    
    # Metadata
    screenshot_paths: List[str] = []
    notes: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    last_checked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        use_enum_values = True
    
    def update_status(self, new_status: BacklinkStatus, notes: str = None):
        """Met à jour le statut avec timestamp"""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        if notes:
            self.notes = notes
        
        # Timestamps spécifiques
        if new_status == BacklinkStatus.SUBMITTED:
            self.submitted_at = datetime.now(timezone.utc)
        elif new_status == BacklinkStatus.EMAIL_FOUND:
            self.verification_link_found_at = datetime.now(timezone.utc)
        elif new_status == BacklinkStatus.VERIFICATION_CLICKED:
            self.verification_clicked_at = datetime.now(timezone.utc)
        elif new_status == BacklinkStatus.VERIFIED:
            self.verified_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour MongoDB"""
        return self.model_dump()
    
    @classmethod
    def from_submission_result(cls, result: SubmissionResult, domain: str = "luxuradistribution.com"):
        """Crée un BacklinkRecord depuis un SubmissionResult"""
        return cls(
            domain=domain,
            directory_key=result.directory_key,
            directory_name=result.directory_name,
            status=result.status,
            submission_url=result.submission_url,
            fields_filled=result.fields_filled,
            submitted_at=result.submitted_at,
            email_required=result.requires_email_verification,
            screenshot_paths=[result.screenshot_path] if result.screenshot_path else [],
            notes=result.notes,
            error_message=result.error_message
        )


class EmailVerificationResult(BaseModel):
    """Résultat de la recherche d'email de vérification"""
    directory_key: str
    found: bool = False
    email_subject: Optional[str] = None
    email_from: Optional[str] = None
    email_date: Optional[datetime] = None
    verification_link: Optional[str] = None
    raw_body_preview: Optional[str] = None
    
    class Config:
        use_enum_values = True


class VerificationClickResult(BaseModel):
    """Résultat du clic sur un lien de vérification"""
    directory_key: str
    link: str
    success: bool = False
    final_url: Optional[str] = None
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    clicked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BacklinkCycleReport(BaseModel):
    """Rapport d'un cycle complet de backlinks"""
    cycle_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    # Compteurs
    directories_attempted: int = 0
    submissions_success: int = 0
    submissions_failed: int = 0
    emails_found: int = 0
    verifications_clicked: int = 0
    
    # Détails
    results: List[Dict] = []
    errors: List[str] = []
    
    def add_result(self, result: SubmissionResult):
        """Ajoute un résultat au rapport"""
        self.directories_attempted += 1
        if result.status in [BacklinkStatus.SUBMITTED, BacklinkStatus.EMAIL_PENDING]:
            self.submissions_success += 1
        elif result.status == BacklinkStatus.FAILED:
            self.submissions_failed += 1
        self.results.append(result.model_dump())
    
    def complete(self):
        """Marque le cycle comme terminé"""
        self.completed_at = datetime.now(timezone.utc)
    
    def get_summary(self) -> Dict:
        """Retourne un résumé du cycle"""
        return {
            "cycle_id": self.cycle_id,
            "duration_seconds": (self.completed_at - self.started_at).total_seconds() if self.completed_at else None,
            "directories_attempted": self.directories_attempted,
            "success_rate": round(self.submissions_success / max(1, self.directories_attempted) * 100, 1),
            "submissions_success": self.submissions_success,
            "submissions_failed": self.submissions_failed,
            "emails_found": self.emails_found,
            "verifications_clicked": self.verifications_clicked,
            "errors_count": len(self.errors)
        }
