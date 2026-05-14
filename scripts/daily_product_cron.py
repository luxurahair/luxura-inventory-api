#!/usr/bin/env python3
"""
🛍️ LUXURA DAILY PRODUCT CRON - 18h00 QUOTIDIEN
===============================================
Publication automatique quotidienne à 18h00 (heure Montréal).
Sélectionne un produit aléatoire et une mise en scène variée.
SAUVEGARDE TOUTES LES IMAGES DANS WIX MEDIA MANAGER!

Configuration Render Cron:
  - Name: daily-product-18h
  - Command: python scripts/daily_product_cron.py
  - Schedule: 0 22 * * *  (22h UTC = 18h Montréal été)
  
Variables requises:
  - XAI_API_KEY: Pour images Grok
  - FB_PAGE_ACCESS_TOKEN + FB_PAGE_ID: Pour Facebook
  - WIX_API_KEY + WIX_SITE_ID: Pour sauvegarder les images
  - DATABASE_URL: Pour stocker les métadonnées
"""

import os
import sys
import random
import requests
import asyncio
import uuid
from datetime import datetime

# Ajouter le chemin backend pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip()
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "1838415193042352")
WIX_API_KEY = os.getenv("WIX_API_KEY", "").strip()
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def log(msg):
    print(f"[DAILY 18H] {datetime.now().strftime('%H:%M:%S')} {msg}")


# ============================================
# 🖼️ SAUVEGARDE IMAGES DANS WIX
# ============================================

async def save_image_to_wix(grok_url: str, product: dict, scene: dict) -> str:
    """
    Sauvegarde l'image Grok dans Wix Media Manager et retourne l'URL permanente.
    Stocke aussi les métadonnées dans Supabase.
    """
    import httpx
    import asyncpg
    
    if not WIX_API_KEY or not WIX_SITE_ID:
        log("⚠️ WIX_API_KEY ou WIX_SITE_ID manquant - utilisation URL Grok temporaire")
        return grok_url
    
    try:
        # Générer un nom de fichier descriptif
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        scene_slug = scene['name'].lower().replace(' ', '-').replace("'", "")
        unique_id = uuid.uuid4().hex[:6]
        file_name = f"luxura-{product['id']}-{scene_slug}-{timestamp}-{unique_id}.jpg"
        
        log(f"📤 Upload vers Wix Media Manager: {file_name}")
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            # 1. Importer l'image depuis l'URL Grok
            import_response = await client.post(
                "https://www.wixapis.com/site-media/v1/files/import",
                headers={
                    "Authorization": WIX_API_KEY,
                    "wix-site-id": WIX_SITE_ID,
                    "Content-Type": "application/json"
                },
                json={
                    "url": grok_url,
                    "displayName": file_name,
                    "mediaType": "IMAGE",
                    "mimeType": "image/jpeg",
                    "filePath": f"/luxura-ai-images/{file_name}"
                }
            )
            
            if import_response.status_code not in (200, 201):
                log(f"⚠️ Erreur import Wix: {import_response.status_code}")
                return grok_url  # Fallback sur URL Grok
            
            data = import_response.json()
            file_id = data.get("file", {}).get("id") or data.get("id")
            
            if not file_id:
                log("⚠️ Pas de file_id - utilisation URL Grok")
                return grok_url
            
            # 2. Attendre que l'image soit prête (max 45 sec)
            wix_url = None
            for attempt in range(45):
                check = await client.get(
                    f"https://www.wixapis.com/site-media/v1/files/{file_id}",
                    headers={
                        "Authorization": WIX_API_KEY,
                        "wix-site-id": WIX_SITE_ID,
                    }
                )
                if check.status_code == 200:
                    file_data = check.json().get("file", {})
                    if file_data.get("operationStatus") == "READY":
                        wix_url = f"https://static.wixstatic.com/media/{file_id}"
                        break
                await asyncio.sleep(1)
            
            if not wix_url:
                wix_url = f"https://static.wixstatic.com/media/{file_id}"
            
            log(f"✅ Image sauvegardée dans Wix: {wix_url[:60]}...")
            
            # 3. Sauvegarder dans Supabase (métadonnées)
            if DATABASE_URL:
                try:
                    conn = await asyncpg.connect(DATABASE_URL)
                    
                    # Créer la table si nécessaire
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS generated_images (
                            id SERIAL PRIMARY KEY,
                            grok_url TEXT NOT NULL,
                            wix_url TEXT NOT NULL,
                            product_id VARCHAR(100) NOT NULL,
                            product_name VARCHAR(255),
                            color_name VARCHAR(100),
                            scene VARCHAR(100),
                            post_type VARCHAR(50),
                            created_at TIMESTAMP DEFAULT NOW(),
                            used_count INTEGER DEFAULT 1
                        )
                    """)
                    
                    # Insérer l'image
                    await conn.execute("""
                        INSERT INTO generated_images 
                        (grok_url, wix_url, product_id, product_name, color_name, scene, post_type)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, grok_url, wix_url, product['id'], product['name'], 
                        product['color_name'], scene['name'], "facebook")
                    
                    await conn.close()
                    log(f"✅ Métadonnées sauvegardées dans DB")
                except Exception as db_err:
                    log(f"⚠️ Erreur DB: {db_err}")
            
            return wix_url
            
    except Exception as e:
        log(f"⚠️ Exception sauvegarde Wix: {e}")
        return grok_url  # Fallback sur URL Grok


def save_image_sync(grok_url: str, product: dict, scene: dict) -> str:
    """Wrapper synchrone pour la sauvegarde async."""
    try:
        return asyncio.run(save_image_to_wix(grok_url, product, scene))
    except Exception as e:
        log(f"⚠️ Erreur async: {e}")
        return grok_url


# ============================================
# 📦 CATALOGUE COMPLET GENIUS WEFT (18 produits)
# ============================================

PRODUCTS = [
    {
        "id": "onyx-noir-1",
        "name": "Genius Vivian Onyx Noir #1",
        "shade": "#1",
        "color_name": "Onyx Noir",
        "color_desc": "noir profond intense",
        "price": "249,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-noir-foncé-1",
        "image_url": "https://static.wixstatic.com/media/f1b961_ebf51cc4c86346d8894294e7550cf082~mv2.jpg",
        "prompt_color": "jet black, deep onyx black with subtle blue undertones, NO brown, pure black",
        "hair_type": "black",
        "emoji": "🖤",
    },
    {
        "id": "chocolat-profond-dc",
        "name": "Genius Vivian Chocolat Profond #DC",
        "shade": "#DC",
        "color_name": "Chocolat Profond",
        "color_desc": "brun chocolat riche et profond",
        "price": "249,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-dark-chocolate-dc",
        "image_url": "https://static.wixstatic.com/media/f1b961_be2093b37a7445fab7f8a23083c22f2d~mv2.jpg",
        "prompt_color": "dark chocolate brown, rich deep cocoa brown, NO highlights, solid dark brown",
        "hair_type": "brunette",
        "emoji": "🍫",
    },
    {
        "id": "espresso-intense-2",
        "name": "Genius Vivian Espresso Intense #2",
        "shade": "#2",
        "color_name": "Espresso Intense",
        "color_desc": "brun espresso intense",
        "price": "249,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-brun-2",
        "image_url": "https://static.wixstatic.com/media/f1b961_2596437db6134f7bbdc1c5b2d72907fd~mv2.jpg",
        "prompt_color": "rich espresso brown, dark coffee brown with natural depth, NO highlights",
        "hair_type": "brunette",
        "emoji": "☕",
    },
    {
        "id": "cacao-velours",
        "name": "Genius Vivian Cacao Velours #CACAO",
        "shade": "#CACAO",
        "color_name": "Cacao Velours",
        "color_desc": "brun cacao velouté",
        "price": "299,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-ssd-trame-invisible-série-vivian-brun-cacao",
        "image_url": "https://static.wixstatic.com/media/f1b961_80553585b8c14372907f1aefb8364ee3~mv2.jpg",
        "prompt_color": "velvety cacao brown, warm milk chocolate, soft medium brown",
        "hair_type": "brunette",
        "emoji": "🤎",
    },
    {
        "id": "chataigne-douce-3",
        "name": "Genius Vivian Châtaigne Douce #3",
        "shade": "#3",
        "color_name": "Châtaigne Douce",
        "color_desc": "châtain doux et naturel",
        "price": "279,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-brun-moyen-3",
        "image_url": "https://static.wixstatic.com/media/f1b961_47ff485b2f674fdc9245cc856004cd46~mv2.png",
        "prompt_color": "soft chestnut brown, medium natural brown with warm tones",
        "hair_type": "brunette",
        "emoji": "🌰",
    },
    {
        "id": "caramel-dore-6",
        "name": "Genius Vivian Caramel Doré #6",
        "shade": "#6",
        "color_name": "Caramel Doré",
        "color_desc": "caramel doré lumineux",
        "price": "269,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-série-vivian-brun-lumineux-blond-foncé-6",
        "image_url": "https://static.wixstatic.com/media/f1b961_5769d9b826004a6f91eb9112dc140cfb~mv2.png",
        "prompt_color": "golden caramel, warm honey blonde with caramel highlights, dark blonde",
        "hair_type": "blonde",
        "emoji": "🍯",
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
        "prompt_color": "pure platinum blonde, icy white blonde with silver undertones, very light blonde",
        "hair_type": "blonde",
        "emoji": "💎",
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
        "emoji": "🥂",
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
        "prompt_color": "dark blonde base with golden honey highlights, sun-kissed balayage effect",
        "hair_type": "balayage",
        "emoji": "🌅",
    },
    {
        "id": "diamant-glace-613-18a",
        "name": "Genius Vivian Diamant Glacé #613/18A",
        "shade": "#613/18A",
        "color_name": "Diamant Glacé",
        "color_desc": "blond diamant glacé",
        "price": "319,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-série-vivian-balayage-blond-cendré-613-18a",
        "image_url": "https://static.wixstatic.com/media/f1b961_c15e5a01c6024a1699cb92a2be325f8f~mv2.png",
        "prompt_color": "icy diamond blonde with ash undertones, platinum and cool silver blend",
        "hair_type": "blonde",
        "emoji": "❄️",
    },
    {
        "id": "cendre-celeste-pha",
        "name": "Genius Vivian Cendré Céleste #PHA",
        "shade": "#PHA",
        "color_name": "Cendré Céleste",
        "color_desc": "blond cendré céleste",
        "price": "269,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-perfect-highlift-ash-pha",
        "image_url": "https://static.wixstatic.com/media/f1b961_0fdc2ccdccc64d65bde5f1ceb6629ce6~mv2.jpg",
        "prompt_color": "celestial ash blonde, cool silvery blonde with ethereal undertones",
        "hair_type": "blonde",
        "emoji": "✨",
    },
    {
        "id": "cannelle-epicee",
        "name": "Genius Vivian Cannelle Épicée #CINNAMON",
        "shade": "#CINNAMON",
        "color_name": "Cannelle Épicée",
        "color_desc": "cannelle cuivrée épicée",
        "price": "269,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-nouvelle-trame-invisible-série-vivian-cannelle-cinnamon",
        "image_url": "https://static.wixstatic.com/media/f1b961_23960136c3df4e84852f5dde15475d17~mv2.jpg",
        "prompt_color": "spiced cinnamon auburn, warm copper with red undertones, ginger spice",
        "hair_type": "auburn",
        "emoji": "🔥",
    },
    {
        "id": "miel-sauvage-ombre",
        "name": "Genius Vivian Miel Sauvage Ombré #CB",
        "shade": "#CB",
        "color_name": "Miel Sauvage Ombré",
        "color_desc": "ombré miel sauvage",
        "price": "319,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-série-vivian-ombré-blond-miel-cb",
        "image_url": "https://static.wixstatic.com/media/f1b961_5e027a0d94d749e99ad76830129b42da~mv2.png",
        "prompt_color": "wild honey ombré, brown roots melting into warm honey blonde ends",
        "hair_type": "ombre",
        "emoji": "🍯",
    },
    {
        "id": "noisette-ombre-platine",
        "name": "Genius Vivian Noisette Ombré Platine #5AT60",
        "shade": "#5AT60",
        "color_name": "Noisette Ombré Platine",
        "color_desc": "ombré noisette vers platine",
        "price": "359,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-ssd-série-vivian-ombré-blond-cendré-5at60",
        "image_url": "https://static.wixstatic.com/media/f1b961_5cab009ec1a64e689baa767cbf3bcb8e~mv2.jpg",
        "prompt_color": "hazelnut brown roots fading to platinum blonde ends, dramatic ombré",
        "hair_type": "ombre",
        "emoji": "🌙",
    },
    {
        "id": "espresso-balayage-glace",
        "name": "Genius Vivian Espresso Balayage Glacé #2BTP18/1006",
        "shade": "#2BTP18/1006",
        "color_name": "Espresso Balayage Glacé",
        "color_desc": "espresso avec balayage glacé",
        "price": "354,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-sdd-série-vivian-ombré-2btp18-1006",
        "image_url": "https://static.wixstatic.com/media/f1b961_75316de55cf441ecb82211cbc8d91010~mv2.jpg",
        "prompt_color": "dark espresso brown with icy blonde balayage highlights, cool-toned dimension",
        "hair_type": "balayage",
        "emoji": "🧊",
    },
    {
        "id": "noisette-balayage-cendre",
        "name": "Genius Vivian Noisette Balayage Cendré #5ATP18B62",
        "shade": "#5ATP18B62",
        "color_name": "Noisette Balayage Cendré",
        "color_desc": "noisette avec balayage cendré",
        "price": "349,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-5atp18b62",
        "image_url": "https://static.wixstatic.com/media/f1b961_0e7cf48e1d59418bbf1b562c21494176~mv2.jpg",
        "prompt_color": "hazelnut brown with ash blonde balayage highlights, dimensional cool tones",
        "hair_type": "balayage",
        "emoji": "🌿",
    },
    {
        "id": "chatain-soyeux-chengtu",
        "name": "Genius Vivian Châtain Soyeux #CHENGTU",
        "shade": "#CHENGTU",
        "color_name": "Châtain Soyeux",
        "color_desc": "châtain soyeux premium",
        "price": "359,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-chengtu",
        "image_url": "https://static.wixstatic.com/media/f1b961_302097ceefaf4f69a608838f489b57a2~mv2.jpg",
        "prompt_color": "silky chestnut brown, luxurious medium brown with natural shine",
        "hair_type": "brunette",
        "emoji": "👑",
    },
    {
        "id": "foochow",
        "name": "Genius Vivian FOOCHOW #FOOCHOW",
        "shade": "#FOOCHOW",
        "color_name": "FOOCHOW",
        "color_desc": "brun naturel asiatique premium",
        "price": "359,95 $CA",
        "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-foochow",
        "image_url": "https://static.wixstatic.com/media/f1b961_1d56319f8a3c4e4dba09ce1c80385fbc~mv2.jpg",
        "prompt_color": "natural Asian dark brown, silky dark brown with subtle warm tones",
        "hair_type": "brunette",
        "emoji": "🌸",
    },
]


# ============================================
# 🎬 MISES EN SCÈNE QUÉBÉCOISES (20 variétés)
# ============================================

SCENES = [
    # MONTRÉAL
    {
        "name": "Rooftop Montréal",
        "desc": "at a chic Montreal downtown rooftop terrace during golden hour sunset, city skyline with Mount Royal in soft background",
        "season": "summer",
    },
    {
        "name": "Vieux-Port Montréal",
        "desc": "walking along Montreal's Old Port waterfront at sunset, historic Bonsecours Market dome visible, romantic evening light",
        "season": "summer",
    },
    {
        "name": "Café Plateau",
        "desc": "at a trendy Plateau Mont-Royal café terrace, iconic colorful spiral staircases visible, bohemian Montreal vibes",
        "season": "summer",
    },
    {
        "name": "Mont-Royal Belvédère",
        "desc": "at the Kondiaronk Belvedere on Mount Royal, breathtaking panoramic view of Montreal skyline at golden hour",
        "season": "fall",
    },
    {
        "name": "Quartier des Spectacles",
        "desc": "in Montreal's Quartier des Spectacles at twilight, colorful light installations in background, urban chic atmosphere",
        "season": "summer",
    },
    
    # QUÉBEC CITY
    {
        "name": "Château Frontenac",
        "desc": "on the Dufferin Terrace with majestic Château Frontenac castle in background, romantic Quebec City golden hour",
        "season": "all",
    },
    {
        "name": "Petit Champlain",
        "desc": "on charming cobblestone Petit Champlain street, oldest commercial district in North America, European fairy-tale atmosphere",
        "season": "all",
    },
    {
        "name": "Grande Allée",
        "desc": "on a lively Grande Allée terrace in Quebec City, Victorian mansions and festive 5 à 7 atmosphere",
        "season": "summer",
    },
    {
        "name": "Plaines d'Abraham",
        "desc": "at the Plains of Abraham park with panoramic Quebec City and St. Lawrence River view, golden autumn light",
        "season": "fall",
    },
    
    # CHARLEVOIX
    {
        "name": "Manoir Richelieu",
        "desc": "at the luxurious Fairmont Le Manoir Richelieu terrace, stunning Charlevoix mountains and St. Lawrence River view",
        "season": "summer",
    },
    {
        "name": "Baie-Saint-Paul",
        "desc": "in the artistic village of Baie-Saint-Paul, charming art galleries and Charlevoix mountains backdrop",
        "season": "fall",
    },
    {
        "name": "Spa Charlevoix",
        "desc": "at a luxury Charlevoix spa infinity pool, serene mountain landscape, wellness retreat atmosphere",
        "season": "all",
    },
    
    # LAURENTIDES
    {
        "name": "Village Tremblant",
        "desc": "in the colorful European-style pedestrian village of Mont-Tremblant, boutiques and gondola visible",
        "season": "all",
    },
    {
        "name": "Lac Tremblant",
        "desc": "on a private dock at Lac Tremblant, crystal clear water reflecting mountains, luxury cottage country",
        "season": "summer",
    },
    {
        "name": "Scandinave Spa",
        "desc": "at the Scandinave Spa Mont-Tremblant, outdoor Nordic baths with forest and mountain view, steam rising",
        "season": "winter",
    },
    
    # CANTONS-DE-L'EST
    {
        "name": "Vignoble Estrie",
        "desc": "at a Quebec Eastern Townships vineyard during golden hour, rolling hills, grapevines, wine country sophistication",
        "season": "fall",
    },
    {
        "name": "Spa Eastman",
        "desc": "at the holistic Spa Eastman terrace, zen garden and Appalachian mountains view, wellness sanctuary",
        "season": "all",
    },
    {
        "name": "North Hatley",
        "desc": "at a charming Victorian inn in North Hatley, Lake Massawippi view, English village elegance",
        "season": "summer",
    },
    
    # AUTRES
    {
        "name": "Îles-de-la-Madeleine",
        "desc": "on the dramatic red sandstone cliffs of Îles-de-la-Madeleine, turquoise water, wild wind in hair, island paradise",
        "season": "summer",
    },
    {
        "name": "Gaspésie Percé",
        "desc": "with the iconic Percé Rock in background, dramatic Gaspésie coastline at sunset, quintessential Quebec landmark",
        "season": "summer",
    },
]


# ============================================
# 📝 TEMPLATES DE POSTS (variété)
# ============================================

POST_TEMPLATES = [
    # Template 1: Coup de coeur
    """{emoji} COUP DE CŒUR | {name}

La teinte {color_name} qui fait sensation! 😍

🎨 Teinte: {color_name} ({shade})
💰 Prix: {price}

✅ Cheveux 100% Remy naturels
✅ Trame ultra-fine invisible  
✅ Brillance et volume garantis

{color_desc_cap} - Une couleur qui vous sublime!

🛒 COMMANDEZ ICI 👇
{url}

📍 Luxura Distribution - St-Georges, Beauce
🚚 Livraison rapide partout au Québec

#LuxuraDistribution #GeniusWeft #{hashtag} #ExtensionsQuebec""",

    # Template 2: Produit vedette
    """🌟 PRODUIT VEDETTE | {name}

{emoji} La teinte {color_name} fait fureur au Québec!

📌 Collection: Série Vivian
📌 Teinte: {shade}
📌 Prix: {price}

Un {color_desc} qui illumine votre visage et fait tourner les têtes!

👉 ACHETEZ MAINTENANT:
{url}

📍 Luxura Distribution
🚚 Livraison 1-2 jours au Québec

#LuxuraDistribution #GeniusWeft #TransformationCapillaire #Quebec""",

    # Template 3: Question engagement
    """💭 Vous rêvez de cheveux {color_desc}?

Découvrez le {name}! {emoji}

🏷️ {price}
🎨 Teinte: {color_name}

Ce que nos clientes adorent:
• Trame invisible ultra-fine
• Cheveux 100% Remy premium
• Durée 3-4 mois
• Confort absolu

🛍️ MAGASINEZ:
{url}

Quelle est VOTRE teinte préférée? 👇

#LuxuraDistribution #GeniusWeft #SondageBeauté #ExtensionsCheveux""",

    # Template 4: Nouveau look
    """✂️ NOUVEAU LOOK | {name}

{emoji} Transformez-vous avec le {color_name}!

🎨 {shade} - {color_desc_cap}
💰 Seulement {price}

Pourquoi nos clientes l'adorent:
✨ Couleur naturelle parfaite
✨ Volume instantané  
✨ Qualité salon premium

🔗 DÉCOUVREZ:
{url}

#LuxuraDistribution #GeniusWeft #NouveauLook #BeautéQuebec""",

    # Template 5: Best-seller
    """🏆 BEST-SELLER | {name}

{emoji} Notre teinte {color_name} est LA préférée des Québécoises!

✅ {color_desc_cap}
✅ Cheveux Remy 100% naturels
✅ Trame Genius ultra-discrète

💰 {price}

👉 OBTENEZ LE VÔTRE:
{url}

📍 Luxura Distribution - Qualité premium
🚚 Livraison express au Québec

#LuxuraDistribution #GeniusWeft #BestSeller #CheveuxDeReve""",
]


def get_random_product():
    """Sélectionne un produit aléatoire."""
    return random.choice(PRODUCTS)


def get_random_scene():
    """Sélectionne une mise en scène aléatoire."""
    return random.choice(SCENES)


def generate_image(product, scene):
    """Génère l'image avec Grok - cheveux EXACTEMENT comme le produit."""
    if not XAI_API_KEY:
        log("❌ XAI_API_KEY manquant")
        return None
    
    prompt = f"""Real photograph of a glamorous Québec woman in her early 30s {scene['desc']}.

HAIR COLOR (MANDATORY - MUST MATCH EXACTLY):
{product['prompt_color']}

HAIR LENGTH - THIS IS THE MOST IMPORTANT RULE:
⚠️ HAIR MUST BE SHOULDER-LENGTH TO MID-BACK MAXIMUM ⚠️
- Hair ends at BRA-STRAP level (middle of back)
- Hair is ABOVE the waist - NOT touching waist
- Hair is SHORT OF the hips - nowhere near hips
- Hair length is approximately 18-20 inches from scalp
- DO NOT generate long mermaid hair
- DO NOT generate hair past the waist
- DO NOT generate hair reaching hips or thighs
- Think "medium-long" NOT "ultra-long"

CORRECT LENGTH: Hair tips end between shoulder blades and waist.
WRONG LENGTH: Hair going to waist, hips, thighs, or knees.

Hair style: Soft waves, voluminous, healthy shine

Woman: Québécoise 30s, elegant casual attire, confident smile, golden hour lighting.

The hair showcases {product['color_name']} shade. Professional photography.
No text, no watermarks."""

    log(f"🎨 Génération image: {product['color_name']} @ {scene['name']}")
    
    try:
        response = requests.post(
            "https://api.x.ai/v1/images/generations",
            headers={"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "grok-imagine-image", "prompt": prompt, "n": 1},
            timeout=120
        )
        
        if response.status_code == 200:
            url = response.json()["data"][0]["url"]
            log(f"✅ Image générée!")
            return url
        else:
            log(f"❌ Erreur Grok: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Exception: {e}")
        return None


def generate_post_text(product):
    """Génère le texte du post avec un template aléatoire et identifiant."""
    template = random.choice(POST_TEMPLATES)
    
    # Créer le hashtag à partir du nom de couleur
    hashtag = product['color_name'].replace(' ', '').replace('é', 'e').replace('è', 'e').replace('ô', 'o')
    
    text = template.format(
        emoji=product['emoji'],
        name=product['name'],
        color_name=product['color_name'],
        shade=product['shade'],
        price=product['price'],
        url=product['url'],
        color_desc=product['color_desc'],
        color_desc_cap=product['color_desc'].capitalize(),
        hashtag=hashtag,
    )
    
    # Ajouter identifiant pour traçabilité
    return f"{text}\n📌 LUX-DAILY-18H"


def post_to_facebook(message, image_url):
    """Publie sur Facebook."""
    if not FB_PAGE_ACCESS_TOKEN:
        log("❌ FB_PAGE_ACCESS_TOKEN manquant")
        return False
    
    log("📘 Publication sur Facebook...")
    
    try:
        response = requests.post(
            f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos",
            data={
                "url": image_url,
                "caption": message,
                "published": "true",
                "access_token": FB_PAGE_ACCESS_TOKEN
            },
            timeout=60
        )
        
        result = response.json()
        
        if "error" in result:
            log(f"❌ Erreur: {result['error'].get('message')}")
            return False
        
        post_id = result.get("id") or result.get("post_id")
        log(f"✅ Publié! Post ID: {post_id}")
        return True
        
    except Exception as e:
        log(f"❌ Exception: {e}")
        return False


def main():
    log("=" * 60)
    log("🛍️ LUXURA DAILY PRODUCT CRON - 18H00")
    log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # Vérifier les clés
    log(f"\n🔑 Clés configurées:")
    log(f"   XAI_API_KEY: {'✅' if XAI_API_KEY else '❌'}")
    log(f"   FB_PAGE_ACCESS_TOKEN: {'✅' if FB_PAGE_ACCESS_TOKEN else '❌'}")
    log(f"   WIX_API_KEY: {'✅' if WIX_API_KEY else '⚠️ (images non sauvegardées)'}")
    log(f"   DATABASE_URL: {'✅' if DATABASE_URL else '⚠️ (métadonnées non sauvées)'}")
    
    # 1. Sélection aléatoire
    product = get_random_product()
    scene = get_random_scene()
    
    log(f"\n📦 Produit: {product['name']}")
    log(f"🎨 Couleur: {product['color_name']}")
    log(f"💰 Prix: {product['price']}")
    log(f"🎬 Scène: {scene['name']}")
    
    # 2. Générer l'image avec Grok
    log("")
    grok_image_url = generate_image(product, scene)
    
    if not grok_image_url:
        log("❌ Échec génération image")
        sys.exit(1)
    
    # 3. SAUVEGARDER DANS WIX MEDIA MANAGER
    log("")
    log("🖼️ Sauvegarde de l'image dans Wix...")
    final_image_url = save_image_sync(grok_image_url, product, scene)
    
    if final_image_url.startswith("https://static.wixstatic.com"):
        log(f"✅ Image permanente Wix prête!")
    else:
        log(f"⚠️ Utilisation de l'URL Grok temporaire")
    
    # 4. Générer le texte
    post_text = generate_post_text(product)
    log(f"\n📝 Post généré ({len(post_text)} chars)")
    
    # 5. Publier sur Facebook (avec l'URL Wix permanente!)
    log("")
    success = post_to_facebook(post_text, final_image_url)
    
    log("\n" + "=" * 60)
    if success:
        log("✅ PUBLICATION RÉUSSIE!")
        log(f"   📦 {product['name']}")
        log(f"   🎬 {scene['name']}")
        log(f"   🔗 {product['url']}")
        log(f"   🖼️ Image: {final_image_url[:60]}...")
    else:
        log("❌ PUBLICATION ÉCHOUÉE")
    log("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
