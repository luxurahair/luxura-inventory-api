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

#LuxuraDistribution #TapeIn #GeniusWeft #ExtensionsQuebec""",
            "image_prompt": "Split comparison image showing two types of hair extensions side by side, tape-in extensions on left and weft extensions on right, clean professional product photography, white background, beauty industry aesthetic, no text"
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
        {
            "title": "Inspiration Weekend",
            "text": """🌸 INSPIRATION WEEKEND

Parce que vous méritez de vous sentir belle chaque jour! ✨

Ce weekend, prenez soin de vous:
• Un masque capillaire nourrissant
• Une coiffure qui vous fait sourire
• Un moment rien que pour vous

💕 La beauté commence par se sentir bien dans sa peau.

Bon weekend les beautés! 🥰

📍 Luxura Distribution - Pour des cheveux de rêve

#LuxuraDistribution #WeekendVibes #SelfCare #BeautéQuebec #Inspiration""",
            "image_prompt": "Relaxing self-care scene with woman brushing beautiful long hair near window, soft natural morning light, cozy bedroom aesthetic, lifestyle photography, peaceful and feminine atmosphere, no face clearly visible, no text"
        },
        {
            "title": "Transformation du dimanche",
            "text": """🦋 TRANSFORMATION SUNDAY

Nouvelle semaine, nouveau look? 

Nos clientes nous inspirent chaque jour avec leurs transformations incroyables!

De cheveux fins à volume spectaculaire...
La magie des extensions Luxura! ✨

💭 Quel look rêvez-vous d'essayer?
Dites-nous en commentaire! 👇

#LuxuraDistribution #Transformation #AvantAprès #ExtensionsCheveux #Quebec""",
            "image_prompt": "Dramatic before and after hair transformation concept, split image showing thin hair transforming to voluminous long hair, artistic beauty photography, elegant salon setting, inspirational and aspirational mood, no text"
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
    """Retourne le contenu approprié pour le type de post"""
    templates = CONTENT_TEMPLATES.get(post_type, CONTENT_TEMPLATES["educational"])
    # Rotation basée sur le jour du mois
    day = datetime.now().day
    return templates[day % len(templates)]


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


def generate_image_grok(post_type: str) -> Optional[str]:
    """
    Génère une image avec GROK et les prompts v3 Ultra-Glamour.
    TOUJOURS des femmes glamour, JAMAIS des produits sur table.
    """
    xai_api_key = os.getenv("XAI_API_KEY")
    if not xai_api_key:
        log("❌ XAI_API_KEY non configuré")
        return None
    
    log(f"🎨 Génération image GROK v3 Ultra-Glamour...")
    
    # Import des prompts v3 Luxura
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from app.services.luxura_image_prompts import get_preset_prompt
        
        # Mapper le post_type vers le preset
        preset_mapping = {
            "educational": "educational",
            "product": "product",  # Utilise les prompts v3 avec FEMMES
            "weekend": "weekend"
        }
        preset = preset_mapping.get(post_type, "product")
        base_prompt = get_preset_prompt(preset)
        
    except Exception as e:
        log(f"⚠️ Import prompts échoué, utilisation fallback: {e}")
        base_prompt = "Real photograph of a glamorous woman on a luxury yacht deck at sunset, with voluminous thick hair extensions flowing in the breeze. Elegant white designer dress. Shot from 3/4 back angle. Golden hour lighting."
    
    # Ajouter la contrainte de longueur des cheveux
    hair_constraint = "Hair length MUST end at the natural waist level, approximately three-quarters down the back. Hair must NOT extend below the waist, NOT reach the hips or knees. This is critical."
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
    """
    if not FB_PAGE_ACCESS_TOKEN:
        log("❌ FB_PAGE_ACCESS_TOKEN non configuré")
        return False
    
    log(f"📘 Publication Facebook...")
    
    try:
        if image_url:
            # Post avec image (photo)
            log(f"   Avec image: {image_url[:50]}...")
            response = requests.post(
                f"https://graph.facebook.com/{FB_API_VERSION}/{FB_PAGE_ID}/photos",
                data={
                    "url": image_url,
                    "caption": message,
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
                    "message": message,
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
    log(f"")
    image_url = generate_image_grok(post_type)
    
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
