# image_brief_generator.py
"""
Module V6 - Brief visuel intelligent
RÈGLES STRICTES: Jamais d'hommes, cheveux TRÈS longs uniquement
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def _detect_visual_mode(blog_data: Dict[str, Any]) -> str:
    """Détecte le type d'image le plus adapté selon le contenu du blog"""
    text = " ".join([
        str(blog_data.get("title", "")),
        str(blog_data.get("excerpt", "")),
        str(blog_data.get("content", "")),
    ]).lower()
    
    category = str(blog_data.get("category", "")).lower()

    # =====================================================
    # DÉTECTION PAR CATÉGORIE D'ABORD (plus fiable)
    # =====================================================
    
    # GENIUS WEFT - Couture (CHECK FIRST car plus commun)
    if category == "genius" or any(k in text for k in ["genius", "weft", "vivian", "trame cousue"]):
        if any(k in text for k in ["couture", "cousue", "installation", "pose", "rangée perlée", "beaded", "étape"]):
            return "installation_genius"
        if any(k in text for k in ["entretien", "repositionnement", "soins"]):
            return "maintenance"
        return "result_genius"
    
    # TAPE-IN - Bandes adhésives
    if category == "tape" or any(k in text for k in ["tape-in", "tape in", "tapein", "aurora", "adhésif", "adhesif", "bande adhésive"]):
        if any(k in text for k in ["installation", "pose", "étape", "comment", "poser", "sandwich"]):
            return "installation_tape"
        if any(k in text for k in ["entretien", "repositionnement", "soins"]):
            return "maintenance"
        return "result_tape"
    
    # I-TIP - Kératine/Microbilles
    if category == "itip" or any(k in text for k in ["i-tip", "itip", "i tip", "kératine", "keratin", "mèche par mèche", "microbille"]):
        if any(k in text for k in ["installation", "pose", "pince", "clamp"]):
            return "installation_itip"
        if any(k in text for k in ["entretien", "repositionnement", "soins"]):
            return "maintenance"
        return "result_itip"
    
    # HALO - Fil invisible (CHECK LAST car moins technique)
    if category == "halo" or any(k in text for k in ["halo", "fil invisible", "wire", "everly"]):
        if any(k in text for k in ["pose", "installation", "comment", "guide", "débutant"]):
            return "installation_halo"
        return "result_halo"
    
    # Comparatifs
    if any(k in text for k in ["vs", "versus", "comparatif", "comparaison", "différence"]):
        return "comparison"
    
    # Entretien général
    if any(k in text for k in ["entretien", "soins", "durée", "repositionnement", "shampoing"]):
        return "maintenance"

    # Par défaut : résultat beauté
    return "beauty_result"


def generate_image_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    V6: Génère un brief STRICT - JAMAIS d'hommes, toujours cheveux très longs
    """
    mode = _detect_visual_mode(blog_data)
    category = blog_data.get("category", "general")
    product = blog_data.get("focus_product", "extensions capillaires")
    title = blog_data.get("title", "")

    logger.info(f"📋 Brief V6 - Mode: {mode} | Catégorie: {category}")

    # =====================================================
    # RÈGLE ABSOLUE - À AJOUTER À TOUS LES PROMPTS
    # =====================================================
    ABSOLUTE_RULES = """
ABSOLUTE MANDATORY RULES (CRITICAL - NEVER BREAK):
- ONLY WOMEN - absolutely NO men, NO masculine features, NO beards, NO male bodies
- ONLY VERY LONG HAIR - minimum waist length, preferably hip length on EVERY woman
- NO short hair, NO bob cuts, NO shoulder-length hair on ANY person
- NO groups with mixed genders - women ONLY
- If showing a group: 2-4 WOMEN ONLY, all with very long feminine hair
"""

    # =====================================================
    # PROMPTS PAR MODE
    # =====================================================
    
    if mode == "installation_halo":
        cover_scene = f"""
Professional beauty photography of ONE elegant woman putting on a Halo wire hair extension.
She is adjusting the invisible wire on top of her head, her natural hair covering the wire.
The Halo extension adds instant length - her hair now reaches her waist.
Soft natural lighting, clean background, focus on the simplicity of the technique.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Close-up of hands adjusting the invisible wire of a Halo extension on a woman's head.
Showing how the wire sits hidden under the natural hair at the crown.
The extensions blend seamlessly, creating instant waist-length hair.
{ABSOLUTE_RULES}
"""

    elif mode == "result_halo":
        cover_scene = f"""
Stunning portrait of ONE beautiful woman with gorgeous waist-length hair thanks to Halo extensions.
Natural, flowing, healthy-looking very long hair with beautiful movement.
Elegant feminine setting, soft warm lighting, aspirational beauty photography.
Focus on the natural result and the beautiful long hair.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Close-up beauty shot showing the texture and shine of very long Halo extension hair.
Natural movement, healthy shine, seamless blending with natural hair.
Professional beauty photography style.
{ABSOLUTE_RULES}
"""

    elif mode == "installation_tape":
        cover_scene = f"""
Professional salon photo: close-up of stylist hands installing Tape-in extensions.
Visible: two thin tape wefts being pressed together with natural hair sandwiched between.
The adhesive strips visible, clean horizontal section of hair.
Professional technique, educational style photography.
Focus on the sandwich method technique.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Extreme close-up of Tape-in sandwich technique.
One tape weft positioned under a thin hair section, second weft on top.
Showing the adhesive tape about to bond, creating a secure attachment.
Technical documentation style, professional lighting.
{ABSOLUTE_RULES}
"""

    elif mode == "result_tape":
        cover_scene = f"""
Beautiful woman showing off her very long, voluminous hair achieved with Tape-in extensions.
Hair reaches her waist, natural movement, healthy shine.
Elegant setting, soft lighting, aspirational beauty result.
Focus on the natural, seamless look of the extensions.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Close-up of the seamless blend where Tape-in extensions meet natural hair.
Showing the invisible attachment, natural volume, healthy texture.
Very long waist-length hair with beautiful shine.
{ABSOLUTE_RULES}
"""

    elif mode == "installation_genius":
        cover_scene = f"""
Professional salon photo: stylist sewing a Genius Weft onto a beaded row.
Close-up of hands with needle and thread, sewing the ultra-thin weft.
Visible: silicone-lined beads forming a horizontal track, sectioned hair with clips.
Educational technical photography showing the real sewing technique.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Extreme close-up of Genius Weft attachment.
The thin weft being sewn through microbeads, thread visible.
Professional precision, clean technique on sectioned hair.
Technical documentation style.
{ABSOLUTE_RULES}
"""

    elif mode == "result_genius":
        cover_scene = f"""
Stunning woman with incredibly long, thick, voluminous hair from Genius Weft extensions.
Hair flows past her waist, natural movement, luxurious volume.
Elegant feminine setting, premium beauty photography.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Close-up showing the flat, seamless lie of Genius Weft extensions at the root.
Very long, thick hair with natural movement and healthy shine.
Focus on the invisible attachment and natural blending.
{ABSOLUTE_RULES}
"""

    elif mode == "installation_itip":
        cover_scene = f"""
Professional close-up: stylist using pliers to clamp a microbead for I-Tip extension.
Visible: silicone microbead, individual I-tip strand with keratin tip, clamping pliers.
Strand-by-strand technique, educational documentation style.
Clean sectioned hair, professional salon lighting.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Extreme close-up of I-Tip microbead attachment.
The small bead being clamped flat, keratin strand secured next to natural hair.
Technical precision, showing the actual mechanical bond.
{ABSOLUTE_RULES}
"""

    elif mode == "result_itip":
        cover_scene = f"""
Beautiful woman with incredibly natural-looking very long hair from I-Tip extensions.
Individual strands create the most natural movement, hair reaches her hips.
Soft lighting, elegant setting, premium beauty result.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Close-up showing the natural fall and movement of I-Tip extended hair.
Individual strands blend perfectly, very long flowing hair.
Focus on the realistic, natural appearance.
{ABSOLUTE_RULES}
"""

    elif mode == "comparison":
        cover_scene = f"""
Professional beauty image: ONE elegant woman with stunning very long waist-length hair.
Clean, simple composition suitable for a comparison article.
Premium beauty photography, soft lighting, focus on hair quality.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Side view of a woman showing her very long, voluminous hair.
Clean background, professional lighting, focus on length and volume.
Suitable for demonstrating extension results.
{ABSOLUTE_RULES}
"""

    elif mode == "maintenance":
        cover_scene = f"""
Elegant woman gently brushing her very long extension hair with a soft brush.
Showing proper care technique, hair reaching past her waist.
Soft natural lighting, clean feminine setting.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Close-up of healthy, shiny, well-maintained very long extension hair.
Focus on texture, shine, and healthy appearance after proper care.
{ABSOLUTE_RULES}
"""

    else:  # beauty_result
        cover_scene = f"""
Stunning portrait of ONE beautiful woman with gorgeous very long flowing hair.
Hair reaches her waist or hips, natural movement, healthy shine.
Premium beauty photography, soft warm lighting, elegant feminine setting.
Aspirational, luxurious, natural result.
{ABSOLUTE_RULES}
"""
        content_scene = f"""
Close-up beauty shot of very long, healthy, shiny hair.
Natural texture, beautiful movement, premium quality.
Professional beauty photography style.
{ABSOLUTE_RULES}
"""

    brief = {
        "brand": "Luxura Distribution",
        "category": category,
        "product": product,
        "visual_mode": mode,
        "title": title,
        "cover": {
            "scene": cover_scene.strip(),
            "absolute_rules": ABSOLUTE_RULES.strip()
        },
        "content": {
            "scene": content_scene.strip(),
            "absolute_rules": ABSOLUTE_RULES.strip()
        },
        "is_technical": "installation" in mode
    }

    logger.info(f"   Title: {title[:50]}...")
    logger.info(f"   Technical: {brief.get('is_technical', False)}")

    return brief
