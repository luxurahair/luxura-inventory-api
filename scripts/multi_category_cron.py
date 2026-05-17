#!/usr/bin/env python3
"""
🛍️ LUXURA MULTI-CATEGORY CRON - 4 Publications/jour aux meilleures heures
==========================================================================
Publie 4 posts par jour, un de chaque catégorie d'extensions:
- GENIUS WEFT (Trame invisible) → 18h00
- HALO (Fil invisible, 2 min d'installation) → 12h00
- I-TIP (Microbilles, cheveux russes premium) → 20h30
- TAPE (Bande adhésive) → 07h30

HEURES OPTIMALES POUR FEMMES QUÉBÉCOISES 20-45 ANS:
📱 07h30 - Réveil/café, scroll matinal
📱 12h00 - Pause lunch
📱 18h00 - Retour maison, détente
📱 20h30 - Prime time soirée

DURÉE DE VIE CORRIGÉE:
✅ Toutes les extensions: 8+ MOIS (selon entretien)
✅ Remontage requis: aux 4-8 semaines (croissance cheveux)
✅ Halo: Pas de remontage, s'installe en 2 minutes

Configuration Render Cron Jobs:
  1. halo-12h:      0 16 * * *  python scripts/multi_category_cron.py halo
  2. genius-18h:    0 22 * * *  python scripts/multi_category_cron.py genius
  3. itip-2030:     30 0 * * *  python scripts/multi_category_cron.py itip   (lendemain UTC)
  4. tape-0730:     30 11 * * * python scripts/multi_category_cron.py tape
"""

import os
import sys
import random
import requests
import asyncio
import uuid
from datetime import datetime

# Ajouter le chemin backend
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
BACKEND_DIR = os.path.join(ROOT_DIR, 'backend')
sys.path.insert(0, BACKEND_DIR)

# Charger les variables d'environnement depuis TOUS les fichiers .env
from dotenv import load_dotenv

# 1. Charger .secrets.env (clés API principales)
secrets_env = os.path.join(ROOT_DIR, '.secrets.env')
if os.path.exists(secrets_env):
    load_dotenv(secrets_env)
    print(f"[LUXURA] ✅ Secrets chargés depuis .secrets.env")

# 2. Charger backend/.env (override si nécessaire)
backend_env = os.path.join(BACKEND_DIR, '.env')
if os.path.exists(backend_env):
    load_dotenv(backend_env, override=True)
    print(f"[LUXURA] ✅ Variables chargées depuis backend/.env")

# Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip()
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "1838415193042352")
WIX_API_KEY = os.getenv("WIX_API_KEY", "").strip()
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def log(msg):
    print(f"[LUXURA] {datetime.now().strftime('%H:%M:%S')} {msg}")


# ============================================
# 🖼️ SAUVEGARDE IMAGES DANS WIX
# ============================================

async def save_to_wix(grok_url: str, product: dict, scene: dict, category: str) -> str:
    """Sauvegarde l'image dans Wix Media Manager."""
    import httpx
    
    if not WIX_API_KEY or not WIX_SITE_ID:
        log("⚠️ Clés Wix manquantes - URL Grok utilisée")
        return grok_url
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        scene_slug = scene['name'].lower().replace(' ', '-').replace("'", "")
        file_name = f"luxura-{category}-{product['id']}-{scene_slug}-{timestamp}-{uuid.uuid4().hex[:4]}.jpg"
        
        log(f"📤 Upload Wix: {file_name}")
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
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
                    "filePath": f"/luxura-ai-{category}/{file_name}"
                }
            )
            
            if resp.status_code in (200, 201):
                file_id = resp.json().get("file", {}).get("id") or resp.json().get("id")
                if file_id:
                    # Attendre READY
                    for _ in range(30):
                        check = await client.get(
                            f"https://www.wixapis.com/site-media/v1/files/{file_id}",
                            headers={"Authorization": WIX_API_KEY, "wix-site-id": WIX_SITE_ID}
                        )
                        if check.status_code == 200:
                            if check.json().get("file", {}).get("operationStatus") == "READY":
                                wix_url = f"https://static.wixstatic.com/media/{file_id}"
                                log(f"✅ Sauvegardé dans Wix!")
                                return wix_url
                        await asyncio.sleep(1)
                    return f"https://static.wixstatic.com/media/{file_id}"
            
            log(f"⚠️ Erreur Wix {resp.status_code}")
            return grok_url
            
    except Exception as e:
        log(f"⚠️ Exception Wix: {e}")
        return grok_url


def save_to_wix_sync(grok_url: str, product: dict, scene: dict, category: str) -> str:
    """Wrapper synchrone."""
    try:
        return asyncio.run(save_to_wix(grok_url, product, scene, category))
    except:
        return grok_url


# ============================================
# 📦 CATALOGUES PAR CATÉGORIE
# ============================================

# GENIUS WEFT - Trame invisible (Collection Vivian)
GENIUS_PRODUCTS = [
    {"id": "genius-chocolat-dc", "name": "Genius Vivian Chocolat Profond #DC", "shade": "#DC", "color_name": "Chocolat Profond", "color_desc": "brun chocolat riche", "price": "249,95 $CA", "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-dark-chocolate-dc", "prompt_color": "dark chocolate brown, rich deep cocoa", "emoji": "🍫"},
    {"id": "genius-caramel-6", "name": "Genius Vivian Caramel Doré #6", "shade": "#6", "color_name": "Caramel Doré", "color_desc": "caramel doré lumineux", "price": "269,95 $CA", "url": "https://www.luxuradistribution.com/product-page/genius-série-vivian-brun-lumineux-blond-foncé-6", "prompt_color": "golden caramel, warm honey blonde", "emoji": "🍯"},
    {"id": "genius-platine-60a", "name": "Genius Vivian Platine Pur #60A", "shade": "#60A", "color_name": "Platine Pur", "color_desc": "blond platine lumineux", "price": "269,95 $CA", "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-blond-platine-60a", "prompt_color": "pure platinum blonde, icy white", "emoji": "💎"},
    {"id": "genius-chataigne-3", "name": "Genius Vivian Châtaigne Douce #3", "shade": "#3", "color_name": "Châtaigne Douce", "color_desc": "châtain doux naturel", "price": "279,95 $CA", "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-brun-moyen-3", "prompt_color": "soft chestnut brown, medium natural", "emoji": "🌰"},
    {"id": "genius-golden-hour", "name": "Genius Vivian Golden Hour #6/24", "shade": "#6/24", "color_name": "Golden Hour", "color_desc": "balayage doré lumineux", "price": "289,95 $CA", "url": "https://www.luxuradistribution.com/product-page/genius-trame-invisible-série-vivian-balayage-blond-foncé-6-24", "prompt_color": "dark blonde with golden highlights", "emoji": "🌅"},
    {"id": "genius-miel-ombre", "name": "Genius Vivian Miel Sauvage Ombré #CB", "shade": "#CB", "color_name": "Miel Sauvage Ombré", "color_desc": "ombré miel sauvage", "price": "319,95 $CA", "url": "https://www.luxuradistribution.com/product-page/genius-série-vivian-ombré-blond-miel-cb", "prompt_color": "brown roots to honey blonde ends", "emoji": "🍯"},
]

# HALO - Fil invisible, 2 minutes d'installation (Collection Everly)
HALO_PRODUCTS = [
    {"id": "halo-noir-soie-1b", "name": "Halo Everly Noir Soie #1B", "shade": "#1B", "color_name": "Noir Soie", "color_desc": "noir soyeux naturel", "price": "239,95 $CA", "url": "https://www.luxuradistribution.com/product-page/halo-série-everly-noir-doux-brun-foncé-1b", "prompt_color": "soft black, natural dark brown-black", "emoji": "🖤"},
    {"id": "halo-chataigne-3", "name": "Halo Everly Châtaigne Douce #3", "shade": "#3", "color_name": "Châtaigne Douce", "color_desc": "châtain doux et naturel", "price": "239,95 $CA", "url": "https://www.luxuradistribution.com/product-page/halo-série-everly-brun-moyen-3", "prompt_color": "soft chestnut brown", "emoji": "🌰"},
    {"id": "halo-caramel-6", "name": "Halo Everly Caramel Doré #6", "shade": "#6", "color_name": "Caramel Doré", "color_desc": "caramel doré lumineux", "price": "239,95 $CA", "url": "https://www.luxuradistribution.com/product-page/halo-série-everly-brun-lumineux-blond-foncé-6", "prompt_color": "golden caramel, dark blonde", "emoji": "🍯"},
    {"id": "halo-platine-60a", "name": "Halo Everly Platine Pur #60A", "shade": "#60A", "color_name": "Platine Pur", "color_desc": "blond platine pur", "price": "279,95 $CA", "url": "https://www.luxuradistribution.com/product-page/halo-série-everly-blond-platine-60a", "prompt_color": "pure platinum blonde, icy", "emoji": "💎"},
    {"id": "halo-golden-hour", "name": "Halo Everly Golden Hour #6/24", "shade": "#6/24", "color_name": "Golden Hour", "color_desc": "balayage doré", "price": "279,95 $CA", "url": "https://www.luxuradistribution.com/product-page/halo-série-everly-balayage-blond-foncé-6-24", "prompt_color": "dark blonde golden balayage", "emoji": "🌅"},
    {"id": "halo-champagne-18-22", "name": "Halo Everly Champagne Doré #18/22", "shade": "#18/22", "color_name": "Champagne Doré", "color_desc": "blond champagne élégant", "price": "279,95 $CA", "url": "https://www.luxuradistribution.com/product-page/halo-série-everly-balayage-blond-beige-18-22", "prompt_color": "champagne blonde, beige blonde", "emoji": "🥂"},
    {"id": "halo-miel-ombre", "name": "Halo Everly Miel Sauvage Ombré #CB", "shade": "#CB", "color_name": "Miel Sauvage Ombré", "color_desc": "ombré miel sauvage", "price": "299,95 $CA", "url": "https://www.luxuradistribution.com/product-page/halo-série-everly-ombré-blond-miel-cb", "prompt_color": "brown to honey blonde ombre", "emoji": "🍯"},
]

# I-TIP - Microbilles, cheveux russes premium (Collection Eleanor)
ITIP_PRODUCTS = [
    {"id": "itip-noir-soie-1b", "name": "I-Tip Eleanor Noir Soie #1B", "shade": "#1B", "color_name": "Noir Soie", "color_desc": "noir soyeux premium", "price": "89,95 $CA", "url": "https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-brun-foncé-noir-doux-1b", "prompt_color": "soft black, silky dark", "emoji": "🖤"},
    {"id": "itip-chataigne-3", "name": "I-Tip Eleanor Châtaigne Douce #3", "shade": "#3", "color_name": "Châtaigne Douce", "color_desc": "châtain doux premium", "price": "89,95 $CA", "url": "https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-brun-moyen-3", "prompt_color": "soft chestnut brown", "emoji": "🌰"},
    {"id": "itip-caramel-6", "name": "I-Tip Eleanor Caramel Doré #6", "shade": "#6", "color_name": "Caramel Doré", "color_desc": "caramel doré luxueux", "price": "89,95 $CA", "url": "https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-brun-lumineux-blond-foncé-6", "prompt_color": "golden caramel", "emoji": "🍯"},
    {"id": "itip-platine-60a", "name": "I-Tip Eleanor Platine Pur #60A", "shade": "#60A", "color_name": "Platine Pur", "color_desc": "blond platine premium", "price": "104,95 $CA", "url": "https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-blond-platine-60a", "prompt_color": "pure platinum blonde", "emoji": "💎"},
    {"id": "itip-diamant-glace", "name": "I-Tip Eleanor Diamant Glacé #613/18A", "shade": "#613/18A", "color_name": "Diamant Glacé", "color_desc": "blond diamant glacé", "price": "104,95 $CA", "url": "https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-balayage-blond-cendré-613-18a", "prompt_color": "icy diamond blonde with ash", "emoji": "❄️"},
    {"id": "itip-miel-ombre", "name": "I-Tip Eleanor Miel Sauvage Ombré #CB", "shade": "#CB", "color_name": "Miel Sauvage Ombré", "color_desc": "ombré miel premium", "price": "119,95 $CA", "url": "https://www.luxuradistribution.com/product-page/i-tips-série-eleanor-ombré-blond-miel-cb", "prompt_color": "brown to honey ombre", "emoji": "🍯"},
]

# TAPE - Bande adhésive (Collection Aurora)
TAPE_PRODUCTS = [
    {"id": "tape-chocolat-dc", "name": "Tape Aurora Chocolat Profond #DC", "shade": "#DC", "color_name": "Chocolat Profond", "color_desc": "brun chocolat riche", "price": "84,95 $CA", "url": "https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-dark-chocolate-dc", "prompt_color": "dark chocolate brown, rich cocoa", "emoji": "🍫"},
    {"id": "tape-noir-1", "name": "Tape Aurora Onyx Noir #1", "shade": "#1", "color_name": "Onyx Noir", "color_desc": "noir onyx intense", "price": "84,95 $CA", "url": "https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-noir-foncé-1-jet-black", "prompt_color": "jet black, onyx", "emoji": "🖤"},
    {"id": "tape-caramel-6", "name": "Tape Aurora Caramel Doré #6", "shade": "#6", "color_name": "Caramel Doré", "color_desc": "caramel doré", "price": "84,95 $CA", "url": "https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-brun-lumineux-blond-foncé-6", "prompt_color": "golden caramel", "emoji": "🍯"},
    {"id": "tape-chataigne-3", "name": "Tape Aurora Châtaigne Douce #3", "shade": "#3", "color_name": "Châtaigne Douce", "color_desc": "châtain doux", "price": "84,95 $CA", "url": "https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-brun-moyen-3", "prompt_color": "soft chestnut brown", "emoji": "🌰"},
    {"id": "tape-platine-60a", "name": "Tape Aurora Platine Pur #60A", "shade": "#60A", "color_name": "Platine Pur", "color_desc": "blond platine", "price": "99,95 $CA", "url": "https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-blond-platine-60a", "prompt_color": "pure platinum blonde", "emoji": "💎"},
    {"id": "tape-diamant-glace", "name": "Tape Aurora Diamant Glacé #613/18A", "shade": "#613/18A", "color_name": "Diamant Glacé", "color_desc": "blond diamant", "price": "99,95 $CA", "url": "https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-balayage-blond-cendré-613-18a", "prompt_color": "icy diamond blonde", "emoji": "❄️"},
    {"id": "tape-miel-ombre", "name": "Tape Aurora Miel Sauvage Ombré #CB", "shade": "#CB", "color_name": "Miel Sauvage Ombré", "color_desc": "ombré miel", "price": "109,95 $CA", "url": "https://www.luxuradistribution.com/product-page/bande-adhésive-série-aurora-ombré-blond-miel-cb", "prompt_color": "brown to honey ombre", "emoji": "🍯"},
]


# ============================================
# 🎬 SCÈNES QUÉBÉCOISES
# ============================================

SCENES = [
    # 🍸 BARS & COCKTAILS - 5 à 7 entre copines
    {"name": "Cocktail Bar", "desc": "with her best girlfriend at a trendy Montreal cocktail bar, both holding fancy drinks, dim romantic lighting, chic lounge atmosphere"},
    {"name": "5 à 7 Copines", "desc": "at happy hour (5 à 7) with two girlfriends at a stylish downtown bar, laughing together, cocktails on table, warm ambient lighting"},
    {"name": "Rooftop Lounge", "desc": "with her friend at a glamorous Montreal rooftop lounge at sunset, champagne glasses, city skyline backdrop, VIP atmosphere"},
    {"name": "Wine Bar", "desc": "at an upscale wine bar with a close friend, elegant wine glasses, sophisticated decor, intimate conversation moment"},
    
    # 🍣 RESTAURANTS CHIC
    {"name": "Sushi Bar", "desc": "at a trendy Montreal sushi restaurant with friends, modern Japanese decor, enjoying omakase experience, elegant ambiance"},
    {"name": "Steakhouse", "desc": "at a high-end Quebec steakhouse with her girlfriend, leather booths, warm lighting, celebrating a special occasion"},
    {"name": "Terrasse Restaurant", "desc": "at an upscale Old Montreal restaurant terrace with friends, al fresco dining, string lights, evening atmosphere"},
    {"name": "Brunch Chic", "desc": "at a trendy brunch spot with girlfriends, mimosas on table, bright modern interior, weekend vibes"},
    
    # 🎉 SORTIES & NIGHTLIFE
    {"name": "Girls Night", "desc": "on a girls night out with two friends at a chic Montreal nightclub lounge, VIP booth, glamorous setting"},
    {"name": "Bachelorette", "desc": "at a bachelorette party with friends, festive atmosphere, champagne toast, stylish venue"},
    {"name": "Birthday Dinner", "desc": "celebrating a birthday dinner with close friends at an elegant restaurant, candles, joyful moment"},
    {"name": "After Work", "desc": "at an after-work gathering with colleagues at a trendy bar, relaxed professional atmosphere, end of day drinks"},
]


# ============================================
# 📝 INFOS PRODUITS PAR CATÉGORIE
# ============================================

CATEGORY_INFO = {
    "genius": {
        "name": "Genius Weft",
        "collection": "Série Vivian",
        "type": "Trame invisible ultra-fine",
        "install_time": "pose en salon (45-60 min)",
        "lifespan": "8+ mois avec entretien",
        "maintenance": "remontage aux 4-8 semaines",
        "highlight": "La trame la plus discrète du marché",
        "base_url": "https://www.luxuradistribution.com/genius",
        "guide_image": None,  # Pas de guide spécifique
    },
    "halo": {
        "name": "Halo",
        "collection": "Série Everly",
        "type": "Fil invisible à clipser",
        "install_time": "s'installe en 2 MINUTES",
        "lifespan": "8+ mois avec entretien",
        "maintenance": "aucun remontage requis - clipser/déclipper!",
        "highlight": "Volume instantané sans engagement",
        "base_url": "https://www.luxuradistribution.com/halo",
        "guide_image": "https://static.wixstatic.com/media/f1b961_ab68d2899ded456b8bb7599e972621fa~mv2.jpeg",  # Guide installation
    },
    "itip": {
        "name": "I-Tip",
        "collection": "Série Eleanor",
        "type": "Pose microbilles - Cheveux russes premium",
        "install_time": "pose en salon (2-3h)",
        "lifespan": "8+ mois avec entretien",
        "maintenance": "remontage aux 4-8 semaines",
        "highlight": "Cheveux russes de très haute qualité",
        "base_url": "https://www.luxuradistribution.com/i-tip",
        "guide_image": None,
    },
    "tape": {
        "name": "Tape-in",
        "collection": "Série Aurora",
        "type": "Bande adhésive discrète",
        "install_time": "pose en salon (30-45 min)",
        "lifespan": "8+ mois avec entretien",
        "maintenance": "remontage aux 4-8 semaines",
        "highlight": "La pose la plus rapide en salon",
        "base_url": "https://www.luxuradistribution.com/tape",
        "guide_image": None,
    },
}


def get_products_for_category(category: str):
    """Retourne les produits de la catégorie."""
    return {
        "genius": GENIUS_PRODUCTS,
        "halo": HALO_PRODUCTS,
        "itip": ITIP_PRODUCTS,
        "tape": TAPE_PRODUCTS,
    }.get(category, GENIUS_PRODUCTS)


def generate_image(product: dict, scene: dict, category: str) -> str:
    """Génère l'image avec Grok."""
    if not XAI_API_KEY:
        log("❌ XAI_API_KEY manquant")
        return None
    
    info = CATEGORY_INFO[category]
    
    prompt = f"""Real photograph of glamorous Québec women in their early 30s {scene['desc']}.

SCENE REQUIREMENT:
- Show 2-3 girlfriends together enjoying the moment
- Social, fun, luxurious atmosphere
- Natural interaction between friends

HAIR COLOR FOR MAIN SUBJECT (MANDATORY):
{product['prompt_color']}
- Other women can have different hair colors

HAIR LENGTH - THIS IS THE MOST IMPORTANT RULE:
⚠️ ALL WOMEN: HAIR MUST BE SHOULDER-LENGTH TO MID-BACK MAXIMUM ⚠️
- Hair ends at BRA-STRAP level (middle of back)
- Hair is ABOVE the waist - NOT touching waist
- Hair is SHORT OF the hips - nowhere near hips
- DO NOT generate long mermaid hair
- DO NOT generate hair past the waist

Hair style: Soft waves, voluminous, healthy shine, glamorous styling

Setting: Upscale, trendy, Quebec nightlife/restaurant scene
Lighting: Warm ambient, flattering
Mood: Fun, confident, aspirational, social

The hair showcases {product['color_name']} shade.
Professional lifestyle photography.
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
            return response.json()["data"][0]["url"]
        else:
            log(f"❌ Erreur Grok: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Exception: {e}")
        return None


def generate_post_text(product: dict, category: str) -> str:
    """
    Génère le texte du post - FORMAT COURT (2-3 lignes max).
    Référence: Publication "PLACEMENT DES EXTENSIONS" de Luxura.
    Inclut un identifiant pour traçabilité.
    """
    info = CATEGORY_INFO[category]
    
    # Identifiants par catégorie pour traçabilité
    CRON_IDS = {
        "halo": "LUX-HALO-12H",
        "genius": "LUX-GENIUS-18H",
        "itip": "LUX-ITIP-2030",
        "tape": "LUX-TAPE-0730"
    }
    cron_id = CRON_IDS.get(category, "LUX-MULTI")
    
    # Templates COURTS par catégorie
    if category == "halo":
        templates = [
            f"""{product['emoji']} HALO | {product['color_name']}

Volume instantané en 2 MINUTES. Fil invisible, aucun outil requis. Clipser le matin, retirer le soir.

{product['url']}

#LuxuraDistribution #Halo #Quebec
📌 {cron_id}""",
            
            f"""{product['emoji']} HALO EVERLY | {product['shade']}

S'installe en 2 minutes chrono. Zéro dommage, résultat immédiat. Durée de vie: 8+ mois.

{product['url']}

#LuxuraDistribution #HaloExtensions #Quebec
📌 {cron_id}""",
        ]
    elif category == "itip":
        templates = [
            f"""{product['emoji']} I-TIP | {product['color_name']}

Cheveux russes premium. Pose microbilles ultra-discrète. Durée de vie: 8+ mois.

{product['url']}

#LuxuraDistribution #ITip #Quebec
📌 {cron_id}""",
            
            f"""{product['emoji']} I-TIP ELEANOR | {product['shade']}

Pose mèche par mèche pour un résultat ultra-naturel. Cheveux russes 100% naturels.

{product['url']}

#LuxuraDistribution #Microbilles #Quebec
📌 {cron_id}""",
        ]
    elif category == "tape":
        templates = [
            f"""{product['emoji']} TAPE-IN | {product['color_name']}

La pose la plus rapide en salon (30-45 min). Bande adhésive ultra-discrète. Durée: 8+ mois.

{product['url']}

#LuxuraDistribution #TapeIn #Quebec
📌 {cron_id}""",
            
            f"""{product['emoji']} TAPE AURORA | {product['shade']}

Idéal cheveux fins à moyens. Pose rapide, résultat naturel. Remontage aux 4-8 semaines.

{product['url']}

#LuxuraDistribution #BandeAdhésive #Quebec
📌 {cron_id}""",
        ]
    else:  # genius
        templates = [
            f"""{product['emoji']} GENIUS WEFT | {product['color_name']}

Trame invisible ultra-fine (0.78mm). Cheveux 100% Remy naturels. Durée de vie: 8+ mois.

{product['url']}

#LuxuraDistribution #GeniusWeft #Quebec
📌 {cron_id}""",
            
            f"""{product['emoji']} GENIUS VIVIAN | {product['shade']}

La trame la plus discrète du marché. Coupe sans effilochage. Le choix des professionnelles.

{product['url']}

#LuxuraDistribution #TrameInvisible #Quebec
📌 {cron_id}""",
        ]
    
    return random.choice(templates)


def post_to_facebook(message: str, image_url: str) -> bool:
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


def main(category: str):
    """Point d'entrée principal."""
    if category not in CATEGORY_INFO:
        log(f"❌ Catégorie invalide: {category}")
        log("   Catégories valides: genius, halo, itip, tape")
        sys.exit(1)
    
    info = CATEGORY_INFO[category]
    
    log("=" * 60)
    log(f"🛍️ LUXURA {info['name'].upper()} - Publication automatique")
    log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # 1. Sélection aléatoire
    products = get_products_for_category(category)
    product = random.choice(products)
    scene = random.choice(SCENES)
    
    log(f"\n📦 Catégorie: {info['name']} ({info['collection']})")
    log(f"🎨 Produit: {product['name']}")
    log(f"💰 Prix: {product['price']}")
    log(f"🎬 Scène: {scene['name']}")
    log(f"⏱️ {info['install_time']}")
    log(f"📆 Durée: {info['lifespan']}")
    
    # 2. Générer l'image
    log("")
    grok_image_url = generate_image(product, scene, category)
    
    if not grok_image_url:
        log("❌ Échec génération image")
        sys.exit(1)
    
    # 3. SAUVEGARDER DANS WIX MEDIA MANAGER
    log("")
    log("🖼️ Sauvegarde dans Wix Media Manager...")
    final_image_url = save_to_wix_sync(grok_image_url, product, scene, category)
    
    # 4. Générer le texte
    post_text = generate_post_text(product, category)
    log(f"\n📝 Post généré ({len(post_text)} chars)")
    
    # 5. Publier sur Facebook
    log("")
    success = post_to_facebook(post_text, final_image_url)
    
    log("\n" + "=" * 60)
    if success:
        log("✅ PUBLICATION RÉUSSIE!")
        log(f"   📦 {info['name']}: {product['name']}")
        log(f"   🔗 {product['url']}")
        log(f"   🖼️ Image Wix: {final_image_url[:60]}...")
    else:
        log("❌ PUBLICATION ÉCHOUÉE")
    log("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python multi_category_cron.py <category>")
        print("Categories: genius, halo, itip, tape")
        print("\nHoraires optimaux femmes QC 20-45 ans:")
        print("  07h30 - Tape (scroll matinal)")
        print("  12h00 - Halo (pause lunch)")
        print("  18h00 - Genius (retour maison)")
        print("  20h30 - I-Tip (prime time soirée)")
        sys.exit(1)
    
    main(sys.argv[1])
