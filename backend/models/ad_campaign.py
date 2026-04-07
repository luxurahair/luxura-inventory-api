"""
Luxura Marketing - Modèles de données pour campagnes publicitaires
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class OfferType(str, Enum):
    DIRECT_SALE = "direct_sale"
    SALON_AFFILIE = "salon_affilie"


class AdStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    PUBLISHED = "published"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"


class AdFormat(str, Enum):
    STORY_916 = "story_9:16"
    FEED_45 = "feed_4:5"
    BOTH = "both"


# ============ INPUT SCHEMAS ============

class AdJobInput(BaseModel):
    """Fiche pub entrante pour génération"""
    offer_type: OfferType = Field(..., description="Type d'offre: direct_sale ou salon_affilie")
    product_name: str = Field(..., description="Nom du produit/offre")
    hook: str = Field(..., description="Accroche principale")
    proof: Optional[str] = Field(None, description="Preuve/bénéfice")
    cta: str = Field(default="Commander", description="Call-to-action")
    landing_url: str = Field(..., description="URL de destination")
    images: List[str] = Field(default=[], description="URLs des images source")
    target_audience: Optional[str] = Field(None, description="Audience cible")
    ad_format: AdFormat = Field(default=AdFormat.BOTH, description="Format pub")
    

class AdApprovalInput(BaseModel):
    """Validation/activation d'une pub"""
    job_id: str
    approve: bool = True
    

# ============ OUTPUT SCHEMAS ============

class GeneratedCopy(BaseModel):
    """Textes publicitaires générés"""
    primary_text: str
    headline: str
    description: Optional[str] = None
    story_script: str
    feed_script: str
    fal_prompt_story: str
    fal_prompt_feed: str


class GeneratedVideo(BaseModel):
    """Vidéo générée par Fal.ai"""
    request_id: str
    video_url: Optional[str] = None
    status: str
    format: str  # "9:16" ou "4:5"
    file_size: Optional[int] = None


class MetaAdDraft(BaseModel):
    """Brouillon pub Meta"""
    campaign_id: Optional[str] = None
    adset_id: Optional[str] = None
    creative_id: Optional[str] = None
    ad_id: Optional[str] = None
    status: str = "draft"


class AdJob(BaseModel):
    """Job complet de génération pub"""
    job_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: AdStatus = AdStatus.DRAFT
    
    # Input
    input: AdJobInput
    
    # Generated content
    copy: Optional[GeneratedCopy] = None
    story_video: Optional[GeneratedVideo] = None
    feed_video: Optional[GeneratedVideo] = None
    
    # Meta integration
    meta_draft: Optional[MetaAdDraft] = None
    
    # Errors
    error: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AdJobResponse(BaseModel):
    """Réponse API standard"""
    success: bool
    job_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    data: Optional[dict] = None
