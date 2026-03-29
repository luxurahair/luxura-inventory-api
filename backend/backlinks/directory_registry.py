# directory_registry.py
"""
Source de vérité unique pour les annuaires / citations Luxura.

Objectifs:
- centraliser la liste des annuaires
- indiquer lesquels sont actifs
- préciser s'ils demandent une vérification email
- donner une priorité d'exécution
- préparer la migration vers citation_engine.py
"""

from typing import Dict, List, Optional


DIRECTORY_REGISTRY: Dict[str, Dict] = {
    # ==========================================
    # ANNUAIRES ACTIFS ET TESTÉS
    # ==========================================
    "brownbook": {
        "key": "brownbook",
        "name": "Brownbook",
        "domain": "brownbook.net",
        "submission_url": "https://www.brownbook.net/add-business",
        "category": "directory",
        "country": "CA",
        "language": ["en"],
        "niche": ["general_business", "global"],
        "active": True,
        "priority": 1,
        "requires_email_verification": True,
        "submission_method": "playwright",
        "notes": "DA 73. Formulaire sans compte. Multi-step."
    },
    
    # ==========================================
    # ANNUAIRES À VÉRIFIER / OBSOLÈTES
    # ==========================================
    "hotfrog": {
        "key": "hotfrog",
        "name": "Hotfrog",
        "domain": "hotfrog.ca",
        "submission_url": "https://www.hotfrog.ca/add",
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["general_business", "local"],
        "active": False,  # Requiert login maintenant
        "priority": 1,
        "requires_email_verification": True,
        "submission_method": "playwright",
        "notes": "⚠️ Requiert login/compte. Désactivé pour l'instant."
    },
    "cylex": {
        "key": "cylex",
        "name": "Cylex",
        "domain": "cylex-canada.ca",
        "submission_url": "https://www.cylex-canada.ca/company-add",
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["general_business", "local"],
        "active": False,  # Cloudflare 403
        "priority": 1,
        "requires_email_verification": True,
        "submission_method": "playwright",
        "notes": "⚠️ Bloqué par Cloudflare (403). Désactivé."
    },
    "canpages": {
        "key": "canpages",
        "name": "Canpages",
        "domain": "canpages.ca",
        "submission_url": "https://www.canpages.ca/page/add-your-business",
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["local", "canada"],
        "active": False,  # Page 404
        "priority": 1,
        "requires_email_verification": True,
        "submission_method": "playwright",
        "notes": "⚠️ Page de soumission 404. Désactivé."
    },
    "411": {
        "key": "411",
        "name": "411.ca",
        "domain": "411.ca",
        "submission_url": "https://www.411.ca/business/add",
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["local", "canada"],
        "active": False,  # 403 Forbidden
        "priority": 1,
        "requires_email_verification": True,
        "submission_method": "playwright",
        "notes": "⚠️ 403 Forbidden. Désactivé."
    },
    "iglobal": {
        "key": "iglobal",
        "name": "iGlobal",
        "domain": "ca.iglobal.co",
        "submission_url": "https://ca.iglobal.co/add-business",
        "category": "directory",
        "country": "CA",
        "language": ["en"],
        "niche": ["general_business"],
        "active": False,  # DNS mort
        "priority": 2,
        "requires_email_verification": True,
        "submission_method": "playwright",
        "notes": "⚠️ Domaine inaccessible. Désactivé."
    },
    "indexbeaute": {
        "key": "indexbeaute",
        "name": "Index Beauté",
        "domain": "indexbeaute.ca",
        "submission_url": None,
        "category": "beauty_directory",
        "country": "CA",
        "language": ["fr"],
        "niche": ["beauty", "hair", "salon"],
        "active": True,
        "priority": 1,
        "requires_email_verification": True,
        "submission_method": "playwright",
        "notes": "Très pertinent niche beauté/coiffure si soumission encore possible."
    },
    "yelp": {
        "key": "yelp",
        "name": "Yelp",
        "domain": "yelp.ca",
        "submission_url": "https://biz.yelp.com",
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["local", "reviews"],
        "active": False,
        "priority": 3,
        "requires_email_verification": True,
        "submission_method": "manual_or_playwright",
        "notes": "Souvent plus compliqué / modération / login lourd. Désactivé par défaut."
    },
    "yellowpages": {
        "key": "yellowpages",
        "name": "YellowPages",
        "domain": "yellowpages.ca",
        "submission_url": "https://www.yellowpages.ca/business/",
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["local", "canada"],
        "active": False,
        "priority": 3,
        "requires_email_verification": True,
        "submission_method": "manual_or_playwright",
        "notes": "Peut être utile mais souvent plus lourd ou moins simple à automatiser."
    },
    "google_business_profile": {
        "key": "google_business_profile",
        "name": "Google Business Profile",
        "domain": "business.google.com",
        "submission_url": None,
        "category": "business_profile",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["local", "maps"],
        "active": False,
        "priority": 1,
        "requires_email_verification": False,
        "submission_method": "manual",
        "notes": "Haute valeur, mais gestion souvent manuelle. Ne pas automatiser au hasard."
    },
}


BUSINESS_DATA_TEMPLATE = {
    "business_name": "Luxura Distribution",
    "website": "https://www.luxuradistribution.com",
    "email": "info@luxuradistribution.com",
    "phone": "",
    "address_line_1": "",
    "address_line_2": "",
    "city": "",
    "province": "QC",
    "postal_code": "",
    "country": "Canada",
    "description_short": (
        "Luxura Distribution est un importateur et distributeur d'extensions capillaires "
        "haut de gamme au Québec, avec vente en ligne et partenariats salons."
    ),
    "description_long": (
        "Luxura Distribution propose des extensions capillaires haut de gamme au Québec "
        "pour les consommatrices et les salons professionnels, incluant des partenariats "
        "salons et des solutions d'inventaire."
    ),
    "category_primary": "Extensions capillaires",
    "category_secondary": "Beauté / Coiffure",
    "facebook_url": "",
    "instagram_url": "",
}


def get_directory(key: str) -> Optional[Dict]:
    return DIRECTORY_REGISTRY.get(key)


def get_all_directories() -> List[Dict]:
    return list(DIRECTORY_REGISTRY.values())


def get_active_directories() -> List[Dict]:
    return [d for d in DIRECTORY_REGISTRY.values() if d.get("active") is True]


def get_directories_requiring_email_verification() -> List[Dict]:
    return [
        d for d in DIRECTORY_REGISTRY.values()
        if d.get("active") is True and d.get("requires_email_verification") is True
    ]


def get_directories_by_priority(priority: int) -> List[Dict]:
    return [
        d for d in DIRECTORY_REGISTRY.values()
        if d.get("active") is True and d.get("priority") == priority
    ]


def get_directories_by_category(category: str) -> List[Dict]:
    return [
        d for d in DIRECTORY_REGISTRY.values()
        if d.get("active") is True and d.get("category") == category
    ]


def get_directories_by_niche(niche: str) -> List[Dict]:
    return [
        d for d in DIRECTORY_REGISTRY.values()
        if d.get("active") is True and niche in d.get("niche", [])
    ]


def get_submission_queue() -> List[Dict]:
    """
    Retourne les annuaires actifs triés par priorité puis nom.
    """
    active = get_active_directories()
    return sorted(active, key=lambda x: (x.get("priority", 99), x.get("name", "")))


def is_directory_active(key: str) -> bool:
    directory = get_directory(key)
    return bool(directory and directory.get("active") is True)


def build_business_payload(overrides: Optional[Dict] = None) -> Dict:
    """
    Construit un payload standard Luxura, modifiable par overrides.
    """
    data = BUSINESS_DATA_TEMPLATE.copy()
    if overrides:
        data.update(overrides)
    return data
