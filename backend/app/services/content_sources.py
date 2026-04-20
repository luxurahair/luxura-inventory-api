"""
Sources et requêtes pour la collecte de contenu
Centralise les mots-clés, sources fiables et filtres
NOUVELLE VERSION: Tendances Mode Féminine Internationale (Europe, Italie, USA)
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
    country: str = "international"  # "france", "italy", "usa", "uk"


# ============================================
# REQUÊTES DE RECHERCHE - DIVERSIFIÉES INTERNATIONALES
# ============================================

SEARCH_QUERIES = [
    # ==== TENDANCES COIFFURE 2026 ====
    "bob haircut trends 2026",
    "lob hairstyle women 2026",
    "fringe bangs trends 2026",
    "micro bang hairstyle",
    "curtain bangs styling",
    "glossy hair trend 2026",
    
    # ==== EXTENSIONS CAPILLAIRES ====
    "hair extensions trends 2026",
    "tape-in hair extensions natural",
    "halo extensions invisible",
    "weft extensions seamless",
    "clip-in extensions styling",
    "hand-tied weft extensions",
    
    # ==== MODE FÉMININE INTERNATIONALE ====
    "women hair trends Europe 2026",
    "Italian fashion hairstyles 2026",
    "French women hair trends",
    "Milan fashion week hair",
    "Paris fashion hair trends",
    
    # ==== LIFESTYLE & BEAUTÉ ====
    "quiet luxury hair aesthetic",
    "healthy shiny hair tips",
    "hair volume solutions women",
    "bridal hairstyles 2026",
    "celebrity hairstyles 2026",
    
    # ==== CANADA/QUÉBEC ====
    "hair extensions Canada salon",
    "extensions cheveux Québec tendance",
    "coiffure femme tendance Montréal",
]

# ============================================
# REQUÊTES SPÉCIFIQUES PAR PAYS (ROTATION)
# ============================================

INTERNATIONAL_QUERIES = {
    "france": [
        "tendances coiffure femme 2026",
        "bob carré tendance Paris",
        "extensions cheveux naturels France",
        "coupe femme élégante 2026",
    ],
    "italy": [
        "hair trends Milan 2026",
        "Italian women hairstyles",
        "glossy hair Italian style",
        "capelli tendenze 2026",
    ],
    "usa": [
        "hair trends New York 2026",
        "celebrity hair extensions Hollywood",
        "American women hairstyles trends",
        "hair volume trends USA",
    ],
    "uk": [
        "hair trends London 2026",
        "British women hairstyles",
        "Kate Middleton hair style",
        "UK beauty hair trends",
    ],
}

# ============================================
# SOURCES FIABLES - INTERNATIONALES
# ============================================

TRUSTED_SOURCES = [
    # ==== 🇫🇷 FRANCE ====
    "elle.fr",
    "vogue.fr",
    "marieclaire.fr",
    "glamourparis.com",
    "journaldesfemmes.fr",
    "femmeactuelle.fr",
    "grazia.fr",
    
    # ==== 🇮🇹 ITALIE ====
    "vogue.it",
    "grazia.it",
    "elle.it",
    "vanityfair.it",
    "marieclaire.it",
    
    # ==== 🇺🇸 USA ====
    "allure.com",
    "elle.com",
    "glamour.com",
    "byrdie.com",
    "harpersbazaar.com",
    "vogue.com",
    "cosmopolitan.com",
    "refinery29.com",
    "beautylaunchpad.com",
    "instyle.com",
    
    # ==== 🇬🇧 UK ====
    "elle.com/uk",
    "glamourmagazine.co.uk",
    "harpersbazaar.com/uk",
    "marieclaire.co.uk",
    
    # ==== 🇨🇦 CANADA ====
    "fashionmagazine.com",
    "thekit.ca",
    "cbc.ca/life",
    "modernbeauty.ca",
    "salonmagazine.ca",
]

# ============================================
# RSS FEEDS INTERNATIONAUX (TENDANCES COIFFURE)
# ============================================

INTERNATIONAL_RSS_FEEDS = {
    "france": [
        "https://www.elle.fr/rss/beaute",
        "https://www.marieclaire.fr/rss/beaute.xml",
    ],
    "italy": [
        "https://www.vogue.it/rss/bellezza.xml",
    ],
    "usa": [
        "https://www.allure.com/feed/rss",
        "https://www.byrdie.com/rss",
    ],
    "uk": [
        "https://www.glamourmagazine.co.uk/topic/hair/rss",
    ],
}

# ============================================
# MOTS-CLÉS DE PERTINENCE
# ============================================

# =============================================
# MOTS-CLÉS OBLIGATOIRES - EXTENSIONS OU TENDANCES COIFFURE
# Un article DOIT contenir au moins UN de ces mots pour être accepté
# =============================================
REQUIRED_EXTENSION_KEYWORDS = [
    # ==== EXTENSIONS CAPILLAIRES ====
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
    
    # ==== TENDANCES COIFFURE 2026 (NOUVEAU) ====
    "bob haircut", "bob cut", "lob haircut", "lob hairstyle",
    "fringe", "bangs", "frange", "micro bang", "curtain bangs",
    "glossy hair", "shiny hair", "cheveux brillants",
    "hair trends", "tendances coiffure", "tendance cheveux",
    "hairstyle", "coiffure femme", "coupe femme",
    "hair volume", "volume cheveux",
    "long hair", "cheveux longs", "longueurs",
    "healthy hair", "cheveux sains",
]

# Mots-clés bonus (augmentent le score mais pas obligatoires)
INCLUDE_KEYWORDS = [
    # ==== QUALITÉ CHEVEUX ====
    "remy", "remy hair", "human hair", "cheveux naturels",
    "virgin hair", "premium hair", "luxury hair",
    "100% human", "100% naturel", "real hair",
    "silky", "soyeux", "smooth", "lisse",
    
    # ==== STYLE & LIFESTYLE ====
    "elegant", "élégant", "chic", "sophisticated",
    "natural looking", "naturel", "authentic",
    "quiet luxury", "luxe discret",
    "lifestyle", "fashion", "mode",
    
    # ==== TENDANCES ====
    "trending", "tendance", "trend", "2026", "2025",
    "milan fashion", "paris fashion", "new york fashion",
    "celebrity", "célébrité", "star", "red carpet",
    
    # ==== INSTALLATION/SOINS ====
    "extension installation", "pose extension", "application",
    "extension care", "soin extension", "maintenance",
    "hair transformation", "transformation cheveux",
    "before and after", "avant après",
    
    # ==== FÉMININ ====
    "women", "woman", "femme", "femmes", "feminine", "féminin",
    "bride", "bridal", "mariée", "mariage",
    "beauty", "beauté", "glamour", "gorgeous",
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
# TON LUXURA - STYLE MAGAZINE FÉMININ
# ============================================

LUXURA_TONE = {
    "style": "magazine féminin, chic, expert mais accessible, québécois",
    "target": "femmes québécoises 25-55 ans passionnées de beauté",
    "values": ["qualité", "expertise", "beauté naturelle", "confiance", "authenticité"],
    "avoid": ["agressif", "cheap", "discount", "urgence artificielle", "stock photo style", "promotionnel direct"],
    "cta_examples": [
        "Et toi, tu préfères quoi?",
        "Quelle option te tente le plus?",
        "Partage ton avis en commentaire!",
        "Découvrez plus sur luxuradistribution.com",
        "Envie d'en savoir plus? Visitez-nous!",
    ],
    "hashtags": [
        "#ExtensionsCapillaires", "#Luxura", "#CheveuxPremium",
        "#BeautéQuébec", "#Tendances2026", "#CoiffureFemme",
        "#BobHaircut", "#CheveuxBrillants", "#QuietLuxury",
        "#CoiffureMontréal", "#StyleFéminin",
    ],
}

# ============================================
# THÈMES DE POSTS MAGAZINE
# ============================================

MAGAZINE_THEMES = {
    "tendance_coupe": {
        "name": "Décryptage Tendance Coupe",
        "description": "Analyse d'une coupe tendance (bob, lob, frange)",
        "tone": "informatif, expert",
        "example_titles": [
            "Le bob 2026 est partout... mais il ne va pas à tout le monde",
            "Frange micro ou curtain bangs: le match",
            "Le lob: la coupe qui va à toutes les formes de visage",
        ],
    },
    "comparatif_extensions": {
        "name": "Comparatif Extensions",
        "description": "Comparaison des méthodes d'extensions",
        "tone": "éducatif, conseil pro",
        "example_titles": [
            "Halo, tape-in ou weft invisible: quelle méthode pour toi?",
            "Extensions: ce qu'on ne te dit pas ailleurs",
            "Le vrai coût des extensions: comparatif complet",
        ],
    },
    "conseils_erreurs": {
        "name": "Conseils / Erreurs à éviter",
        "description": "Conseils pratiques ou erreurs courantes",
        "tone": "utile, bienveillant",
        "example_titles": [
            "Les 5 erreurs qui vieillissent ta coiffure",
            "Comment garder des cheveux brillants tout l'été",
            "Les secrets des cheveux glossy des Italiennes",
        ],
    },
    "quiet_luxury": {
        "name": "Quiet Luxury Cheveux",
        "description": "Tendance luxe discret appliquée aux cheveux",
        "tone": "aspirationnel, élégant",
        "example_titles": [
            "Pourquoi les cheveux brillants font plus luxe que les cheveux longs",
            "Le glossy hair: nouvelle obsession des fashionistas",
            "La beauté à l'italienne: ce qu'on peut apprendre de Milan",
        ],
    },
    "inspiration_internationale": {
        "name": "Inspiration Internationale",
        "description": "Tendances de Paris, Milan, NYC, Londres",
        "tone": "inspirant, tendance",
        "example_titles": [
            "Ce qu'on a vu à la Fashion Week de Milan",
            "Les tendances cheveux qui débarquent de Paris",
            "Comment les New-Yorkaises portent les extensions",
        ],
    },
}

# ============================================
# TEMPLATES DE POSTS - STYLE MAGAZINE
# ============================================

POST_TEMPLATES = {
    "magazine_tendance": """✨ **{title}**

{intro}

{content}

💡 **Notre conseil Luxura:** {conseil}

{question_engagement}

👉 luxuradistribution.com

{hashtags}
""",
    
    "magazine_comparatif": """🔍 **{title}**

{intro}

{comparaison}

💭 **Ce qu'on ne te dit pas ailleurs:** {insight}

{question_engagement}

👉 Consultation gratuite: luxuradistribution.com

{hashtags}
""",
    
    "magazine_conseils": """⚡ **{title}**

{intro}

{conseils_liste}

✨ **Le secret?** {secret}

{question_engagement}

👉 luxuradistribution.com

{hashtags}
""",
    
    "magazine_inspiration": """💎 **{title}**

{intro}

{tendance_description}

🌟 **Chez Luxura:** {lien_luxura}

{question_engagement}

👉 luxuradistribution.com

{hashtags}
""",

    # Templates classiques (conservés)
    "news": """📰 ACTUALITÉ

{content}

➡️ Source: {source}

{hashtags}

🌐 luxuradistribution.com
""",
    
    "trend": """✨ TENDANCE DU MOMENT

{content}

💇‍♀️ Vous voulez ce look? Nos extensions premium vous permettent de l'obtenir!

{hashtags}

🌐 luxuradistribution.com
""",
    
    "tip": """💡 CONSEIL PRO

{content}

👉 Besoin de conseils personnalisés? Contactez-nous!

{hashtags}

📧 info@luxuradistribution.com
🌐 luxuradistribution.com
""",
    
    "inspiration": """🌟 INSPIRATION

{content}

❤️ Partagez si vous aimez ce look!

{hashtags}

🌐 luxuradistribution.com
""",
}

# ============================================
# IMAGES STOCK NATURELLES (FALLBACK)
# ============================================

NATURAL_HAIR_IMAGES = [
    "https://images.unsplash.com/photo-1496440737103-cd596325d314",  # Woman flipping hair
    "https://images.pexels.com/photos/113042/pexels-photo-113042.jpeg",  # Hair texture
    "https://images.pexels.com/photos/29521440/pexels-photo-29521440.jpeg",  # Natural sunlight
    "https://images.unsplash.com/photo-1503830232159-4b417691001e",  # Flowing hair
    "https://images.pexels.com/photos/36784935/pexels-photo-36784935.jpeg",  # Salon look
]
