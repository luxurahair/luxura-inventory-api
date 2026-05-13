#!/usr/bin/env python3
"""
🛍️ LUXURA PRODUCT FACEBOOK CRON v3 - AVEC PRODUITS RÉELS
=========================================================
Génère des posts Facebook promotionnels avec:
1. Image AI glamour personnalisée (couleur exacte du produit)
2. Photo produit du site Luxura
3. Lien d'achat direct

Configuration Render:
  - Start Command: python scripts/product_promo_cron.py
  - Schedule: Selon calendrier éditorial (mardi/jeudi 19h)

Variables requises:
  - XAI_API_KEY: Pour images Grok
  - FB_PAGE_ACCESS_TOKEN + FB_PAGE_ID: Pour Facebook
"""

import os
import sys
import json
import random
import requests
from datetime import datetime
from typing import Optional, Dict, List

# Ajouter le chemin backend pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip()
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "1838415193042352")
FB_API_VERSION = "v21.0"


def log(msg):
    """Log avec timestamp"""
    print(f"[PRODUCT PROMO] {datetime.now().strftime('%H:%M:%S')} {msg}")


# ============================================
# 📦 CATALOGUE PRODUITS GENIUS WEFT
# ============================================

GENIUS_PRODUCTS = [
    {
        "id": "caramel-dore-6",
        "name": "Genius Vivian Caramel Doré #6",
        "shade": "#6",
        "color_name": "Caramel Doré",
        "color_desc": "caramel doré lumineux",
        "price": "269,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-série-vivian-brun-lumineux-blond-foncé-6",
        "image_url": "https://static.wixstatic.com/media/f1b961_5769d9b826004a6f91eb9112dc140cfb~mv2.png",
        "prompt_color": "golden caramel, warm honey blonde with caramel highlights",
        "hair_type": "blonde",
    },
    {
        "id": "chocolat-profond-dc",
        "name": "Genius Vivian Chocolat Profond #DC",
        "shade": "#DC",
        "color_name": "Chocolat Profond",
        "color_desc": "brun chocolat riche",
        "price": "249,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-dark-chocolate-dc",
        "image_url": "https://static.wixstatic.com/media/f1b961_be2093b37a7445fab7f8a23083c22f2d~mv2.jpg",
        "prompt_color": "rich dark chocolate brown, deep cocoa with warm undertones",
        "hair_type": "brunette",
    },
    {
        "id": "platine-pur-60a",
        "name": "Genius Vivian Platine Pur #60A",
        "shade": "#60A",
        "color_name": "Platine Pur",
        "color_desc": "blond platine lumineux",
        "price": "269,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-blond-platine-60a",
        "image_url": "https://static.wixstatic.com/media/f1b961_c3168b50e6d9464db8365cdef0b16557~mv2.png",
        "prompt_color": "pure platinum blonde, icy white blonde with silver undertones",
        "hair_type": "blonde",
    },
    {
        "id": "golden-hour-6-24",
        "name": "Genius Vivian Golden Hour #6/24",
        "shade": "#6/24",
        "color_name": "Golden Hour",
        "color_desc": "balayage doré lumineux",
        "price": "289,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-balayage-blond-foncé-6-24",
        "image_url": "https://static.wixstatic.com/media/f1b961_387bbe6d47cd4217a7b0157f398d9a63~mv2.png",
        "prompt_color": "dark blonde base with golden honey highlights, sun-kissed golden hour effect",
        "hair_type": "balayage",
    },
    {
        "id": "chataigne-douce-3",
        "name": "Genius Vivian Châtaigne Douce #3",
        "shade": "#3",
        "color_name": "Châtaigne Douce",
        "color_desc": "châtain doux naturel",
        "price": "279,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-brun-moyen-3",
        "image_url": "https://static.wixstatic.com/media/f1b961_47ff485b2f674fdc9245cc856004cd46~mv2.png",
        "prompt_color": "soft chestnut brown, medium brown with warm natural tones",
        "hair_type": "brunette",
    },
    {
        "id": "cannelle-epicee-cinnamon",
        "name": "Genius Vivian Cannelle Épicée #CINNAMON",
        "shade": "#CINNAMON",
        "color_name": "Cannelle Épicée",
        "color_desc": "cannelle cuivrée épicée",
        "price": "269,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-nouvelle-trame-invisible-série-vivian-cannelle-cinnamon",
        "image_url": "https://static.wixstatic.com/media/f1b961_23960136c3df4e84852f5dde15475d17~mv2.jpg",
        "prompt_color": "spiced cinnamon auburn, warm copper with red undertones",
        "hair_type": "auburn",
    },
    {
        "id": "miel-sauvage-ombre-cb",
        "name": "Genius Vivian Miel Sauvage Ombré #CB",
        "shade": "#CB",
        "color_name": "Miel Sauvage Ombré",
        "color_desc": "ombré miel sauvage",
        "price": "319,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-série-vivian-ombré-blond-miel-cb",
        "image_url": "https://static.wixstatic.com/media/f1b961_5e027a0d94d749e99ad76830129b42da~mv2.png",
        "prompt_color": "wild honey ombré, brown roots melting into warm honey blonde ends",
        "hair_type": "ombre",
    },
    {
        "id": "champagne-dore-18-22",
        "name": "Genius Vivian Champagne Doré #18/22",
        "shade": "#18/22",
        "color_name": "Champagne Doré",
        "color_desc": "blond champagne élégant",
        "price": "319,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-balayage-blond-beige-18-22",
        "image_url": "https://static.wixstatic.com/media/f1b961_b7d3eb648bf443cb8d30e3e23fa62ad8~mv2.png",
        "prompt_color": "golden champagne blonde, warm beige blonde with golden highlights",
        "hair_type": "blonde",
    },
]


# ============================================
# 🎨 DÉCORS QUÉBÉCOIS VARIÉS
# ============================================

QUEBEC_SETTINGS = [
    {
        "key": "montreal_rooftop",
        "desc": "at a chic Montreal rooftop terrace during golden hour sunset, downtown skyline softly blurred in background",
        "season": ["summer", "spring"],
    },
    {
        "key": "vieux_quebec",
        "desc": "walking along the romantic cobblestone streets of Old Quebec City, Château Frontenac tower visible in soft background",
        "season": ["all"],
    },
    {
        "key": "spa_charlevoix",
        "desc": "relaxing at a luxury Charlevoix spa terrace, stunning mountain view in background, serene atmosphere",
        "season": ["all"],
    },
    {
        "key": "cafe_plateau",
        "desc": "at a trendy Plateau Mont-Royal café terrace, colorful spiral staircases and Montreal street art visible",
        "season": ["summer", "spring", "fall"],
    },
    {
        "key": "vineyard_estrie",
        "desc": "at a Quebec Eastern Townships vineyard during golden hour, rolling hills and grapevines in background",
        "season": ["summer", "fall"],
    },
    {
        "key": "tremblant_village",
        "desc": "in the charming pedestrian village of Mont-Tremblant, European mountain resort atmosphere",
        "season": ["all"],
    },
    {
        "key": "vieux_port",
        "desc": "at Montreal's Old Port waterfront promenade at sunset, historic buildings and water reflections",
        "season": ["summer", "spring"],
    },
    {
        "key": "grande_allee",
        "desc": "on a lively Grande Allée terrace in Quebec City, Victorian architecture and festive atmosphere",
        "season": ["summer"],
    },
]


def get_product_of_the_day() -> Dict:
    """Sélectionne le produit du jour (rotation basée sur le jour)."""
    day_of_year = datetime.now().timetuple().tm_yday
    return GENIUS_PRODUCTS[day_of_year % len(GENIUS_PRODUCTS)]


def get_random_setting() -> Dict:
    """Sélectionne un décor québécois aléatoire."""
    return random.choice(QUEBEC_SETTINGS)


def generate_glamour_image(product: Dict, setting: Dict) -> Optional[str]:
    """
    Génère une image glamour AI avec Grok, personnalisée pour le produit.
    """
    if not XAI_API_KEY:
        log("❌ XAI_API_KEY manquant")
        return None
    
    prompt = f"""Real photograph of a glamorous Québec woman in her early 30s {setting['desc']}.

She has stunning {product['color_desc']} hair extensions - the exact shade of {product['prompt_color']}. 

ABSOLUTELY CRITICAL HAIR LENGTH - READ CAREFULLY:
The hair MUST be MEDIUM-LONG, NOT ULTRA-LONG.
Hair length: ENDS AT BRA-STRAP LEVEL ONLY.
Hair DOES NOT reach the waist.
Hair DOES NOT reach the hips.
Hair DOES NOT reach the thighs.
Hair ends approximately 3/4 down her back - NO LONGER.

Hair style:
- Soft flowing waves with volume and shine
- Thick, healthy-looking, catching the golden sunlight

She's wearing elegant casual-chic attire, looking confident with a radiant smile. The overall mood is aspirational luxury lifestyle.

This is a REALISTIC hair extension advertisement - extensions are typically 16-20 inches.
The hair is the HERO of the image - showcasing the natural shine and luxurious volume of premium Genius Weft extensions in the {product['color_name']} shade.

Professional beauty photography, warm golden tones, authentic Quebec lifestyle aesthetic.
No text, no watermarks, no logos."""

    log(f"🎨 Génération image Grok pour {product['color_name']}...")
    log(f"   Décor: {setting['key']}")
    
    try:
        response = requests.post(
            "https://api.x.ai/v1/images/generations",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-imagine-image",
                "prompt": prompt,
                "n": 1
            },
            timeout=120
        )
        
        if response.status_code == 200:
            image_url = response.json()["data"][0]["url"]
            log(f"✅ Image générée!")
            return image_url
        else:
            log(f"❌ Erreur Grok: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Exception: {e}")
        return None


def generate_post_text(product: Dict) -> str:
    """
    Génère le texte du post Facebook avec photo produit et lien d'achat.
    """
    
    templates = [
        # Template 1: Coup de coeur
        f"""✨ COUP DE CŒUR | {product['name']}

Série Vivian - La perfection capillaire! 💇‍♀️

🎨 Teinte: {product['color_name']} ({product['shade']})
💰 Prix: {product['price']}

✅ Cheveux 100% Remy naturels
✅ Trame ultra-fine invisible  
✅ Confort maximal

{product['color_desc'].capitalize()} - Sublimez votre beauté naturelle!

🛒 COMMANDER MAINTENANT 👇
{product['url']}

📍 Luxura Distribution - St-Georges, Beauce
🚚 Livraison rapide partout au Québec

#LuxuraDistribution #GeniusWeft #{product['color_name'].replace(' ', '')} #ExtensionsQuebec""",

        # Template 2: Produit vedette
        f"""🌟 PRODUIT VEDETTE | {product['name']}

La teinte {product['color_name']} fait sensation! ⭐

📌 Collection: Série Vivian
📌 Teinte: {product['shade']}
📌 Prix: {product['price']}

Un {product['color_desc']} qui illumine votre visage et fait tourner les têtes!

👉 ACHETEZ ICI:
{product['url']}

📍 Luxura Distribution - Excellence québécoise
🚚 Livraison 1-2 jours au Québec

#LuxuraDistribution #GeniusWeft #TransformationCapillaire #Quebec""",

        # Template 3: Question engagement
        f"""💭 Vous rêvez de cheveux {product['color_desc']}?

Découvrez le {product['name']}! ✨

🏷️ {product['price']}
🎨 Teinte: {product['color_name']}

Ce que nos clientes adorent:
• Trame invisible ultra-fine
• Cheveux 100% Remy premium
• Durée 3-4 mois
• Confort absolu

🛍️ MAGASINEZ:
{product['url']}

Quelle est VOTRE teinte préférée? 👇

#LuxuraDistribution #GeniusWeft #SondageBeauté #ExtensionsCheveux""",
    ]
    
    # Rotation basée sur le jour
    template_index = datetime.now().day % len(templates)
    text = templates[template_index]
    
    # Ajouter identifiant pour traçabilité
    return f"{text}\n📌 LUX-PROMO"


def post_to_facebook_with_images(
    message: str,
    glamour_image_url: str,
    product_image_url: str
) -> bool:
    """
    Publie sur Facebook avec l'image glamour ET mentionne la photo produit.
    Note: Facebook ne permet qu'une seule image par post photo standard.
    On utilise l'image glamour et on mentionne le lien produit dans le texte.
    """
    if not FB_PAGE_ACCESS_TOKEN:
        log("❌ FB_PAGE_ACCESS_TOKEN manquant")
        return False
    
    log(f"📘 Publication Facebook avec image glamour...")
    
    try:
        # Post avec image glamour (l'image principale)
        response = requests.post(
            f"https://graph.facebook.com/{FB_API_VERSION}/{FB_PAGE_ID}/photos",
            data={
                "url": glamour_image_url,
                "caption": message,
                "published": "true",
                "access_token": FB_PAGE_ACCESS_TOKEN
            },
            timeout=60
        )
        
        result = response.json()
        
        if "error" in result:
            log(f"❌ Erreur Facebook: {result['error'].get('message')}")
            return False
        
        post_id = result.get("id") or result.get("post_id")
        log(f"✅ Publié! Post ID: {post_id}")
        return True
        
    except Exception as e:
        log(f"❌ Exception: {e}")
        return False


def main():
    """Point d'entrée principal"""
    log("=" * 60)
    log("🛍️ LUXURA PRODUCT PROMO CRON v3")
    log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # Vérifier les variables
    log(f"🔑 XAI_API_KEY: {'✅' if XAI_API_KEY else '❌'}")
    log(f"🔑 FB_PAGE_ACCESS_TOKEN: {'✅' if FB_PAGE_ACCESS_TOKEN else '❌'}")
    
    # 1. Sélectionner le produit du jour
    product = get_product_of_the_day()
    log(f"")
    log(f"📦 Produit du jour: {product['name']}")
    log(f"   💰 Prix: {product['price']}")
    log(f"   🎨 Couleur: {product['color_name']}")
    log(f"   🔗 URL: {product['url'][:50]}...")
    
    # 2. Sélectionner un décor québécois
    setting = get_random_setting()
    log(f"")
    log(f"🏔️ Décor: {setting['key']}")
    
    # 3. Générer l'image glamour AI
    log(f"")
    glamour_url = generate_glamour_image(product, setting)
    
    if not glamour_url:
        log("❌ Échec génération image, arrêt")
        sys.exit(1)
    
    # 4. Générer le texte du post
    log(f"")
    post_text = generate_post_text(product)
    log(f"📝 Texte généré ({len(post_text)} caractères)")
    
    # 5. Publier sur Facebook
    log(f"")
    success = post_to_facebook_with_images(
        message=post_text,
        glamour_image_url=glamour_url,
        product_image_url=product['image_url']
    )
    
    log(f"")
    log("=" * 60)
    if success:
        log("✅ PUBLICATION RÉUSSIE!")
        log(f"   📦 Produit: {product['name']}")
        log(f"   🔗 Lien: {product['url']}")
    else:
        log("❌ PUBLICATION ÉCHOUÉE")
    log("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
