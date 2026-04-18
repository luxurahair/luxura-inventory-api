"""
Sources et requêtes pour la collecte de contenu
Centralise les mots-clés, sources fiables et filtres
"""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class ContentSource:
    name: str
    url: str
    type: str  # "rss", "google_news", "scraper"
    category: str  # "hair", "beauty", "fashion"
    priority: int = 1  # 1 = haute, 3 = basse


# ============================================
# REQUÊTES DE RECHERCHE
# ============================================

SEARCH_QUERIES = [
    # Extensions capillaires
    "hair extensions trends 2026",
    "tape-in hair extensions",
    "clip-in extensions styling",
    "seamless hair extensions",
    "hand-tied weft extensions",
    "keratin bond extensions",
    
    # Canada spécifique
    "hair extensions Canada",
    "extensions cheveux Québec",
    "salon extensions Montréal",
    
    # Tendances
    "hair trends women 2026",
    "long hair styling tips",
    "hair volume solutions",
    "celebrity hair extensions",
    
    # Qualité
    "Remy human hair",
    "premium hair extensions",
    "natural looking extensions",
]

# ============================================
# SOURCES FIABLES
# ============================================

TRUSTED_SOURCES = [
    # Magazines beauté majeurs
    "allure.com",
    "elle.com",
    "glamour.com",
    "byrdie.com",
    "harpersbazaar.com",
    "vogue.com",
    "cosmopolitan.com",
    "refinery29.com",
    "beautytap.com",
    
    # Canada
    "fashionmagazine.com",
    "cbc.ca",
    "globalnews.ca",
    "thekit.ca",
    
    # Industrie
    "modernbeauty.ca",
    "salonmagazine.ca",
    "beautyindependent.com",
]

# ============================================
# MOTS-CLÉS DE PERTINENCE
# ============================================

# =============================================
# MOTS-CLÉS OBLIGATOIRES - EXTENSIONS CAPILLAIRES SEULEMENT
# Un article DOIT contenir au moins UN de ces mots pour être accepté
# =============================================
REQUIRED_EXTENSION_KEYWORDS = [
    # Extensions - OBLIGATOIRE
    "extension", "extensions", "hair extension", "hair extensions",
    "rallonge", "rallonges", "rajout", "rajouts",
    "tape-in", "tape in", "tapein", "tape extension",
    "clip-in", "clip in", "clipin", "clip extension",
    "weft", "genius weft", "hand-tied", "hand tied", "handtied",
    "keratin extension", "kératine extension", "fusion extension",
    "k-tip", "i-tip", "u-tip", "flat tip",
    "micro-link", "microlink", "micro ring", "micro bead",
    "ponytail extension", "queue de cheval extension",
    "halo extension", "wire extension", "invisible wire",
    "topper", "toppers", "hair topper", "wiglet",
    "weave", "sew-in", "sew in",
    "hair piece", "hairpiece", "postiche",
]

# Mots-clés bonus (augmentent le score mais pas obligatoires)
INCLUDE_KEYWORDS = [
    # Qualité extensions
    "remy", "remy hair", "human hair", "cheveux naturels",
    "virgin hair", "premium hair", "luxury hair",
    "100% human", "100% naturel", "real hair",
    
    # Installation/Entretien extensions
    "extension installation", "pose extension", "application",
    "extension removal", "retrait extension",
    "extension maintenance", "entretien extension",
    "extension care", "soin extension",
    
    # Transformation avec extensions
    "hair transformation", "transformation cheveux",
    "before and after", "avant après",
    "length", "longueur", "volume",
    
    # Féminin
    "women", "woman", "femme", "femmes",
    "bride", "bridal", "mariée", "mariage",
    "celebrity", "célébrité", "star",
    "beauty", "beauté", "glamour",
]

# Mots-clés d'exclusion
EXCLUDE_KEYWORDS = [
    # Hors sujet
    "wig", "perruque", "bald", "chauve", "toupee", "toupée",
    "hair loss treatment", "traitement perte cheveux",
    "minoxidil", "finasteride", "hair transplant", "greffe",
    
    # Médical
    "medical", "médical", "cancer", "chimio", "chemo",
    "alopecia", "alopécie",
    
    # =============================================
    # MASCULIN / HOMMES - BLOQUER COMPLÈTEMENT
    # =============================================
    "men's hair", "beard", "barbe", "male pattern",
    "masculine", "masculin", "masculinity", "masculinité",
    "men's fashion", "mode masculine", "menswear", "mode homme",
    "men's style", "style homme", "for men", "pour homme",
    "homme", "hommes", "man", "men",
    "gentleman", "gentlemen",
    "barbershop", "barbier", "barber",
    "male grooming", "soins homme",
    "men's week", "semaine homme",
    "guy", "guys", "gars",
    
    # Spam/Pub
    "buy now", "discount code", "promo code", "coupon",
    "casino", "lottery", "crypto", "bitcoin", "forex",
    "click here", "subscribe now", "limited time",
    
    # Contenu faible
    "sponsored", "advertorial", "paid partnership",
]

# Mots-clés Canada (bonus de score)
CANADA_KEYWORDS = [
    "canada", "canadian", "canadien", "canadienne",
    "québec", "quebec", "québécois",
    "montréal", "montreal",
    "toronto", "vancouver", "ottawa", "calgary", "edmonton",
    "ontario", "british columbia", "alberta",
]

# ============================================
# TON LUXURA
# ============================================

LUXURA_TONE = {
    "style": "premium, féminin, professionnel, québécois",
    "target": "femmes québécoises 25-55 ans",
    "values": ["qualité", "confiance", "beauté", "transformation", "naturel"],
    "avoid": ["agressif", "cheap", "discount", "urgence artificielle"],
    "cta_examples": [
        "Découvrez notre collection sur luxuradistribution.com",
        "Transformez votre look avec Luxura",
        "Commandez vos extensions premium dès maintenant",
        "Visitez-nous pour une consultation gratuite",
    ],
    "hashtags": [
        "#ExtensionsCapillaires", "#Luxura", "#CheveuxPremium",
        "#BeautéQuébec", "#TransformationCheveux", "#CoiffureMontréal",
        "#ExtensionsProfessionnelles", "#CheveuxNaturels", "#RaltongesCheveux",
    ],
}

# ============================================
# TEMPLATES DE POSTS
# ============================================

POST_TEMPLATES = {
    "news": """
📰 ACTUALITÉ EXTENSIONS

{content}

➡️ Source: {source}

{hashtags}

🌐 luxuradistribution.com
""",
    
    "trend": """
✨ TENDANCE DU MOMENT

{content}

💇‍♀️ Vous voulez ce look? Nos extensions premium vous permettent de l'obtenir!

{hashtags}

🌐 luxuradistribution.com
""",
    
    "tip": """
💡 CONSEIL PRO

{content}

👉 Besoin de conseils personnalisés? Contactez-nous!

{hashtags}

📧 info@luxuradistribution.com
🌐 luxuradistribution.com
""",
    
    "inspiration": """
🌟 INSPIRATION

{content}

❤️ Partagez si vous aimez ce look!

{hashtags}

🌐 luxuradistribution.com
""",
}
