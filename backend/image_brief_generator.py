# image_brief_generator.py - V9 DURCI
# Architecture 2 couches: Vérité technique PUIS style visuel
# Chaque catégorie a des règles STRICTES qui ne peuvent pas être violées

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# =====================================================
# COUCHE 1: RÈGLES TECHNIQUES VERROUILLÉES PAR CATÉGORIE
# Ces règles définissent la VÉRITÉ de chaque méthode
# =====================================================

TECHNIQUE_RULES = {
    "halo": {
        "mode": "halo_self_install",
        "technique": "halo hair extension on invisible wire, non-permanent, single self-application at home, no salon required",
        "must_show_cover": "woman standing in front of mirror at home, placing invisible wire halo extension on her own head in one simple motion, natural light, casual home setting",
        "must_show_detail": "extreme close-up of the invisible wire sitting on top of head with natural hair falling over it, showing how the halo blends seamlessly",
        "negative": "NO salon, NO stylist hands, NO glue, NO tape tabs, NO sewn weft, NO microbeads visible, NO clips, NO adhesive, NO permanent installation, NO complex technique"
    },
    "itip": {
        "mode": "itip_salon_install", 
        "technique": "i-tip hair extensions installed strand by strand using microbeads or micro-rings, professional salon technique",
        "must_show_cover": "professional salon scene with stylist working on client's hair, installing i-tip extensions strand by strand, salon mirror visible, professional atmosphere",
        "must_show_detail": "extreme macro close-up of a single microbead being clamped with pliers onto one strand of natural hair, showing the keratin i-tip inside the bead",
        "negative": "NO tape tabs, NO sewn weft, NO adhesive sandwich, NO glue blobs, NO halo wire, NO bulk application"
    },
    "tape": {
        "mode": "tapein_salon_install",
        "technique": "tape-in hair extensions applied with flat adhesive tabs in sandwich method, thin section of natural hair between two adhesive tabs",
        "must_show_cover": "professional salon scene with stylist applying tape-in extensions, showing the sandwich method with client seated, clean professional environment",
        "must_show_detail": "extreme close-up of two flat adhesive tape wefts being pressed together with a thin section of natural hair sandwiched in between",
        "negative": "NO microbeads, NO sewn rows, NO keratin tips, NO i-tip pliers, NO halo wire, NO thick visible tabs"
    },
    "genius": {
        "mode": "genius_sewn_install",
        "technique": "genius weft installed with invisible beaded row foundation and sewn-in weft method, professional salon technique",
        "must_show_cover": "professional salon scene with stylist sewing genius weft onto beaded row, client seated at station, showing the professional installation process",
        "must_show_detail": "extreme macro close-up of thread and needle sewing ultra-thin weft onto a row of silicone-lined beads, showing the precise stitching technique",
        "negative": "NO tape tabs, NO glue, NO strand-by-strand i-tip, NO halo wire, NO adhesive, NO clips"
    }
}

# =====================================================
# SCÈNES CRÉATIVES POUR LE RÉSULTAT FINAL
# Utilisées aléatoirement pour varier les images
# =====================================================

GLAMOUR_RESULT_SCENES = [
    # Soirée de filles
    "group of 4 glamorous women laughing together at an upscale rooftop bar at golden hour, all with extremely long flowing hair reaching their waist, champagne glasses, warm sunset lighting, chic summer dresses",
    
    # Femme seule élégante
    "stunning woman with very long flowing hair past her hips walking confidently down a European cobblestone street, wearing elegant designer outfit, golden hour sunlight catching her hair",
    
    # Miroir glamour
    "beautiful woman admiring her extremely long luxurious hair in an ornate vintage mirror, soft romantic lighting, elegant bedroom setting, hair cascading down her back",
    
    # Café parisien
    "elegant woman with waist-length silky hair sitting at a Parisian café terrace, sipping espresso, chic outfit, soft morning light, hair gently moving in the breeze",
    
    # Plage luxueuse
    "gorgeous woman on a luxury yacht deck, very long windswept hair flowing dramatically, sunset over the ocean, glamorous resort wear",
    
    # Événement gala
    "sophisticated woman at an elegant gala event, extremely long sleek hair styled perfectly, wearing evening gown, crystal chandeliers in background, red carpet atmosphere",
    
    # Jardin romantique
    "beautiful woman in a lush garden setting, very long hair adorned with small flowers, soft natural lighting, romantic and ethereal mood, flowing dress",
    
    # Studio mode
    "high-fashion editorial shot of woman with dramatically long hair in motion, studio lighting, minimalist background, hair creating beautiful flowing shapes",
    
    # Spa luxueux
    "serene woman in luxury spa setting, extremely long healthy shiny hair draped over white robe, soft diffused lighting, zen atmosphere",
    
    # Balcon urbain
    "confident woman on penthouse balcony overlooking city skyline at dusk, very long hair catching the wind, sophisticated evening outfit, metropolitan glamour"
]

# =====================================================
# COUCHE 2: STYLES VISUELS
# Appliqués APRÈS les règles techniques
# =====================================================

VISUAL_STYLES = {
    "installation_technical": {
        "style": "professional documentary photography, clean salon lighting, educational close-up, realistic hands and technique",
        "focus": "technical precision and believable installation process",
        "atmosphere": "professional salon environment, clean and focused"
    },
    "result_natural": {
        "style": "premium beauty photography, natural soft lighting, realistic proportions",
        "focus": "natural-looking hair result, believable transformation",
        "atmosphere": "elegant and natural, not overly glamorous"
    },
    "lifestyle_social": {
        "style": "warm candlelit photography, social gathering atmosphere",
        "focus": "beautiful long flowing hair on multiple women",
        "atmosphere": "elegant girls night, sophisticated social setting"
    },
    "maintenance_care": {
        "style": "clean beauty photography, soft natural lighting",
        "focus": "hair care and maintenance, healthy hair texture",
        "atmosphere": "calm, nurturing, professional care"
    }
}

# =====================================================
# RÈGLES DE SÉCURITÉ GLOBALES
# =====================================================

GLOBAL_SAFETY_RULES = """
ABSOLUTE RULES - NEVER VIOLATE:
- ONLY beautiful feminine women with VERY LONG hair (waist length or longer)
- NO men, NO masculine features, NO short hair, NO bob cuts, NO shoulder length hair
- NO hair rollers, NO curlers, NO styling tools that aren't part of the specific technique
- NO cartoon, NO illustration, NO text overlays, NO watermarks in the generated image
- Photorealistic only, believable proportions, natural skin tones
- Hair must look natural, healthy, and luxurious
"""

# =====================================================
# DÉTECTION DU MODE VISUEL
# =====================================================

def _detect_visual_mode(blog_data: Dict[str, Any]) -> tuple:
    """
    Détecte le mode visuel et la catégorie technique.
    Retourne (mode, category, is_installation)
    """
    text = " ".join([str(blog_data.get(k, "")) for k in ["title", "excerpt", "content"]]).lower()
    category = str(blog_data.get("category", "")).lower()
    
    # Détecter si c'est un article d'installation/pose
    is_installation = any(k in text for k in [
        "installation", "pose", "étape", "tutoriel", "comment poser", 
        "comment installer", "technique", "méthode", "step by step",
        "microbille", "sandwich", "couture", "rangée perlée", "beaded row",
        "sewing", "sewn", "clamp", "pliers"
    ])
    
    # Détecter la catégorie depuis le texte si pas définie
    if not category or category == "general":
        if any(k in text for k in ["halo", "fil invisible", "invisible wire", "everly"]):
            category = "halo"
        elif any(k in text for k in ["i-tip", "itip", "microbille", "micro-ring", "keratin tip", "eleanor"]):
            category = "itip"
        elif any(k in text for k in ["tape", "adhésive", "sandwich", "adhesive tab", "aurora"]):
            category = "tape"
        elif any(k in text for k in ["genius", "weft", "trame", "cousue", "sewn", "beaded row", "vivian"]):
            category = "genius"
    
    # Déterminer le mode
    if is_installation and category in TECHNIQUE_RULES:
        mode = TECHNIQUE_RULES[category]["mode"]
    elif any(k in text for k in ["soirée", "fille", "amies", "girls night", "dîner", "cocktail"]):
        mode = "lifestyle_social"
    elif any(k in text for k in ["entretien", "soins", "maintenance", "care", "wash", "brush"]):
        mode = "maintenance_care"
    else:
        mode = "result_natural"
    
    return mode, category, is_installation


def build_installation_prompt(category: str, image_type: str = "cover") -> str:
    """
    Construit un prompt d'installation TECHNIQUE basé sur les règles verrouillées.
    
    image_type peut être:
    - "cover": Vue d'ensemble de l'installation (salon scene)
    - "content" ou "detail": Close-up technique extrême
    - "result": Résultat final glamour
    """
    import random
    
    rules = TECHNIQUE_RULES.get(category, TECHNIQUE_RULES["genius"])
    style = VISUAL_STYLES["installation_technical"]
    
    if image_type == "cover":
        prompt = f"""Realistic professional photograph showing {rules['technique']}.

MUST SHOW: {rules['must_show_cover']}

{rules['negative']}

STYLE: {style['style']}
FOCUS: {style['focus']}

{GLOBAL_SAFETY_RULES}"""

    elif image_type in ("content", "detail"):
        prompt = f"""Extreme macro close-up documentary photograph of {rules['technique']}.

MUST SHOW IN PRECISE DETAIL: {rules['must_show_detail']}

{rules['negative']}

STYLE: Extreme close-up, macro photography, technical precision
FOCUS: The exact technique and materials used

{GLOBAL_SAFETY_RULES}"""

    else:  # result - glamour final
        scene = random.choice(GLAMOUR_RESULT_SCENES)
        prompt = f"""Premium luxury lifestyle photography.

SCENE: {scene}

HAIR REQUIREMENTS:
- Every woman must have EXTREMELY LONG hair reaching waist or longer
- Hair must look healthy, shiny, thick, and luxurious
- Natural movement and flow in the hair
- Premium hair quality that showcases the result of professional extensions

{GLOBAL_SAFETY_RULES}

STYLE: High-end fashion editorial, cinematic lighting, aspirational luxury
MOOD: Confident, glamorous, effortlessly beautiful"""

    return prompt.strip()


def build_result_prompt(category: str, product: str, image_type: str = "cover") -> str:
    """
    Construit un prompt de RÉSULTAT (pas d'installation, juste le rendu final).
    """
    style = VISUAL_STYLES["result_natural"]
    
    if image_type == "cover":
        prompt = f"""Premium beauty photography showing a beautiful woman with very long, natural-looking {product} hair extensions.

MUST SHOW: Natural hair movement, healthy shine, believable length reaching waist or longer, seamless blend with natural hair

DO NOT SHOW: Any installation technique, any tools, any salon hands, any visible attachment points

STYLE: {style['style']}
FOCUS: {style['focus']}
ATMOSPHERE: {style['atmosphere']}

{GLOBAL_SAFETY_RULES}"""
    else:
        prompt = f"""Close-up beauty photograph showing the texture and quality of very long {product} hair extensions.

MUST SHOW: Hair texture, natural shine, smooth strands, healthy appearance

DO NOT SHOW: Installation technique, tools, hands, attachment points

{GLOBAL_SAFETY_RULES}"""
    
    return prompt.strip()


def build_lifestyle_prompt(product: str, image_type: str = "cover") -> str:
    """
    Construit un prompt LIFESTYLE (soirée de filles, social).
    """
    style = VISUAL_STYLES["lifestyle_social"]
    
    if image_type == "cover":
        prompt = f"""Warm candlelit photograph of a group of 4-5 elegant women at a sophisticated girls night dinner.

MUST SHOW: ALL women with extremely long, luxurious flowing hair reaching waist or hips, warm social atmosphere, champagne glasses, beautiful feminine energy, genuine smiles

DO NOT SHOW: Any hair tools, installation techniques, salon environment, short hair on any woman

STYLE: {style['style']}
FOCUS: {style['focus']}
ATMOSPHERE: {style['atmosphere']}

{GLOBAL_SAFETY_RULES}"""
    else:
        prompt = f"""Close moment between girlfriends admiring each other's very long beautiful hair extensions.

MUST SHOW: Long flowing hair, feminine connection, warm atmosphere

{GLOBAL_SAFETY_RULES}"""
    
    return prompt.strip()


def build_maintenance_prompt(product: str, image_type: str = "cover") -> str:
    """
    Construit un prompt ENTRETIEN (soins, maintenance).
    """
    style = VISUAL_STYLES["maintenance_care"]
    
    if image_type == "cover":
        prompt = f"""Clean beauty photograph showing proper care for very long {product} hair extensions.

MUST SHOW: Beautiful woman with very long healthy-looking hair, gentle care moment, premium hair quality

DO NOT SHOW: Installation technique, salon tools, microbeads, tape tabs, any attachment method visible, hair rollers, curlers

STYLE: {style['style']}
FOCUS: Hair health and proper maintenance
ATMOSPHERE: Calm, nurturing, clean

{GLOBAL_SAFETY_RULES}"""
    else:
        prompt = f"""Close-up showing healthy, well-maintained very long hair extensions texture.

MUST SHOW: Smooth strands, natural shine, healthy hair quality

{GLOBAL_SAFETY_RULES}"""
    
    return prompt.strip()


# =====================================================
# FONCTION PRINCIPALE
# =====================================================

def generate_image_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    V9 DURCI: Génère un brief avec architecture 2 couches + 3 types d'images.
    
    Couche 1: Règles techniques verrouillées (TECHNIQUE_RULES)
    Couche 2: Style visuel (VISUAL_STYLES)
    
    3 types d'images:
    - cover: Vue d'ensemble de l'installation (technique salon)
    - detail: Close-up extrême du détail technique
    - result: Résultat final glamour (femmes cheveux longs)
    """
    mode, category, is_installation = _detect_visual_mode(blog_data)
    product = blog_data.get("focus_product", "extensions Luxura")
    
    logger.info(f"📸 Brief V9 DURCI - Mode: {mode} | Catégorie: {category} | Installation: {is_installation}")
    
    # Construire les prompts selon le mode
    if is_installation and category in TECHNIQUE_RULES:
        cover_prompt = build_installation_prompt(category, "cover")
        detail_prompt = build_installation_prompt(category, "detail")
        result_prompt = build_installation_prompt(category, "result")
        visual_mode = f"installation_{category}"
    elif mode == "lifestyle_social":
        cover_prompt = build_lifestyle_prompt(product, "cover")
        detail_prompt = build_lifestyle_prompt(product, "content")
        result_prompt = build_lifestyle_prompt(product, "cover")  # Lifestyle est déjà glamour
        visual_mode = "editorial_lifestyle"
    elif mode == "maintenance_care":
        cover_prompt = build_maintenance_prompt(product, "cover")
        detail_prompt = build_maintenance_prompt(product, "content")
        result_prompt = build_result_prompt(category, product, "cover")
        visual_mode = "result_maintenance"
    else:
        cover_prompt = build_result_prompt(category, product, "cover")
        detail_prompt = build_result_prompt(category, product, "content")
        result_prompt = build_result_prompt(category, product, "cover")
        visual_mode = "result_natural"
    
    return {
        "visual_mode": visual_mode,
        "category": category,
        "product": product,
        "is_technical": is_installation,
        "technique_rules": TECHNIQUE_RULES.get(category, {}) if is_installation else None,
        "cover": {
            "scene": cover_prompt,
            "style": "professional realistic photography"
        },
        "content": {
            "scene": detail_prompt,
            "style": "close-up realistic photography"
        },
        "detail": {
            "scene": detail_prompt,
            "style": "extreme macro photography"
        },
        "result": {
            "scene": result_prompt,
            "style": "luxury lifestyle photography"
        }
    }
