"""
🛍️ LUXURA PRODUCT SCRAPER - Récupération des produits du site Wix
==================================================================
Scrape les produits Luxura pour générer des publications personnalisées
avec les vraies photos produits et liens d'achat.

Utilisation:
    from app.services.luxura_product_scraper import get_genius_products, get_product_for_promotion
"""

import requests
import random
from typing import Dict, List, Optional
from datetime import datetime

# URL de base Luxura
LUXURA_BASE_URL = "https://www.luxuradistribution.com"

# ============================================
# 📦 CATALOGUE PRODUITS GENIUS WEFT
# Données extraites du site Luxura
# ============================================

GENIUS_WEFT_PRODUCTS = [
    {
        "id": "genius-vivian-onyx-noir-1",
        "name": "Genius Vivian Onyx Noir #1",
        "shade": "#1",
        "color_name": "Onyx Noir",
        "color_description": "noir profond intense",
        "price": "249,95 $CA",
        "price_value": 249.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-noir-foncé-1",
        "image_url": "https://static.wixstatic.com/media/f1b961_ebf51cc4c86346d8894294e7550cf082~mv2.jpg",
        "in_stock": True,
        "hair_type": "brunette",
        "prompt_color": "jet black, deep onyx black with blue undertones",
    },
    {
        "id": "genius-vivian-chocolat-profond-dc",
        "name": "Genius Vivian Chocolat Profond #DC",
        "shade": "#DC",
        "color_name": "Chocolat Profond",
        "color_description": "brun chocolat riche et profond",
        "price": "249,95 $CA",
        "price_value": 249.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-dark-chocolate-dc",
        "image_url": "https://static.wixstatic.com/media/f1b961_be2093b37a7445fab7f8a23083c22f2d~mv2.jpg",
        "in_stock": True,
        "hair_type": "brunette",
        "prompt_color": "rich dark chocolate brown, deep cocoa with warm undertones",
    },
    {
        "id": "genius-vivian-espresso-intense-2",
        "name": "Genius Vivian Espresso Intense #2",
        "shade": "#2",
        "color_name": "Espresso Intense",
        "color_description": "brun espresso intense",
        "price": "249,95 $CA",
        "price_value": 249.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-brun-2",
        "image_url": "https://static.wixstatic.com/media/f1b961_2596437db6134f7bbdc1c5b2d72907fd~mv2.jpg",
        "in_stock": True,
        "hair_type": "brunette",
        "prompt_color": "rich espresso brown, dark coffee brown with natural depth",
    },
    {
        "id": "genius-vivian-cacao-velours-cacao",
        "name": "Genius Vivian Cacao Velours #CACAO",
        "shade": "#CACAO",
        "color_name": "Cacao Velours",
        "color_description": "brun cacao velouté",
        "price": "299,95 $CA",
        "price_value": 299.95,
        "collection": "Série Vivian",
        "type": "Genius Weft Super Double Draw",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-ssd-trame-invisible-série-vivian-brun-cacao",
        "image_url": "https://static.wixstatic.com/media/f1b961_80553585b8c14372907f1aefb8364ee3~mv2.jpg",
        "in_stock": True,
        "hair_type": "brunette",
        "prompt_color": "velvety cacao brown, warm milk chocolate with soft undertones",
    },
    {
        "id": "genius-vivian-chataigne-douce-3",
        "name": "Genius Vivian Châtaigne Douce #3",
        "shade": "#3",
        "color_name": "Châtaigne Douce",
        "color_description": "châtain doux et naturel",
        "price": "279,95 $CA",
        "price_value": 279.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-brun-moyen-3",
        "image_url": "https://static.wixstatic.com/media/f1b961_47ff485b2f674fdc9245cc856004cd46~mv2.png",
        "in_stock": True,
        "hair_type": "brunette",
        "prompt_color": "soft chestnut brown, medium brown with warm natural tones",
    },
    {
        "id": "genius-vivian-caramel-dore-6",
        "name": "Genius Vivian Caramel Doré #6",
        "shade": "#6",
        "color_name": "Caramel Doré",
        "color_description": "caramel doré lumineux",
        "price": "269,95 $CA",
        "price_value": 269.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-série-vivian-brun-lumineux-blond-foncé-6",
        "image_url": "https://static.wixstatic.com/media/f1b961_5769d9b826004a6f91eb9112dc140cfb~mv2.png",
        "in_stock": True,
        "hair_type": "blonde",
        "prompt_color": "golden caramel, warm honey blonde with caramel highlights",
    },
    {
        "id": "genius-vivian-foochow",
        "name": "Genius Vivian FOOCHOW #FOOCHOW",
        "shade": "#FOOCHOW",
        "color_name": "FOOCHOW",
        "color_description": "brun naturel asiatique premium",
        "price": "359,95 $CA",
        "price_value": 359.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-foochow",
        "image_url": "https://static.wixstatic.com/media/f1b961_1d56319f8a3c4e4dba09ce1c80385fbc~mv2.jpg",
        "in_stock": True,
        "hair_type": "brunette",
        "prompt_color": "natural Asian brown, silky dark brown with subtle warm tones",
    },
    {
        "id": "genius-vivian-platine-pur-60a",
        "name": "Genius Vivian Platine Pur #60A",
        "shade": "#60A",
        "color_name": "Platine Pur",
        "color_description": "blond platine pur et lumineux",
        "price": "269,95 $CA",
        "price_value": 269.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-blond-platine-60a",
        "image_url": "https://static.wixstatic.com/media/f1b961_c3168b50e6d9464db8365cdef0b16557~mv2.png",
        "in_stock": True,
        "hair_type": "blonde",
        "prompt_color": "pure platinum blonde, icy white blonde with silver undertones",
    },
    {
        "id": "genius-vivian-noisette-balayage-cendre",
        "name": "Genius Vivian Noisette Balayage Cendré #5ATP18B62",
        "shade": "#5ATP18B62",
        "color_name": "Noisette Balayage Cendré",
        "color_description": "noisette avec balayage cendré",
        "price": "349,95 $CA",
        "price_value": 349.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-5atp18b62",
        "image_url": "https://static.wixstatic.com/media/f1b961_0e7cf48e1d59418bbf1b562c21494176~mv2.jpg",
        "in_stock": True,
        "hair_type": "balayage",
        "prompt_color": "hazelnut brown with ash blonde balayage highlights, dimensional cool tones",
    },
    {
        "id": "genius-vivian-noisette-ombre-platine",
        "name": "Genius Vivian Noisette Ombré Platine #5AT60",
        "shade": "#5AT60",
        "color_name": "Noisette Ombré Platine",
        "color_description": "ombré de noisette vers platine",
        "price": "359,95 $CA",
        "price_value": 359.95,
        "collection": "Série Vivian",
        "type": "Genius Weft Super Double Draw",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-ssd-série-vivian-ombré-blond-cendré-5at60",
        "image_url": "https://static.wixstatic.com/media/f1b961_5cab009ec1a64e689baa767cbf3bcb8e~mv2.jpg",
        "in_stock": True,
        "hair_type": "ombre",
        "prompt_color": "hazelnut brown roots fading to platinum blonde ends, stunning ombré effect",
    },
    {
        "id": "genius-vivian-espresso-balayage-glace",
        "name": "Genius Vivian Espresso Balayage Glacé #2BTP18/1006",
        "shade": "#2BTP18/1006",
        "color_name": "Espresso Balayage Glacé",
        "color_description": "espresso avec balayage glacé",
        "price": "354,95 $CA",
        "price_value": 354.95,
        "collection": "Série Vivian",
        "type": "Genius Weft Super Double Draw",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-sdd-série-vivian-ombré-2btp18-1006",
        "image_url": "https://static.wixstatic.com/media/f1b961_75316de55cf441ecb82211cbc8d91010~mv2.jpg",
        "in_stock": True,
        "hair_type": "balayage",
        "prompt_color": "dark espresso brown with icy blonde balayage, cool-toned dimensional highlights",
    },
    {
        "id": "genius-vivian-cendre-celeste-pha",
        "name": "Genius Vivian Cendré Céleste #PHA",
        "shade": "#PHA",
        "color_name": "Cendré Céleste",
        "color_description": "blond cendré céleste",
        "price": "269,95 $CA",
        "price_value": 269.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-perfect-highlift-ash-pha",
        "image_url": "https://static.wixstatic.com/media/f1b961_0fdc2ccdccc64d65bde5f1ceb6629ce6~mv2.jpg",
        "in_stock": True,
        "hair_type": "blonde",
        "prompt_color": "celestial ash blonde, cool silvery blonde with ethereal undertones",
    },
    {
        "id": "genius-vivian-cannelle-epicee",
        "name": "Genius Vivian Cannelle Épicée #CINNAMON",
        "shade": "#CINNAMON",
        "color_name": "Cannelle Épicée",
        "color_description": "cannelle épicée cuivrée",
        "price": "269,95 $CA",
        "price_value": 269.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-nouvelle-trame-invisible-série-vivian-cannelle-cinnamon",
        "image_url": "https://static.wixstatic.com/media/f1b961_23960136c3df4e84852f5dde15475d17~mv2.jpg",
        "in_stock": True,
        "hair_type": "auburn",
        "prompt_color": "spiced cinnamon auburn, warm copper with red undertones",
    },
    {
        "id": "genius-vivian-champagne-dore-18-22",
        "name": "Genius Vivian Champagne Doré #18/22",
        "shade": "#18/22",
        "color_name": "Champagne Doré",
        "color_description": "blond champagne doré",
        "price": "319,95 $CA",
        "price_value": 319.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-balayage-blond-beige-18-22",
        "image_url": "https://static.wixstatic.com/media/f1b961_b7d3eb648bf443cb8d30e3e23fa62ad8~mv2.png",
        "in_stock": True,
        "hair_type": "blonde",
        "prompt_color": "golden champagne blonde, warm beige blonde with golden highlights",
    },
    {
        "id": "genius-vivian-golden-hour-6-24",
        "name": "Genius Vivian Golden Hour #6/24",
        "shade": "#6/24",
        "color_name": "Golden Hour",
        "color_description": "balayage golden hour lumineux",
        "price": "289,95 $CA",
        "price_value": 289.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-balayage-blond-foncé-6-24",
        "image_url": "https://static.wixstatic.com/media/f1b961_387bbe6d47cd4217a7b0157f398d9a63~mv2.png",
        "in_stock": True,
        "hair_type": "balayage",
        "prompt_color": "dark blonde base with golden honey highlights, sun-kissed golden hour effect",
    },
    {
        "id": "genius-vivian-diamant-glace-613-18a",
        "name": "Genius Vivian Diamant Glacé #613/18A",
        "shade": "#613/18A",
        "color_name": "Diamant Glacé",
        "color_description": "blond diamant glacé",
        "price": "319,95 $CA",
        "price_value": 319.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-série-vivian-balayage-blond-cendré-613-18a",
        "image_url": "https://static.wixstatic.com/media/f1b961_c15e5a01c6024a1699cb92a2be325f8f~mv2.png",
        "in_stock": True,
        "hair_type": "blonde",
        "prompt_color": "icy diamond blonde with ash undertones, platinum and cool silver blend",
    },
    {
        "id": "genius-vivian-chatain-soyeux-chengtu",
        "name": "Genius Vivian Châtain Soyeux #CHENGTU",
        "shade": "#CHENGTU",
        "color_name": "Châtain Soyeux",
        "color_description": "châtain soyeux premium",
        "price": "359,95 $CA",
        "price_value": 359.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-trame-invisible-série-vivian-chengtu",
        "image_url": "https://static.wixstatic.com/media/f1b961_302097ceefaf4f69a608838f489b57a2~mv2.jpg",
        "in_stock": True,
        "hair_type": "brunette",
        "prompt_color": "silky chestnut brown, luxurious medium brown with natural shine",
    },
    {
        "id": "genius-vivian-miel-sauvage-ombre-cb",
        "name": "Genius Vivian Miel Sauvage Ombré #CB",
        "shade": "#CB",
        "color_name": "Miel Sauvage Ombré",
        "color_description": "ombré miel sauvage",
        "price": "319,95 $CA",
        "price_value": 319.95,
        "collection": "Série Vivian",
        "type": "Genius Weft",
        "url": f"{LUXURA_BASE_URL}/product-page/genius-série-vivian-ombré-blond-miel-cb",
        "image_url": "https://static.wixstatic.com/media/f1b961_5e027a0d94d749e99ad76830129b42da~mv2.png",
        "in_stock": True,
        "hair_type": "ombre",
        "prompt_color": "wild honey ombré, brown roots melting into warm honey blonde ends",
    },
]


# ============================================
# 🎯 FONCTIONS DE SÉLECTION DE PRODUITS
# ============================================

def get_all_genius_products() -> List[Dict]:
    """Retourne tous les produits Genius Weft."""
    return GENIUS_WEFT_PRODUCTS


def get_products_in_stock() -> List[Dict]:
    """Retourne uniquement les produits en stock."""
    return [p for p in GENIUS_WEFT_PRODUCTS if p["in_stock"]]


def get_product_by_id(product_id: str) -> Optional[Dict]:
    """Retourne un produit spécifique par son ID."""
    for product in GENIUS_WEFT_PRODUCTS:
        if product["id"] == product_id:
            return product
    return None


def get_product_by_shade(shade: str) -> Optional[Dict]:
    """Retourne un produit par son code teinte."""
    for product in GENIUS_WEFT_PRODUCTS:
        if product["shade"].lower() == shade.lower():
            return product
    return None


def get_products_by_hair_type(hair_type: str) -> List[Dict]:
    """Retourne les produits par type de cheveux (brunette, blonde, balayage, ombre, auburn)."""
    return [p for p in GENIUS_WEFT_PRODUCTS if p["hair_type"] == hair_type and p["in_stock"]]


def get_random_product_for_promotion() -> Dict:
    """
    Sélectionne un produit aléatoire pour promotion.
    Favorise les produits en stock et varie selon le jour.
    """
    in_stock = get_products_in_stock()
    if not in_stock:
        return random.choice(GENIUS_WEFT_PRODUCTS)
    
    # Rotation basée sur le jour pour éviter répétitions
    day_of_year = datetime.now().timetuple().tm_yday
    index = day_of_year % len(in_stock)
    return in_stock[index]


def get_product_for_facebook_post() -> Dict:
    """
    Sélectionne un produit optimisé pour un post Facebook.
    Retourne le produit avec toutes les infos nécessaires.
    """
    product = get_random_product_for_promotion()
    return product


# ============================================
# 🖼️ GÉNÉRATION DE PROMPTS PERSONNALISÉS
# ============================================

def generate_product_image_prompt(product: Dict, setting: str = "montreal_terrace") -> str:
    """
    Génère un prompt Grok personnalisé basé sur le produit spécifique.
    
    Args:
        product: Dict du produit Luxura
        setting: Type de décor (montreal_terrace, quebec_city, spa, cafe, etc.)
    """
    
    SETTINGS = {
        "montreal_terrace": "at a chic Montreal rooftop terrace during golden hour sunset, city skyline softly blurred in background",
        "quebec_city": "walking along the cobblestone streets of Old Quebec City, Château Frontenac visible in soft background",
        "spa_charlevoix": "at a luxury Charlevoix spa terrace, serene mountain view in background",
        "cafe_plateau": "at a trendy Plateau Mont-Royal café terrace, colorful Montreal neighborhood vibes",
        "vineyard": "at a Quebec Eastern Townships vineyard during golden hour, rolling hills in background",
        "tremblant": "at Mont-Tremblant resort village, European mountain charm atmosphere",
        "vieux_port": "at Montreal's Old Port waterfront at sunset, historic architecture backdrop",
    }
    
    setting_desc = SETTINGS.get(setting, SETTINGS["montreal_terrace"])
    
    prompt = f"""Real photograph of a glamorous Québec woman in her 30s {setting_desc}.

She has stunning {product['color_description']} hair extensions - the exact shade of {product['prompt_color']}. Her thick, voluminous hair flows past her shoulders in soft glamorous waves, catching the golden sunlight beautifully.

She's wearing elegant casual-chic attire, looking confident and radiant. The overall mood is aspirational luxury lifestyle.

The hair is the HERO of the image - showcasing the natural shine, seamless blend, and luxurious volume of premium {product['type']} extensions in the {product['color_name']} shade.

Professional beauty photography, warm golden tones, authentic Quebec lifestyle aesthetic. Hair must end at mid-back level, NOT below waist. No text, no watermarks, no logos."""

    return prompt


def generate_facebook_post_text(product: Dict, post_style: str = "product_spotlight") -> str:
    """
    Génère le texte du post Facebook avec lien d'achat.
    
    Args:
        product: Dict du produit Luxura
        post_style: Style de post (product_spotlight, testimonial, promo)
    """
    
    if post_style == "product_spotlight":
        text = f"""✨ COUP DE CŒUR | {product['name']}

{product['collection']} - La perfection capillaire! 💇‍♀️

🌟 Teinte: {product['color_name']} ({product['shade']})
💰 Prix: {product['price']}
✅ Cheveux 100% Remy naturels
✅ Trame ultra-fine invisible
✅ Confort maximal toute la journée

{product['color_description'].capitalize()} - Une couleur qui sublime votre beauté naturelle!

🛒 COMMANDEZ MAINTENANT:
👉 {product['url']}

📍 Luxura Distribution - St-Georges, Beauce
🚚 Livraison rapide partout au Québec

#LuxuraDistribution #GeniusWeft #{product['color_name'].replace(' ', '')} #ExtensionsQuebec #CheveuxDeReve"""

    elif post_style == "testimonial":
        text = f"""💬 \"Mes extensions {product['name']} ont changé ma vie!\"

Une de nos clientes nous partage sa transformation... 🥰

🌟 Sa teinte: {product['color_name']} ({product['shade']})
💰 Seulement {product['price']}

\"J'ai enfin les cheveux de mes rêves. Le {product['color_description']} est EXACTEMENT ce que je cherchais!\"

👉 Votre tour: {product['url']}

📍 Luxura Distribution - Excellence québécoise
🚚 Livraison 1-2 jours au Québec

#LuxuraDistribution #Transformation #AvantAprès #GeniusWeft"""

    else:  # promo
        text = f"""🔥 PRODUIT VEDETTE | {product['name']}

La teinte {product['color_name']} fait fureur! ⭐

✨ {product['type']} - {product['collection']}
💰 {product['price']}

Cheveux 100% Remy | Trame invisible | Qualité salon

🛒 Magasinez maintenant:
{product['url']}

#LuxuraDistribution #GeniusWeft #ExtensionsCheveux #Quebec"""

    return text


# ============================================
# 🧪 TEST
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛍️ LUXURA PRODUCT SCRAPER - Test")
    print("=" * 60)
    
    print(f"\n📦 {len(GENIUS_WEFT_PRODUCTS)} produits Genius Weft catalogués")
    print(f"✅ {len(get_products_in_stock())} en stock")
    
    print("\n🎯 Produit du jour pour promotion:")
    product = get_product_for_facebook_post()
    print(f"   • {product['name']}")
    print(f"   • {product['price']}")
    print(f"   • {product['url']}")
    
    print("\n🖼️ Prompt d'image généré:")
    prompt = generate_product_image_prompt(product)
    print(f"   {prompt[:200]}...")
    
    print("\n📱 Texte Facebook généré:")
    fb_text = generate_facebook_post_text(product)
    print(fb_text)
