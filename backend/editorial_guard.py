"""
EDITORIAL GUARD - Système anti-doublon et contrôle éditorial
Version: 1.0
Date: 2026-03-29

Fonctionnalités:
- Détection de doublons par similarité de titre
- Rotation forcée des catégories éditoriales
- Historique des sujets utilisés
- Blocage si similarité trop forte
- Flags de production pour traçabilité
"""

import os
import re
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION
# =====================================================

# Seuil de similarité (0.0 à 1.0) - au-dessus = trop similaire
SIMILARITY_THRESHOLD = 0.65

# Catégories avec rotation forcée
EDITORIAL_CATEGORIES = [
    "cheveux_fins",      # Consommateur
    "entretien",         # Consommateur  
    "guide",             # Consommateur
    "achat_en_ligne",    # Consommateur
    "comparatif",        # Comparaison
    "b2b_salon",         # Salon affilié
]

# Mots-clés à ignorer pour la comparaison
STOPWORDS = {
    'les', 'des', 'pour', 'avec', 'votre', 'vos', 'une', 'sur', 'dans', 
    'qui', 'que', 'est', 'sont', 'au', 'aux', 'de', 'la', 'le', 'et', 'en',
    'comment', 'pourquoi', 'quand', 'quel', 'quelle', 'quels', 'quelles',
    'extensions', 'capillaires', 'cheveux', 'luxura', 'distribution'
}


# =====================================================
# FONCTIONS UTILITAIRES
# =====================================================

def normalize_title(title: str) -> str:
    """Normalise un titre pour comparaison."""
    title = title.lower()
    # Supprimer emojis et caractères spéciaux
    title = re.sub(r'[^\w\sàâäéèêëïîôùûüç]', '', title)
    # Supprimer stopwords
    words = [w for w in title.split() if w not in STOPWORDS and len(w) > 2]
    return ' '.join(words)


def compute_topic_hash(title: str, category: str) -> str:
    """Génère un hash unique pour un sujet."""
    normalized = normalize_title(title)
    data = f"{category}:{normalized}"
    return hashlib.md5(data.encode()).hexdigest()[:12]


def compute_similarity(title1: str, title2: str) -> float:
    """Calcule la similarité entre deux titres (0.0 à 1.0)."""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def extract_keywords(title: str) -> List[str]:
    """Extrait les mots-clés principaux d'un titre."""
    keywords = []
    title_lower = title.lower()
    
    # Produits Luxura
    product_keywords = {
        'halo': ['halo', 'everly'],
        'genius': ['genius', 'weft', 'trame'],
        'tape': ['tape', 'adhésive', 'bande'],
        'itip': ['i-tip', 'itip', 'froid', 'eleanor'],
        'clip': ['clip', 'sophia']
    }
    
    for key, terms in product_keywords.items():
        if any(term in title_lower for term in terms):
            keywords.append(key)
    
    # Thèmes
    theme_keywords = {
        'entretien': ['entretien', 'soins', 'durée', 'prolonger'],
        'salon': ['salon', 'coiffeur', 'professionnel'],
        'comparatif': ['comparatif', 'vs', 'versus', 'différence'],
        'cheveux_fins': ['cheveux fins', 'volume', 'densité'],
        'guide': ['guide', 'complet', 'ultime', 'tout savoir'],
        'depot': ['dépôt', 'inventaire', 'partenaire'],
        'local_seo': ['montréal', 'québec', 'lévis', 'beauce', 'saint-georges']
    }
    
    for key, terms in theme_keywords.items():
        if any(term in title_lower for term in terms):
            keywords.append(key)
    
    return keywords


# =====================================================
# CLASSE PRINCIPALE
# =====================================================

class EditorialGuard:
    """
    Gardien éditorial pour éviter les doublons et maintenir
    une rotation saine des catégories.
    """
    
    def __init__(self, db=None):
        self.db = db
        self._category_rotation_index = 0
        self._used_topics_cache = set()
    
    async def load_existing_titles(self) -> List[str]:
        """Charge tous les titres existants depuis la DB."""
        if not self.db:
            return []
        
        try:
            posts = await self.db.blog_posts.find({}, {"title": 1}).to_list(1000)
            return [p.get("title", "") for p in posts if p.get("title")]
        except Exception as e:
            logger.error(f"Error loading existing titles: {e}")
            return []
    
    async def is_duplicate(self, new_title: str, existing_titles: List[str] = None) -> Tuple[bool, Optional[str], float]:
        """
        Vérifie si un titre est un doublon d'un titre existant.
        
        Returns:
            (is_duplicate, matched_title, similarity_score)
        """
        if existing_titles is None:
            existing_titles = await self.load_existing_titles()
        
        new_normalized = normalize_title(new_title)
        
        for existing in existing_titles:
            similarity = compute_similarity(new_title, existing)
            
            if similarity >= SIMILARITY_THRESHOLD:
                logger.warning(f"🚫 Doublon détecté! Similarité={similarity:.2f}")
                logger.warning(f"   Nouveau: {new_title[:50]}")
                logger.warning(f"   Existant: {existing[:50]}")
                return True, existing, similarity
        
        return False, None, 0.0
    
    def get_next_category(self, exclude_recent: List[str] = None) -> str:
        """
        Retourne la prochaine catégorie dans la rotation.
        Évite les catégories récemment utilisées.
        """
        if exclude_recent is None:
            exclude_recent = []
        
        available = [c for c in EDITORIAL_CATEGORIES if c not in exclude_recent]
        
        if not available:
            available = EDITORIAL_CATEGORIES.copy()
        
        # Rotation circulaire
        category = available[self._category_rotation_index % len(available)]
        self._category_rotation_index += 1
        
        return category
    
    def create_production_metadata(
        self,
        title: str,
        category: str,
        draft_id: str = None,
        cover_applied: bool = False
    ) -> Dict:
        """
        Crée les métadonnées de production pour traçabilité.
        """
        return {
            "editorial_angle": category,
            "topic_hash": compute_topic_hash(title, category),
            "keywords": extract_keywords(title),
            "cover_v2_applied": cover_applied,
            "cover_patch_payload_version": "v2" if cover_applied else None,
            "needs_human_review": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "wix_draft_id": draft_id,
            "pipeline_version": "v2_stable"
        }
    
    async def validate_topic(self, topic_data: Dict, existing_titles: List[str] = None) -> Tuple[bool, str]:
        """
        Valide un sujet avant génération.
        
        Returns:
            (is_valid, reason)
        """
        title = topic_data.get("topic", "")
        category = topic_data.get("category", "")
        
        # Vérifier titre vide
        if not title or len(title) < 10:
            return False, "Titre trop court ou vide"
        
        # Vérifier catégorie valide
        if category not in EDITORIAL_CATEGORIES and category not in ["halo", "genius", "tape", "itip", "tendances"]:
            logger.warning(f"Catégorie non standard: {category}")
        
        # Vérifier doublons
        is_dup, matched, score = await self.is_duplicate(title, existing_titles)
        if is_dup:
            return False, f"Doublon détecté (similarité {score:.0%}) avec: {matched[:40]}..."
        
        # Vérifier mots-clés interdits
        forbidden_terms = ["académie", "formation", "certification", "cours", "classe"]
        title_lower = title.lower()
        for term in forbidden_terms:
            if term in title_lower:
                return False, f"Terme interdit détecté: '{term}' (Luxura n'est pas une école)"
        
        return True, "OK"


# =====================================================
# FONCTIONS STANDALONE
# =====================================================

async def check_duplicate_before_generation(
    title: str,
    db=None,
    existing_titles: List[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Vérifie rapidement si un titre est un doublon.
    Utilisable sans instancier EditorialGuard.
    
    Returns:
        (is_ok_to_generate, error_message)
    """
    guard = EditorialGuard(db)
    is_dup, matched, score = await guard.is_duplicate(title, existing_titles)
    
    if is_dup:
        return False, f"Doublon: {matched[:40]}... (similarité {score:.0%})"
    
    return True, None


def log_production_event(
    event_type: str,
    title: str,
    category: str,
    draft_id: str = None,
    cover_v2: bool = False,
    extra: Dict = None
):
    """
    Log structuré pour traçabilité production.
    """
    log_data = {
        "event": event_type,
        "title": title[:60],
        "category": category,
        "topic_hash": compute_topic_hash(title, category),
        "cover_v2_applied": cover_v2,
        "draft_id": draft_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if extra:
        log_data.update(extra)
    
    # Log formaté
    if event_type == "BLOG_GENERATED":
        logger.info(f"📝 {event_type} | {title[:50]} | cat={category} | hash={log_data['topic_hash']}")
    elif event_type == "COVER_APPLIED":
        logger.info(f"🖼️ {event_type} | draft={draft_id} | cover_v2={cover_v2}")
    elif event_type == "DUPLICATE_BLOCKED":
        logger.warning(f"🚫 {event_type} | {title[:50]} | blocked")
    else:
        logger.info(f"📋 {event_type} | {log_data}")
    
    return log_data


# =====================================================
# RAPPORT D'AUDIT
# =====================================================

async def generate_editorial_audit_report(db, wix_titles: List[str] = None) -> Dict:
    """
    Génère un rapport d'audit éditorial complet.
    """
    guard = EditorialGuard(db)
    existing_titles = await guard.load_existing_titles()
    
    if wix_titles:
        existing_titles.extend(wix_titles)
    
    # Analyser doublons internes
    duplicates = []
    for i, title1 in enumerate(existing_titles):
        for title2 in existing_titles[i+1:]:
            sim = compute_similarity(title1, title2)
            if sim >= SIMILARITY_THRESHOLD:
                duplicates.append({
                    "title1": title1[:50],
                    "title2": title2[:50],
                    "similarity": round(sim, 2)
                })
    
    # Compter par catégorie
    category_counts = {}
    for title in existing_titles:
        keywords = extract_keywords(title)
        for kw in keywords:
            category_counts[kw] = category_counts.get(kw, 0) + 1
    
    return {
        "total_titles": len(existing_titles),
        "duplicates_found": len(duplicates),
        "duplicates": duplicates[:10],  # Top 10
        "category_distribution": category_counts,
        "audit_date": datetime.now(timezone.utc).isoformat()
    }
