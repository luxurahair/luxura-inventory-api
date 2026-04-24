"""
🏖️ LUXURA IMAGE PROMPT RULES v2
================================
Règles centralisées pour toutes les générations d'images Luxura.
Appliquées à tous les crons et services.

STYLE: Glamour, sensuel, élégant avec focus sur cheveux extensions longs volumineux.
"""

import random


# ============================================
# RÈGLES DE BASE LUXURA
# ============================================

LUXURA_IMAGE_RULES = """
RÈGLES CRITIQUES - STYLE LUXURA EXTENSIONS:
1. Commence TOUJOURS par "Real photograph of a glamorous woman"
2. ANGLE: 3/4 back view OU semi-profile OU looking over shoulder - pour montrer les cheveux
3. CHEVEUX LUXURA: Long (past shoulders to mid-back), voluminous, flowing, silky hair extensions
4. Les cheveux doivent être LE FOCUS principal - en mouvement naturel
5. LUMIÈRE: Golden hour, sunset, natural sunlight highlighting the hair shine
6. AMBIANCE: Glamorous, seductive, feminine, aspirational but natural
7. Sensuelle mais élégante (jamais vulgaire)
8. NO text, NO watermarks, NO logos in image
"""


# ============================================
# DÉCORS LUXUEUX VARIÉS
# ============================================

LUXURY_LOCATIONS = {
    "beach": [
        "Amalfi Coast Italy beach",
        "Santorini Greece white sand beach", 
        "Maldives tropical beach",
        "Monaco beach club",
        "French Riviera beach",
        "Positano Italy coastline",
        "Mykonos Greece beach",
        "Bora Bora overwater",
    ],
    "sunset": [
        "luxury yacht deck at sunset",
        "rooftop bar with city skyline view",
        "infinity pool edge overlooking ocean",
        "private terrace sunset view",
        "beachfront restaurant at golden hour",
        "Monaco harbor at dusk",
    ],
    "city": [
        "Paris balcony with Eiffel Tower view",
        "Milan fashion district street",
        "Monaco harbor promenade",
        "Rome Spanish Steps area",
        "New York Manhattan rooftop",
        "London Mayfair elegant street",
        "Dubai Marina skyline",
    ],
    "nature": [
        "Lavender fields Provence France",
        "Tuscan vineyard golden hour",
        "Tropical garden luxury resort",
        "Cherry blossom garden Japan",
        "Amalfi Coast lemon grove",
        "Swiss Alps luxury chalet terrace",
    ],
    "evening": [
        "grand hotel terrace evening",
        "luxury restaurant terrace",
        "gala event red carpet entrance",
        "opera house steps",
        "champagne bar rooftop",
        "casino Monte Carlo entrance",
    ]
}


# ============================================
# TENUES GLAMOUR
# ============================================

GLAMOROUS_OUTFITS = {
    "beach": [
        "elegant white one-piece swimsuit",
        "chic bikini with flowing sarong",
        "luxury resort wear cover-up",
        "designer beach dress",
        "silk caftan",
    ],
    "evening": [
        "flowing red silk evening gown",
        "elegant black cocktail dress",
        "champagne silk maxi dress",
        "designer backless dress",
        "sequined glamorous gown",
    ],
    "daytime": [
        "chic white sundress",
        "elegant linen outfit",
        "sophisticated casual cream ensemble",
        "designer summer dress",
        "silk blouse and wide pants",
    ],
    "luxury": [
        "haute couture inspired dress",
        "red carpet style gown",
        "designer elegant outfit",
        "exclusive fashion piece",
    ]
}


# ============================================
# DESCRIPTIONS CHEVEUX LUXURA
# ============================================

LUXURA_HAIR_DESCRIPTIONS = [
    "incredibly voluminous thick hair extensions with dramatic body and movement",
    "luxurious full-bodied bouncy hair with stunning volume cascading naturally",
    "gorgeous thick voluminous hair extensions with glamorous waves and body",
    "dramatic Hollywood-style voluminous hair with incredible fullness and shine",
    "stunning thick bouncy hair extensions with red carpet worthy volume",
    "voluminous glamorous hair with incredible body and natural movement",
    "full thick luxurious hair extensions with dramatic volume and bounce",
    "breathtakingly voluminous silky hair with show-stopping body and shine",
]


# ============================================
# ANGLES PHOTO
# ============================================

PHOTO_ANGLES = [
    "from 3/4 back angle",
    "in semi-profile",
    "looking over her shoulder",
    "turning her head with hair in motion",
    "from behind showing hair length",
    "side profile with hair flowing",
]


# ============================================
# GÉNÉRATEUR DE PROMPTS
# ============================================

def generate_luxura_image_prompt(
    context: str = "general",
    location_type: str = None,
    outfit_type: str = None,
    specific_location: str = None
) -> str:
    """
    Génère un prompt d'image style Luxura.
    
    Args:
        context: Type de contenu (product, educational, weekend, magazine, etc.)
        location_type: Type de lieu (beach, sunset, city, nature, evening)
        outfit_type: Type de tenue (beach, evening, daytime, luxury)
        specific_location: Lieu spécifique optionnel
    
    Returns:
        Prompt complet pour génération d'image
    """
    
    # Sélectionner le type de lieu si non spécifié
    if location_type is None:
        location_type = random.choice(list(LUXURY_LOCATIONS.keys()))
    
    # Sélectionner le lieu
    if specific_location:
        location = specific_location
    else:
        location = random.choice(LUXURY_LOCATIONS.get(location_type, LUXURY_LOCATIONS["city"]))
    
    # Sélectionner la tenue appropriée
    if outfit_type is None:
        outfit_type = location_type if location_type in GLAMOROUS_OUTFITS else "daytime"
    outfit = random.choice(GLAMOROUS_OUTFITS.get(outfit_type, GLAMOROUS_OUTFITS["daytime"]))
    
    # Sélectionner description cheveux
    hair = random.choice(LUXURA_HAIR_DESCRIPTIONS)
    
    # Sélectionner angle
    angle = random.choice(PHOTO_ANGLES)
    
    # Construire le prompt
    prompt = f"Real photograph of a glamorous woman {angle} at {location}, {hair}, wearing {outfit}, golden hour natural lighting, seductive elegant mood, aspirational luxury lifestyle, no text, no watermarks"
    
    return prompt


def get_prompt_for_content_type(content_type: str) -> str:
    """
    Retourne un prompt adapté au type de contenu.
    
    Args:
        content_type: product, educational, weekend, testimonial, b2b, magazine
    
    Returns:
        Prompt d'image approprié
    """
    
    content_configs = {
        "product": {
            "location_types": ["city", "evening", "sunset"],
            "outfit_types": ["luxury", "evening", "daytime"],
        },
        "educational": {
            "location_types": ["city", "nature", "sunset"],
            "outfit_types": ["daytime", "luxury"],
        },
        "weekend": {
            "location_types": ["beach", "sunset", "nature"],
            "outfit_types": ["beach", "daytime"],
        },
        "testimonial": {
            "location_types": ["city", "nature", "evening"],
            "outfit_types": ["daytime", "evening"],
        },
        "b2b": {
            "location_types": ["city", "evening"],
            "outfit_types": ["luxury", "daytime"],
        },
        "magazine": {
            "location_types": ["beach", "evening", "city", "sunset"],
            "outfit_types": ["luxury", "evening", "beach"],
        },
    }
    
    config = content_configs.get(content_type, content_configs["product"])
    
    location_type = random.choice(config["location_types"])
    outfit_type = random.choice(config["outfit_types"])
    
    return generate_luxura_image_prompt(
        context=content_type,
        location_type=location_type,
        outfit_type=outfit_type
    )


# ============================================
# PROMPTS PRÉ-DÉFINIS PAR TYPE
# ============================================

PRESET_PROMPTS = {
    "product": [
        "Real photograph of glamorous woman from 3/4 back on Monaco yacht deck, long voluminous silky hair extensions flowing in Mediterranean breeze, elegant white designer dress, golden sunset light, luxury lifestyle",
        "Real photo of sensual woman looking over shoulder in Milan fashion district, luxurious thick hair cascading down her back, chic cream outfit, warm natural light, Italian glamour",
        "Real photograph of elegant woman on Paris hotel balcony with Eiffel Tower, long gorgeous hair catching golden hour light, black silk dress, romantic Parisian mood",
    ],
    "educational": [
        "Real photograph of glamorous woman in semi-profile at Tuscan vineyard, voluminous flowing hair extensions in gentle breeze, elegant linen sundress, golden hour, sophisticated lifestyle",
        "Real photo of elegant woman turning head in London Mayfair, long silky hair in natural movement, designer casual outfit, soft afternoon light, refined beauty",
    ],
    "weekend": [
        "Real photograph of glamorous woman from behind on Amalfi Coast beach, long voluminous hair flowing in sea breeze, elegant white swimsuit, golden sunset, Mediterranean paradise",
        "Real photo of sensual woman looking over shoulder at infinity pool Maldives, luxurious thick hair wet and flowing, chic one-piece swimsuit, tropical sunset glow",
        "Real photograph of elegant woman at Santorini white terrace, gorgeous flowing hair catching sunset light, flowing summer dress, breathtaking ocean view backdrop",
    ],
    "testimonial": [
        "Real photograph of glamorous woman in semi-profile at French cafe terrace, long voluminous silky hair with natural movement, chic Parisian outfit, warm golden light, confident elegant mood",
        "Real photo of radiant woman looking over shoulder in beautiful garden, luxurious flowing hair extensions, elegant sundress, natural soft lighting, happy confident expression",
    ],
    "b2b": [
        "Real photograph of sophisticated woman from 3/4 back at luxury hotel lobby, long voluminous professional hair extensions, elegant business chic outfit, refined lighting, premium salon quality",
        "Real photo of elegant woman in semi-profile at upscale salon setting, gorgeous flowing hair showcasing extensions, designer outfit, professional yet glamorous mood",
    ],
    "magazine": [
        "Real photograph of glamorous woman from 3/4 back at Monaco Grand Prix terrace, long voluminous hair flowing dramatically, stunning red evening gown, golden hour, high fashion editorial",
        "Real photo of sensual woman looking over shoulder on Positano beach, luxurious thick hair cascading in wind, designer bikini with sarong, Italian Riviera sunset, Vogue editorial style",
        "Real photograph of elegant woman at Paris Fashion Week, gorgeous long hair in motion, haute couture dress, sophisticated urban backdrop, magazine cover worthy",
    ],
}


def get_preset_prompt(content_type: str) -> str:
    """Retourne un prompt pré-défini aléatoire pour le type de contenu."""
    prompts = PRESET_PROMPTS.get(content_type, PRESET_PROMPTS["product"])
    return random.choice(prompts)


def get_contextual_prompt(title: str, content: str = "") -> str:
    """
    Génère un prompt basé sur le titre et contenu de l'article.
    
    RÈGLES CRITIQUES CHEVEUX:
    - Maximum mi-dos (entre omoplates et taille)
    - JAMAIS plus long que la taille
    - JAMAIS jusqu'aux hanches, fesses ou genoux
    """
    full_text = f"{title} {content}".lower()
    
    # Contrainte STRICTE pour la longueur des cheveux - RENFORCÉE
    HAIR_CONSTRAINT = "CRITICAL HAIR LENGTH RULE: Hair MUST end at MID-BACK level only, between shoulder blades and waist. Hair must NEVER extend below the waist. Hair must NEVER reach the hips. Hair must NEVER reach the buttocks or knees. Maximum length is bra-strap level. This constraint is absolutely critical and non-negotiable."
    
    # Déterminer le contexte basé sur les mots-clés
    if any(w in full_text for w in ["salon", "coiffeuse", "styliste", "professionnel", "partenaire", "affilié"]):
        base = random.choice([
            "Real photograph of a glamorous hairstylist working on a client's voluminous hair extensions in an ultra-luxury salon with crystal chandeliers. Hair at mid-back length only. Both women beautiful. Soft professional lighting.",
            "Real photograph of two women in an exclusive Beverly Hills hair salon, one styling the other's thick voluminous extensions at shoulder-blade length. Elegant mirrors, marble counters. Soft professional lighting.",
            "Real photograph of a glamorous woman in an ultra-luxurious high-end hair salon with crystal chandeliers. Hair ending at mid-back. Shot from 3/4 back angle. Soft professional lighting."
        ])
    
    elif any(w in full_text for w in ["mariage", "wedding", "mariée", "bride", "cérémonie"]):
        base = random.choice([
            "Real photograph of three bridesmaids with matching gorgeous voluminous hair extensions at a luxury wedding venue. Romantic golden hour lighting. Ultra-realistic luxury photography.",
            "Real photograph of a glamorous bride at an Italian villa wedding venue in Tuscany, with stunning voluminous hair extensions. Shot from 3/4 back angle. Golden hour romantic lighting.",
            "Real photograph of elegant woman at a French château wedding reception, with thick flowing hair extensions, wearing a stunning evening gown. Golden hour lighting."
        ])
    
    elif any(w in full_text for w in ["plage", "beach", "été", "summer", "vacances", "vacation", "yacht"]):
        base = random.choice([
            "Real photograph of two glamorous women on a luxury yacht deck at sunset, both with thick voluminous extensions blowing in the Mediterranean breeze. Golden hour lighting.",
            "Real photograph of a glamorous woman on the white sand beach of Santorini at golden hour, with luxurious bouncy hair. Elegant white one-piece swimsuit. Shot from 3/4 back angle.",
            "Real photograph of elegant woman at an exclusive Amalfi Coast beach club, with gorgeous thick hair extensions. Chic designer bikini with flowing silk sarong. Golden sunset lighting."
        ])
    
    elif any(w in full_text for w in ["soirée", "gala", "événement", "party", "fête", "red carpet"]):
        base = random.choice([
            "Real photograph of two glamorous women in evening gowns at a gala event, both with spectacular voluminous hair extensions. Red carpet elegance, dramatic lighting. Ultra-realistic photography.",
            "Real photograph of elegant woman on the red carpet at a film premiere, with stunning thick bouncy hair extensions. Designer backless sequined gown. Shot looking over shoulder.",
            "Real photograph of glamorous woman at a Cannes Film Festival gala, with voluminous Hollywood-style hair. Stunning red silk evening gown with open back. Golden hour lighting."
        ])
    
    elif any(w in full_text for w in ["entretien", "soin", "routine", "laver", "brush", "shampoo"]):
        base = random.choice([
            "Real photograph of a glamorous woman at a luxury spa resort in Bali, with voluminous silky hair extensions. Elegant silk robe. Natural soft lighting highlighting hair shine.",
            "Real photograph of elegant woman in a Swiss Alps wellness retreat with mountain views, with stunning thick healthy hair extensions. Chic spa outfit. Soft natural lighting."
        ])
    
    elif any(w in full_text for w in ["tendance", "trend", "mode", "fashion", "style", "2025", "2026"]):
        base = random.choice([
            "Real photograph of glamorous woman strolling through Milan's fashion district, with gorgeous thick voluminous hair extensions. Chic designer summer dress. Golden hour natural lighting.",
            "Real photograph of elegant woman at a Paris haute couture show, with stunning voluminous hair in motion. Sophisticated designer outfit. Fashion week atmosphere."
        ])
    
    else:
        base = random.choice([
            "Real photograph of a glamorous woman on the deck of a luxury superyacht at sunset Mediterranean, with voluminous thick hair extensions. Elegant white designer dress. Shot from 3/4 back angle. Golden hour lighting.",
            "Real photograph of two glamorous best friends with matching voluminous hair extensions, laughing together at a luxurious rooftop bar at sunset. Golden hour lighting.",
            "Real photograph of elegant woman on a Paris rooftop terrace with Eiffel Tower view at dusk, with stunning thick bouncy hair extensions. Chic Parisian outfit. Shot looking over shoulder.",
            "Real photograph of a glamorous woman at a prestigious Milan salon with modern minimalist design, with gorgeous voluminous hair extensions. Elegant casual outfit. Soft professional lighting."
        ])
    
    # Ajouter la contrainte stricte de longueur
    return f"{base} {HAIR_CONSTRAINT} No text, no watermarks."
