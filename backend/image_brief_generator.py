# image_brief_generator.py
"""
Module responsable de créer un brief visuel intelligent à partir du contenu du blog.
Il décide QUOI montrer avant que l'image ne soit générée.

V5 - Prompts techniques RÉALISTES pour installations
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

    # TAPE-IN d'abord (priorité car plus commun)
    if category == "tape" or any(k in text for k in ["tape-in", "tape in", "tapein", "adhésif", "adhesif", "sandwich", "bande adhésive", "bande adhesive"]):
        if any(k in text for k in ["installation", "pose", "étape", "comment", "poser", "coller"]):
            return "installation_tape_sandwich"
    
    # GENIUS WEFT - Technique de couture
    if category == "genius" or any(k in text for k in ["genius", "weft", "trame"]):
        if any(k in text for k in ["couture", "cousue", "coudre", "rangée perlée", "beaded row", "sew-in", "cousu", "installation", "pose"]):
            return "installation_genius_sewn"
    
    # I-TIP - Technique micro-billes
    if category == "itip" or any(k in text for k in ["i-tip", "itip", "i tip", "kératine", "keratin"]):
        if any(k in text for k in ["microbille", "micro-bille", "micro bille", "pince", "clamp", "installation", "pose"]):
            return "installation_itip_bead"
    
    # Articles techniques généraux (installation, pose, étapes) - sans catégorie spécifique
    if any(k in text for k in ["installation", "pose", "étape", "tutoriel", "comment installer", "poser"]):
        return "installation_pro"

    # Articles d'entretien / soins / durée
    if any(k in text for k in ["entretien", "soins", "durée", "repositionnement", "brosse", "shampoing", "sans sulfate"]):
        return "result_maintenance"

    # Articles lifestyle / soirée / look
    if any(k in text for k in ["soirée", "fille", "amies", "soiree", "girls night", "table", "dîner", "élégant", "glamour"]):
        return "editorial_lifestyle"

    # Par défaut : résultat naturel
    return "result_natural"


def generate_image_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un brief visuel structuré basé sur le contenu réel du blog.
    V5: Prompts techniques ULTRA-RÉALISTES pour les installations.
    """
    mode = _detect_visual_mode(blog_data)
    category = blog_data.get("category", "general")
    product = blog_data.get("focus_product", "extensions capillaires")

    logger.info(f"📋 Brief Generator V5 - Mode détecté: {mode} pour catégorie: {category}")

    # =====================================================
    # PROMPTS TECHNIQUES RÉALISTES - BASÉS SUR LA VRAIE TECHNIQUE
    # =====================================================
    
    if mode == "installation_genius_sewn":
        # Genius Weft - Technique de couture sur rangée perlée
        cover_scene = """
REAL professional salon photo of Genius Weft hair extension installation.
Close-up of stylist's hands sewing a thin weft onto a beaded row track.
Visible elements: silicone-lined beads forming a horizontal row, needle and thread, 
ultra-thin genius weft being sewn through the beads, clean sectioned hair.
Professional lighting in a modern salon. Hair is sectioned with clips.
Documentary style, educational, showing the REAL technique step-by-step.
This is a TECHNICAL photo, not a glamour shot.
"""
        content_scene = """
Close-up detail shot of beaded row technique for Genius Weft.
Showing: small silicone-lined microbeads clamped on natural hair forming a track,
the genius weft positioned ready to be sewn, stylist fingers holding the weft.
Clean, precise, professional salon environment. Natural lighting.
Focus on the TECHNIQUE and the invisible blending at the root area.
Educational photo showing how the beads secure without glue or heat.
"""

    elif mode == "installation_itip_bead":
        # I-Tip - Technique micro-billes avec pince
        cover_scene = """
REAL professional close-up of I-Tip keratin micro bead hair extension installation.
Stylist hands using specialized clamping pliers to flatten a silicone-lined microbead.
Visible: loop tool, individual I-tip strand with keratin tip inserted in bead,
natural hair threaded through bead, pliers compressing the bead flat.
Clean sectioned hair, professional salon lighting.
Documentary/educational style showing the ACTUAL strand-by-strand technique.
NOT a glamour photo - this is technical installation documentation.
"""
        content_scene = """
Extreme close-up of micro bead installation for I-Tip extensions.
Detail showing: one small silicone microbead positioned 1/4 inch from scalp,
I-tip keratin strand aligned inside the bead next to natural hair,
pliers about to clamp. Clean, precise work on sectioned hair.
This shows the REAL mechanical clamping technique without heat or glue.
Professional educational photography style.
"""

    elif mode == "installation_tape_sandwich":
        # Tape-in - Technique sandwich adhésif
        cover_scene = """
REAL professional photo of Tape-in hair extension installation using sandwich method.
Stylist hands pressing two tape wefts together with natural hair in between.
Visible: thin adhesive tape strips on extensions, clean horizontal hair section,
two wefts being sandwiched together, fingers pressing firmly.
Professional salon with good lighting. Hair sectioned with rat-tail comb visible.
Documentary style showing the ACTUAL tape sandwich technique step-by-step.
Educational photo, not a glamour shot.
"""
        content_scene = """
Close-up detail of tape-in sandwich method.
Showing: one tape weft positioned under a thin section of natural hair,
second tape weft aligned on top ready to press down,
the adhesive tape visible on both wefts about to bond.
Clean, precise technique in professional salon.
Focus on how the natural hair is sandwiched between two adhesive strips.
Technical/educational photography style.
"""

    elif mode == "installation_pro":
        # Installation générique professionnelle
        cover_scene = f"Professional salon close-up of {product} installation technique. Stylist hands working on sectioned hair, showing precise placement and technique. Clean, well-lit salon environment. Educational documentation style, NOT a glamour photo. Focus on the technical process."
        content_scene = f"Detail shot of {product} installation showing the attachment method. Close-up of the technique being performed by professional hands. Clean sectioned hair, professional lighting. Technical documentation style."

    elif mode == "editorial_lifestyle":
        # Lifestyle - Soirée de filles chic
        cover_scene = "Group of 4 to 5 elegant women at a chic girls night dinner party. Laughing, toasting with champagne, warm candlelight ambiance. ALL women have extremely long, thick, voluminous hair extensions reaching waist or hips. Joyful, glamorous, aspirational lifestyle photography."
        content_scene = "Intimate moment between elegant girlfriends admiring each other's beautiful very long flowing hair. Warm, feminine atmosphere. Close-up showing hair texture and natural movement."

    elif mode == "result_maintenance":
        # Entretien / Résultats
        cover_scene = f"Beautiful woman showing off healthy, shiny, very long hair after proper maintenance of {product}. Natural lighting, elegant setting. Focus on hair quality, shine and movement. Premium beauty photography."
        content_scene = f"Close-up on the texture and shine of well-maintained {product}. Showing healthy, flowing very long hair. Soft natural lighting emphasizing the quality and luster."

    else:  # result_natural
        # Résultat naturel par défaut
        cover_scene = f"Elegant woman with beautiful, natural-looking very long voluminous hair thanks to {product}. Realistic result, premium lighting, sophisticated setting. Focus on natural blending and hair quality."
        content_scene = f"Close-up showing natural movement and quality of very long hair with {product}. Soft lighting, focus on texture and seamless blending with natural hair."

    brief = {
        "brand": "Luxura Distribution",
        "category": category,
        "product": product,
        "visual_mode": mode,
        "cover": {
            "scene": cover_scene.strip(),
            "style": "professional photography, realistic, high detail" if "installation" in mode else "luxury beauty lifestyle photography, soft warm lighting",
            "focus": "technical accuracy and real technique" if "installation" in mode else "hair quality, natural result",
            "avoid": ["fake looking", "cartoon", "illustration", "text in image", "watermark", "men", "short hair", "unrealistic anatomy", "overly glamorous if technical"]
        },
        "content": {
            "scene": content_scene.strip(),
            "style": "close-up documentary style" if "installation" in mode else "editorial beauty shot",
            "focus": "technical detail and precision" if "installation" in mode else "hair texture and movement",
            "avoid": ["fake", "cartoon", "text", "watermark", "short hair"]
        },
        "logo_overlay": True,
        "hair_length_rule": "very long hair (waist to hip length) on any woman shown in result photos",
        "is_technical": "installation" in mode
    }

    logger.info(f"   Mode: {mode}")
    logger.info(f"   Technical: {brief.get('is_technical', False)}")
    logger.info(f"   Cover: {cover_scene[:80].strip()}...")

    return brief
