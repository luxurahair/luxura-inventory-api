# image_brief_generator.py
"""
V6 - Version durcie pour forcer cheveux TRÈS LONGS + seulement femmes
+ prompts plus efficaces pour les modèles 2026
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def _detect_visual_mode(blog_data: Dict[str, Any]) -> str:
    text = " ".join([
        str(blog_data.get("title", "")),
        str(blog_data.get("excerpt", "")),
        str(blog_data.get("content", "")),
    ]).lower()

    category = str(blog_data.get("category", "")).lower()

    # === INSTALLATIONS TECHNIQUES ===
    if category == "tape" or any(k in text for k in ["tape-in", "tape in", "adhésif", "sandwich", "bande adhésive", "aurora"]):
        if any(k in text for k in ["installation", "pose", "étape", "comment"]):
            return "installation_tape_sandwich"

    if category == "genius" or any(k in text for k in ["genius", "weft", "trame", "vivian"]):
        if any(k in text for k in ["couture", "cousue", "coudre", "rangée perlée", "beaded row", "installation", "pose"]):
            return "installation_genius_sewn"

    if category == "itip" or any(k in text for k in ["i-tip", "itip", "kératine", "keratin"]):
        if any(k in text for k in ["microbille", "micro-bille", "pince", "clamp", "installation", "pose"]):
            return "installation_itip_bead"

    if any(k in text for k in ["installation", "pose", "étape", "tutoriel", "comment installer"]):
        return "installation_pro"

    # === AUTRES MODES ===
    if any(k in text for k in ["entretien", "soins", "durée", "repositionnement", "brosse", "shampoing"]):
        return "result_maintenance"

    if any(k in text for k in ["soirée", "fille", "amies", "soiree", "girls night", "table", "dîner"]):
        return "editorial_lifestyle"

    return "result_natural"


def generate_image_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    mode = _detect_visual_mode(blog_data)
    category = blog_data.get("category", "general")
    product = blog_data.get("focus_product", "extensions capillaires")

    logger.info(f"📋 Brief V6 DURCI - Mode: {mode} | Catégorie: {category}")

    # Base de sécurité forte (cheveux très longs + seulement femmes)
    base_safety = """
ONLY beautiful feminine women. 
Hair MUST be extremely long on every woman - minimum waist length, preferably hip length or longer.
Thick, voluminous, luxurious flowing hair is the hero of the image.
No men, no short hair, no bob, no shoulder length, no pixie cut on any woman.
No brushes, no combs, no styling tools visible.
Photorealistic only, no cartoon, no text, no watermark.
"""

    if mode.startswith("installation_"):
        # Prompts techniques réalistes + sécurité forte
        if mode == "installation_genius_sewn":
            cover_scene = "Professional close-up of Genius Weft sewing technique in a clean salon. Stylist hands sewing ultra-thin weft onto a beaded row. Visible beads and thread. Clean sectioned hair. Educational documentary style."
            content_scene = "Detail shot of beaded row with Genius Weft being sewn. Show the thin weft and precise stitching. Professional lighting, technical focus."
        elif mode == "installation_itip_bead":
            cover_scene = "Close-up of I-Tip micro-bead installation. Stylist using pliers to clamp a microbead on natural hair. Individual keratin tip visible. Clean professional salon. Technical documentary style."
            content_scene = "Extreme close-up of micro-bead being flattened on a strand of hair. Show the technique precisely."
        elif mode == "installation_tape_sandwich":
            cover_scene = "Close-up of Tape-in sandwich method. Two adhesive wefts being pressed together with natural hair in between. Clean section, professional hands. Educational style."
            content_scene = "Detail of tape sandwich application showing adhesive strips and hair placement."
        else:
            cover_scene = f"Professional salon close-up of {product} installation technique. Clean, precise, educational documentary style."
            content_scene = f"Technical detail of {product} attachment method."

        cover_scene += " " + base_safety
        content_scene += " " + base_safety

    elif mode == "editorial_lifestyle":
        cover_scene = f"Group of 4-5 elegant women at a chic girls night dinner. Warm candlelight, smiling, toasting. ALL have extremely long, thick, luxurious hair extensions reaching waist or hips. Joyful feminine atmosphere."
        content_scene = "Close moment between girlfriends admiring each other's very long beautiful hair. Warm, elegant, feminine."
        cover_scene += " " + base_safety
        content_scene += " " + base_safety

    elif mode == "result_maintenance":
        cover_scene = f"Beautiful woman showing healthy, shiny, very long hair after proper care of {product}. Natural movement and quality."
        content_scene = f"Close-up on texture and shine of well-maintained long hair."
        cover_scene += " " + base_safety
        content_scene += " " + base_safety

    else:  # result_natural
        cover_scene = f"Elegant woman with beautiful, natural-looking very long voluminous hair thanks to {product}. Realistic premium result."
        content_scene = f"Close-up showing natural movement and quality of very long hair with {product}."
        cover_scene += " " + base_safety
        content_scene += " " + base_safety

    return {
        "brand": "Luxura Distribution",
        "category": category,
        "product": product,
        "visual_mode": mode,
        "cover": {
            "scene": cover_scene.strip(),
            "style": "professional realistic photography, high detail, clean lighting",
            "focus": "hair quality and technique" if "installation" in mode else "natural long hair result",
            "avoid": ["men", "short hair", "cartoon", "text", "watermark", "unrealistic"]
        },
        "content": {
            "scene": content_scene.strip(),
            "style": "close-up realistic photography",
            "focus": "technical detail" if "installation" in mode else "hair texture and movement",
            "avoid": ["men", "short hair", "cartoon", "text", "watermark"]
        },
        "logo_overlay": True,
        "hair_length_rule": "extremely long hair - waist to hip length minimum on EVERY woman"
    }
