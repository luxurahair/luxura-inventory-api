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

# Mots-clés obligatoires (au moins un)
INCLUDE_KEYWORDS = [
    # Types d'extensions
    "extension", "extensions", "hair extension", "hair extensions",
    "rallonge", "rallonges", "rajout", "rajouts",
    "tape-in", "tape in", "tapein",
    "clip-in", "clip in", "clipin",
    "weft", "genius weft", "hand-tied", "hand tied", "handtied",
    "keratin", "kératine", "fusion", "k-tip", "i-tip", "u-tip",
    "micro-link", "microlink", "micro ring",
    "ponytail extension", "queue de cheval",
    "halo extension", "wire extension",
    "topper", "toppers", "hair topper",
    
    # Cheveux
    "long hair", "cheveux longs",
    "hair volume", "volume cheveux",
    "thick hair", "cheveux épais",
    "hair length", "longueur cheveux",
    "hair transformation", "transformation cheveux",
    
    # Qualité
    "remy", "remy hair", "human hair", "cheveux naturels",
    "virgin hair", "premium hair", "luxury hair",
    "100% human", "100% naturel",
    
    # Salon/Pro
    "salon", "coiffeur", "coiffeuse", "styliste", "stylist",
    "hair professional", "professionnel cheveux",
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
    
    # Homme
    "men's hair", "beard", "barbe", "male pattern",
    
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
