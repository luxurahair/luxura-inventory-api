"""
DIRECTORY REGISTRY - Source unique de vérité pour les annuaires
Version: 1.0
Date: 2026-03-29

Ce fichier centralise TOUS les annuaires supportés.
Plus de listes éparpillées dans 6 fichiers différents.
"""

from typing import Dict, List, Optional
from enum import Enum


class DirectoryCategory(str, Enum):
    """Catégories d'annuaires"""
    GENERAL = "general"           # Annuaires généraux (Yelp, 411, etc.)
    LOCAL = "local"               # Annuaires locaux Québec/Canada
    BEAUTY = "beauty"             # Annuaires spécialisés beauté
    BUSINESS = "business"         # Annuaires B2B


class SubmissionType(str, Enum):
    """Type de soumission"""
    PLAYWRIGHT = "playwright"     # Automatisation navigateur
    API = "api"                   # Via API directe
    MANUAL = "manual"             # Soumission manuelle requise


# =====================================================
# DONNÉES BUSINESS LUXURA (centralisées)
# =====================================================

LUXURA_BUSINESS = {
    "name": "Luxura Distribution",
    "description": "Importateur et distributeur direct d'extensions capillaires professionnelles au Québec. Qualité salon haut de gamme.",
    "description_long": """Luxura Distribution est le leader québécois des extensions capillaires professionnelles. 
Nous offrons des extensions Genius Weft, Tape-in, Halo et I-Tip de qualité supérieure. 
Plus de 30 salons partenaires au Québec. Livraison rapide partout au Canada.""",
    "address": "1887, 83e Rue",
    "city": "St-Georges",
    "province": "Québec",
    "province_short": "QC",
    "postal_code": "G6A 1M9",
    "country": "Canada",
    "full_address": "1887, 83e Rue, St-Georges, QC G6A 1M9, Canada",
    "phone": "(418) 222-3939",
    "phone_clean": "4182223939",
    "email": "info@luxuradistribution.com",
    "website": "https://www.luxuradistribution.com",
    "categories": [
        "Hair Extensions",
        "Beauty Supplies",
        "Salon Supplies",
        "Extensions capillaires",
        "Fournitures de salon"
    ],
    "keywords": [
        "extensions capillaires",
        "hair extensions",
        "genius weft",
        "tape-in extensions",
        "halo extensions",
        "i-tip extensions",
        "salon partenaire",
        "Québec"
    ]
}


# =====================================================
# REGISTRE DES ANNUAIRES
# =====================================================

DIRECTORY_REGISTRY: Dict[str, Dict] = {
    # ==================== ANNUAIRES GÉNÉRAUX ====================
    "hotfrog": {
        "name": "Hotfrog Canada",
        "url": "https://www.hotfrog.ca/add-a-business",
        "category": DirectoryCategory.GENERAL,
        "country": "CA",
        "language": "en",
        "requires_email_verification": True,
        "active": True,
        "priority": 1,  # 1 = haute, 5 = basse
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "easy",
        "estimated_time_minutes": 5,
        "notes": "Formulaire simple, email de vérification rapide",
        "selectors": {
            "business_name": ['input[name="businessName"]', '#businessName'],
            "phone": ['input[name="phone"]', '#phone', 'input[type="tel"]'],
            "email": ['input[name="email"]', '#email', 'input[type="email"]'],
            "website": ['input[name="website"]', '#website', 'input[type="url"]'],
            "address": ['input[name="address"]', '#address'],
            "description": ['textarea[name="description"]', '#description', 'textarea'],
            "submit": ['button[type="submit"]', 'input[type="submit"]', '.btn-submit']
        }
    },
    
    "cylex": {
        "name": "Cylex Canada",
        "url": "https://www.cylex.ca/add-company",
        "category": DirectoryCategory.GENERAL,
        "country": "CA",
        "language": "en",
        "requires_email_verification": True,
        "active": True,
        "priority": 1,
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "easy",
        "estimated_time_minutes": 5,
        "notes": "Bon annuaire, email de vérification",
        "selectors": {
            "company_name": ['#company_name', 'input[name="company_name"]', 'input[name="company"]'],
            "street": ['#street', 'input[name="street"]', 'input[name="address"]'],
            "city": ['#city', 'input[name="city"]'],
            "postal": ['#zip', 'input[name="zip"]', 'input[name="postal"]'],
            "phone": ['#phone', 'input[name="phone"]'],
            "email": ['#email', 'input[name="email"]'],
            "website": ['#website', 'input[name="website"]']
        }
    },
    
    "yelp": {
        "name": "Yelp Canada",
        "url": "https://biz.yelp.ca/signup_business/new",
        "category": DirectoryCategory.GENERAL,
        "country": "CA",
        "language": "en/fr",
        "requires_email_verification": True,
        "active": True,
        "priority": 1,
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "medium",
        "estimated_time_minutes": 10,
        "notes": "Haute autorité SEO, vérification téléphone possible",
        "selectors": {
            "biz_name": ['input[name="biz_name"]', '#biz_name'],
            "address": ['input[name="address1"]', '#address1'],
            "city": ['input[name="city"]', '#city'],
            "state": ['input[name="state"]', '#state', 'select[name="state"]'],
            "zip": ['input[name="zip"]', '#zip'],
            "phone": ['input[name="phone"]', '#phone', 'input[type="tel"]']
        }
    },
    
    "411": {
        "name": "411.ca",
        "url": "https://www.411.ca/",
        "category": DirectoryCategory.LOCAL,
        "country": "CA",
        "language": "en/fr",
        "requires_email_verification": False,
        "active": True,
        "priority": 2,
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "medium",
        "estimated_time_minutes": 10,
        "notes": "Annuaire téléphonique canadien, claim business"
    },
    
    "pagesjaunes": {
        "name": "Pages Jaunes Canada",
        "url": "https://www.pagesjaunes.ca/",
        "category": DirectoryCategory.LOCAL,
        "country": "CA",
        "language": "fr",
        "requires_email_verification": True,
        "active": True,
        "priority": 1,
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "medium",
        "estimated_time_minutes": 15,
        "notes": "Pages Jaunes officiel, haute autorité locale"
    },
    
    "canpages": {
        "name": "Canpages",
        "url": "https://www.canpages.ca/",
        "category": DirectoryCategory.LOCAL,
        "country": "CA",
        "language": "en",
        "requires_email_verification": False,
        "active": True,
        "priority": 3,
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "easy",
        "estimated_time_minutes": 5,
        "notes": "Annuaire canadien"
    },
    
    "iglobal": {
        "name": "iGlobal Canada",
        "url": "https://ca.iglobal.co/register",
        "category": DirectoryCategory.BUSINESS,
        "country": "CA",
        "language": "en",
        "requires_email_verification": True,
        "active": True,
        "priority": 2,
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "easy",
        "estimated_time_minutes": 5,
        "notes": "Annuaire business international",
        "selectors": {
            "company": ['input[name="company"]', '#company'],
            "email": ['input[name="email"]', '#email', 'input[type="email"]'],
            "phone": ['input[name="phone"]', '#phone'],
            "website": ['input[name="website"]', '#website']
        }
    },
    
    # ==================== ANNUAIRES BEAUTÉ ====================
    "indexbeaute": {
        "name": "IndexBeauté.ca",
        "url": "https://www.indexbeaute.ca/",
        "category": DirectoryCategory.BEAUTY,
        "country": "CA",
        "language": "fr",
        "requires_email_verification": True,
        "active": True,
        "priority": 1,
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "medium",
        "estimated_time_minutes": 10,
        "notes": "Annuaire spécialisé beauté Québec - TRÈS pertinent"
    },
    
    # ==================== ANNUAIRES LOCAUX QUÉBEC ====================
    "indexquebec": {
        "name": "Index Québec",
        "url": "https://www.indexquebec.com/",
        "category": DirectoryCategory.LOCAL,
        "country": "CA",
        "language": "fr",
        "requires_email_verification": True,
        "active": True,
        "priority": 2,
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "easy",
        "estimated_time_minutes": 5,
        "notes": "Annuaire local Québec"
    },
    
    "quebecentreprises": {
        "name": "Québec Entreprises",
        "url": "https://www.quebecentreprises.com/",
        "category": DirectoryCategory.BUSINESS,
        "country": "CA",
        "language": "fr",
        "requires_email_verification": True,
        "active": True,
        "priority": 2,
        "submission_type": SubmissionType.PLAYWRIGHT,
        "difficulty": "easy",
        "estimated_time_minutes": 5,
        "notes": "Annuaire B2B Québec"
    },
    
    # ==================== GOOGLE ====================
    "google_business": {
        "name": "Google Business Profile",
        "url": "https://business.google.com/",
        "category": DirectoryCategory.GENERAL,
        "country": "GLOBAL",
        "language": "fr",
        "requires_email_verification": True,
        "active": True,
        "priority": 1,
        "submission_type": SubmissionType.MANUAL,
        "difficulty": "medium",
        "estimated_time_minutes": 30,
        "notes": "CRITIQUE - Vérification postale ou téléphone"
    },
    
    # ==================== FACEBOOK ====================
    "facebook_page": {
        "name": "Facebook Business Page",
        "url": "https://www.facebook.com/pages/create",
        "category": DirectoryCategory.GENERAL,
        "country": "GLOBAL",
        "language": "fr",
        "requires_email_verification": False,
        "active": True,
        "priority": 1,
        "submission_type": SubmissionType.MANUAL,
        "difficulty": "easy",
        "estimated_time_minutes": 15,
        "notes": "Page business Facebook"
    }
}


# =====================================================
# FONCTIONS UTILITAIRES
# =====================================================

def get_active_directories() -> List[Dict]:
    """Retourne tous les annuaires actifs triés par priorité"""
    active = [
        {"key": key, **data}
        for key, data in DIRECTORY_REGISTRY.items()
        if data.get("active", False)
    ]
    return sorted(active, key=lambda x: x.get("priority", 5))


def get_directory_by_key(key: str) -> Optional[Dict]:
    """Retourne un annuaire par sa clé"""
    if key in DIRECTORY_REGISTRY:
        return {"key": key, **DIRECTORY_REGISTRY[key]}
    return None


def get_directories_by_category(category: DirectoryCategory) -> List[Dict]:
    """Retourne les annuaires d'une catégorie"""
    return [
        {"key": key, **data}
        for key, data in DIRECTORY_REGISTRY.items()
        if data.get("category") == category and data.get("active", False)
    ]


def get_playwright_directories() -> List[Dict]:
    """Retourne les annuaires automatisables via Playwright"""
    return [
        {"key": key, **data}
        for key, data in DIRECTORY_REGISTRY.items()
        if data.get("submission_type") == SubmissionType.PLAYWRIGHT and data.get("active", False)
    ]


def get_email_verification_directories() -> List[Dict]:
    """Retourne les annuaires nécessitant une vérification email"""
    return [
        {"key": key, **data}
        for key, data in DIRECTORY_REGISTRY.items()
        if data.get("requires_email_verification", False) and data.get("active", False)
    ]


def get_business_data() -> Dict:
    """Retourne les données business Luxura"""
    return LUXURA_BUSINESS.copy()


# =====================================================
# STATISTIQUES
# =====================================================

def get_registry_stats() -> Dict:
    """Retourne les statistiques du registre"""
    all_dirs = list(DIRECTORY_REGISTRY.values())
    active = [d for d in all_dirs if d.get("active", False)]
    
    return {
        "total": len(all_dirs),
        "active": len(active),
        "by_category": {
            cat.value: len([d for d in active if d.get("category") == cat])
            for cat in DirectoryCategory
        },
        "by_submission_type": {
            st.value: len([d for d in active if d.get("submission_type") == st])
            for st in SubmissionType
        },
        "requiring_email": len([d for d in active if d.get("requires_email_verification", False)]),
        "estimated_total_time_minutes": sum(d.get("estimated_time_minutes", 0) for d in active)
    }
