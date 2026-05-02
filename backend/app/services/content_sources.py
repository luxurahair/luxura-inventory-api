"""
Sources et requêtes pour la collecte de contenu
Centralise les mots-clés, sources fiables et filtres
VERSION 3.0: Grands Magazines Féminins Internationaux + Sujets Diversifiés
- Vogue, Elle, Harper's Bazaar, Marie Claire, Cosmopolitan, Glamour, Allure, Grazia
- Entretien cheveux, Look féminin, Mode internationale
IMPORTANT: Anti-doublon - évite de répéter les mêmes sujets
"""

from typing import List, Dict
from dataclasses import dataclass
import random


@dataclass
class ContentSource:
    name: str
    url: str
    type: str  # "rss", "google_news", "scraper"
    category: str  # "hair", "beauty", "fashion"
    priority: int = 1  # 1 = haute, 3 = basse
    country: str = "international"  # "france", "italy", "usa", "uk"


# ============================================
# REQUÊTES DE RECHERCHE - MAGAZINES FÉMININS INTERNATIONAUX
# ============================================
# VERSION 3.0: Diversité maximale - plus de bob haircuts en boucle!
# Sources: Vogue, Elle, Harper's Bazaar, Marie Claire, Glamour, Allure, Cosmopolitan

SEARCH_QUERIES = [
    # ==== 🌟 EXTENSIONS CAPILLAIRES (PRIORITÉ HAUTE) ====
    "hair extensions trends 2026 Vogue",
    "tape-in extensions natural look Elle magazine",
    "halo extensions invisible styling Harper's Bazaar",
    "weft extensions seamless Marie Claire",
    "clip-in extensions transformation Glamour",
    "hand-tied weft extensions luxury Allure",
    "hair extensions thin hair volume solutions",
    "hair extensions wedding bridal looks",
    "hair extensions celebrity red carpet",
    "ponytail extensions elegant style",
    
    # ==== 💇‍♀️ ENTRETIEN CHEVEUX (NOUVEAU - ÉLARGI) ====
    "hair care routine healthy shiny 2026",
    "hair maintenance tips professional salon",
    "deep conditioning treatment damaged hair",
    "hair oil treatment benefits natural",
    "protect hair from heat styling tips",
    "hair mask DIY natural ingredients",
    "how to prevent hair breakage tips",
    "best hair products for volume 2026",
    "scalp care routine healthy hair growth",
    "overnight hair treatments beauty sleep",
    
    # ==== 👠 LOOK FÉMININ & MODE (NOUVEAU) ====
    "women fashion look trends 2026 Vogue",
    "elegant feminine style Milan Fashion Week",
    "Paris Fashion Week women looks 2026",
    "Italian women style la dolce vita chic",
    "French girl aesthetic effortless beauty",
    "quiet luxury fashion trend women",
    "celebrity fashion looks red carpet 2026",
    "office chic women professional style",
    "weekend casual elegant women look",
    "evening glamour women style gala",
    
    # ==== 📰 MAGAZINES FÉMININS - ACTUALITÉS MODE ====
    "Vogue beauty hair trends 2026",
    "Elle magazine hair styling tips",
    "Harper's Bazaar women fashion 2026",
    "Marie Claire beauty secrets",
    "Glamour magazine hair transformation",
    "Allure best hair products 2026",
    "Cosmopolitan beauty trends women",
    "Grazia fashion style women Italy",
    "InStyle celebrity hair looks",
    "Who What Wear fashion trends",
    
    # ==== 🌍 TENDANCES INTERNATIONALES ====
    "Italian bob haircut elegant Milan",
    "French girl hair effortless chic Paris",
    "Hollywood celebrity hairstyles 2026",
    "London Fashion Week hair trends",
    "New York women style trends",
    "Korean beauty hair trends K-beauty",
    "Scandinavian minimalist hair style",
    
    # ==== 💄 BEAUTÉ & LIFESTYLE ====
    "natural beauty tips women 2026",
    "self care routine hair skin",
    "bridal beauty hair makeup wedding",
    "summer hair care beach protection",
    "winter hair care moisturizing tips",
    "hair color trends 2026 balayage highlights",
    "healthy hair diet nutrition tips",
    
    # ==== 🇨🇦 CANADA/QUÉBEC ====
    "hair extensions Canada premium quality",
    "coiffure femme Montréal tendance 2026",
    "extensions cheveux Québec salons",
    "beauté femme canadienne tendances",
    
    # ==== V4 🇪🇺 MARQUES EXTENSIONS EUROPÉENNES ====
    "Great Lengths extensions trends 2026",
    "Hairdreams extensions techniques nouvelles",
    "Balmain Hair Couture collection 2026",
    "Gold Fever Hair UK trends",
    "Beauty Works extensions celebrity news",
    "SHE Hair Extensions Italy professional",
    "Racoon International UK extensions news",
    "Euro SoCap extensions professional trends",
    
    # ==== V4 🇦🇺 MARQUES EXTENSIONS AUSTRALIENNES ====
    "ZALA Hair Extensions Australia trends",
    "Showpony Professional Australia news",
    "Amazing Hair Australia extensions 2026",
    "Bohyme extensions Australia professional",
    "Australian hair extensions industry news",
]

def get_randomized_queries(max_queries: int = 10) -> List[str]:
    """
    Retourne une liste aléatoire de requêtes pour diversifier les résultats.
    Évite de toujours commencer par les mêmes requêtes.
    Augmenté à 10 requêtes pour plus de diversité.
    """
    shuffled = SEARCH_QUERIES.copy()
    random.shuffle(shuffled)
    return shuffled[:max_queries]

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
    # V4 NOUVEAU - Sources Européennes Extensions
    "europe_extensions": [
        "Great Lengths extensions news 2026",
        "Hairdreams extensions trends Europe",
        "Balmain Hair Couture new collection",
        "She Hair Extensions Europe",
        "Gold Fever Hair extensions trends",
        "Socap Original extensions Italy",
        "Racoon International UK extensions",
        "Cinderella Hair Extensions news",
        "Euro SoCap extensions professional",
        "Beauty Works extensions UK trends",
    ],
    # V4 NOUVEAU - Sources Australiennes Extensions
    "australia_extensions": [
        "ZALA hair extensions Australia trends",
        "Showpony Professional Australia news",
        "EVY Professional extensions Australia",
        "Bellami Hair Australia collection",
        "Hairlocs Australia extensions trends",
        "Amazing Hair extensions Perth",
        "Bohyme Australia hair extensions",
        "Hotheads Australia professional",
    ],
}

# ============================================
# 🌍 V4 - MARQUES D'EXTENSIONS EUROPÉENNES/AUSTRALIENNES À SUIVRE
# ============================================

EXTENSION_BRANDS_TO_MONITOR = {
    "europe": {
        "great_lengths": {
            "name": "Great Lengths",
            "country": "Italy/Germany",
            "website": "greatlengths.com",
            "blog": "greatlengths.com/blog",
            "specialty": "Fusion kératine premium",
        },
        "hairdreams": {
            "name": "Hairdreams",
            "country": "Austria",
            "website": "hairdreams.com",
            "specialty": "Extensions scientifiques haute qualité",
        },
        "balmain": {
            "name": "Balmain Hair Couture",
            "country": "Netherlands/France",
            "website": "balmainhair.com",
            "specialty": "Luxury fashion extensions",
        },
        "she_hair": {
            "name": "SHE Hair Extensions",
            "country": "Italy",
            "website": "she-hair.com",
            "specialty": "Extensions professionnelles italiennes",
        },
        "gold_fever": {
            "name": "Gold Fever",
            "country": "UK",
            "website": "goldfeverhair.com",
            "specialty": "Luxury ethical hair",
        },
        "beauty_works": {
            "name": "Beauty Works",
            "country": "UK",
            "website": "beautyworksonline.com",
            "blog": "beautyworksonline.com/blogs/news",
            "specialty": "Celebrity-loved extensions UK",
        },
        "racoon": {
            "name": "Racoon International",
            "country": "UK",
            "website": "racooninternational.com",
            "specialty": "Professional salon extensions",
        },
    },
    "australia": {
        "zala": {
            "name": "ZALA Hair Extensions",
            "country": "Australia",
            "website": "zalahairextensions.com.au",
            "blog": "zalahairextensions.com.au/blogs",
            "specialty": "Clip-in extensions populaires",
        },
        "showpony": {
            "name": "Showpony Professional",
            "country": "Australia",
            "website": "showponyhair.com",
            "specialty": "Tape-in professionnels",
        },
        "amazing_hair": {
            "name": "Amazing Hair",
            "country": "Australia",
            "website": "amazinghair.com.au",
            "specialty": "Extensions naturelles remy",
        },
        "bohyme": {
            "name": "Bohyme",
            "country": "Australia/USA",
            "website": "bohyme.com",
            "specialty": "Premium weave extensions",
        },
    },
}

# ============================================
# SOURCES FIABLES - GRANDS MAGAZINES FÉMININS INTERNATIONAUX
# ============================================
# VERSION 3.0: Top magazines mondiaux pour contenu premium

TRUSTED_SOURCES = [
    # ==== 🌟 TOP 10 MAGAZINES MONDIAUX ====
    "vogue.com",
    "harpersbazaar.com",
    "elle.com",
    "marieclaire.com",
    "cosmopolitan.com",
    "glamour.com",
    "allure.com",
    "instyle.com",
    "wmagazine.com",
    "whowhatwear.com",
    
    # ==== 🇫🇷 FRANCE ====
    "vogue.fr",
    "elle.fr",
    "marieclaire.fr",
    "glamourparis.com",
    "grazia.fr",
    "journaldesfemmes.fr",
    "femmeactuelle.fr",
    "madamefigaro.fr",
    
    # ==== 🇮🇹 ITALIE ====
    "vogue.it",
    "elle.it",
    "grazia.it",
    "vanityfair.it",
    "marieclaire.it",
    "cosmopolitan.it",
    
    # ==== 🇺🇸 USA ====
    "byrdie.com",
    "refinery29.com",
    "beautylaunchpad.com",
    "thecut.com",
    "popsugar.com",
    "today.com",
    "goodhousekeeping.com",
    
    # ==== 🇬🇧 UK ====
    "vogue.co.uk",
    "elle.com/uk",
    "harpersbazaar.com/uk",
    "glamourmagazine.co.uk",
    "marieclaire.co.uk",
    "stylist.co.uk",
    
    # ==== 🇪🇸 ESPAGNE ====
    "vogue.es",
    "elle.es",
    "harpersbazaar.com/es",
    
    # ==== 🇩🇪 ALLEMAGNE ====
    "vogue.de",
    "elle.de",
    "glamour.de",
    
    # ==== 🇨🇦 CANADA ====
    "fashionmagazine.com",
    "thekit.ca",
    "cbc.ca/life",
    "salonmagazine.ca",
    "beautycouncil.ca",
    
    # ==== 🌏 ASIE ====
    "vogue.co.jp",
    "elle.co.kr",
    "harpersbazaar.com.hk",
    
    # ==== V4 🇪🇺 MARQUES EXTENSIONS EUROPÉENNES ====
    "greatlengths.com",
    "greatlengthsusa.com",
    "hairdreams.com",
    "balmainhair.com",
    "goldfeverhair.com",
    "beautyworksonline.com",
    "racooninternational.com",
    "she-hair.com",
    "eurosocap.com",
    "cinderellahair.com",
    
    # ==== V4 🇦🇺 AUSTRALIE - MARQUES EXTENSIONS ====
    "zalahairextensions.com.au",
    "showponyhair.com",
    "amazinghair.com.au",
    "bohyme.com",
    "hairlocs.com.au",
    "hotheadshairextensions.com.au",
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
# SUJETS EN COOLDOWN - ÉVITER TEMPORAIREMENT
# Ces sujets ont été répétés trop souvent récemment
# =============================================
TEMPORARY_COOLDOWN_KEYWORDS = [
    # 🚫 Sujets sur-utilisés à éviter pendant 7 jours
    "bob haircut", "bob cut", "coupe bob", "coupes bob",
    "lob haircut", "lob hairstyle",
    "micro bang", "micro bangs",
    "refinery29",  # Source qui génère trop de doublons
    "12 coupes",   # Article spécifique répété
]

# =============================================
# EXCLUSIONS PERMANENTES
# Ces termes indiquent du contenu non pertinent
# =============================================
EXCLUDE_KEYWORDS = [
    # Contenu non pertinent
    "man", "men", "homme", "masculin",
    "barbe", "beard", "mustache",
    "children", "enfant", "kids", "bébé",
    "pet", "dog", "cat", "animal",
    "politics", "politique", "election",
    "sport", "football", "basketball",
    "cryptocurrency", "bitcoin",
    # Marques concurrentes
    "great lengths", "balmain hair",
    # Sujets médicaux
    "cancer", "chemotherapy", "alopecia medical",
]

# =============================================
# MOTS-CLÉS OBLIGATOIRES - HIÉRARCHIE DE PRIORITÉ
# =============================================

# PRIORITÉ 1: EXTENSIONS CAPILLAIRES (Score +10)
EXTENSION_KEYWORDS_HIGH_PRIORITY = [
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

# PRIORITÉ 2: ENTRETIEN CHEVEUX (Score +7)
HAIR_CARE_KEYWORDS = [
    "hair care", "hair maintenance", "entretien cheveux",
    "shampoo", "conditioner", "masque cheveux", "hair mask",
    "hair oil", "huile cheveux", "treatment", "traitement",
    "healthy hair", "cheveux sains", "shiny hair", "cheveux brillants",
    "deep conditioning", "hydration cheveux",
    "protect hair", "protéger cheveux", "heat protection",
    "hair growth", "pousse cheveux", "scalp care", "soin cuir chevelu",
    "hair breakage", "casse cheveux", "split ends", "pointes fourchues",
]

# PRIORITÉ 3: LOOK FÉMININ & MODE (Score +5)
FASHION_LOOK_KEYWORDS = [
    "fashion look", "look féminin", "women style", "style femme",
    "elegant", "élégant", "chic", "sophisticated", "glamour",
    "Milan Fashion Week", "Paris Fashion Week", "London Fashion Week",
    "red carpet", "tapis rouge", "celebrity style", "celebrity look",
    "French girl", "Italian style", "quiet luxury", "luxe discret",
    "office style", "professional look", "evening look", "look soirée",
    "bridal", "mariage", "wedding", "gala",
]

# PRIORITÉ 4: TENDANCES COIFFURE (Score +3) - LIMITÉ pour éviter bob-spam
HAIRSTYLE_TRENDS_KEYWORDS = [
    "hair trends", "tendances coiffure", "tendance cheveux",
    "hairstyle", "coiffure femme", "coupe femme",
    "hair volume", "volume cheveux",
    "long hair", "cheveux longs", "longueurs",
    "fringe", "bangs", "frange", "curtain bangs",
    "glossy hair", "balayage", "highlights", "mèches",
    "layers", "dégradé", "layered cut",
]

# Combinaison pour backward compatibility
REQUIRED_EXTENSION_KEYWORDS = (
    EXTENSION_KEYWORDS_HIGH_PRIORITY + 
    HAIR_CARE_KEYWORDS + 
    FASHION_LOOK_KEYWORDS + 
    HAIRSTYLE_TRENDS_KEYWORDS
)

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
