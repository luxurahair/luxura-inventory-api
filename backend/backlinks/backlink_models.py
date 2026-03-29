# backlink_models.py
"""
Modèles de données standards pour le système backlinks / citations Luxura.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field


BacklinkStatus = Literal[
    "new",
    "queued",
    "submitted",
    "email_pending",
    "email_found",
    "verification_clicked",
    "verified",
    "live",
    "failed",
    "skipped"
]


class VerificationLink(BaseModel):
    url: str
    source_email_subject: Optional[str] = None
    source_email_from: Optional[str] = None
    found_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    clicked: bool = False
    clicked_at: Optional[datetime] = None
    notes: Optional[str] = None


class SubmissionResult(BaseModel):
    directory_key: str
    directory_name: str
    domain: str
    status: BacklinkStatus
    requires_email_verification: bool = False
    submission_url: Optional[str] = None
    notes: Optional[str] = None
    raw_data: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BacklinkRecord(BaseModel):
    """
    Enregistrement central d'une soumission / citation / backlink.
    """
    business_name: str = "Luxura Distribution"
    directory_key: str
    directory_name: str
    domain: str

    category: str = "directory"
    country: str = "CA"
    language: List[str] = Field(default_factory=lambda: ["fr", "en"])
    niche: List[str] = Field(default_factory=list)

    status: BacklinkStatus = "new"
    priority: int = 1

    requires_email_verification: bool = False
    verification_links: List[VerificationLink] = Field(default_factory=list)

    submitted_at: Optional[datetime] = None
    email_found_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    live_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    submission_url: Optional[str] = None
    live_url: Optional[str] = None
    contact_email: Optional[str] = None

    last_error: Optional[str] = None
    notes: Optional[str] = None

    pipeline_version: str = "backlinks_v1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def mark_submitted(self, submission_url: Optional[str] = None, notes: Optional[str] = None):
        self.status = "submitted"
        self.submitted_at = datetime.now(timezone.utc)
        self.updated_at = self.submitted_at
        if submission_url:
            self.submission_url = submission_url
        if notes:
            self.notes = notes

    def mark_email_pending(self):
        self.status = "email_pending"
        self.updated_at = datetime.now(timezone.utc)

    def mark_email_found(self):
        self.status = "email_found"
        self.email_found_at = datetime.now(timezone.utc)
        self.updated_at = self.email_found_at

    def mark_verification_clicked(self):
        self.status = "verification_clicked"
        self.verified_at = datetime.now(timezone.utc)
        self.updated_at = self.verified_at

    def mark_verified(self):
        self.status = "verified"
        self.verified_at = datetime.now(timezone.utc)
        self.updated_at = self.verified_at

    def mark_live(self, live_url: Optional[str] = None):
        self.status = "live"
        self.live_at = datetime.now(timezone.utc)
        self.updated_at = self.live_at
        if live_url:
            self.live_url = live_url

    def mark_failed(self, error_message: str):
        self.status = "failed"
        self.failed_at = datetime.now(timezone.utc)
        self.updated_at = self.failed_at
        self.last_error = error_message

    def add_verification_link(
        self,
        url: str,
        source_email_subject: Optional[str] = None,
        source_email_from: Optional[str] = None,
        notes: Optional[str] = None
    ):
        self.verification_links.append(
            VerificationLink(
                url=url,
                source_email_subject=source_email_subject,
                source_email_from=source_email_from,
                notes=notes
            )
        )
        self.mark_email_found()


class BacklinkRunSummary(BaseModel):
    """
    Résumé d'un cycle complet de soumission / vérification.
    """
    total_directories: int = 0
    submitted: int = 0
    email_pending: int = 0
    email_found: int = 0
    verification_clicked: int = 0
    verified: int = 0
    live: int = 0
    failed: int = 0
    skipped: int = 0
    notes: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None

    def finish(self):
        self.finished_at = datetime.now(timezone.utc)


class ProspectRecord(BaseModel):
    """
    Prévu pour la future couche outreach / guest post / partenariat.
    On le met déjà pour éviter de tout recasser plus tard.
    """
    domain: str
    name: Optional[str] = None
    source_type: Literal[
        "directory",
        "beauty_blog",
        "resource_page",
        "partner_salon",
        "school",
        "magazine",
        "general_outreach"
    ] = "general_outreach"

    country: str = "CA"
    language: List[str] = Field(default_factory=lambda: ["fr"])
    niche: List[str] = Field(default_factory=list)

    contact_email: Optional[str] = None
    contact_page: Optional[str] = None
    notes: Optional[str] = None

    quality_score: int = 0
    relevance_score: int = 0
    outreach_status: Literal[
        "new",
        "qualified",
        "contacted",
        "responded",
        "won",
        "lost",
        "ignored"
    ] = "new"

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
