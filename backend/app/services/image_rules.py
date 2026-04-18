"""
LUXURA IMAGE RULES - Règles partagées pour toutes les images
=============================================================
Ce fichier définit les règles de génération d'images pour:
- Daily Content Pipeline (run_content_scan.py)
- Facebook Cron (facebook_cron.py)
- Blog Cron (blog_cron.py)
- Toute autre génération d'image Luxura
"""

from datetime import datetime
from typing import Dict

# =====================================================
# RÈGLES DE BASE POUR LES IMAGES LUXURA
# =====================================================

HAIR_RULES = """
CHEVEUX - RÈGLES ESSENTIELLES (COMPAGNIE D'EXTENSIONS):
1. Cheveux avec un BEAU VOLUME NATUREL - pas exagéré, pas artificiel
2. Texture SOYEUSE, brillante mais naturelle
3. LONGUEUR MINIMUM: mi-dos, tombant vers l'avant sur la poitrine
4. LONGUEUR MAXIMUM: trois-quarts du dos
5. Les cheveux peuvent tomber vers l'avant, encadrer le visage
6. Volume élégant et naturel - pas "perruque" ou "trop parfait"
7. Termes: "naturally full hair", "silky healthy hair", "hair falling over shoulders"
"""

STYLE_RULES = """
STYLE NATUREL ET AUTHENTIQUE:
1. Photos CANDIDES, moments naturels
2. Maximum 1 à 2 personnes
3. Lumière naturelle réaliste
4. Expression naturelle
5. Style lifestyle authentique
6. PAS de style "stock photo" artificiel
"""

FORBIDDEN = """
CE QU'ON NE VEUT PAS:
- Volume exagéré type publicité L'Oréal
- Cheveux fins sans volume
- Cheveux trop courts (minimum mi-dos)
- Cheveux trop longs (maximum 3/4 du dos)
- Groupes de 5+ personnes
- Style artificiel ou CGI
- Poses trop parfaites synchronisées
"""

# =====================================================
# CONTEXTE SAISONNIER
# =====================================================

def get_current_season() -> Dict:
    """Retourne la saison actuelle"""
    month = datetime.now().month
    
    if month in [3, 4, 5]:
        return {
            "name": "Printemps",
            "colors": "pastel, vert tendre, rose, lavande",
            "atmosphere": "spring flowers, cherry blossoms, fresh morning light, renewal",
            "elements": "fleurs, nature en éveil, lumière douce du matin"
        }
    elif month in [6, 7, 8]:
        return {
            "name": "Été",
            "colors": "doré, turquoise, corail, blanc soleil",
            "atmosphere": "summer sunshine, golden hour, beach vibes, outdoor lifestyle",
            "elements": "soleil, plage, terrasse, vacances"
        }
    elif month in [9, 10, 11]:
        return {
            "name": "Automne",
            "colors": "roux, bordeaux, moutarde, brun chaud",
            "atmosphere": "autumn leaves, golden light, cozy fall fashion",
            "elements": "feuilles, couleurs chaudes, cocooning"
        }
    else:
        return {
            "name": "Hiver",
            "colors": "blanc, argenté, bleu glacé, bordeaux",
            "atmosphere": "winter cozy scene, soft snow, warm indoor lighting",
            "elements": "fêtes, neige, intérieur chaleureux"
        }


def get_upcoming_event() -> Dict:
    """Retourne l'événement le plus proche"""
    now = datetime.now()
    month, day = now.month, now.day
    
    events = [
        ((2, 14), "Saint-Valentin", "romantic, red roses, elegant date"),
        ((3, 21), "Début Printemps", "spring renewal, fresh start"),
        ((4, 20), "Pâques", "spring flowers, family brunch, pastel colors"),
        ((5, 10), "Fête des Mères", "mother daughter, elegant brunch, gift"),
        ((5, 30), "Bals de graduation", "prom, elegant gown, special hairstyle"),
        ((6, 24), "St-Jean-Baptiste", "Quebec celebration, summer outdoor"),
        ((6, 21), "Début Été", "summer sunshine, vacation vibes"),
        ((9, 1), "Rentrée", "back to school, new beginnings"),
        ((10, 31), "Halloween", "costume, dramatic looks"),
        ((10, 14), "Action de grâce", "autumn harvest, family gathering"),
        ((12, 25), "Noël", "holiday party, festive elegance"),
        ((12, 31), "Nouvel An", "glamour, midnight celebration"),
    ]
    
    for (e_month, e_day), name, theme in events:
        days_until = (datetime(now.year, e_month, e_day) - now).days
        if -3 <= days_until <= 14:
            return {"name": name, "theme": theme, "days_until": days_until}
    
    return None


def build_image_prompt(context: str, style: str = "lifestyle") -> str:
    """
    Construit un prompt d'image avec les règles Luxura
    
    Args:
        context: Le contexte du post (ex: "brunch de Pâques", "produit extensions")
        style: "lifestyle", "product", "transformation"
    """
    season = get_current_season()
    event = get_upcoming_event()
    
    # Base du prompt
    base = "Candid photo of woman with healthy shiny naturally full hair, mid-back length silky hair falling over shoulders"
    
    # Ajouter le contexte saisonnier
    seasonal = f", {season['atmosphere']}"
    
    # Ajouter l'événement si proche
    if event:
        seasonal += f", {event['theme']}"
    
    # Ajouter le contexte spécifique
    specific = f", {context}"
    
    # Règles toujours présentes
    rules = ", authentic moment, natural lighting, one or two women maximum"
    
    return base + seasonal + specific + rules


# =====================================================
# PROMPTS PRÉ-DÉFINIS PAR TYPE
# =====================================================

def get_educational_prompt() -> str:
    """Prompt pour posts éducatifs"""
    return build_image_prompt("woman learning about hair care, salon consultation atmosphere")


def get_product_prompt(product_name: str = "extensions") -> str:
    """Prompt pour posts produits"""
    return build_image_prompt(f"showcasing beautiful {product_name}, elegant presentation")


def get_lifestyle_prompt() -> str:
    """Prompt pour posts lifestyle/weekend"""
    season = get_current_season()
    return build_image_prompt(f"relaxed lifestyle moment, {season['elements']}")


def get_transformation_prompt() -> str:
    """Prompt pour posts avant/après"""
    return build_image_prompt("confident woman with beautiful transformed hair, happy expression")


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    print("🎨 LUXURA IMAGE RULES")
    print("=" * 50)
    
    season = get_current_season()
    print(f"\n📅 Saison: {season['name']}")
    print(f"   Couleurs: {season['colors']}")
    
    event = get_upcoming_event()
    if event:
        print(f"\n🎉 Événement: {event['name']} (dans {event['days_until']} jours)")
    
    print("\n📷 Exemples de prompts:")
    print(f"\n1. Lifestyle:\n   {get_lifestyle_prompt()[:100]}...")
    print(f"\n2. Produit:\n   {get_product_prompt()[:100]}...")
    print(f"\n3. Éducatif:\n   {get_educational_prompt()[:100]}...")
