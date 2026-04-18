"""
Modèles de données pour le système de contenu automatisé
Gestion des articles trouvés et des posts Facebook générés
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, Float, JSON
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid

# Import de la base depuis le projet existant
try:
    from app.db.session import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class PostStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class ContentSourceItem(Base):
    """
    Article/contenu trouvé sur le web
    Stocke les sources brutes avant transformation
    """
    __tablename__ = "content_source_items"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name = Column(String(255), nullable=False)  # "Google News", "Allure", etc.
    source_url = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    title_fr = Column(Text, nullable=True)  # Version traduite
    summary = Column(Text, nullable=True)
    summary_fr = Column(Text, nullable=True)  # Version traduite
    raw_content = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    country = Column(String(10), default="CA")
    language = Column(String(10), default="en")
    url_hash = Column(String(64), unique=True, index=True)  # Pour dédoublonnage
    title_hash = Column(String(64), index=True)
    is_relevant = Column(Boolean, default=False)
    relevance_score = Column(Float, default=0.0)
    keywords_matched = Column(JSON, default=list)  # Liste des mots-clés trouvés
    is_processed = Column(Boolean, default=False)  # Post généré?
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<ContentSourceItem {self.title[:40]}...>"


class AutoSocialPost(Base):
    """
    Post Facebook généré automatiquement
    Brouillon ou publié
    """
    __tablename__ = "auto_social_posts"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_item_id = Column(String(50), nullable=True)  # Référence à ContentSourceItem
    platform = Column(String(50), default="facebook")
    language = Column(String(10), default="fr")
    tone = Column(String(50), default="luxura")  # luxura, educational, promotional
    
    # Contenu du post
    post_title = Column(Text, nullable=True)  # Titre interne
    post_text = Column(Text, nullable=False)  # Texte du post Facebook
    hashtags = Column(JSON, default=list)
    cta_text = Column(String(255), nullable=True)  # Call to action
    source_url = Column(Text, nullable=True)  # Lien vers l'article source
    
    # Image
    image_url = Column(Text, nullable=True)  # URL de l'image générée
    image_prompt = Column(Text, nullable=True)  # Prompt DALL-E utilisé
    has_image = Column(Boolean, default=False)
    
    # Statut et scores
    status = Column(String(20), default="draft")  # draft, review, approved, published, rejected
    confidence_score = Column(Float, default=0.0)  # Score de confiance (0-1)
    quality_score = Column(Float, default=0.0)  # Score de qualité du contenu
    
    # Publication
    published_post_id = Column(String(100), nullable=True)  # ID du post Facebook
    published_at = Column(DateTime, nullable=True)
    publish_error = Column(Text, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AutoSocialPost {self.status} - {self.post_text[:40]}...>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "source_item_id": self.source_item_id,
            "platform": self.platform,
            "post_text": self.post_text,
            "hashtags": self.hashtags,
            "image_url": self.image_url,
            "status": self.status,
            "confidence_score": self.confidence_score,
            "published_post_id": self.published_post_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
