"""
GENIUS PRODUCT IMAGE TEMPLATE
=============================
Configuration stable pour générer des images produit cohérentes
pour la gamme Genius Vivian de Luxura Distribution.

Basé sur l'analyse du gabarit original IMG_7586.jpeg
"""

import os
import asyncio
from typing import Optional
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

# Configuration du gabarit basée sur l'analyse précise
TEMPLATE_CONFIG = {
    # Position des cheveux (pourcentages)
    "hair_position": {
        "horizontal_start": 45,  # % depuis la gauche
        "horizontal_end": 70,    # % depuis la gauche  
        "vertical_span": "0-95%"  # de haut en bas
    },
    
    # Forme de la courbe S
    "s_curve": {
        "upper": "légère courbe vers la gauche (concave)",
        "middle": "mouvement large vers la droite (pic du S)",
        "lower": "retour vers la gauche (convexe), fin douce"
    },
    
    # Watermark
    "watermark": {
        "serie_position": {"x": 10, "y": 36},  # %
        "vivian_position": {"x": 13, "y": 43},  # % (le V stylisé)
        "extensions_position": {"x": 15, "y": 56},  # %
        "color_hex": "#D4C9B5",  # Beige/crème clair
        "opacity": "60-70%",
        "font_serie": "serif élégant, script",
        "font_vivian": "calligraphique avec V stylisé large",
        "font_extensions": "capitales serif élégant"
    },
    
    # Background
    "background_hex": "#FFFFFF",
    
    # Texture cheveux
    "hair_texture": "lisse, légère ondulation, sans frisottis, mèches définies, brillance naturelle modérée"
}

# Prompt template stable
def get_product_prompt(hair_color_description: str, color_name: str) -> str:
    """
    Génère un prompt stable pour créer une image produit Genius.
    
    Args:
        hair_color_description: Description détaillée de la couleur (ex: "jet black, solid deep black")
        color_name: Nom commercial de la couleur (ex: "Onyx Noir #1")
    
    Returns:
        Prompt formaté pour gpt-image-1
    """
    
    prompt = f'''Luxury hair extension product photography for high-end brand catalog.

=== HAIR WEFT POSITION (CRITICAL - MUST FOLLOW EXACTLY) ===
- Hair weft positioned on the RIGHT SIDE of image (occupying 45-70% horizontal area)
- Two small silver keratin I-tip connectors at the VERY TOP (around 5% from top, 55% from left)
- Hair flows from top to bottom, spanning nearly full height of image (0-95% vertical)

=== S-CURVE SHAPE (ALMOST STRAIGHT - VERY MINIMAL CURVE) ===
- The hair flows ALMOST VERTICALLY with only the slightest gentle curve
- UPPER SECTION: Hair goes STRAIGHT DOWN from the keratin tips, barely any curve
- MIDDLE SECTION: Only a VERY SLIGHT, almost imperceptible curve to the right
- LOWER SECTION: Hair ends taper off with minimal curve toward bottom-left
- Overall: Think of this as STRAIGHT HAIR with just a hint of natural drape
- The shape should be like a gentle diagonal line from top-right to bottom-left
- NOT wavy, NOT bouncy, NOT curly - just naturally STRAIGHT with gravity
- Maximum curve amplitude should be less than 10% of the image width

=== WATERMARK (VERY IMPORTANT - SUBTLE AND PRECISE) ===
- "Série" in small elegant italic serif script at position (10% from left, 36% from top)
- "Vivian" in larger stylized calligraphic font with distinctive large decorative "V", positioned at (13% from left, 43% from top)
- "EXTENSIONS À TRAME INVISIBLE" in small elegant serif capitals at (15% from left, 56% from top)
- Watermark color: LIGHT BEIGE/CREAM (#D4C9B5)
- Opacity: Very subtle, 60-70% transparent - text should appear BEHIND the hair as a ghosted brand imprint
- Watermark spans horizontally across left-center area of image

=== HAIR COLOR (THIS PRODUCT) ===
{hair_color_description}
Product name: {color_name}

=== HAIR TEXTURE ===
- Silky smooth, straight with very slight natural wave
- Individual strands well-defined and visible
- Healthy moderate shine (natural, not artificial gloss)
- No frizz, no tangles, premium quality appearance

=== BACKGROUND ===
- Pure pristine white (#FFFFFF)
- Clean, no shadows, no gradients
- Commercial catalog aesthetic

=== STYLE ===
- High-end luxury hair brand
- Minimalist, elegant composition  
- Professional product photography
- 8K resolution quality'''

    return prompt


# Dictionnaire des couleurs Genius à générer
GENIUS_COLORS = {
    "IVORY": {
        "description": "Creamy ivory blonde, very light warm white-blonde color, soft platinum with golden undertones",
        "name": "Genius Vivian IVORY #IVORY"
    },
    "5ATP18B62": {
        "description": "Noisette balayage with ash tones - medium brown roots (#5A4A3D) blending into ash blonde highlights (#A89B8B) with cool undertones",
        "name": "Genius Vivian Noisette Balayage Cendré #5ATP18B62"
    },
    "2": {
        "description": "Deep espresso brown, rich dark chocolate color (#2C1810), solid uniform dark brown, no highlights",
        "name": "Genius Vivian Espresso Intense #2"
    },
    "CACAO": {
        "description": "Warm cacao brown, medium-dark chocolate (#4A3525), velvety rich brown with subtle warm undertones",
        "name": "Genius Vivian Cacao Velours #CACAO"
    },
    "2BTP18/1006": {
        "description": "Espresso balayage glacé - dark espresso roots (#1C1410) blending into icy ash blonde highlights (#C4B8A8)",
        "name": "Genius Vivian Espresso Balayage Glacé #2BTP18/1006"
    },
    "T14/P14/24": {
        "description": "Golden blonde balayage - medium blonde roots (#9C8A70) with golden honey highlights (#C4A870) and lighter blonde tips (#D4C090)",
        "name": "Genius Vivian Blond Balayage Doré #T14/P14/24"
    },
    "FOOCHOW": {
        "description": "Rich auburn brown with warm copper undertones (#5A3A2A), elegant warm brown",
        "name": "Genius Vivian FOOCHOW #FOOCHOW"
    },
    "5AT60": {
        "description": "Noisette ombré platine - medium brown roots (#6A5A4A) transitioning dramatically to platinum blonde tips (#E8E0D8)",
        "name": "Genius Vivian Noisette Ombré Platine #5AT60"
    },
    "CHENGTU": {
        "description": "Silky chestnut brown, warm medium brown (#5A4535) with soft natural shine, uniform color",
        "name": "Genius Vivian Châtain Soyeux #CHENGTU"
    },
    "BM": {
        "description": "Medium brown with subtle dimension (#4A3A2A), natural looking brown",
        "name": "Genius Vivian BM #BM"
    },
    "PHA": {
        "description": "Celestial ash blonde, cool-toned light blonde (#C8C0B8) with silver-grey undertones, pearl-like luminosity",
        "name": "Genius Vivian Cendré Céleste #PHA"
    },
    "CINNAMON": {
        "description": "Spicy cinnamon red-brown, warm copper-auburn (#7A4A35) with fiery ginger highlights",
        "name": "Genius Vivian Cannelle Épicée #CINNAMON"
    },
    "1B": {
        "description": "Soft black, natural off-black (#1A1515) with subtle brown undertones, silky appearance",
        "name": "Genius Vivian Noir Soie #1B"
    }
}


async def generate_genius_image(
    color_code: str,
    api_key: str,
    output_path: Optional[str] = None
) -> bytes:
    """
    Génère une image produit pour une couleur Genius spécifique.
    
    Args:
        color_code: Code de la couleur (ex: "2", "IVORY", "PHA")
        api_key: Clé API Emergent
        output_path: Chemin optionnel pour sauvegarder l'image
    
    Returns:
        bytes de l'image générée
    """
    if color_code not in GENIUS_COLORS:
        raise ValueError(f"Couleur inconnue: {color_code}. Couleurs disponibles: {list(GENIUS_COLORS.keys())}")
    
    color_info = GENIUS_COLORS[color_code]
    prompt = get_product_prompt(color_info["description"], color_info["name"])
    
    image_gen = OpenAIImageGeneration(api_key=api_key)
    
    images = await image_gen.generate_images(
        prompt=prompt,
        model="gpt-image-1",
        number_of_images=1,
        quality="high"
    )
    
    if images and len(images) > 0:
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(images[0])
        return images[0]
    
    raise Exception("Aucune image générée")


async def generate_all_genius_images(api_key: str, output_dir: str) -> dict:
    """
    Génère toutes les images Genius manquantes.
    
    Args:
        api_key: Clé API Emergent
        output_dir: Dossier de sortie
    
    Returns:
        Dict avec les résultats {color_code: filepath}
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    for color_code, color_info in GENIUS_COLORS.items():
        print(f"🎨 Génération: {color_info['name']}...")
        try:
            output_path = os.path.join(output_dir, f"genius_{color_code.replace('/', '_')}.png")
            await generate_genius_image(color_code, api_key, output_path)
            results[color_code] = output_path
            print(f"   ✅ Sauvegardé: {output_path}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[color_code] = None
    
    return results


# Test
if __name__ == "__main__":
    import os
    os.environ['EMERGENT_LLM_KEY'] = 'sk-emergent-c23DdEcC8C04049755'
    
    async def test():
        api_key = os.environ['EMERGENT_LLM_KEY']
        # Test avec une couleur
        image_bytes = await generate_genius_image(
            "2",  # Espresso Intense
            api_key,
            "/app/backend/static/test_genius_2.png"
        )
        print(f"✅ Test réussi! Image: {len(image_bytes)} bytes")
    
    asyncio.run(test())
