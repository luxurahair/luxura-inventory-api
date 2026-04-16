# image_brief_generator.py
"""
V7 - Brief generator réaligné sur le vrai modèle Luxura
Luxura = importateur / distributeur / vente en ligne / salons affiliés
Pas de logique "formation" ou "certification" par défaut
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _combined_text(blog_data: Dict[str, Any]) -> str:
    return " ".join([
        _safe_text(blog_data.get("title", "")),
        _safe_text(blog_data.get("excerpt", "")),
        _safe_text(blog_data.get("content", "")),
        _safe_text(blog_data.get("category", "")),
        _safe_text(blog_data.get("focus_product", "")),
    ]).lower()


def _detect_visual_mode(blog_data: Dict[str, Any]) -> str:
    """
    Détecte l'intention visuelle du blog selon le vrai business Luxura.
    On évite volontairement l'angle "formation" sauf si le contenu parle
    réellement d'un tutoriel technique, et même là on le traite comme
    démonstration produit / salon, pas comme école.
    """
    text = _combined_text(blog_data)
    category = _safe_text(blog_data.get("category", "")).lower()

    # === OCCASIONS SPÉCIALES (MARIAGE, GALA, ÉVÉNEMENT) ===
    if any(k in text for k in [
        "mariage", "mariée", "marie", "wedding", "bride", "noces",
        "gala", "événement", "evenement", "bal", "soirée", "soiree",
        "fête", "fete", "célébration", "celebration", "occasion spéciale",
        "occasion speciale", "tapis rouge", "red carpet"
    ]):
        return "special_occasion"

    # === AXE B2B / SALONS / PARTENAIRES ===
    if any(k in text for k in [
        "salon affilié", "salons affiliés", "devenir revendeur", "revendeur",
        "partenaire salon", "partenariat salon", "programme partenaire",
        "distributeur", "grossiste", "wholesale", "b2b", "inventaire",
        "déposer de l'inventaire", "depot d'inventaire", "stock en salon",
        "vente en salon", "revente en salon"
    ]):
        return "salon_partner_b2b"

    # === GUIDE ENTRETIEN / DURÉE DE VIE ===
    if any(k in text for k in [
        "entretien", "soins", "durée", "duree", "repositionnement",
        "brosse", "shampoing", "shampooing", "lavage", "maintenance",
        "comment entretenir", "prolonger la durée de vie"
    ]):
        return "maintenance_article"

    # === COMPARATIFS / CHOIX PRODUIT ===
    if any(k in text for k in [
        " vs ", "versus", "comparatif", "comparaison", "différence",
        "difference", "quelle méthode", "quel type", "comment choisir",
        "halo ou", "tape-in ou", "genius weft ou", "i-tip ou", "itip ou"
    ]):
        return "comparison_article"

    # === ARTICLE PRODUIT / AVANTAGES / BÉNÉFICES ===
    if any(k in text for k in [
        "avantages", "bénéfices", "benefices", "pourquoi choisir",
        "pourquoi les salons choisissent", "solution haut de gamme",
        "résultat naturel", "resultat naturel", "volume", "longueur",
        "extensions capillaires professionnelles", "premium"
    ]):
        return "product_benefits"

    # === GUIDE CONSOMMATRICE / ACHAT EN LIGNE ===
    if any(k in text for k in [
        "acheter en ligne", "achat en ligne", "commander", "acheter",
        "cliente", "consommatrice", "cheveux fins", "quel style de vie",
        "quelle méthode choisir", "guide complet", "guide ultime", "faq"
    ]):
        return "consumer_guide"

    # === TECHNIQUE / INSTALLATION / POSE ===
    # On traite ça comme article technique produit/salon, pas comme école.
    if any(k in text for k in [
        "installation", "pose", "étape", "etape", "tutoriel",
        "comment installer", "application", "méthode", "methode",
        "couture", "cousue", "coudre", "rangée perlée", "rangee perlee",
        "beaded row", "microbille", "micro-bille", "sandwich", "adhésif",
        "adhesif", "tape-in", "tape in"
    ]):
        return "technical_installation"

    # === PAR DÉFAUT SELON LA CATÉGORIE ===
    if category in ["halo", "genius", "tape", "itip", "i-tip"]:
        return "product_benefits"

    return "consumer_guide"


def _resolve_product_label(blog_data: Dict[str, Any]) -> str:
    focus_product = _safe_text(blog_data.get("focus_product", ""))
    category = _safe_text(blog_data.get("category", "")).lower()

    if focus_product:
        return focus_product

    mapping = {
        "halo": "extensions Halo Luxura",
        "genius": "extensions Genius Weft Luxura",
        "tape": "extensions Tape-in Luxura",
        "itip": "extensions I-Tip Luxura",
        "i-tip": "extensions I-Tip Luxura",
    }
    return mapping.get(category, "extensions capillaires Luxura")


def _brand_rules() -> str:
    """Brand rules with ARTISTIC STYLE like Luxura Facebook posts"""
    import random
    
    # Variété de couleurs de cheveux
    hair_colors = [
        "rich dark brown with subtle highlights",
        "warm caramel brown with golden undertones", 
        "deep chocolate brown",
        "honey blonde with natural dimension",
        "auburn with copper reflections",
        "natural black with shine",
        "champagne blonde",
        "chestnut brown with warm tones",
        "platinum blonde with soft roots",
        "golden brown balayage",
    ]
    
    # Styles ARTISTIQUES comme les pubs FB
    artistic_styles = [
        "hair dramatically flowing in the wind, movement captured",
        "close-up profile shot focusing on hair texture and length",
        "hair cascading over shoulders, natural movement",
        "wind-blown hair creating dynamic motion",
        "hair falling naturally with soft movement",
        "artistic side profile showcasing hair length",
        "hair in motion against dark background",
        "soft natural hair movement, editorial style",
    ]
    
    # Ambiances/Lighting comme FB
    moods = [
        "dramatic black and white photography, high contrast",
        "warm golden hour lighting, natural tones",
        "soft moody lighting with shadows",
        "dramatic studio lighting, dark background",
        "natural soft light, warm brown tones",
        "editorial fashion photography style",
        "cinematic lighting with depth",
        "intimate portrait lighting",
    ]
    
    chosen_color = random.choice(hair_colors)
    chosen_style = random.choice(artistic_styles)
    chosen_mood = random.choice(moods)
    
    return f"""
Brand context: Luxura Distribution is a premium hair extension importer and distributor in Quebec.
Business model: direct-to-consumer e-commerce plus salon partner distribution.

ARTISTIC STYLE (CRITICAL - match Luxura Facebook aesthetic):
- Photography style: {chosen_mood}
- Hair presentation: {chosen_style}
- Hair color: {chosen_color}

THE IMAGE MUST LOOK LIKE A LUXURA FACEBOOK AD:
- Dramatic, artistic, editorial quality
- Hair is the HERO - focus on texture, length, movement
- Natural authentic beauty, not overly posed
- Magazine-quality, high-end commercial photography
- Close-ups or profile shots that showcase the hair
- Motion and flow in the hair when possible

CRITICAL HAIR RULES:
- Hair MUST be the hero of every image
- Hair length: mid-back to very long (below shoulders minimum, ideally to waist)
- Hair volume: full, luxurious, healthy-looking
- Hair texture: smooth, shiny, natural movement
- Hair color: {chosen_color}
- Show hair from angles that demonstrate length: from behind, three-quarter view, side profile, or close-up
- Capture movement, flow, and texture

AVOID ABSOLUTELY:
- Generic stock photo look
- Stiff posed photos
- Men, short hair, pixie cuts, bob haircuts
- Cartoons, text overlays, watermarks
- Training/classroom scenes
- Low quality or amateur look
""".strip()


def _common_avoid() -> list[str]:
    return [
        "men",
        "short hair",
        "pixie cut",
        "bob haircut",
        "shoulder-length hair only",
        "hair hidden or not visible",
        "front-facing shot hiding hair length",
        "cartoon",
        "text",
        "watermark",
        "training classroom",
        "teacher lecture scene",
        "cheap beauty aesthetic",
        "unrealistic hair",
        "face covering hair",
        "hair tied up completely",
    ]


def generate_image_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    mode = _detect_visual_mode(blog_data)
    category = _safe_text(blog_data.get("category", "general")).lower()
    product = _resolve_product_label(blog_data)
    title = _safe_text(blog_data.get("title", ""))

    logger.info(f"📋 Brief V7 - Mode: {mode} | Catégorie: {category} | Produit: {product}")

    base_rules = _brand_rules()

    # Par défaut
    cover_style = "premium realistic commercial photography, clean composition, soft professional lighting, horizontal blog cover framing"
    content_style = "realistic editorial beauty photography, higher detail, closer framing, professional salon-grade lighting"

    if mode == "special_occasion":
        cover_scene = f"""
Elegant bride or gala-ready woman photographed from behind or three-quarter view, showcasing very long flowing hair extensions reaching mid-back or lower.
Delicate bridal veil or elegant accessory partially visible but NOT covering the hair length.
The hair must be the hero: luxurious volume, beautiful movement, visible length demonstrating {product} quality.
Premium wedding/gala atmosphere, soft romantic lighting, high-end Quebec salon result.
{base_rules}
"""
        content_scene = f"""
Close-up detail shot of beautiful long bridal or event hairstyle enhanced by {product}.
Focus on hair texture, shine, length, and extension blend quality. Hair cascading down the back, visible volume and movement.
Romantic elegant lighting, premium result that sells the dream of perfect hair for special occasions.
{base_rules}
"""
        cover_focus = "long flowing hair from behind, visible length and volume, bridal/gala elegance"
        content_focus = "hair texture detail, extension quality, romantic premium result"

    elif mode == "salon_partner_b2b":
        cover_scene = f"""
Premium salon partnership scene for {product}. Elegant stylist in a high-end salon with a client who has long, beautiful extension-enhanced hair.
Commercial B2B beauty atmosphere, refined Quebec salon environment, trustworthy distributor brand feeling, ideal for a blog card cover.
{base_rules}
"""
        content_scene = f"""
Professional salon scene showing a stylist and a client with beautiful long hair enhanced by {product}.
Subtle product relevance, premium service atmosphere, realistic partner-salon context, no classroom feeling.
{base_rules}
"""
        cover_focus = "salon partnership credibility, premium result, long hair"
        content_focus = "real salon context, stylist-client relationship, product credibility"

    elif mode == "maintenance_article":
        cover_scene = f"""
Elegant woman with long healthy-looking hair extensions maintained with proper care using {product}.
Beautiful shine, smooth texture, premium result, clear and simple commercial composition for a blog cover.
{base_rules}
"""
        content_scene = f"""
Close-up realistic beauty image showing the shine, texture, softness, and healthy appearance of well-maintained long hair using {product}.
Luxury salon-quality finish.
{base_rules}
"""
        cover_focus = "healthy premium hair result, shine, durability"
        content_focus = "texture, shine, maintained extension quality"

    elif mode == "comparison_article":
        cover_scene = f"""
Premium beauty comparison-style image related to {product}, featuring one elegant woman with long luxurious hair and a clear high-end salon result.
Image should communicate choice, method comparison, and informed buying without using text or split-screen gimmicks.
{base_rules}
"""
        content_scene = f"""
Detailed realistic salon-beauty image supporting a product comparison around {product}.
Focus on believable extension result, texture, attachment discretion, and premium finish.
{base_rules}
"""
        cover_focus = "decision-making, premium extension result, clarity"
        content_focus = "method detail, believable comparison support, texture"

    elif mode == "technical_installation":
        cover_scene = f"""
Professional salon application scene for {product}. Show a stylist working on a real female client with long hair in a premium salon.
Keep it commercial and elegant rather than educational classroom style. Technique may be implied, but the image must still sell the result.
{base_rules}
"""
        content_scene = f"""
Closer realistic salon detail of {product} application on long hair. Hands may be visible. Clean sections, believable extension work, premium technical detail.
No school or classroom atmosphere.
{base_rules}
"""
        cover_focus = "premium salon application, believable result, long hair"
        content_focus = "application detail, hands, clean sections, realistic technique"

    elif mode == "product_benefits":
        cover_scene = f"""
Elegant woman with long luxurious hair enhanced by {product}. Premium salon-quality result, visible length and volume, clean commercial beauty image suitable for Luxura Distribution.
{base_rules}
"""
        content_scene = f"""
Closer product-result image showing the texture, movement, density, and realistic luxury finish of {product} on long beautiful hair.
{base_rules}
"""
        cover_focus = "premium product result, visible volume and length"
        content_focus = "texture, movement, believable luxury hair"

    else:  # consumer_guide
        cover_scene = f"""
Premium direct-to-consumer beauty image for {product}. Elegant woman with long beautiful hair extensions, realistic volume and length, clean upscale composition suitable for e-commerce blog content.
{base_rules}
"""
        content_scene = f"""
Closer editorial beauty image showing the realistic result of {product} for a consumer audience: soft movement, healthy texture, natural blend, premium finish.
{base_rules}
"""
        cover_focus = "consumer appeal, premium result, long extension-friendly hair"
        content_focus = "realistic result, blend, softness, texture"

    return {
        "brand": "Luxura Distribution",
        "category": category,
        "product": product,
        "title": title,
        "visual_mode": mode,
        "brand_rules": base_rules,
        "cover": {
            "scene": " ".join(cover_scene.split()),
            "style": cover_style,
            "focus": cover_focus,
            "avoid": _common_avoid(),
        },
        "content": {
            "scene": " ".join(content_scene.split()),
            "style": content_style,
            "focus": content_focus,
            "avoid": _common_avoid(),
        },
        "logo_overlay": True,
        "hair_length_rule": "mid-back to very long hair preferred; no short-hair hero images; extension result must be believable",
    }
