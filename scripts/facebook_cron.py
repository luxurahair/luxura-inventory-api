#!/usr/bin/env python3
"""
LUXURA FACEBOOK CRON v2 - AVEC IMAGES
=====================================
Cron pour publier sur Facebook AVEC des images générées par AI.

Fonctionnement:
1. Détermine le type de post selon le calendrier éditorial
2. Génère une image avec OpenAI DALL-E
3. Upload l'image pour obtenir une URL publique
4. Publie sur Facebook avec texte + image

Configuration Render:
  - Build Command: pip install requests openai pillow
  - Start Command: python scripts/facebook_cron.py
  - Schedule: Selon le type de post

Variables d'environnement requises:
  - API_URL: URL de l'API Luxura
  - OPENAI_API_KEY: Pour générer les images DALL-E
  - FB_PAGE_ACCESS_TOKEN: Token Facebook
  - FB_PAGE_ID: ID de la page Facebook
"""

import os
import sys
import json
import base64
import requests
from datetime import datetime
from typing import Optional, Dict, Tuple

# Configuration
API_URL = os.getenv("API_URL", "https://luxura-inventory-api.onrender.com").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("EMERGENT_LLM_KEY")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "1838415193042352")
FB_API_VERSION = "v25.0"

# Type de post (passé en argument ou déterminé automatiquement)
POST_TYPE = os.getenv("POST_TYPE", "auto")  # educational, product, weekend, auto


def log(msg):
    """Log avec timestamp"""
    print(f"[FB CRON] {datetime.now().strftime('%H:%M:%S')} {msg}")


# =====================================================
# CALENDRIER ÉDITORIAL FACEBOOK
# =====================================================

FACEBOOK_SCHEDULE = {
    "educational": {
        "days": ["monday", "wednesday", "friday"],
        "hour": 12,
        "description": "Posts éducatifs sur les extensions"
    },
    "product": {
        "days": ["tuesday", "thursday"],
        "hour": 19,
        "description": "Posts produits avec photos"
    },
    "weekend": {
        "days": ["saturday", "sunday"],
        "hour": 10,
        "description": "Posts lifestyle/inspiration weekend"
    }
}

# Templates de contenu
CONTENT_TEMPLATES = {
    "educational": [
        {
            "title": "Comment choisir la bonne longueur d'extensions",
            "text": """✨ GUIDE | Comment choisir la bonne longueur d'extensions?

📏 Voici nos conseils:

• 14-16 pouces: Look naturel, parfait pour le quotidien
• 18-20 pouces: Longueur mi-dos, polyvalent et élégant  
• 22-24 pouces: Effet glamour, idéal pour les occasions
• 26+ pouces: Look dramatique, pour les audacieuses!

💡 Astuce: Mesurez de votre nuque jusqu'où vous voulez que vos cheveux arrivent!

🚚 Livraison rapide partout au Québec
📍 Luxura Distribution - St-Georges, Beauce

#LuxuraDistribution #ExtensionsCheveux #ConseilsBeauté #Quebec #Coiffure""",
            "image_prompt": "Professional hair salon photography showing different hair extension lengths on elegant mannequin heads, from short to very long, clean white background, premium beauty brand aesthetic, soft lighting, no text"
        },
        {
            "title": "Entretien de vos extensions",
            "text": """💆‍♀️ CONSEILS | Comment prendre soin de vos extensions?

🌟 Routine d'entretien essentielle:

1️⃣ Brossez délicatement AVANT le lavage
2️⃣ Utilisez un shampooing sans sulfate
3️⃣ Appliquez un revitalisant sur les longueurs
4️⃣ Séchez à l'air libre ou température basse
5️⃣ Dormez avec une tresse légère

⏰ Résultat: Extensions qui durent 12+ mois!

📍 Luxura Distribution - Qualité premium
🚚 Livraison partout au Québec

#LuxuraDistribution #SoinsCheveux #Extensions #BeautéQuebec""",
            "image_prompt": "Flatlay photography of premium hair care products with hair brush and silk scrunchie, elegant feminine aesthetic, soft pink and white tones, luxury beauty brand style, no text, no logos"
        },
        {
            "title": "Différence entre Tape-in et Genius Weft",
            "text": """🤔 COMPARATIF | Tape-in VS Genius Weft

Quelle méthode choisir?

📌 TAPE-IN (Bande adhésive):
• Pose rapide (45 min)
• Idéal cheveux fins
• Repositionnable
• Durée: 6-8 semaines

📌 GENIUS WEFT:
• Ultra-plat et invisible
• Cheveux Remy 100%
• Confort maximal
• Durée: 3-4 mois

💡 Notre conseil: Consultez votre styliste Luxura pour le meilleur choix!

📍 6+ salons partenaires au Québec

🔗 https://luxuradistribution.com

#LuxuraDistribution #TapeIn #GeniusWeft #ExtensionsQuebec""",
            "image_prompt": "comparison_v1"
        },
        {
            "title": "Tape-in ou Genius Weft - Le guide",
            "text": """💇‍♀️ GUIDE EXPERT | Tape-in ou Genius Weft?

On vous aide à choisir!

✂️ TAPE-IN - Parfait si vous voulez:
• Changer de look souvent (réajustable)
• Pose salon rapide
• Budget accessible
• Cheveux plus fins

🌟 GENIUS WEFT - L'idéal si:
• Vous cherchez la discrétion absolue
• Cheveux plus épais
• Moins de visites salon
• Investissement long terme

🎯 Le verdict? Les deux sont excellents - ça dépend de VOS besoins!

💬 Questions? Écrivez-nous en privé!

🔗 https://luxuradistribution.com

#LuxuraDistribution #Comparatif #Extensions #Quebec""",
            "image_prompt": "comparison_v2"
        },
        {
            "title": "Battle des extensions: Tape vs Weft",
            "text": """⚔️ BATTLE | Tape-in VS Genius Weft

Le match que vous attendiez! 🥊

🏆 TAPE-IN remporte si:
• Vos cheveux sont fins/délicats
• Vous aimez changer de style souvent
• Budget: 💰💰
• Entretien: toutes les 6-8 sem

🏆 GENIUS WEFT gagne si:
• Vous voulez du volume MAXIMAL
• Vous préférez moins de rendez-vous
• Budget: 💰💰💰
• Entretien: tous les 3-4 mois

🤝 Ex æquo: Les deux utilisent des cheveux 100% Remy de qualité supérieure!

📞 Besoin d'aide pour choisir? On est là!

🔗 https://luxuradistribution.com

#LuxuraDistribution #TapeIn #GeniusWeft #ExtensionsCheveux""",
            "image_prompt": "comparison_v3"
        }
    ],
    "product": [
        {
            "title": "Genius Weft - Notre best-seller",
            "text": """✨ PRODUIT VEDETTE | Genius Weft Série Vivian

🌟 Pourquoi c'est notre #1:
• Cheveux 100% Remy russes
• Ultra-plat - invisible même cheveux fins
• Cuticules alignées = zéro emmêlement
• 10+ teintes naturelles disponibles

💰 Qualité salon à prix distributeur
🚚 Livraison 1-2 jours au Québec

👉 DM pour commander ou trouver un salon partenaire!

#LuxuraDistribution #GeniusWeft #Vivian #ExtensionsPremium #Quebec""",
            "image_prompt": "Luxury hair extensions product photography, beautiful long flowing hair extensions in natural brown tones, silk fabric background, premium beauty brand aesthetic, soft studio lighting, elegant and sophisticated, no text"
        },
        {
            "title": "Collection Halo - Série Everly",
            "text": """💫 NOUVEAUTÉ | Collection Halo - Série Everly

Le secret d'un volume instantané!

✅ Installation en 2 minutes
✅ Aucun dommage à vos cheveux
✅ Réutilisable à l'infini
✅ Parfait pour cheveux fins

🎨 Disponible en 15+ teintes
📦 Livraison express Québec

Transformez votre look en un instant! ✨

#LuxuraDistribution #HaloExtensions #Everly #VolumeInstant #BeautéQuebec""",
            "image_prompt": "Beautiful woman from behind showing long flowing hair extensions, natural wavy hair, golden hour lighting, lifestyle beauty photography, Quebec autumn scenery in background blur, elegant and aspirational, no face visible, no text"
        }
    ],
    "weekend": [
        # SAMEDI - Rotation variée (Self-care, Brunch, Shopping, Nature)
        {
            "title": "Self-Care Saturday",
            "text": """🌸 SELF-CARE SATURDAY

Parce que vous méritez de vous sentir belle!

Ce weekend, prenez soin de vous:
• Un masque capillaire nourrissant
• Un moment rien que pour vous

💕 La beauté commence par se sentir bien.

#LuxuraDistribution #SelfCare #BeautéQuebec
📌 LUX-EDITORIAL""",
            "image_prompt": "Single glamorous woman relaxing at luxurious spa, wearing white robe, beautiful mid-back length hair, serene expression, soft lighting, peaceful atmosphere, Quebec spa resort setting, no text"
        },
        {
            "title": "Brunch Glam",
            "text": """☕ BRUNCH GOALS

Le weekend parfait commence par un bon brunch et des cheveux parfaits!

Où allez-vous bruncher ce weekend? 👇

#LuxuraDistribution #BrunchQuebec #WeekendVibes
📌 LUX-EDITORIAL""",
            "image_prompt": "Single elegant woman at trendy Montreal brunch cafe, sitting alone at table, beautiful mid-back hair catching morning light, casual chic outfit, coffee and croissant, urban Quebec aesthetic, no text"
        },
        {
            "title": "Shopping Day",
            "text": """🛍️ SHOPPING DAY

Un look parfait pour une journée shopping au centre-ville!

Quel est votre quartier préféré pour magasiner? 👇

#LuxuraDistribution #ShoppingQuebec #MontréalStyle
📌 LUX-EDITORIAL""",
            "image_prompt": "Single stylish woman walking on Rue Sainte-Catherine Montreal, shopping bags, beautiful mid-back flowing hair, chic urban outfit, sunny day, city lifestyle photography, no text"
        },
        {
            "title": "Nature Escape",
            "text": """🌲 NATURE ESCAPE

Cheveux au vent dans la nature québécoise!

Quel est votre coin de nature préféré? 👇

#LuxuraDistribution #NatureQuebec #PleinAir
📌 LUX-EDITORIAL""",
            "image_prompt": "Single woman hiking in Laurentian mountains Quebec, mid-back length hair flowing in breeze, athletic casual wear, scenic forest backdrop, golden hour, adventurous spirit, no text"
        },
        # DIMANCHE - Rotation variée (Transformation, Detente, Preparation semaine)
        {
            "title": "Transformation Sunday",
            "text": """🦋 TRANSFORMATION SUNDAY

Nouvelle semaine, nouveau look?

De cheveux fins à volume spectaculaire... La magie des extensions! ✨

Quel look rêvez-vous d'essayer? 👇

#LuxuraDistribution #Transformation #Quebec
📌 LUX-EDITORIAL""",
            "image_prompt": "BEFORE AND AFTER hair transformation, split image concept, left side showing thin short hair, right side showing voluminous mid-back length hair, same woman from behind, salon setting, dramatic difference, no text"
        },
        {
            "title": "Lazy Sunday",
            "text": """☀️ LAZY SUNDAY

Le dimanche parfait: pyjama, café, cheveux détachés.

Comment passez-vous votre dimanche? 👇

#LuxuraDistribution #LazySunday #Détente
📌 LUX-EDITORIAL""",
            "image_prompt": "Single woman in cozy home setting, Sunday morning vibes, wearing comfortable loungewear, beautiful natural mid-back hair, reading book near window, soft morning light, Quebec home interior, no text"
        },
        {
            "title": "Sunday Prep",
            "text": """💼 PREP YOUR WEEK

Dimanche = préparation pour une semaine réussie!

Cheveux parfaits, confiance maximale. 💪

#LuxuraDistribution #SundayPrep #ConfidenceBoost
📌 LUX-EDITORIAL""",
            "image_prompt": "Single professional woman styling her mid-back length hair in mirror, getting ready for the week, modern bathroom or vanity setting, confident expression, natural light, aspirational mood, no text"
        },
        {
            "title": "Sunset Vibes",
            "text": """🌅 SUNSET VIBES

Profiter du coucher de soleil avec des cheveux parfaits.

Quel est votre spot préféré pour admirer le sunset? 👇

#LuxuraDistribution #SunsetQuebec #GoldenHour
📌 LUX-EDITORIAL""",
            "image_prompt": "Single woman watching sunset at Old Port Montreal, silhouette with beautiful mid-back hair flowing, romantic golden hour lighting, waterfront setting, peaceful and dreamy atmosphere, no text"
        },
        {
            "title": "Yoga & Wellness",
            "text": """🧘‍♀️ MIND, BODY, HAIR

Le bien-être commence de l'intérieur.

Prenez soin de vous ce weekend! 🙏

#LuxuraDistribution #Wellness #YogaQuebec
📌 LUX-EDITORIAL""",
            "image_prompt": "Single woman doing yoga outdoors in Quebec park, athletic wear, beautiful mid-back ponytail, morning light, peaceful zen atmosphere, healthy lifestyle aesthetic, no text"
        },
        {
            "title": "Marché Weekend",
            "text": """🍎 MARCHÉ DU WEEKEND

Rien de mieux qu'un tour au marché local!

Quel est votre marché préféré? Jean-Talon? Atwater? 👇

#LuxuraDistribution #MarchéQuebec #LocalLove
📌 LUX-EDITORIAL""",
            "image_prompt": "Single woman shopping at Jean-Talon Market Montreal, beautiful mid-back hair, casual summer dress, browsing fresh produce, vibrant market atmosphere, authentic Quebec lifestyle, no text"
        }
    ]
}


def get_montreal_hour():
    """Retourne l'heure à Montréal"""
    utc_hour = datetime.utcnow().hour
    utc_month = datetime.utcnow().month
    offset = -4 if 3 <= utc_month <= 10 else -5
    return (utc_hour + offset) % 24


def get_current_day():
    """Retourne le jour en anglais"""
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return days[datetime.utcnow().weekday()]


def determine_post_type() -> str:
    """Détermine le type de post selon le jour"""
    day = get_current_day()
    
    for post_type, config in FACEBOOK_SCHEDULE.items():
        if day in config["days"]:
            return post_type
    
    return "educational"  # Default


def get_content_for_type(post_type: str) -> Dict:
    """
    Retourne le contenu approprié pour le type de post.
    Utilise une rotation basée sur la SEMAINE de l'année pour plus de diversité.
    """
    templates = CONTENT_TEMPLATES.get(post_type, CONTENT_TEMPLATES["educational"])
    
    # Rotation basée sur la semaine de l'année + jour (pour diversité maximale)
    week_of_year = datetime.now().isocalendar()[1]  # Semaine 1-52
    day_of_week = datetime.now().weekday()  # 0-6
    
    # Combine semaine + jour pour une rotation unique
    rotation_index = (week_of_year * 7 + day_of_week) % len(templates)
    
    log(f"📅 Rotation: Semaine {week_of_year}, Jour {day_of_week} → Template #{rotation_index + 1}/{len(templates)}")
    
    return templates[rotation_index]


def generate_image_prompt_from_text(post_text: str, post_type: str) -> str:
    """
    Génère un prompt d'image à partir du contenu du post Facebook.
    Utilise OpenAI pour créer un prompt contextuel.
    """
    if not OPENAI_API_KEY:
        # Fallback: prompt générique
        return f"Professional hair extensions photography, beautiful long flowing hair, premium beauty brand aesthetic, luxury salon setting, soft lighting, no text, no logos"
    
    log(f"🤖 Génération du prompt image à partir du texte...")
    
    system_prompt = """Tu es un expert en création de prompts pour DALL-E.
Tu dois créer un prompt d'image basé sur le contenu d'un post Facebook pour Luxura Distribution (extensions capillaires premium au Québec).

RÈGLES IMPORTANTES:
1. L'image doit être PERTINENTE au contenu du post
2. Style: photographie professionnelle de beauté/lifestyle
3. Pas de texte ni de logo dans l'image
4. Pas de visage clairement identifiable (pour éviter les problèmes)
5. Focus sur: cheveux, extensions, ambiance salon, ou lifestyle beauté
6. Couleurs: tons chauds, élégants, premium
7. Format: paysage (1792x1024)

Retourne UNIQUEMENT le prompt en anglais, sans explication."""

    user_prompt = f"""Crée un prompt DALL-E pour illustrer ce post Facebook:

TYPE DE POST: {post_type}

CONTENU DU POST:
{post_text[:1000]}

Génère un prompt d'image qui capture l'essence et le contexte de ce post."""

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 300
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            prompt = data["choices"][0]["message"]["content"].strip()
            log(f"✅ Prompt généré: {prompt[:100]}...")
            return prompt
        else:
            log(f"⚠️ Erreur génération prompt, utilisation fallback")
            return f"Professional hair extensions photography, beautiful long flowing hair, premium beauty brand aesthetic, luxury salon setting, soft lighting, elegant woman with gorgeous hair from behind, no text"
            
    except Exception as e:
        log(f"⚠️ Erreur: {e}, utilisation prompt fallback")
        return f"Professional hair extensions photography, beautiful long flowing hair, premium beauty brand aesthetic, luxury salon setting, soft lighting, no text"


def generate_image_grok(post_type: str, image_prompt_key: str = None) -> Optional[str]:
    """
    Génère une image avec GROK et les prompts v3 Ultra-Glamour.
    TOUJOURS des femmes glamour, JAMAIS des produits sur table.
    
    Args:
        post_type: educational, product, weekend
        image_prompt_key: Clé spécifique du prompt (comparison_v1, comparison_v2, etc.)
    """
    xai_api_key = os.getenv("XAI_API_KEY")
    if not xai_api_key:
        log("❌ XAI_API_KEY non configuré")
        return None
    
    log(f"🎨 Génération image GROK v3 Ultra-Glamour...")
    
    # === PROMPTS VARIÉS POUR LES COMPARATIFS ===
    COMPARISON_PROMPTS = [
        # v1: Salon professionnel
        "Real photograph of a professional hairstylist in an elegant Quebec salon showing hair extension samples to a client, warm wooden interior, both women with gorgeous long hair, soft professional lighting, authentic consultation moment, no text",
        # v2: Transformation miroir  
        "Real photograph of a glamorous woman admiring her new long voluminous hair extensions in a luxurious salon mirror, golden hour lighting through window, elegant reflection shot, Quebec City skyline visible, no text",
        # v3: Terrasse Montréal
        "Real photograph of two stylish girlfriends on a chic Montreal rooftop terrace at sunset, both showing off their stunning hair extensions, one with tape-in the other with weft, golden hour light, city skyline background, no text",
        # v4: Comparaison côte à côte naturelle
        "Real photograph from behind of two elegant women walking arm in arm on a cobblestone street in Old Montreal, showing their different hair extension styles, one slightly wavy one straight, golden autumn light, no text",
        # v5: Spa Charlevoix
        "Real photograph of a relaxed woman at a Charlevoix spa terrace touching her beautiful long hair extensions, mountain view in background, soft natural lighting, serene atmosphere, no text"
    ]
    
    # === PROMPTS GÉNÉRAUX VARIÉS - FEMME SEULE, LIEUX VARIÉS ===
    GENERAL_PROMPTS = [
        # Lifestyle urbain
        "Real photograph of single elegant woman walking down Grande Allée Quebec City at golden hour, stunning mid-back hair flowing behind her, chic summer dress, historic architecture backdrop",
        "Real photograph of single stylish woman at a trendy Montreal cafe terrace, beautiful mid-back hair extensions, enjoying coffee alone, European city vibes, soft natural lighting",
        "Real photograph of single confident woman shopping on Rue Saint-Denis Montreal, beautiful mid-back hair, casual chic outfit, authentic urban lifestyle moment",
        # Nature/Outdoor
        "Real photograph of single woman at Mont-Tremblant lookout point, mid-back hair caught in mountain breeze, athletic casual wear, stunning autumn foliage backdrop",
        "Real photograph of single woman on a peaceful morning walk along Vieux-Port Montreal, mid-back hair gently moving, casual elegant style, water and city skyline",
        "Real photograph of single woman doing yoga in a Quebec park at sunrise, mid-back ponytail, athletic wear, serene peaceful atmosphere",
        # Spa/Wellness
        "Real photograph of single woman at a luxury Charlevoix spa, white robe, touching her beautiful mid-back hair, mountain view through window, serene atmosphere",
        "Real photograph of single woman in cozy home setting brushing her mid-back hair near window, Sunday morning vibes, soft natural light, peaceful moment",
        # Social/Events
        "Real photograph of single elegant woman at an outdoor wine tasting in Quebec wine country, gorgeous mid-back hair, sophisticated casual style, warm afternoon light",
        "Real photograph of single glamorous woman at a Montreal art gallery opening, stunning mid-back hair, elegant black dress, modern art backdrop",
        # Seasonal
        "Real photograph of single woman walking through autumn leaves in Parc Mont-Royal, mid-back hair flowing, cozy fall fashion, golden hour lighting",
        "Real photograph of single woman at a summer terrasse in Old Montreal, mid-back hair catching sunset light, relaxed elegant style, cobblestone street visible"
    ]
    
    # Sélectionner le prompt approprié
    if image_prompt_key and image_prompt_key.startswith("comparison_"):
        # Utiliser un prompt de comparaison spécifique
        version = image_prompt_key.split("_")[1]  # v1, v2, v3
        version_index = {"v1": 0, "v2": 1, "v3": 2, "v4": 3, "v5": 4}.get(version, 0)
        base_prompt = COMPARISON_PROMPTS[version_index % len(COMPARISON_PROMPTS)]
        log(f"   📊 Utilisation prompt comparaison: {version}")
    else:
        # Import des prompts v3 Luxura ou fallback sur prompts généraux variés
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
            from app.services.luxura_image_prompts import get_preset_prompt
            
            preset_mapping = {
                "educational": "educational",
                "product": "product",
                "weekend": "weekend"
            }
            preset = preset_mapping.get(post_type, "product")
            base_prompt = get_preset_prompt(preset)
            
        except Exception as e:
            log(f"⚠️ Import prompts échoué, utilisation prompts variés: {e}")
            # Rotation basée sur le jour pour variété
            day_index = datetime.now().day % len(GENERAL_PROMPTS)
            base_prompt = GENERAL_PROMPTS[day_index]
    
    # Ajouter la contrainte de longueur des cheveux - RÈGLE ULTRA-STRICTE
    hair_constraint = """HAIR LENGTH - THIS IS THE MOST IMPORTANT RULE:
⚠️ HAIR MUST BE SHOULDER-LENGTH TO MID-BACK MAXIMUM ⚠️
Hair ends at BRA-STRAP level (middle of back).
Hair is ABOVE the waist - NOT touching waist.
Hair is SHORT OF the hips - nowhere near hips.
DO NOT generate long mermaid hair.
DO NOT generate hair past the waist.
DO NOT generate hair reaching hips or thighs.
CORRECT: Hair tips end between shoulder blades and waist.
WRONG: Hair going to waist, hips, thighs, or knees."""
    prompt = f"{base_prompt} {hair_constraint} No text, no watermarks, no logos."
    
    log(f"   Prompt: {prompt[:100]}...")
    
    try:
        response = requests.post(
            "https://api.x.ai/v1/images/generations",
            headers={
                "Authorization": f"Bearer {xai_api_key}",
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
            data = response.json()
            image_url = data["data"][0]["url"]
            log(f"✅ Image GROK générée!")
            return image_url
        else:
            log(f"❌ Erreur GROK: {response.status_code}")
            log(response.text[:300])
            return None
            
    except Exception as e:
        log(f"❌ Erreur génération: {e}")
        return None


def post_to_facebook(message: str, image_url: Optional[str] = None) -> bool:
    """
    Publie sur Facebook avec ou sans image.
    Ajoute automatiquement l'identifiant LUX-EDITORIAL pour traçabilité.
    """
    if not FB_PAGE_ACCESS_TOKEN:
        log("❌ FB_PAGE_ACCESS_TOKEN non configuré")
        return False
    
    # Ajouter identifiant pour traçabilité
    message_with_id = f"{message}\n📌 LUX-EDITORIAL"
    
    log(f"📘 Publication Facebook...")
    
    try:
        if image_url:
            # Post avec image (photo)
            log(f"   Avec image: {image_url[:50]}...")
            response = requests.post(
                f"https://graph.facebook.com/{FB_API_VERSION}/{FB_PAGE_ID}/photos",
                data={
                    "url": image_url,
                    "caption": message_with_id,
                    "access_token": FB_PAGE_ACCESS_TOKEN
                },
                timeout=60
            )
        else:
            # Post texte seul
            log(f"   Sans image (texte seul)")
            response = requests.post(
                f"https://graph.facebook.com/{FB_API_VERSION}/{FB_PAGE_ID}/feed",
                data={
                    "message": message_with_id,
                    "access_token": FB_PAGE_ACCESS_TOKEN
                },
                timeout=60
            )
        
        result = response.json()
        
        if "error" in result:
            error = result["error"]
            log(f"❌ Erreur Facebook: {error.get('message')}")
            if error.get("code") == 190:
                log("   ⚠️ Token expiré! Mettez à jour FB_PAGE_ACCESS_TOKEN")
            return False
        
        post_id = result.get("id") or result.get("post_id")
        log(f"✅ Publié! Post ID: {post_id}")
        log(f"   🔗 https://facebook.com/{FB_PAGE_ID}")
        return True
        
    except Exception as e:
        log(f"❌ Erreur publication: {e}")
        return False


def main():
    """Point d'entrée principal"""
    log("=" * 60)
    log("🚀 LUXURA FACEBOOK CRON v2 - AVEC IMAGES")
    log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log(f"🕐 Heure Montréal: {get_montreal_hour()}h")
    log(f"📆 Jour: {get_current_day().capitalize()}")
    log("=" * 60)
    
    # Vérifier les variables
    log(f"🔑 OPENAI_API_KEY: {'✅' if OPENAI_API_KEY else '❌'}")
    log(f"🔑 FB_PAGE_ACCESS_TOKEN: {'✅' if FB_PAGE_ACCESS_TOKEN else '❌'}")
    log(f"🔑 FB_PAGE_ID: {FB_PAGE_ID}")
    
    # Déterminer le type de post
    if POST_TYPE == "auto":
        post_type = determine_post_type()
    else:
        post_type = POST_TYPE
    
    log(f"")
    log(f"📋 Type de post: {post_type.upper()}")
    log(f"   {FACEBOOK_SCHEDULE.get(post_type, {}).get('description', '')}")
    
    # Récupérer le contenu
    content = get_content_for_type(post_type)
    log(f"")
    log(f"📝 Titre: {content['title']}")
    
    # Générer l'image avec GROK et prompts v3 Ultra-Glamour
    # TOUJOURS des femmes glamour, JAMAIS des produits sur table
    # Passe la clé du prompt d'image si disponible (pour les comparatifs notamment)
    log(f"")
    image_prompt_key = content.get("image_prompt")
    image_url = generate_image_grok(post_type, image_prompt_key)
    
    # Publier sur Facebook
    log(f"")
    success = post_to_facebook(content["text"], image_url)
    
    log(f"")
    log("=" * 60)
    if success:
        log("✅ PUBLICATION RÉUSSIE!")
    else:
        log("❌ PUBLICATION ÉCHOUÉE")
    log("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
