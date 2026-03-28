# image_brief_generator.py - V11 VARIÉ + CLOSE-UP AJUSTÉ
# Plus de variété, moins de répétition, close-up moins extrême
# Architecture: Blog (GPT-4o) → Prompt (ce fichier) → Image (gpt-image-1)

import logging
import random
import hashlib
from typing import Dict, Any
from datetime import datetime

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
# SCÈNES COVER VARIÉES (installation + contexte)
# Plus de variété pour éviter la répétition
# =====================================================

COVER_SCENES_HALO = [
    "Beautiful woman in cozy bedroom placing invisible wire halo on her head in front of large mirror, morning sunlight streaming through window, casual chic outfit",
    "Elegant woman in modern bathroom with marble counters, adjusting her halo extension with both hands, soft natural lighting, relaxed at-home moment",
    "Young professional woman in stylish apartment getting ready for work, placing halo extension quickly and easily, natural morning light",
    "Woman in beautiful vanity setup with Hollywood lights, casually placing halo extension, showing how simple and quick the process is",
    "Relaxed woman in bright living room, sitting on couch, easily placing halo extension before going out, effortless style moment"
]

COVER_SCENES_SALON = [
    "Professional salon scene with natural light, skilled stylist working on client's hair, modern minimalist interior, premium atmosphere",
    "Upscale hair salon with large windows, experienced stylist performing precise technique, client relaxed in chair, editorial quality",
    "Boutique salon with exposed brick walls, stylist focused on detailed work, warm ambient lighting, intimate professional setting",
    "Modern salon station with ring light, stylist's hands performing careful technique, client with cape, clean professional environment",
    "High-end salon with plants and natural decor, stylist working methodically, soft diffused daylight, premium beauty experience"
]

# =====================================================
# SCÈNES DETAIL AJUSTÉES (moins extrême, plus contexte)
# Close-up raisonnable, pas macro extrême
# =====================================================

DETAIL_SCENES = {
    "halo": [
        "Medium close-up showing woman's hands placing the invisible wire halo on top of her head, natural hair visible falling over the wire, soft lighting",
        "Close shot of the halo extension sitting comfortably on the crown of the head, thin wire barely visible, natural hair blending seamlessly",
        "Detail shot showing the simple one-step placement of halo extension, woman's profile visible, natural home setting in background"
    ],
    "itip": [
        "Close-up of stylist's hands using pliers to secure microbead on a strand of hair, showing the precise technique, salon background visible",
        "Medium close shot of the i-tip installation process, multiple strands visible, stylist working carefully, professional setting",
        "Detail of microbead being clamped with the keratin tip inside, hands and tools clearly visible, salon chair in background"
    ],
    "tape": [
        "Close-up of two tape wefts being aligned for the sandwich application, thin section of natural hair between them, professional hands",
        "Medium close shot showing the tape-in adhesive strips meeting with hair in between, clean sectioning visible, salon environment",
        "Detail of the flat tape weft application, showing the discreet and thin result, stylist's hands working precisely"
    ],
    "genius": [
        "Close-up of needle and thread sewing the genius weft onto the beaded row, silicone beads visible, stylist's skilled hands",
        "Medium close shot of the genius weft being attached to the foundation row, showing the precise stitching technique",
        "Detail of the finished sewn connection between weft and beaded row, showing how secure and invisible it looks"
    ]
}

# =====================================================
# SCÈNES RÉSULTAT GLAMOUR (grande variété)
# 20 scènes différentes pour éviter la répétition
# =====================================================

GLAMOUR_SCENES = [
    # Soirées et événements
    "Group of 4 glamorous women laughing at upscale rooftop bar, golden hour sunset, champagne glasses, all with extremely long flowing hair",
    "Elegant woman arriving at red carpet gala, paparazzi flashes, stunning evening gown, very long sleek hair cascading down her back",
    "Women toasting at sophisticated wine bar, warm candlelight, designer outfits, luxurious long hair catching the light",
    
    # Voyages et destinations
    "Beautiful woman on luxury yacht deck, Mediterranean sea in background, flowing maxi dress, very long windswept hair",
    "Elegant traveler at Parisian café terrace, morning espresso, chic outfit, waist-length silky hair",
    "Woman walking through lavender fields in Provence, flowing summer dress, extremely long hair in the breeze",
    "Sophisticated woman at Italian piazza fountain, golden hour light, very long hair with natural movement",
    
    # Lifestyle quotidien luxueux
    "Woman in designer penthouse apartment, floor-to-ceiling windows, city view, loungewear, very long natural hair",
    "Elegant brunch scene at upscale restaurant, mimosas, natural light, women with gorgeous long flowing hair",
    "Woman in luxury spa robe on private terrace, morning coffee, serene atmosphere, long healthy shiny hair",
    
    # Mode et beauté
    "High-fashion editorial shot, minimalist white studio, dramatic lighting, model with extremely long flowing hair in motion",
    "Behind-the-scenes fashion show moment, model with stunning very long hair, elegant backstage setting",
    "Beauty campaign style shot, woman touching her very long luxurious hair, soft studio lighting, premium feel",
    
    # Nature et outdoor
    "Woman at sunset beach, bohemian style, long hair flowing in ocean breeze, golden light on waves",
    "Elegant picnic in beautiful garden, summer dress, natural setting, very long hair with flowers",
    "Woman in autumn forest, cozy sweater, fallen leaves, extremely long hair catching dappled sunlight",
    
    # Moments intimes
    "Woman admiring her reflection in ornate vintage mirror, soft romantic lighting, very long hair cascading",
    "Getting ready moment in beautiful boudoir, soft morning light, elegant lingerie, long luxurious hair",
    "Confident woman power posing in corner office, business chic, very long sleek professional hair",
    "Celebration dinner with girlfriends, elegant private dining room, all women with stunning long hair"
]

# Index pour rotation et éviter répétition
_used_scenes = {"cover": set(), "detail": set(), "glamour": set()}

# =====================================================
# VARIÉTÉ DE MODÈLES (couleurs de cheveux + ethnies)
# Pour éviter que toutes les images soient identiques
# =====================================================

HAIR_COLORS = [
    "platinum blonde",
    "honey blonde", 
    "golden blonde",
    "light brown",
    "chocolate brown",
    "dark brown",
    "chestnut brown",
    "auburn red",
    "copper red",
    "jet black",
    "soft black",
    "caramel highlights",
    "balayage brunette",
    "ombre blonde to brown",
]

MODEL_DESCRIPTIONS = [
    "Caucasian woman with fair skin",
    "Mediterranean woman with olive skin",
    "Latina woman with warm golden skin",
    "Light-skinned Black woman",
    "Mixed-race woman with caramel skin",
    "Eastern European woman with porcelain skin",
    "Middle Eastern woman with olive complexion",
    "Southern European woman with sun-kissed skin",
]

_used_hair_colors = set()
_used_models = set()

def _get_diverse_model_description(seed: str = None) -> str:
    """
    Génère une description de modèle UNIQUE pour chaque image.
    Évite de répéter la même couleur de cheveux ou le même type de modèle.
    """
    global _used_hair_colors, _used_models
    
    # Reset si toutes utilisées
    available_colors = [c for c in HAIR_COLORS if c not in _used_hair_colors]
    if not available_colors:
        _used_hair_colors = set()
        available_colors = HAIR_COLORS
    
    available_models = [m for m in MODEL_DESCRIPTIONS if m not in _used_models]
    if not available_models:
        _used_models = set()
        available_models = MODEL_DESCRIPTIONS
    
    # Sélection basée sur le seed pour être déterministe mais varié
    if seed:
        color_idx = int(hashlib.md5(f"{seed}_color".encode()).hexdigest(), 16) % len(available_colors)
        model_idx = int(hashlib.md5(f"{seed}_model".encode()).hexdigest(), 16) % len(available_models)
    else:
        color_idx = random.randint(0, len(available_colors) - 1)
        model_idx = random.randint(0, len(available_models) - 1)
    
    hair_color = available_colors[color_idx]
    model_type = available_models[model_idx]
    
    _used_hair_colors.add(hair_color)
    _used_models.add(model_type)
    
    return f"{model_type}, {hair_color} VERY LONG hair (waist length or longer)"

def _get_unique_scene(scene_list: list, scene_type: str, seed: str = None) -> str:
    """Sélectionne une scène unique non utilisée récemment."""
    global _used_scenes
    
    # Reset si toutes utilisées
    available = [s for s in scene_list if s not in _used_scenes[scene_type]]
    if not available:
        _used_scenes[scene_type] = set()
        available = scene_list
    
    # Utiliser le seed pour une sélection déterministe mais variée
    if seed:
        idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(available)
    else:
        idx = random.randint(0, len(available) - 1)
    
    selected = available[idx]
    _used_scenes[scene_type].add(selected)
    
    return selected


def extract_blog_context(blog_data: Dict) -> Dict:
    """Extrait le contexte pertinent du blog pour personnaliser les prompts."""
    title = blog_data.get("title", "")
    content = blog_data.get("content", "")
    excerpt = blog_data.get("excerpt", "")
    category = blog_data.get("category", "general")
    focus_product = blog_data.get("focus_product", "extensions Luxura")
    
    text = f"{title} {excerpt} {content}".lower()
    
    is_installation = any(k in text for k in [
        "installation", "pose", "poser", "étape", "tutoriel", "comment",
        "méthode", "technique", "step", "guide"
    ])
    
    # Détecter la catégorie si pas définie
    if category == "general":
        if "halo" in text: category = "halo"
        elif "i-tip" in text or "itip" in text: category = "itip"
        elif "tape" in text: category = "tape"
        elif "genius" in text or "weft" in text: category = "genius"
    
    return {
        "title": title,
        "category": category,
        "product": focus_product,
        "is_installation": is_installation,
        "seed": hashlib.md5(title.encode()).hexdigest()[:8]
    }


def build_hyper_realistic_prompt(blog_data: Dict, image_type: str) -> str:
    """
    Construit un prompt HYPER-RÉALISTE avec VARIÉTÉ.
    
    image_type: "cover" | "detail" | "result"
    """
    ctx = extract_blog_context(blog_data)
    category = ctx["category"]
    tech = TECHNIQUE_TRUTH.get(category, TECHNIQUE_TRUTH["genius"])
    seed = ctx["seed"]
    
    # Générer une description de modèle UNIQUE pour cette image
    model_desc = _get_diverse_model_description(f"{seed}_{image_type}")
    
    # Base commune pour le réalisme
    realism_rules = """
PHOTOGRAPHY STYLE:
- Professional DSLR quality (Canon 5D or Sony A7R)
- Natural lighting, authentic atmosphere
- Real skin texture, natural imperfections
- Shallow depth of field for professional look
- NO cartoon, NO illustration, NO AI artifacts
- NO watermarks, NO text overlays
- Magazine editorial quality"""

    # NOUVEAU: Utilise la description de modèle VARIÉE
    women_rules = f"""
SUBJECT:
- {model_desc}
- NO short hair, NO bob, NO shoulder length
- NO men in the image
- Confident, natural expression
- Authentic beauty, not overly retouched"""

    if image_type == "cover":
        # COVER: Scène d'installation variée
        if ctx["is_installation"]:
            if category == "halo":
                scene = _get_unique_scene(COVER_SCENES_HALO, "cover", seed)
            else:
                scene = _get_unique_scene(COVER_SCENES_SALON, "cover", seed)
            
            prompt = f"""{scene}

TECHNIQUE: {tech['method']} - {tech['installation']}
{tech['NOT']}

{realism_rules}
{women_rules}"""
        else:
            scene = _get_unique_scene(GLAMOUR_SCENES, "glamour", seed)
            prompt = f"""{scene}

{realism_rules}
{women_rules}"""

    elif image_type == "detail":
        # DETAIL: Close-up RAISONNABLE (pas macro extrême)
        detail_scenes = DETAIL_SCENES.get(category, DETAIL_SCENES["genius"])
        scene = _get_unique_scene(detail_scenes, "detail", seed)
        
        prompt = f"""{scene}

FRAMING: Medium close-up, NOT extreme macro
CONTEXT: Show enough background to understand the setting
TECHNIQUE: {tech['method']}
{tech['NOT']}

{realism_rules}"""

    else:  # result
        # RESULT: Scène glamour variée
        scene = _get_unique_scene(GLAMOUR_SCENES, "glamour", seed + "_result")
        
        prompt = f"""{scene}

HAIR: Extremely long (waist to hip length), flowing, luxurious, natural movement
MUST SHOW: Beautiful transformation result with premium hair extensions

{realism_rules}
{women_rules}

MOOD: Aspirational, glamorous, confident, effortlessly beautiful"""

    return prompt.strip()


def generate_image_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    V11: Prompts VARIÉS + close-up ajusté.
    
    - Plus de variété dans les scènes (20+ options glamour)
    - Close-up moins extrême (medium close-up)
    - Système anti-répétition
    """
    ctx = extract_blog_context(blog_data)
    
    logger.info(f"📸 Brief V11 - Category: {ctx['category']} | Installation: {ctx['is_installation']}")
    
    # Construire les 3 prompts variés
    cover_prompt = build_hyper_realistic_prompt(blog_data, "cover")
    detail_prompt = build_hyper_realistic_prompt(blog_data, "detail")
    result_prompt = build_hyper_realistic_prompt(blog_data, "result")
    
    # Mode visuel
    if ctx["is_installation"]:
        visual_mode = f"installation_{ctx['category']}"
    else:
        visual_mode = "result_natural"
    
    return {
        "visual_mode": visual_mode,
        "category": ctx["category"],
        "product": ctx["product"],
        "is_technical": ctx["is_installation"],
        "blog_title": ctx["title"],
        "cover": {"scene": cover_prompt, "style": "professional photography"},
        "content": {"scene": detail_prompt, "style": "medium close-up photography"},
        "detail": {"scene": detail_prompt, "style": "medium close-up photography"},
        "result": {"scene": result_prompt, "style": "cinematic lifestyle photography"},
        "logo_overlay": True
    }
