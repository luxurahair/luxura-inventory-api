# directory_registry.py
"""
Source de vérité unique pour les annuaires / citations Luxura.

Classification des submission_method:
- public_form: Formulaire public simple, pas de compte requis
- multi_step: Formulaire public mais en plusieurs étapes
- login_required: Nécessite création de compte + login
- claim_flow: Flow de réclamation de fiche existante
- manual_only: Pas de formulaire automatisable, contact manuel
- dead: Site mort ou inutilisable

Dernière mise à jour: 2026-03-29
"""

from typing import Dict, List, Optional


DIRECTORY_REGISTRY: Dict[str, Dict] = {
    # ==========================================
    # ANNUAIRE ACTIF - EXPLOITABLE
    # ==========================================
    "brownbook": {
        "key": "brownbook",
        "name": "Brownbook",
        "domain": "brownbook.net",
        "submission_url": "https://www.brownbook.net/add-business/",
        "category": "directory",
        "country": "GLOBAL",
        "language": ["en"],
        "niche": ["general_business"],
        "active": True,
        "priority": 1,
        "requires_email_verification": True,
        "submission_method": "multi_step",
        "submission_notes": "Public add-business flow is live, but multi-step. DA 73. Best current option.",
    },
    
    # ==========================================
    # ANNUAIRES VIVANTS MAIS NON AUTOMATIQUES
    # ==========================================
    "hotfrog": {
        "key": "hotfrog",
        "name": "Hotfrog",
        "domain": "hotfrog.ca",
        "submission_url": None,
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["general_business", "local"],
        "active": False,
        "priority": 2,
        "requires_email_verification": True,
        "submission_method": "claim_flow",
        "submission_notes": "Site is live, but practical flow appears to be claim/listing management rather than a simple public form.",
    },
    "cylex": {
        "key": "cylex",
        "name": "Cylex",
        "domain": "cylex-canada.ca",
        "submission_url": "https://www.cylex-canada.ca/",
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["general_business", "local"],
        "active": False,
        "priority": 2,
        "requires_email_verification": True,
        "submission_method": "login_required",
        "submission_notes": "Registration is available, but FAQ shows account creation + sign-in + register business workflow.",
    },
    "411": {
        "key": "411",
        "name": "411.ca",
        "domain": "411.ca",
        "submission_url": "https://login.411.ca/session-transfer/?prompt=&serviceContext=eyJfdHlwZSI6InBhcnRuZXIiLCJwYXJ0bmVyX2lkIjoiNDExQyJ9&serviceProviderId=VBC",
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["local", "canada"],
        "active": False,
        "priority": 2,
        "requires_email_verification": True,
        "submission_method": "login_required",
        "submission_notes": "Business App sign-in/create-account flow confirmed; not a simple public add-business form.",
    },
    "canpages": {
        "key": "canpages",
        "name": "Canpages",
        "domain": "canpages.ca",
        "submission_url": None,
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["local", "canada"],
        "active": False,
        "priority": 2,
        "requires_email_verification": False,
        "submission_method": "manual_only",
        "submission_notes": "Main directory is live, but old add-business URL is obsolete and no clean public submission flow was confirmed.",
    },
    
    # ==========================================
    # ANNUAIRES MORTS / INUTILISABLES
    # ==========================================
    "iglobal": {
        "key": "iglobal",
        "name": "iGlobal",
        "domain": "ca.iglobal.co",
        "submission_url": None,
        "category": "directory",
        "country": "CA",
        "language": ["en"],
        "niche": ["general_business"],
        "active": False,
        "priority": 3,
        "requires_email_verification": False,
        "submission_method": "dead",
        "submission_notes": "No reliable current Canada submission flow confirmed.",
    },
    
    # ==========================================
    # ANNUAIRES À TRAITEMENT MANUEL
    # ==========================================
    "indexbeaute": {
        "key": "indexbeaute",
        "name": "Index Beauté",
        "domain": "indexbeaute.ca",
        "submission_url": None,
        "category": "beauty_directory",
        "country": "CA",
        "language": ["fr"],
        "niche": ["beauty", "hair", "salon"],
        "active": False,
        "priority": 1,
        "requires_email_verification": True,
        "submission_method": "manual_only",
        "submission_notes": "Niche beauté/coiffure pertinent. À vérifier manuellement si soumission possible.",
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
        "submission_method": "login_required",
        "submission_notes": "Yelp Business requires account. Heavy anti-bot. Manual recommended.",
    },
    "yellowpages": {
        "key": "yellowpages",
        "name": "Yellow Pages Canada",
        "domain": "yellowpages.ca",
        "submission_url": None,
        "category": "directory",
        "country": "CA",
        "language": ["fr", "en"],
        "niche": ["local"],
        "active": False,
        "priority": 3,
        "requires_email_verification": True,
        "submission_method": "manual_only",
        "submission_notes": "Large directory but submission process unclear. Manual verification needed.",
    },
    "google_business_profile": {
        "key": "google_business_profile",
        "name": "Google Business Profile",
        "domain": "business.google.com",
        "submission_url": "https://business.google.com",
        "category": "local_seo",
        "country": "GLOBAL",
        "language": ["fr", "en"],
        "niche": ["local", "maps"],
        "active": False,
        "priority": 1,
        "requires_email_verification": True,
        "submission_method": "manual_only",
        "submission_notes": "Critical for local SEO. Requires Google account + address verification. Always manual.",
    },
}


# ==========================================
# BUSINESS INFO - Luxura Distribution
# ==========================================

LUXURA_BUSINESS_INFO: Dict[str, str] = {
    "business_name": "Luxura Distribution",
    "website": "https://www.luxuradistribution.com",
    "email": "info@luxuradistribution.com",
    "phone": "418-774-4315",
    "address_line_1": "8905 Boulevard Lacroix",
    "city": "Saint-Georges",
    "province": "QC",
    "postal_code": "G5Y 1T4",
    "country": "Canada",
    "description": (
        "Luxura Distribution est un importateur et distributeur direct d'extensions capillaires professionnelles au Québec. "
        "Nous offrons des extensions de cheveux de qualité salon pour les coiffeurs professionnels, avec un inventaire "
        "multi-salons et un programme de partenariat exclusif."
    ),
    "description_short": "Distributeur d'extensions capillaires professionnelles au Québec",
    "description_en": (
        "Luxura Distribution is a direct importer and distributor of professional hair extensions in Quebec, Canada. "
        "We offer salon-quality hair extensions for professional hairstylists, with multi-salon inventory and an exclusive partnership program."
    ),
    "categories": ["Hair Extensions", "Beauty Supply", "Salon Products", "Wholesale Hair"],
    "categories_fr": ["Extensions capillaires", "Produits de beauté", "Produits salon", "Cheveux en gros"],
    "facebook_url": "",
    "instagram_url": "",
}


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_directory(key: str) -> Optional[Dict]:
    """Retourne un annuaire par sa clé."""
    return DIRECTORY_REGISTRY.get(key)


def get_all_directories() -> List[Dict]:
    """Retourne tous les annuaires."""
    return list(DIRECTORY_REGISTRY.values())


def get_active_directories() -> List[Dict]:
    """Retourne uniquement les annuaires actifs."""
    return [d for d in DIRECTORY_REGISTRY.values() if d.get("active")]


def get_directories_by_method(method: str) -> List[Dict]:
    """Retourne les annuaires par type de soumission."""
    return [d for d in DIRECTORY_REGISTRY.values() if d.get("submission_method") == method]


def get_submission_queue() -> List[Dict]:
    """
    Retourne la liste des annuaires actifs triés par priorité.
    Priorité 1 = plus important.
    """
    active = get_active_directories()
    return sorted(active, key=lambda d: d.get("priority", 99))


def build_business_payload(overrides: Optional[Dict] = None) -> Dict:
    """
    Construit le payload business pour les soumissions.
    Permet de surcharger certains champs si besoin.
    """
    payload = LUXURA_BUSINESS_INFO.copy()
    if overrides:
        payload.update(overrides)
    return payload


def get_exploitable_directories() -> List[Dict]:
    """
    Retourne les annuaires potentiellement exploitables automatiquement.
    Inclut: public_form, multi_step
    Exclut: login_required, claim_flow, manual_only, dead
    """
    exploitable_methods = {"public_form", "multi_step"}
    return [
        d for d in DIRECTORY_REGISTRY.values()
        if d.get("submission_method") in exploitable_methods and d.get("active")
    ]


def get_registry_summary() -> Dict:
    """Retourne un résumé du registre pour debug/API."""
    all_dirs = get_all_directories()
    
    by_method = {}
    for d in all_dirs:
        method = d.get("submission_method", "unknown")
        if method not in by_method:
            by_method[method] = []
        by_method[method].append(d["key"])
    
    return {
        "total": len(all_dirs),
        "active": len(get_active_directories()),
        "exploitable": len(get_exploitable_directories()),
        "by_method": by_method,
    }
