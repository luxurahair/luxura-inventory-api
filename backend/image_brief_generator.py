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
        "must_show": "woman placing invisible wire halo on her own head, natural hair falling over the halo, simple one-step application",
        "negative": "NO salon, NO stylist hands, NO glue, NO tape tabs, NO sewn weft, NO microbeads visible, NO clips, NO adhesive, NO permanent installation, NO complex technique"
    },
    "itip": {
        "mode": "itip_salon_install", 
        "technique": "i-tip hair extensions installed strand by strand using microbeads or micro-rings, professional salon technique",
        "must_show": "stylist hands using pliers to clamp microbead onto single strand of natural hair, individual keratin tip visible, precise strand-by-strand installation",
        "negative": "NO tape tabs, NO sewn weft, NO adhesive sandwich, NO glue blobs, NO halo wire, NO bulk application"
    },
    "tape": {
        "mode": "tapein_salon_install",
        "technique": "tape-in hair extensions applied with flat adhesive tabs in sandwich method, thin section of natural hair between two adhesive tabs",
        "must_show": "two flat adhesive wefts being pressed together with thin section of hair in between, clean sectioning, flat discreet result",
        "negative": "NO microbeads, NO sewn rows, NO keratin tips, NO i-tip pliers, NO halo wire, NO thick visible tabs"
    },
    "genius": {
        "mode": "genius_sewn_install",
        "technique": "genius weft installed with invisible beaded row foundation and sewn-in weft method, professional salon technique",
        "must_show": "stylist sewing ultra-thin weft onto beaded row track, visible silicone beads on foundation row, thread and needle, precise stitching technique",
        "negative": "NO tape tabs, NO glue, NO strand-by-strand i-tip, NO halo wire, NO adhesive, NO clips"
    }
}

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
    """
    rules = TECHNIQUE_RULES.get(category, TECHNIQUE_RULES["genius"])
    style = VISUAL_STYLES["installation_technical"]
    
    if image_type == "cover":
        prompt = f"""Realistic professional salon photograph showing {rules['technique']}.

MUST SHOW: {rules['must_show']}

{rules['negative']}

STYLE: {style['style']}
FOCUS: {style['focus']}
ATMOSPHERE: {style['atmosphere']}

{GLOBAL_SAFETY_RULES}"""
    else:  # content image - more close-up
        prompt = f"""Extreme close-up documentary photograph of {rules['technique']}.

MUST SHOW IN DETAIL: {rules['must_show']}

{rules['negative']}

STYLE: Close-up {style['style']}
FOCUS: Technical detail and precision

{GLOBAL_SAFETY_RULES}"""
    
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
    V9 DURCI: Génère un brief avec architecture 2 couches.
    
    Couche 1: Règles techniques verrouillées (TECHNIQUE_RULES)
    Couche 2: Style visuel (VISUAL_STYLES)
    
    Le système détecte automatiquement si c'est:
    - Un article d'installation → utilise les règles techniques STRICTES
    - Un article de résultat → montre le rendu final sans technique
    - Un article lifestyle → montre l'ambiance sociale
    - Un article d'entretien → montre les soins
    """
    mode, category, is_installation = _detect_visual_mode(blog_data)
    product = blog_data.get("focus_product", "extensions Luxura")
    
    logger.info(f"📸 Brief V9 DURCI - Mode: {mode} | Catégorie: {category} | Installation: {is_installation}")
    
    # Construire les prompts selon le mode
    if is_installation and category in TECHNIQUE_RULES:
        cover_prompt = build_installation_prompt(category, "cover")
        content_prompt = build_installation_prompt(category, "content")
        visual_mode = f"installation_{category}"
    elif mode == "lifestyle_social":
        cover_prompt = build_lifestyle_prompt(product, "cover")
        content_prompt = build_lifestyle_prompt(product, "content")
        visual_mode = "editorial_lifestyle"
    elif mode == "maintenance_care":
        cover_prompt = build_maintenance_prompt(product, "cover")
        content_prompt = build_maintenance_prompt(product, "content")
        visual_mode = "result_maintenance"
    else:
        cover_prompt = build_result_prompt(category, product, "cover")
        content_prompt = build_result_prompt(category, product, "content")
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
            "scene": content_prompt,
            "style": "close-up realistic photography"
        }
    }
