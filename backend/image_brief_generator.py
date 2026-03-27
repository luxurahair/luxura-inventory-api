# image_brief_generator.py - V10 HYPER-RÉALISTE
# Prompts basés sur le CONTEXTE DU BLOG pour des images ultra-réalistes
# Utilise gpt-image-1 pour un rendu photographique professionnel

import logging
import random
from typing import Dict, Any

logger = logging.getLogger(__name__)

# =====================================================
# RÈGLES TECHNIQUES PAR CATÉGORIE (VÉRITÉ ABSOLUE)
# =====================================================

TECHNIQUE_TRUTH = {
    "halo": {
        "method": "invisible wire halo",
        "installation": "self-application at home in one motion",
        "tools": "no tools needed, just place on head",
        "setting": "home, bedroom, bathroom mirror",
        "NOT": "NO salon, NO stylist, NO glue, NO tape, NO microbeads, NO sewing"
    },
    "itip": {
        "method": "individual strand with micro-ring/microbead",
        "installation": "strand by strand with pliers clamping microbead",
        "tools": "pulling needle, pliers, silicone-lined microbeads",
        "setting": "professional salon, stylist chair",
        "NOT": "NO tape, NO glue, NO sewn weft, NO halo wire"
    },
    "tape": {
        "method": "adhesive tape wefts in sandwich method",
        "installation": "two tape strips pressed with natural hair between",
        "tools": "sectioning clips, rat tail comb, tape wefts",
        "setting": "professional salon",
        "NOT": "NO microbeads, NO sewing, NO keratin, NO halo wire"
    },
    "genius": {
        "method": "ultra-thin weft sewn onto beaded row",
        "installation": "sewing thread attaching weft to row of silicone beads",
        "tools": "curved needle, thread, beaded row foundation",
        "setting": "professional salon",
        "NOT": "NO tape, NO glue, NO microbeads for attachment, NO halo wire"
    }
}

# =====================================================
# SCÈNES GLAMOUR VARIÉES (pour l'image résultat)
# =====================================================

GLAMOUR_SCENES = [
    "rooftop bar at golden hour with city skyline, champagne, elegant dress",
    "Parisian café terrace, morning espresso, chic outfit, cobblestone street",
    "luxury yacht deck at sunset, flowing hair in wind, resort wear",
    "elegant gala event with crystal chandeliers, evening gown, red carpet",
    "romantic garden with soft natural light, flowing summer dress, flowers",
    "penthouse balcony overlooking city at dusk, sophisticated cocktail attire",
    "upscale restaurant, candlelit dinner, designer outfit, warm atmosphere",
    "beach resort at golden hour, bohemian style, natural windswept look",
    "high-end spa, white robe, serene zen atmosphere, natural beauty",
    "fashion editorial studio, minimalist background, dramatic lighting"
]


def extract_blog_context(blog_data: Dict) -> Dict:
    """
    Extrait le contexte pertinent du blog pour personnaliser les prompts.
    """
    title = blog_data.get("title", "")
    content = blog_data.get("content", "")
    excerpt = blog_data.get("excerpt", "")
    category = blog_data.get("category", "general")
    focus_product = blog_data.get("focus_product", "extensions Luxura")
    
    # Détecter le type d'article
    text = f"{title} {excerpt} {content}".lower()
    
    is_installation = any(k in text for k in [
        "installation", "pose", "poser", "étape", "tutoriel", "comment",
        "méthode", "technique", "step", "guide"
    ])
    
    is_maintenance = any(k in text for k in [
        "entretien", "soin", "maintenance", "durée", "repositionnement",
        "laver", "brosser", "protéger"
    ])
    
    is_comparison = any(k in text for k in [
        "vs", "versus", "comparaison", "différence", "comparer",
        "avantages", "inconvénients"
    ])
    
    # Extraire des mots-clés spécifiques du titre
    keywords = []
    if "genius" in text: keywords.append("Genius Weft")
    if "halo" in text: keywords.append("Halo")
    if "i-tip" in text or "itip" in text: keywords.append("I-Tip")
    if "tape" in text: keywords.append("Tape-in")
    if "couture" in text or "sewn" in text: keywords.append("sewn method")
    if "microbille" in text: keywords.append("microbeads")
    if "adhésive" in text: keywords.append("adhesive")
    
    return {
        "title": title,
        "category": category,
        "product": focus_product,
        "is_installation": is_installation,
        "is_maintenance": is_maintenance,
        "is_comparison": is_comparison,
        "keywords": keywords,
        "technique": TECHNIQUE_TRUTH.get(category, TECHNIQUE_TRUTH["genius"])
    }


def build_hyper_realistic_prompt(blog_data: Dict, image_type: str) -> str:
    """
    Construit un prompt HYPER-RÉALISTE basé sur le contexte du blog.
    
    image_type: "cover" | "detail" | "result"
    """
    ctx = extract_blog_context(blog_data)
    tech = ctx["technique"]
    
    # Base commune pour le réalisme
    realism_rules = """
CRITICAL PHOTOGRAPHY RULES:
- Shot with professional DSLR camera (Canon 5D Mark IV or Sony A7R)
- Natural lighting, no artificial studio look
- Real human skin texture, visible pores, natural imperfections
- Real hair texture with individual strands visible
- Shallow depth of field (f/2.8) for professional look
- NO cartoon, NO illustration, NO AI artifacts, NO plastic look
- NO watermarks, NO text overlays
- 8K resolution quality, magazine-worthy"""

    women_rules = """
SUBJECT REQUIREMENTS:
- ONLY beautiful feminine women, age 25-40
- VERY LONG hair reaching waist or hips (minimum)
- Natural hair color (blonde, brunette, or auburn)
- NO short hair, NO bob, NO shoulder length
- NO men, NO masculine features
- Elegant, confident, natural expression"""

    if image_type == "cover":
        # IMAGE 1: Scène d'installation basée sur le contexte
        if ctx["is_installation"]:
            prompt = f"""Professional editorial photograph of {tech['method']} hair extension installation.

SCENE: {tech['setting']}, {tech['installation']}.
VISIBLE: {tech['tools']}
{tech['NOT']}

CONTEXT FROM BLOG: {ctx['title'][:100]}
PRODUCT: {ctx['product']}

{realism_rules}
{women_rules}

STYLE: Documentary beauty photography, National Geographic quality
MOOD: Professional, educational, aspirational"""
        else:
            # Article d'entretien ou général
            prompt = f"""Professional beauty photograph showing woman with luxurious {ctx['product']} hair extensions.

SCENE: Elegant setting, woman showcasing her very long, healthy, shiny hair
CONTEXT: {ctx['title'][:100]}

{realism_rules}
{women_rules}

STYLE: Vogue magazine beauty editorial
MOOD: Elegant, confident, natural beauty"""

    elif image_type == "detail":
        # IMAGE 2: Close-up technique MACRO
        if ctx["is_installation"]:
            prompt = f"""Extreme macro close-up photograph of {tech['method']} installation technique.

MUST SHOW IN SHARP DETAIL: {tech['installation']}
VISIBLE ELEMENTS: {tech['tools']}
{tech['NOT']}

{realism_rules}

TECHNICAL SPECS:
- Macro lens (100mm f/2.8)
- Focus stacking for maximum sharpness
- Visible hair strands and attachment points
- Professional salon lighting
- Educational documentary style"""
        else:
            # Close-up cheveux pour entretien
            prompt = f"""Extreme close-up photograph of healthy, shiny, very long hair texture.

MUST SHOW: Individual hair strands, natural shine, healthy cuticles
CONTEXT: {ctx['title'][:80]}

{realism_rules}

STYLE: Beauty product photography, hair care advertisement
FOCUS: Hair texture, quality, health"""

    else:  # result
        # IMAGE 3: Résultat glamour avec scène variée
        scene = random.choice(GLAMOUR_SCENES)
        
        prompt = f"""Cinematic lifestyle photograph of woman with stunning {ctx['product']} hair extensions.

SCENE: {scene}
HAIR: Extremely long (waist to hip length), flowing, luxurious, natural movement
CONTEXT: Final result of {ctx['product']} - {ctx['title'][:60]}

{realism_rules}
{women_rules}

STYLE: High-end fashion editorial, Vogue or Harper's Bazaar quality
LIGHTING: Golden hour or warm ambient
MOOD: Aspirational, glamorous, confident, effortlessly beautiful
COMPOSITION: Full body or 3/4 shot, hair prominently featured"""

    return prompt.strip()


def generate_image_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    V10 HYPER-RÉALISTE: Génère des briefs avec prompts contextuels.
    
    Chaque prompt est construit à partir du CONTENU RÉEL du blog pour des images
    ultra-pertinentes et hyper-réalistes avec gpt-image-1.
    """
    ctx = extract_blog_context(blog_data)
    
    logger.info(f"📸 Brief V10 - Category: {ctx['category']} | Installation: {ctx['is_installation']} | Keywords: {ctx['keywords']}")
    
    # Construire les 3 prompts hyper-réalistes
    cover_prompt = build_hyper_realistic_prompt(blog_data, "cover")
    detail_prompt = build_hyper_realistic_prompt(blog_data, "detail")
    result_prompt = build_hyper_realistic_prompt(blog_data, "result")
    
    # Déterminer le mode visuel
    if ctx["is_installation"]:
        visual_mode = f"installation_{ctx['category']}"
    elif ctx["is_maintenance"]:
        visual_mode = "maintenance"
    else:
        visual_mode = "result_natural"
    
    return {
        "visual_mode": visual_mode,
        "category": ctx["category"],
        "product": ctx["product"],
        "is_technical": ctx["is_installation"],
        "blog_title": ctx["title"],
        "keywords": ctx["keywords"],
        "cover": {
            "scene": cover_prompt,
            "style": "professional photography"
        },
        "content": {
            "scene": detail_prompt,
            "style": "macro photography"
        },
        "detail": {
            "scene": detail_prompt,
            "style": "extreme macro photography"
        },
        "result": {
            "scene": result_prompt,
            "style": "cinematic lifestyle photography"
        },
        "logo_overlay": True
    }
