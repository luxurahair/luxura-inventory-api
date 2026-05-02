"""
🏖️ LUXURA IMAGE PROMPT RULES v4 - QUEBEC EDITION
==================================================
Règles centralisées pour toutes les générations d'images Luxura.
Appliquées à tous les crons et services.

V4 NOUVEAUTÉS:
- Détection automatique des SAISONS (pas de neige au printemps!)
- Lieux QUÉBEC/CANADA prioritaires
- Styles plus SENSUELS et SEXY
- Diversité ethnique et artistique
- Photos éditoriales variées

STYLE: Glamour, sensuel, élégant, SEXY avec focus sur cheveux extensions longs volumineux.
"""

import random
from datetime import datetime


# ============================================
# 🗓️ DÉTECTION AUTOMATIQUE DES SAISONS
# ============================================

def get_current_season() -> str:
    """
    Détecte la saison actuelle au Québec.
    Retourne: 'winter', 'spring', 'summer', 'fall'
    """
    month = datetime.now().month
    
    # Saisons Québec (climat nordique)
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:  # 9, 10, 11
        return "fall"


def get_seasonal_context() -> dict:
    """
    Retourne le contexte saisonnier complet pour les prompts.
    """
    season = get_current_season()
    month = datetime.now().month
    
    contexts = {
        "winter": {
            "season": "winter",
            "weather": ["snowy", "cold elegant", "cozy chic", "frosty glamour"],
            "clothing_style": ["luxurious fur coat", "elegant cashmere", "chic wool ensemble", "designer winter coat with fur trim"],
            "locations_priority": ["ski_resort", "city_winter", "cozy_luxury"],
            "mood": ["warm intimate", "cozy glamour", "winter wonderland elegance"],
            "avoid": ["beach", "swimsuit", "summer dress", "tropical"],
            "holidays": ["Christmas glamour", "New Year's Eve", "Valentine's romantic"] if month in [12, 1, 2] else [],
        },
        "spring": {
            "season": "spring",
            "weather": ["blooming", "fresh", "renewal", "soft light"],
            "clothing_style": ["light elegant dress", "chic trench coat", "floral designer dress", "pastel silk blouse"],
            "locations_priority": ["city_spring", "garden", "nature_spring"],
            "mood": ["fresh romantic", "renewal energy", "blooming beauty"],
            "avoid": ["heavy winter coat", "snow", "Christmas"],
            "holidays": ["Easter elegance", "Mother's Day"] if month in [4, 5] else [],
        },
        "summer": {
            "season": "summer",
            "weather": ["sunny", "warm", "golden", "tropical heat"],
            "clothing_style": ["elegant bikini", "flowing summer dress", "chic sundress", "designer swimwear", "silk maxi dress"],
            "locations_priority": ["beach", "yacht", "rooftop", "quebec_summer"],
            "mood": ["hot sensual", "beach glamour", "summer paradise", "sexy vacation"],
            "avoid": ["winter coat", "snow", "Christmas", "heavy clothing"],
            "holidays": ["Festival season", "Summer vacation", "Saint-Jean-Baptiste"] if month in [6, 7] else [],
        },
        "fall": {
            "season": "fall",
            "weather": ["golden leaves", "crisp air", "warm tones", "cozy autumn"],
            "clothing_style": ["elegant sweater dress", "chic leather jacket", "designer fall outfit", "cashmere wrap"],
            "locations_priority": ["vineyard", "city_fall", "nature_fall", "quebec_fall"],
            "mood": ["cozy sensual", "autumn romance", "harvest glamour"],
            "avoid": ["swimsuit", "beach", "heavy snow"],
            "holidays": ["Thanksgiving glamour", "Halloween chic"] if month in [10, 11] else [],
        }
    }
    
    return contexts[season]


# ============================================
# RÈGLES DE BASE LUXURA - V4 SEXY
# ============================================

LUXURA_IMAGE_RULES = """
RÈGLES CRITIQUES - STYLE LUXURA SEXY GLAMOUR:
1. Commence TOUJOURS par "Real photograph of a sensual glamorous woman"
2. ANGLE: 3/4 back view OU semi-profile OU looking over shoulder - pour montrer les cheveux ET silhouette
3. CHEVEUX LUXURA: Long (past shoulders to mid-back), voluminous, flowing, silky hair extensions
4. Les cheveux doivent être LE FOCUS principal - en mouvement naturel
5. LUMIÈRE: Golden hour, sunset, natural sunlight highlighting the hair shine
6. AMBIANCE: Glamorous, SEDUCTIVE, SENSUAL, feminine, aspirational but classy
7. SENSUELLE ET SEXY mais élégante (jamais vulgaire, toujours classe)
8. NO text, NO watermarks, NO logos in image
9. Peau lisse et bronzée, corps féminin mis en valeur de façon élégante
"""


# ============================================
# 🍁 LIEUX QUÉBEC/CANADA - PRIORITÉ HAUTE
# ============================================

QUEBEC_CANADA_LOCATIONS = {
    "summer": [
        "Old Montreal cobblestone terrace at sunset",
        "Mont-Tremblant luxury resort by the lake",
        "Charlevoix boutique hotel terrace overlooking St. Lawrence",
        "Quebec City Château Frontenac terrace",
        "Laurentian Mountains luxury spa deck",
        "Toronto Yorkville rooftop at golden hour",
        "Vancouver waterfront luxury restaurant",
        "Muskoka lakeside luxury cottage dock",
        "Prince Edward County vineyard sunset",
        "Niagara-on-the-Lake wine estate",
        "Whistler summer resort terrace",
        "Halifax waterfront at sunset",
        "Îles-de-la-Madeleine pristine beach",
        "Tadoussac whale watching lodge terrace",
    ],
    "fall": [
        "Mont-Tremblant fall foliage luxury resort",
        "Charlevoix autumn colors vineyard",
        "Quebec City Plains of Abraham golden leaves",
        "Laurentian Mountains autumn panorama",
        "Old Montreal fall terrace with maple leaves",
        "Niagara wine region harvest season",
        "Ottawa Parliament Hill autumn backdrop",
        "Prince Edward County fall harvest",
        "Eastern Townships autumn vineyard",
        "Muskoka fall colors lakeside",
    ],
    "winter": [
        "Mont-Tremblant ski chalet terrace",
        "Quebec City winter wonderland Château Frontenac",
        "Laurentian spa resort snowy evening",
        "Whistler luxury ski lodge fireplace",
        "Charlevoix winter resort elegant lobby",
        "Old Montreal Christmas lights terrace",
        "Banff Springs Hotel winter elegance",
        "Lake Louise frozen lake backdrop",
    ],
    "spring": [
        "Montreal botanical garden spring bloom",
        "Quebec City spring terrace flowers",
        "Niagara Falls spring mist rainbow",
        "Ottawa tulip festival backdrop",
        "Vancouver cherry blossom garden",
        "Toronto High Park spring bloom",
    ],
}


# ============================================
# 🌍 DÉCORS LUXUEUX INTERNATIONAUX PAR SAISON
# ============================================

LUXURY_LOCATIONS = {
    "beach": {
        "summer": [
            "Amalfi Coast Italy beach club",
            "Santorini Greece white sand beach",
            "Maldives overwater bungalow",
            "Monaco Beach Club Riviera",
            "French Riviera St-Tropez exclusive beach",
            "Positano Italy colorful coastline",
            "Mykonos Greece beach bar",
            "Bora Bora crystal lagoon",
            "Ibiza sunset beach club",
            "Côte d'Azur glamorous bay",
            "Sardinia Costa Smeralda",
            "Seychelles pristine white sand",
            "Tulum Mexico bohemian luxury beach",
            "Bali Seminyak beach club",
            "Miami South Beach art deco",
            "Capri Italy marina beach",
        ],
        "spring": [
            "Cannes Film Festival beach",
            "Barcelona Barceloneta sunny day",
            "Lisbon Cascais beach",
            "Greek Islands early season",
        ],
        "fall": [
            "Maldives autumn escape",
            "Bali fall retreat",
            "Caribbean late season",
        ],
        "winter": [
            "Maldives winter sun",
            "Caribbean winter escape",
            "Dubai beach winter warmth",
        ],
    },
    "yacht": {
        "all_seasons": [
            "luxury superyacht deck Mediterranean sunset",
            "Monaco harbor yacht party",
            "Amalfi Coast yacht cruise",
            "Dubai Marina superyacht",
            "Caribbean yacht charter",
            "French Riviera yacht sunset",
            "Mykonos yacht party sunset",
            "Ibiza yacht club sunset",
        ]
    },
    "city": {
        "all_seasons": [
            "Paris balcony Eiffel Tower view",
            "Milan fashion district Via Montenapoleone",
            "Monaco harbor promenade",
            "Rome Spanish Steps area",
            "New York Manhattan penthouse rooftop",
            "London Mayfair elegant townhouse",
            "Dubai Marina skyline penthouse",
            "Barcelona Gothic Quarter",
            "Vienna Opera House steps",
            "Florence Ponte Vecchio sunset",
            "Los Angeles Beverly Hills mansion",
            "Singapore Marina Bay Sands infinity pool",
            "Tokyo Ginza luxury district",
            "Sydney Harbour Bridge penthouse view",
        ]
    },
    "nature": {
        "spring": [
            "Provence lavender fields France",
            "Japanese cherry blossom garden",
            "English countryside manor spring",
            "Tulip fields Netherlands",
        ],
        "summer": [
            "Tuscan vineyard golden hour",
            "Napa Valley wine estate summer",
            "Greek olive grove sunset",
            "Mediterranean terraced garden",
            "California palm tree paradise",
        ],
        "fall": [
            "Tuscan vineyard harvest season",
            "Napa Valley autumn colors",
            "English countryside manor fall",
            "Swiss Alps autumn panorama",
        ],
        "winter": [
            "Swiss Alps luxury chalet",
            "Aspen ski resort terrace",
            "Austrian Alps cozy lodge",
        ],
    },
    "evening": {
        "all_seasons": [
            "Monte Carlo Casino entrance",
            "Paris Opera Garnier steps",
            "Milan La Scala opening night",
            "Cannes Film Festival red carpet",
            "New York Met Gala entrance",
            "London Royal Albert Hall",
            "Dubai Burj Al Arab terrace",
            "Monaco Grand Prix gala",
            "Venice Film Festival premiere",
            "Art Basel Miami VIP party",
        ]
    },
}


# ============================================
# 👗 TENUES GLAMOUR SEXY PAR SAISON
# ============================================

GLAMOROUS_OUTFITS = {
    "beach_summer": [
        "elegant high-cut one-piece swimsuit showing curves",
        "chic designer bikini with flowing sheer sarong",
        "barely-there string bikini with gold accents",
        "sexy cutout one-piece revealing toned body",
        "designer white bikini with see-through cover-up",
        "Brazilian cut bikini flattering silhouette",
    ],
    "evening": [
        "flowing red silk backless evening gown",
        "elegant black plunging neckline cocktail dress",
        "champagne silk body-hugging maxi dress",
        "designer sequined gown with thigh-high slit",
        "stunning red carpet backless dress",
        "form-fitting velvet gown showing curves",
    ],
    "daytime_summer": [
        "chic white mini sundress",
        "elegant silk slip dress",
        "sophisticated short summer dress showing legs",
        "designer flowy maxi dress with deep neckline",
        "sexy off-shoulder top with flowing pants",
    ],
    "daytime_spring": [
        "elegant trench coat over silk dress",
        "chic pastel designer dress",
        "sophisticated floral midi dress",
        "light cashmere sweater dress",
    ],
    "daytime_fall": [
        "elegant sweater dress hugging curves",
        "chic leather pants with cashmere top",
        "sophisticated wool coat over silk blouse",
        "designer fall dress with boots",
    ],
    "winter_outdoor": [
        "luxurious fur coat showing elegant figure",
        "designer cashmere coat with sexy boots",
        "chic ski outfit showing silhouette",
        "elegant wool coat with fur trim",
    ],
    "winter_indoor": [
        "cozy cashmere sweater dress",
        "elegant silk robe by fireplace",
        "chic loungewear showing figure",
    ],
}


# ============================================
# 💇 DESCRIPTIONS CHEVEUX LUXURA - DIVERSIFIÉS
# ============================================

LUXURA_HAIR_DESCRIPTIONS = [
    # BLONDES
    "spectacular platinum blonde flowing mane with incredible volume and movement",
    "sun-kissed honey blonde waves cascading past shoulders",
    "cool ash blonde hair with editorial-worthy volume and shine",
    "golden highlighted extensions catching light beautifully",
    "creamy blonde balayage with beachy textured waves",
    
    # BRUNETTES
    "rich chocolate brown cascading waves with stunning natural shine",
    "deep espresso brown voluminous curls with Hollywood glamour",
    "glossy chestnut hair extensions flowing dramatically",
    "dimensional brunette balayage with sophisticated volume",
    "warm caramel highlights through thick brown waves",
    
    # AUBURN/RED
    "fiery auburn hair extensions flowing dramatically in the breeze",
    "warm copper tones in thick voluminous sensual waves",
    "rich burgundy tinted hair with luxurious body",
    "strawberry blonde waves with romantic soft curls",
    
    # BLACK
    "sleek jet black hair with mirror-like shine and dramatic length",
    "raven black voluminous waves with blue undertones",
    "silky black Asian-inspired straight extensions",
    
    # OMBRE/SPECIAL
    "honey blonde ombre fading from dark roots beautifully",
    "mermaid-length flowing hair with romantic soft waves",
    "natural brunette extensions with effortless glamour and body",
    "dimensional balayage hair with sophisticated volume and texture",
]


# ============================================
# 🌍 DIVERSITÉ BEAUTÉ
# ============================================

BEAUTY_DIVERSITY = {
    "ethnicities": [
        "Caucasian",
        "Mediterranean olive skin",
        "Latina sun-kissed complexion",
        "Light-skinned Black woman",
        "Asian with flawless porcelain skin",
        "Middle Eastern exotic beauty",
        "Mixed race stunning features",
    ],
    "ages": [
        "young woman in her 20s",
        "sophisticated woman in her early 30s",
        "elegant woman in her late 30s",
        "glamorous woman in her 40s",
    ],
    "body_types": [
        "slim toned figure",
        "curvy sensual silhouette",
        "athletic elegant body",
        "naturally feminine curves",
    ],
}


# ============================================
# 📸 STYLES PHOTO ARTISTIQUES
# ============================================

PHOTO_STYLES = {
    "editorial": [
        "Vogue magazine editorial style photography",
        "Harper's Bazaar high fashion aesthetic",
        "Elle magazine glamour shoot style",
        "Italian fashion editorial la dolce vita",
    ],
    "cinematic": [
        "cinematic film still aesthetic",
        "Hollywood golden age glamour lighting",
        "French cinema nouvelle vague style",
    ],
    "lifestyle": [
        "aspirational luxury lifestyle photography",
        "candid glamorous moment captured",
        "natural elegant lifestyle shot",
    ],
    "portrait": [
        "studio glamour portrait lighting",
        "natural light beauty portrait",
        "dramatic chiaroscuro portrait style",
    ],
}


# ============================================
# 💃 POSES SENSUELLES
# ============================================

SENSUAL_POSES = [
    "running fingers seductively through her hair",
    "hair caught in a gentle breeze revealing neck",
    "tossing hair back with confident sexy movement",
    "wind-swept hair moment eyes half-closed",
    "touching her hair softly biting lip",
    "hair dramatically blowing looking over shoulder",
    "arching back showing curves hair flowing down",
    "hand on hip hair cascading sensually",
    "turning head with smoldering gaze",
    "walking away hair bouncing showing figure",
]


# ============================================
# 😏 EXPRESSIONS SENSUELLES
# ============================================

SENSUAL_EXPRESSIONS = [
    "mysterious confident smirk",
    "sultry bedroom eyes",
    "playful seductive look",
    "dreamy sensual gaze",
    "confident radiant smile showing teeth",
    "intense passionate expression",
    "natural candid sexy moment",
    "joyful carefree laughing",
    "smoldering come-hither look",
    "innocent yet knowing expression",
]


# ============================================
# 📐 ANGLES PHOTO SENSUELS
# ============================================

SENSUAL_ANGLES = [
    "from 3/4 back angle showing curves and hair",
    "in semi-profile highlighting silhouette",
    "looking over her bare shoulder seductively",
    "turning her head with hair in dramatic motion",
    "from behind showing hair length and figure",
    "side profile with hair flowing down back",
    "slightly from below highlighting jawline and hair",
]


# ============================================
# 🎯 GÉNÉRATEUR DE PROMPTS V4
# ============================================

def generate_luxura_image_prompt(
    context: str = "general",
    force_season: str = None,
    location_preference: str = None,  # "quebec", "international", "mixed"
    sexy_level: str = "elegant_sexy",  # "elegant", "elegant_sexy", "sensual"
) -> str:
    """
    Génère un prompt d'image style Luxura V4.
    
    Args:
        context: Type de contenu (product, educational, weekend, magazine, etc.)
        force_season: Force une saison spécifique (sinon auto-détection)
        location_preference: "quebec" pour prioriser Québec/Canada
        sexy_level: Niveau de sensualité
    
    Returns:
        Prompt complet pour génération d'image
    """
    
    # Auto-détection de la saison
    season = force_season or get_current_season()
    seasonal_ctx = get_seasonal_context()
    
    # Déterminer le type de lieu
    if location_preference == "quebec" or random.random() < 0.6:  # 60% Québec
        # Prioriser Québec/Canada
        quebec_locs = QUEBEC_CANADA_LOCATIONS.get(season, QUEBEC_CANADA_LOCATIONS["summer"])
        location = random.choice(quebec_locs)
    else:
        # International selon saison
        location_types = ["beach", "yacht", "city", "nature", "evening"]
        loc_type = random.choice(location_types)
        
        loc_data = LUXURY_LOCATIONS.get(loc_type, {})
        seasonal_locs = loc_data.get(season, loc_data.get("all_seasons", []))
        
        if not seasonal_locs:
            # Fallback
            seasonal_locs = loc_data.get("all_seasons", ["luxury resort terrace"])
        
        location = random.choice(seasonal_locs)
    
    # Sélectionner la tenue appropriée à la saison
    if season == "summer":
        if "beach" in location.lower() or "yacht" in location.lower():
            outfit = random.choice(GLAMOROUS_OUTFITS["beach_summer"])
        else:
            outfit = random.choice(GLAMOROUS_OUTFITS["daytime_summer"])
    elif season == "winter":
        if any(x in location.lower() for x in ["chalet", "ski", "outdoor", "snow"]):
            outfit = random.choice(GLAMOROUS_OUTFITS["winter_outdoor"])
        else:
            outfit = random.choice(GLAMOROUS_OUTFITS.get("winter_indoor", GLAMOROUS_OUTFITS["evening"]))
    elif season == "spring":
        outfit = random.choice(GLAMOROUS_OUTFITS["daytime_spring"])
    else:  # fall
        outfit = random.choice(GLAMOROUS_OUTFITS["daytime_fall"])
    
    # Contexte soirée override
    if "gala" in location.lower() or "casino" in location.lower() or "opera" in location.lower():
        outfit = random.choice(GLAMOROUS_OUTFITS["evening"])
    
    # Sélectionner description cheveux
    hair = random.choice(LUXURA_HAIR_DESCRIPTIONS)
    
    # Sélectionner diversité (parfois)
    if random.random() < 0.3:  # 30% diversité explicite
        ethnicity = random.choice(BEAUTY_DIVERSITY["ethnicities"])
        body = random.choice(BEAUTY_DIVERSITY["body_types"])
        diversity = f", {ethnicity} with {body}"
    else:
        diversity = ""
    
    # Sélectionner style photo
    photo_style = random.choice(PHOTO_STYLES[random.choice(list(PHOTO_STYLES.keys()))])
    
    # Sélectionner pose et expression selon niveau sexy
    if sexy_level == "sensual":
        pose = random.choice(SENSUAL_POSES)
        expression = random.choice(SENSUAL_EXPRESSIONS)
        mood = "seductive sensual"
    elif sexy_level == "elegant_sexy":
        pose = random.choice(SENSUAL_POSES[:6])  # Poses plus sages
        expression = random.choice(SENSUAL_EXPRESSIONS[:6])
        mood = "elegant yet seductive"
    else:
        pose = random.choice(["hair flowing naturally", "elegant confident stance"])
        expression = random.choice(["confident smile", "serene elegant expression"])
        mood = "sophisticated elegant"
    
    # Sélectionner angle
    angle = random.choice(SENSUAL_ANGLES)
    
    # Construire le prompt V4
    prompt = f"Real photograph of a sensual glamorous woman{diversity} {angle} at {location}, {pose}, {hair}, wearing {outfit}, {expression}, {seasonal_ctx['weather'][0] if seasonal_ctx['weather'] else 'golden hour'} natural lighting, {mood} mood, {photo_style}, aspirational luxury lifestyle, no text, no watermarks"
    
    return prompt


def get_prompt_for_content_type(content_type: str) -> str:
    """
    Retourne un prompt adapté au type de contenu V4.
    """
    season = get_current_season()
    
    content_configs = {
        "product": {
            "location_preference": "mixed",
            "sexy_level": "elegant_sexy",
        },
        "educational": {
            "location_preference": "quebec",
            "sexy_level": "elegant",
        },
        "weekend": {
            "location_preference": "mixed",
            "sexy_level": "sensual",
        },
        "testimonial": {
            "location_preference": "quebec",
            "sexy_level": "elegant_sexy",
        },
        "b2b": {
            "location_preference": "quebec",
            "sexy_level": "elegant",
        },
        "magazine": {
            "location_preference": "international",
            "sexy_level": "sensual",
        },
    }
    
    config = content_configs.get(content_type, content_configs["product"])
    
    return generate_luxura_image_prompt(
        context=content_type,
        location_preference=config["location_preference"],
        sexy_level=config["sexy_level"]
    )


# ============================================
# PROMPTS CONTEXTUELS V4
# ============================================

def get_contextual_prompt(title: str, content: str = "") -> str:
    """
    Génère un prompt basé sur le titre et contenu de l'article V4.
    Avec détection de saison automatique.
    """
    full_text = f"{title} {content}".lower()
    season = get_current_season()
    seasonal_ctx = get_seasonal_context()
    
    # Contrainte STRICTE pour la longueur des cheveux
    HAIR_CONSTRAINT = "CRITICAL: Hair ends at MID-BACK level only, NEVER below waist."
    
    # Choisir les lieux Québec selon saison
    quebec_locs = QUEBEC_CANADA_LOCATIONS.get(season, QUEBEC_CANADA_LOCATIONS["summer"])
    quebec_loc = random.choice(quebec_locs)
    
    # Déterminer le contexte basé sur les mots-clés
    if any(w in full_text for w in ["salon", "coiffeuse", "styliste", "professionnel", "partenaire"]):
        base = f"Real photograph of a glamorous hairstylist in an ultra-luxury Montreal salon with crystal chandeliers, sensual {random.choice(LUXURA_HAIR_DESCRIPTIONS)}, {random.choice(SENSUAL_EXPRESSIONS)}, professional yet seductive atmosphere"
    
    elif any(w in full_text for w in ["mariage", "wedding", "mariée", "bride"]):
        venue = quebec_loc if "château" in quebec_loc.lower() else "Château Frontenac Quebec City"
        base = f"Real photograph of glamorous bride at {venue}, stunning voluminous bridal hair extensions, {random.choice(GLAMOROUS_OUTFITS['evening'])}, romantic golden hour"
    
    elif any(w in full_text for w in ["plage", "beach", "été", "summer", "yacht"]) and season == "summer":
        base = f"Real photograph of sensual woman on {quebec_loc}, {random.choice(LUXURA_HAIR_DESCRIPTIONS)} blowing in breeze, {random.choice(GLAMOROUS_OUTFITS['beach_summer'])}, {random.choice(SENSUAL_POSES)}, summer golden hour"
    
    elif any(w in full_text for w in ["soirée", "gala", "événement", "party"]):
        base = f"Real photograph of glamorous woman at {random.choice(LUXURY_LOCATIONS['evening']['all_seasons'])}, {random.choice(LUXURA_HAIR_DESCRIPTIONS)}, {random.choice(GLAMOROUS_OUTFITS['evening'])}, {random.choice(SENSUAL_EXPRESSIONS)}"
    
    elif any(w in full_text for w in ["hiver", "winter", "neige", "ski"]) and season == "winter":
        winter_loc = random.choice(QUEBEC_CANADA_LOCATIONS["winter"])
        base = f"Real photograph of elegant woman at {winter_loc}, {random.choice(LUXURA_HAIR_DESCRIPTIONS)}, {random.choice(GLAMOROUS_OUTFITS['winter_outdoor'])}, cozy glamour winter mood"
    
    elif any(w in full_text for w in ["automne", "fall", "feuilles"]) and season == "fall":
        fall_loc = random.choice(QUEBEC_CANADA_LOCATIONS["fall"])
        base = f"Real photograph of sensual woman at {fall_loc}, {random.choice(LUXURA_HAIR_DESCRIPTIONS)}, {random.choice(GLAMOROUS_OUTFITS['daytime_fall'])}, autumn golden light"
    
    else:
        # Prompt général selon saison actuelle
        base = f"Real photograph of sensual glamorous woman {random.choice(SENSUAL_ANGLES)} at {quebec_loc}, {random.choice(SENSUAL_POSES)}, {random.choice(LUXURA_HAIR_DESCRIPTIONS)}, {random.choice(seasonal_ctx['clothing_style'])}, {random.choice(SENSUAL_EXPRESSIONS)}, {random.choice(seasonal_ctx['mood'])} atmosphere"
    
    return f"{base}. {HAIR_CONSTRAINT} No text, no watermarks."


# ============================================
# TEST DE GÉNÉRATION
# ============================================

if __name__ == "__main__":
    print(f"Saison actuelle: {get_current_season()}")
    print("\n--- PROMPTS EXEMPLES ---\n")
    
    for content_type in ["product", "weekend", "magazine", "educational"]:
        print(f"\n[{content_type.upper()}]")
        print(get_prompt_for_content_type(content_type))
        print("-" * 50)
