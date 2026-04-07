# app/routes/marketing.py
"""
🚀 LUXURA MARKETING AUTOMATION SYSTEM
======================================
Système complet d'automatisation marketing Meta/Facebook:
- Campagnes structurées (Vente directe / Salons affiliés / Awareness)
- Génération de créatifs (Feed 4:5 / Stories 9:16 / Reels)
- Génération vidéo AI avec Fal.ai
- Calendrier éditorial intelligent
- Templates de contenu non-répétitifs
- Intégration Meta Marketing API

Contrôle total depuis l'application Luxura.
"""

import os
import requests
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum

router = APIRouter(prefix="/marketing", tags=["Marketing Automation"])

# ==================== CONFIGURATION ====================

FB_PAGE_ID = os.getenv("FB_PAGE_ID", "1838415193042352")
FB_API_VERSION = "v25.0"
FB_BASE_URL = f"https://graph.facebook.com/{FB_API_VERSION}"
FAL_KEY = os.getenv("FAL_KEY", "")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID", "")


# ==================== ENUMS ====================

class OfferType(str, Enum):
    DIRECT_SALE = "direct_sale"
    SALON_AFFILIATE = "salon_affilie"
    AWARENESS = "awareness"

class ContentFormat(str, Enum):
    FEED_45 = "feed_4:5"
    STORY_916 = "story_9:16"
    REEL_916 = "reel_9:16"
    CAROUSEL = "carousel"

class ContentAngle(str, Enum):
    QUALITY_PREMIUM = "qualite_premium"
    IMPORTATEUR_DIRECT = "importateur_direct"
    TRANSFORMATION = "transformation"
    EFFET_NATUREL = "effet_naturel"
    DISPONIBILITE = "disponibilite"
    LUXE_CONFIANCE = "luxe_confiance"
    MARGE_PRO = "marge_pro"
    IMAGE_HAUT_GAMME = "image_haut_gamme"
    APPROVISIONNEMENT = "approvisionnement"
    DIFFERENCIATION = "differenciation"

class CampaignObjective(str, Enum):
    SALES = "OUTCOME_SALES"
    LEADS = "OUTCOME_LEADS"
    TRAFFIC = "OUTCOME_TRAFFIC"
    AWARENESS = "OUTCOME_AWARENESS"
    ENGAGEMENT = "OUTCOME_ENGAGEMENT"


# ==================== MODELS ====================

class ContentRequest(BaseModel):
    offer_type: OfferType
    angle: ContentAngle
    format: ContentFormat
    product_type: Optional[str] = "genius"
    color_name: Optional[str] = None
    salon_name: Optional[str] = None
    image_url: Optional[str] = None
    before_url: Optional[str] = None
    after_url: Optional[str] = None
    custom_hook: Optional[str] = None
    landing_url: Optional[str] = "https://www.luxuradistribution.com"

class VideoGenerationRequest(BaseModel):
    offer_type: OfferType
    format: ContentFormat  # story_9:16 ou feed_4:5
    image_url: str
    angle: ContentAngle
    include_logo: bool = True
    include_cta: bool = True
    duration: int = 15  # secondes

class CampaignCreateRequest(BaseModel):
    offer_type: OfferType
    name: str
    daily_budget: float = 20.0  # CAD
    objective: CampaignObjective = CampaignObjective.TRAFFIC

class AdSetCreateRequest(BaseModel):
    campaign_id: str
    name: str
    targeting_type: str  # broad, transformation, retargeting, salon_owner, indie_stylist
    daily_budget: float = 10.0

class AdCreateRequest(BaseModel):
    adset_id: str
    name: str
    creative_type: str  # video, image, carousel
    media_url: str
    primary_text: str
    headline: str
    cta: str = "SHOP_NOW"
    landing_url: str


# ==================== CONTENT TEMPLATES ====================

HOOKS = {
    OfferType.DIRECT_SALE: {
        ContentAngle.QUALITY_PREMIUM: [
            "Des rallonges premium, directement de l'importateur",
            "La qualité qui fait la différence",
            "Texture soyeuse. Rendu naturel. Qualité salon.",
            "Le luxe commence par la bonne fibre",
        ],
        ContentAngle.IMPORTATEUR_DIRECT: [
            "Importateur direct de rallonges capillaires premium",
            "Qualité salon, vente directe Luxura",
            "Des cheveux pro. Sans détour.",
            "Directement de l'importateur à vous",
        ],
        ContentAngle.TRANSFORMATION: [
            "Avant / après Luxura",
            "La différence se voit tout de suite",
            "Transformation réelle, résultat premium",
            "Une vraie transformation, pas une illusion",
        ],
        ContentAngle.EFFET_NATUREL: [
            "Un rendu si naturel qu'on n'y voit que du feu",
            "Impossible de faire la différence",
            "L'effet naturel que vous cherchiez",
            "Personne ne saura. Tout le monde remarquera.",
        ],
        ContentAngle.DISPONIBILITE: [
            "Livraison rapide partout au Québec",
            "Commandez aujourd'hui, recevez cette semaine",
            "Toujours en stock, toujours disponible",
            "Pas d'attente. Pas de rupture.",
        ],
        ContentAngle.LUXE_CONFIANCE: [
            "Le choix des femmes exigeantes",
            "Quand la qualité n'est pas négociable",
            "Pour celles qui n'acceptent que le meilleur",
            "La confiance d'une marque premium",
        ],
    },
    OfferType.SALON_AFFILIATE: {
        ContentAngle.MARGE_PRO: [
            "Accès prix pro exclusif",
            "Marge avantageuse pour votre salon",
            "Rentabilité premium garantie",
            "Votre marge, notre priorité",
        ],
        ContentAngle.IMAGE_HAUT_GAMME: [
            "Élevez l'image de votre salon",
            "Rejoignez le réseau Luxura",
            "Salon affilié = salon premium",
            "Montez d'un cran avec Luxura",
        ],
        ContentAngle.APPROVISIONNEMENT: [
            "Approvisionnement stable, qualité constante",
            "Fini les ruptures de stock",
            "Un partenaire fiable pour votre salon",
            "Votre salon mérite mieux qu'un fournisseur instable",
        ],
        ContentAngle.DIFFERENCIATION: [
            "Démarquez-vous de la concurrence",
            "Offrez ce que les autres n'ont pas",
            "L'avantage compétitif que vous cherchiez",
            "Exclusivité locale disponible",
        ],
    },
    OfferType.AWARENESS: {
        ContentAngle.LUXE_CONFIANCE: [
            "Luxura Distribution - L'excellence capillaire",
            "La référence premium au Québec",
            "Depuis 2020, la qualité ne change pas",
            "Découvrez pourquoi les salons nous font confiance",
        ],
    },
}

PRIMARY_TEXTS = {
    OfferType.DIRECT_SALE: {
        "default": """Découvrez Luxura, importateur de rallonges capillaires premium. Qualité professionnelle, rendu naturel et options adaptées aux femmes exigeantes.

✨ Cheveux 100% Remy russes
🎯 Cuticules alignées
💎 Résultat salon garanti
🚚 Livraison rapide au Québec""",
        
        "transformation": """La transformation qui parle d'elle-même.

Avec Luxura, vos rallonges offrent:
• Un rendu haut de gamme
• Une finition naturelle
• Une vraie présence visuelle

Voyez la différence par vous-même.""",
        
        "promo": """🔥 OFFRE SPÉCIALE

Qualité premium à prix accessible.
Importateur direct = pas d'intermédiaire = meilleur prix.

Profitez-en maintenant!""",
    },
    OfferType.SALON_AFFILIATE: {
        "default": """Vous êtes propriétaire de salon ou styliste?

Rejoignez Luxura et accédez à:
✅ Qualité importateur direct
✅ Marge avantageuse (jusqu'à 40%)
✅ Support marketing inclus
✅ Formation complète
✅ Stock en consignation possible

Déjà 25+ salons partenaires au Québec!""",
        
        "marge": """Augmentez votre rentabilité avec Luxura.

Accès direct importateur = meilleure marge.
Qualité constante = clientes satisfaites.
Support marketing = moins d'efforts.

C'est mathématique.""",
        
        "image": """Élevez l'image de votre salon.

Avec Luxura comme partenaire:
• Une marque premium reconnue
• Des produits qui parlent d'eux-mêmes
• Une différenciation claire

Vos clientes méritent le meilleur.""",
    },
}

HEADLINES = {
    OfferType.DIRECT_SALE: [
        "Qualité salon. Vente directe.",
        "Le luxe commence ici",
        "Importateur direct Québec",
        "Transformation garantie",
        "Des cheveux qui impressionnent",
    ],
    OfferType.SALON_AFFILIATE: [
        "Devenez salon affilié",
        "Accès pro Luxura",
        "Rejoignez le réseau",
        "Partenariat premium",
        "Salon partenaire recherché",
    ],
    OfferType.AWARENESS: [
        "Luxura Distribution",
        "L'excellence capillaire",
        "Importateur premium Québec",
    ],
}

CTA_MAP = {
    OfferType.DIRECT_SALE: "SHOP_NOW",
    OfferType.SALON_AFFILIATE: "LEARN_MORE",
    OfferType.AWARENESS: "LEARN_MORE",
}

VIDEO_STORYBOARDS = {
    OfferType.DIRECT_SALE: {
        ContentFormat.STORY_916: [
            {"time": "0-2s", "scene": "Hook text overlay", "visual": "Premium hair close-up texture"},
            {"time": "2-6s", "scene": "Product showcase", "visual": "Glossy hair movement, shine"},
            {"time": "6-10s", "scene": "Transformation/result", "visual": "Before/after or model reveal"},
            {"time": "10-13s", "scene": "Brand message", "visual": "Luxura logo + premium feel"},
            {"time": "13-15s", "scene": "CTA", "visual": "Commandez maintenant"},
        ],
        ContentFormat.FEED_45: [
            {"time": "0-3s", "scene": "Hook + brand intro", "visual": "Elegant opening, logo subtle"},
            {"time": "3-8s", "scene": "Problem/solution", "visual": "Hair transformation sequence"},
            {"time": "8-12s", "scene": "Product proof", "visual": "Texture detail, application"},
            {"time": "12-18s", "scene": "Social proof", "visual": "Client result, confidence"},
            {"time": "18-20s", "scene": "CTA", "visual": "Acheter maintenant + logo"},
        ],
    },
    OfferType.SALON_AFFILIATE: {
        ContentFormat.STORY_916: [
            {"time": "0-2s", "scene": "Hook B2B", "visual": "Professional salon environment"},
            {"time": "2-6s", "scene": "Offer intro", "visual": "Stylist working with extensions"},
            {"time": "6-10s", "scene": "Benefits", "visual": "Quality close-up, happy client"},
            {"time": "10-13s", "scene": "Brand credibility", "visual": "Luxura network showcase"},
            {"time": "13-15s", "scene": "CTA", "visual": "Demandez les conditions"},
        ],
        ContentFormat.FEED_45: [
            {"time": "0-3s", "scene": "B2B hook", "visual": "Premium salon atmosphere"},
            {"time": "3-8s", "scene": "Partnership benefits", "visual": "Professional application"},
            {"time": "8-14s", "scene": "Results showcase", "visual": "Client transformation"},
            {"time": "14-18s", "scene": "Credibility", "visual": "Network of salons"},
            {"time": "18-20s", "scene": "CTA", "visual": "Rejoignez Luxura"},
        ],
    },
}

FAL_PROMPTS = {
    OfferType.DIRECT_SALE: {
        ContentFormat.STORY_916: """Create a premium vertical social ad video (9:16 aspect ratio).

Brand: Luxura - Premium hair extension importer
Target: Women seeking luxury salon-quality hair extensions
Goal: Drive direct sales

Visual direction:
- Elegant, premium, modern beauty aesthetic
- Glossy healthy hair movement and shine
- Close-up texture shots showing quality
- Subtle camera movements (push-ins, slow pans)
- Clean luxury lighting (soft, flattering)
- Color palette: black, gold, soft neutrals
- NO chaotic transitions
- NO cheap influencer style
- NO watermarks or distorted elements

Style: Polished, luxurious, conversion-focused
Duration: 12-15 seconds""",
        
        ContentFormat.FEED_45: """Create a polished square/vertical video (4:5 aspect ratio) for Facebook/Instagram feed.

Brand: Luxura - Premium hair extensions
Focus: Direct importer quality, transformation results

Visual direction:
- Premium hair texture detail
- Natural shine and movement
- Upscale salon atmosphere
- Model confidence shots
- Slightly slower pacing than Stories
- Professional color grading

Style: Elegant, trustworthy, premium
Duration: 15-20 seconds""",
    },
    OfferType.SALON_AFFILIATE: {
        ContentFormat.STORY_916: """Create a vertical B2B social ad video (9:16) for salon professionals.

Brand: Luxura - Salon affiliate program
Target: Salon owners, hairstylists, beauty professionals
Goal: Generate partner leads

Visual direction:
- Upscale salon environment
- Professional stylist at work
- Premium hair extension application
- Business-confident tone
- Modern and polished, not flashy
- Black, gold, neutral luxury palette

Style: Professional, aspirational, B2B-focused
Duration: 12-15 seconds""",
        
        ContentFormat.FEED_45: """Create a 4:5 B2B video for salon professionals on Facebook feed.

Brand: Luxura - Professional partnership
Focus: Quality, margins, brand prestige for salons

Visual direction:
- Professional salon setting
- Stylist expertise showcase
- Premium product quality
- Client satisfaction moments
- Business credibility feel

Style: Serious, premium, lead-generation focused
Duration: 15-20 seconds""",
    },
}


# ==================== HELPER FUNCTIONS ====================

def get_fb_token():
    token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="FB_PAGE_ACCESS_TOKEN non configuré")
    return token

def get_random_hook(offer_type: OfferType, angle: ContentAngle) -> str:
    hooks = HOOKS.get(offer_type, {}).get(angle, ["Découvrez Luxura"])
    return random.choice(hooks)

def get_random_headline(offer_type: OfferType) -> str:
    headlines = HEADLINES.get(offer_type, ["Luxura Distribution"])
    return random.choice(headlines)

def generate_hashtags(offer_type: OfferType, angle: ContentAngle) -> str:
    base_tags = ["LuxuraDistribution", "ExtensionsCheveux", "Quebec"]
    
    if offer_type == OfferType.DIRECT_SALE:
        base_tags.extend(["RallongesCapillaires", "CheveuxPremium", "Beaute"])
        if angle == ContentAngle.TRANSFORMATION:
            base_tags.extend(["AvantApres", "Transformation", "HairGoals"])
    elif offer_type == OfferType.SALON_AFFILIATE:
        base_tags.extend(["SalonPartenaire", "B2B", "CoiffeurQuebec", "Professionnel"])
    
    return " ".join([f"#{tag}" for tag in base_tags])


# ==================== CONTENT GENERATION ====================

@router.post("/content/generate")
def generate_content(request: ContentRequest):
    """
    🎨 Générer un contenu marketing complet (texte + structure).
    
    Retourne le hook, texte principal, headline, hashtags et storyboard vidéo.
    """
    # Sélectionner le hook
    hook = request.custom_hook or get_random_hook(request.offer_type, request.angle)
    
    # Sélectionner le texte principal
    text_variants = PRIMARY_TEXTS.get(request.offer_type, {})
    angle_key = "transformation" if request.angle == ContentAngle.TRANSFORMATION else "default"
    primary_text = text_variants.get(angle_key, text_variants.get("default", ""))
    
    # Headline
    headline = get_random_headline(request.offer_type)
    
    # Hashtags
    hashtags = generate_hashtags(request.offer_type, request.angle)
    
    # Storyboard si vidéo
    storyboard = None
    if request.format in [ContentFormat.STORY_916, ContentFormat.FEED_45, ContentFormat.REEL_916]:
        storyboard = VIDEO_STORYBOARDS.get(request.offer_type, {}).get(request.format)
    
    # CTA
    cta = CTA_MAP.get(request.offer_type, "LEARN_MORE")
    
    # Construire le message complet pour post organique
    full_message = f"{hook}\n\n{primary_text}\n\n{hashtags}"
    
    return {
        "success": True,
        "content": {
            "hook": hook,
            "primary_text": primary_text,
            "headline": headline,
            "hashtags": hashtags,
            "cta": cta,
            "full_message": full_message,
            "storyboard": storyboard,
            "format": request.format,
            "offer_type": request.offer_type,
            "angle": request.angle,
        },
        "meta": {
            "landing_url": request.landing_url,
            "image_url": request.image_url,
        }
    }


@router.post("/content/variations")
def generate_variations(request: ContentRequest, count: int = 3):
    """
    🔄 Générer plusieurs variations d'un contenu.
    
    Parfait pour A/B testing Meta Ads.
    """
    variations = []
    angles = [request.angle]
    
    # Ajouter d'autres angles pertinents
    if request.offer_type == OfferType.DIRECT_SALE:
        all_angles = [ContentAngle.QUALITY_PREMIUM, ContentAngle.IMPORTATEUR_DIRECT, 
                     ContentAngle.TRANSFORMATION, ContentAngle.EFFET_NATUREL]
    else:
        all_angles = [ContentAngle.MARGE_PRO, ContentAngle.IMAGE_HAUT_GAMME,
                     ContentAngle.APPROVISIONNEMENT, ContentAngle.DIFFERENCIATION]
    
    for i in range(min(count, len(all_angles))):
        angle = all_angles[i]
        hook = get_random_hook(request.offer_type, angle)
        headline = get_random_headline(request.offer_type)
        
        variations.append({
            "variation_id": f"V{i+1}",
            "angle": angle,
            "hook": hook,
            "headline": headline,
            "hashtags": generate_hashtags(request.offer_type, angle),
        })
    
    return {
        "success": True,
        "offer_type": request.offer_type,
        "format": request.format,
        "variations": variations,
        "recommendation": "Testez ces variations en Dynamic Creative pour optimisation automatique"
    }


# ==================== VIDEO GENERATION (FAL.AI) ====================

@router.post("/video/generate")
async def generate_video(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    """
    🎬 Générer une vidéo marketing avec Fal.ai.
    
    Utilise les templates de prompts optimisés pour chaque type d'offre et format.
    """
    if not FAL_KEY:
        raise HTTPException(status_code=400, detail="FAL_KEY non configuré")
    
    # Obtenir le prompt approprié
    prompt_template = FAL_PROMPTS.get(request.offer_type, {}).get(request.format)
    if not prompt_template:
        raise HTTPException(status_code=400, detail=f"Pas de template pour {request.offer_type}/{request.format}")
    
    # Ajouter les détails de l'angle
    hook = get_random_hook(request.offer_type, request.angle)
    
    full_prompt = f"""{prompt_template}

Marketing angle: {request.angle}
Hook text to overlay: "{hook}"
Include logo: {request.include_logo}
Include CTA: {request.include_cta}

Generate a video that converts."""
    
    try:
        # Appeler Fal.ai pour générer la vidéo
        headers = {
            "Authorization": f"Key {FAL_KEY}",
            "Content-Type": "application/json"
        }
        
        # Utiliser l'endpoint image-to-video de Fal
        payload = {
            "image_url": request.image_url,
            "prompt": full_prompt,
            "duration": request.duration,
            "aspect_ratio": "9:16" if "916" in request.format else "4:5",
        }
        
        response = requests.post(
            "https://fal.run/fal-ai/kling-video/v1.5/pro/image-to-video",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Fal.ai error: {response.text}",
                "fallback": "Utilisez le storyboard pour créer manuellement",
                "storyboard": VIDEO_STORYBOARDS.get(request.offer_type, {}).get(request.format)
            }
        
        result = response.json()
        
        return {
            "success": True,
            "video_url": result.get("video", {}).get("url"),
            "request_id": result.get("request_id"),
            "format": request.format,
            "offer_type": request.offer_type,
            "prompt_used": full_prompt[:200] + "...",
            "storyboard": VIDEO_STORYBOARDS.get(request.offer_type, {}).get(request.format)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback": "Utilisez le storyboard manuel",
            "storyboard": VIDEO_STORYBOARDS.get(request.offer_type, {}).get(request.format)
        }


@router.get("/video/storyboard")
def get_storyboard(offer_type: OfferType, format: ContentFormat):
    """
    📋 Obtenir le storyboard vidéo pour un type de contenu.
    """
    storyboard = VIDEO_STORYBOARDS.get(offer_type, {}).get(format)
    hook = get_random_hook(offer_type, ContentAngle.QUALITY_PREMIUM if offer_type == OfferType.DIRECT_SALE else ContentAngle.IMAGE_HAUT_GAMME)
    
    return {
        "offer_type": offer_type,
        "format": format,
        "storyboard": storyboard,
        "suggested_hook": hook,
        "duration": "15s" if "916" in format else "20s",
        "aspect_ratio": "9:16 vertical" if "916" in format else "4:5 feed"
    }


# ==================== PUBLISHING ====================

@router.post("/publish/organic")
def publish_organic(request: ContentRequest):
    """
    📤 Publier un post organique sur Facebook.
    """
    fb_token = get_fb_token()
    
    # Générer le contenu
    content = generate_content(request)["content"]
    
    try:
        if request.image_url:
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/photos",
                data={
                    "url": request.image_url,
                    "caption": content["full_message"],
                    "access_token": fb_token
                },
                timeout=30
            )
        else:
            data = {
                "message": content["full_message"],
                "access_token": fb_token
            }
            if request.landing_url:
                data["link"] = request.landing_url
            response = requests.post(f"{FB_BASE_URL}/{FB_PAGE_ID}/feed", data=data, timeout=30)
        
        result = response.json()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"].get("message"))
        
        return {
            "success": True,
            "post_id": result.get("id"),
            "content_used": content,
            "type": "organic"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish/story")
def publish_story(media_url: str, media_type: str = "photo"):
    """
    📱 Publier une Story Facebook.
    """
    fb_token = get_fb_token()
    
    try:
        endpoint = f"{FB_BASE_URL}/{FB_PAGE_ID}/photo_stories" if media_type == "photo" else f"{FB_BASE_URL}/{FB_PAGE_ID}/video_stories"
        key = "photo_url" if media_type == "photo" else "video_url"
        
        response = requests.post(
            endpoint,
            data={key: media_url, "access_token": fb_token},
            timeout=60
        )
        
        result = response.json()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"].get("message"))
        
        return {
            "success": True,
            "post_id": result.get("post_id"),
            "type": "story",
            "media_type": media_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish/reel")
def publish_reel(video_url: str, offer_type: OfferType, angle: ContentAngle):
    """
    🎬 Publier un Reel Facebook.
    """
    fb_token = get_fb_token()
    
    # Générer la description
    hook = get_random_hook(offer_type, angle)
    hashtags = generate_hashtags(offer_type, angle)
    description = f"{hook}\n\n{hashtags}"
    
    try:
        # Phase 1: Initialize
        init_response = requests.post(
            f"{FB_BASE_URL}/{FB_PAGE_ID}/video_reels",
            data={"upload_phase": "start", "access_token": fb_token},
            timeout=30
        )
        init_result = init_response.json()
        
        if "error" in init_result:
            raise HTTPException(status_code=400, detail=f"Init: {init_result['error'].get('message')}")
        
        video_id = init_result.get("video_id")
        upload_url = init_result.get("upload_url")
        
        # Phase 2: Download and upload video
        video_content = requests.get(video_url, timeout=120).content
        requests.post(upload_url, headers={"Content-Type": "video/mp4"}, data=video_content, timeout=120)
        
        # Phase 3: Finish
        finish_response = requests.post(
            f"{FB_BASE_URL}/{FB_PAGE_ID}/video_reels",
            data={
                "upload_phase": "finish",
                "video_id": video_id,
                "video_state": "PUBLISHED",
                "description": description,
                "title": f"Luxura - {offer_type.value}",
                "access_token": fb_token
            },
            timeout=30
        )
        finish_result = finish_response.json()
        
        if "error" in finish_result:
            raise HTTPException(status_code=400, detail=f"Finish: {finish_result['error'].get('message')}")
        
        return {
            "success": True,
            "video_id": video_id,
            "type": "reel",
            "description": description
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CALENDAR ====================

@router.get("/calendar")
def get_calendar():
    """
    📅 Obtenir le calendrier de publication sur 4 semaines.
    """
    calendar = {
        "week_1_products": {
            "theme": "Produits vedettes",
            "posts": [
                {"day": "monday", "time": "10:00", "type": "organic", "offer": "direct_sale", "content": "product_showcase", "format": "feed_4:5"},
                {"day": "tuesday", "time": "12:00", "type": "reel", "offer": "direct_sale", "content": "transformation", "format": "reel_9:16"},
                {"day": "wednesday", "time": "19:00", "type": "story", "offer": "direct_sale", "content": "behind_scenes", "format": "story_9:16"},
                {"day": "thursday", "time": "08:00", "type": "organic", "offer": "salon_affilie", "content": "b2b_offer", "format": "feed_4:5"},
                {"day": "friday", "time": "14:00", "type": "carousel", "offer": "direct_sale", "content": "color_trends", "format": "carousel"},
                {"day": "saturday", "time": "11:00", "type": "reel", "offer": "direct_sale", "content": "tutorial", "format": "reel_9:16"},
                {"day": "sunday", "time": "20:00", "type": "story", "offer": "direct_sale", "content": "testimonial", "format": "story_9:16"},
            ]
        },
        "week_2_education": {
            "theme": "Éducation & guides",
            "posts": [
                {"day": "monday", "time": "10:00", "type": "organic", "offer": "direct_sale", "content": "care_guide", "format": "feed_4:5"},
                {"day": "tuesday", "time": "12:00", "type": "reel", "offer": "direct_sale", "content": "comparison", "format": "reel_9:16"},
                {"day": "wednesday", "time": "19:00", "type": "story", "offer": "direct_sale", "content": "qa_session", "format": "story_9:16"},
                {"day": "thursday", "time": "08:00", "type": "organic", "offer": "salon_affilie", "content": "training", "format": "feed_4:5"},
                {"day": "friday", "time": "14:00", "type": "carousel", "offer": "direct_sale", "content": "mistakes_avoid", "format": "carousel"},
                {"day": "saturday", "time": "11:00", "type": "reel", "offer": "direct_sale", "content": "routine", "format": "reel_9:16"},
                {"day": "sunday", "time": "20:00", "type": "story", "offer": "direct_sale", "content": "before_after", "format": "story_9:16"},
            ]
        },
        "week_3_testimonials": {
            "theme": "Témoignages & preuves sociales",
            "posts": [
                {"day": "monday", "time": "10:00", "type": "organic", "offer": "direct_sale", "content": "salon_testimonial", "format": "feed_4:5"},
                {"day": "tuesday", "time": "12:00", "type": "reel", "offer": "direct_sale", "content": "wow_reaction", "format": "reel_9:16"},
                {"day": "wednesday", "time": "19:00", "type": "story", "offer": "direct_sale", "content": "salon_day", "format": "story_9:16"},
                {"day": "thursday", "time": "08:00", "type": "organic", "offer": "salon_affilie", "content": "partner_results", "format": "feed_4:5"},
                {"day": "friday", "time": "14:00", "type": "carousel", "offer": "direct_sale", "content": "transformations", "format": "carousel"},
                {"day": "saturday", "time": "11:00", "type": "reel", "offer": "direct_sale", "content": "texture_demo", "format": "reel_9:16"},
                {"day": "sunday", "time": "20:00", "type": "story", "offer": "direct_sale", "content": "weekend_vibes", "format": "story_9:16"},
            ]
        },
        "week_4_inspiration": {
            "theme": "Inspiration & tendances",
            "posts": [
                {"day": "monday", "time": "10:00", "type": "organic", "offer": "direct_sale", "content": "seasonal_look", "format": "feed_4:5"},
                {"day": "tuesday", "time": "12:00", "type": "reel", "offer": "direct_sale", "content": "3_styles", "format": "reel_9:16"},
                {"day": "wednesday", "time": "19:00", "type": "story", "offer": "direct_sale", "content": "photoshoot_bts", "format": "story_9:16"},
                {"day": "thursday", "time": "08:00", "type": "organic", "offer": "salon_affilie", "content": "new_collection", "format": "feed_4:5"},
                {"day": "friday", "time": "14:00", "type": "carousel", "offer": "direct_sale", "content": "trends_2025", "format": "carousel"},
                {"day": "saturday", "time": "11:00", "type": "reel", "offer": "direct_sale", "content": "wedding_look", "format": "reel_9:16"},
                {"day": "sunday", "time": "20:00", "type": "story", "offer": "direct_sale", "content": "week_prep", "format": "story_9:16"},
            ]
        },
    }
    
    # Calculer la semaine actuelle
    week_num = ((datetime.now().isocalendar()[1] - 1) % 4) + 1
    week_key = list(calendar.keys())[week_num - 1]
    current_week = calendar[week_key]
    
    # Trouver le prochain post
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    current_day = day_names[datetime.now().weekday()]
    
    next_post = None
    for post in current_week["posts"]:
        if post["day"] == current_day:
            next_post = post
            break
    
    return {
        "current_week": week_num,
        "current_theme": current_week["theme"],
        "current_day": current_day,
        "next_post": next_post,
        "week_schedule": current_week["posts"],
        "full_calendar": calendar,
    }


@router.get("/calendar/next")
def get_next_post():
    """
    ⏭️ Obtenir le prochain post à publier.
    """
    cal = get_calendar()
    return {
        "next_post": cal["next_post"],
        "week": cal["current_week"],
        "theme": cal["current_theme"],
        "action": "Utilisez /marketing/publish/* pour publier ce contenu"
    }


# ==================== CAMPAIGNS (META ADS) ====================

@router.get("/campaigns/structure")
def get_campaign_structure():
    """
    🏗️ Voir la structure de campagnes recommandée.
    """
    return {
        "campaigns": [
            {
                "name": "LUXURA_QC_PROSPECTING_DIRECT_2026Q2",
                "objective": "SALES",
                "offer_type": "direct_sale",
                "ad_sets": [
                    {"name": "BROAD_F23-45", "targeting": "Femmes 23-45, beauté, coiffure"},
                    {"name": "TRANSFORMATION", "targeting": "Intérêt transformation, avant-après"},
                    {"name": "RTG_30D", "targeting": "Visiteurs site + interactions 30j"},
                ],
                "daily_budget_cad": 30,
            },
            {
                "name": "LUXURA_QC_PROSPECTING_SALON_2026Q2",
                "objective": "LEADS",
                "offer_type": "salon_affilie",
                "ad_sets": [
                    {"name": "SALON_OWNER", "targeting": "Propriétaires salon, coiffeurs"},
                    {"name": "INDIE_STYLIST", "targeting": "Stylistes indépendants"},
                    {"name": "PRO_RTG_30D", "targeting": "Visiteurs page affilié"},
                ],
                "daily_budget_cad": 20,
            },
            {
                "name": "LUXURA_QC_AWARENESS_BRAND_2026Q2",
                "objective": "AWARENESS",
                "offer_type": "awareness",
                "ad_sets": [
                    {"name": "BRAND", "targeting": "Large, marque premium"},
                    {"name": "RESULTS", "targeting": "Transformations, témoignages"},
                    {"name": "NETWORK", "targeting": "Réseau salons affiliés"},
                ],
                "daily_budget_cad": 15,
            },
        ],
        "total_daily_budget_cad": 65,
        "formats_required": ["feed_4:5", "story_9:16"],
        "creatives_per_adset": 2,
        "note": "Utilisez /marketing/content/variations pour générer les créatifs"
    }


@router.get("/templates")
def get_all_templates():
    """
    📝 Voir tous les templates disponibles.
    """
    return {
        "hooks": HOOKS,
        "primary_texts": PRIMARY_TEXTS,
        "headlines": HEADLINES,
        "video_storyboards": VIDEO_STORYBOARDS,
        "fal_prompts": {k: {kk: vv[:100] + "..." for kk, vv in v.items()} for k, v in FAL_PROMPTS.items()},
        "cta_map": CTA_MAP,
    }


@router.get("/status")
def marketing_status():
    """
    📊 Statut global du système marketing.
    """
    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    fal_configured = bool(FAL_KEY)
    
    fb_status = {"configured": bool(fb_token), "valid": False, "page_name": None}
    
    if fb_token:
        try:
            response = requests.get(
                f"{FB_BASE_URL}/{FB_PAGE_ID}",
                params={"access_token": fb_token, "fields": "name"},
                timeout=5
            )
            result = response.json()
            fb_status["valid"] = "error" not in result
            fb_status["page_name"] = result.get("name")
        except:
            pass
    
    cal = get_calendar()
    
    return {
        "facebook": fb_status,
        "fal_ai": {"configured": fal_configured},
        "calendar": {
            "current_week": cal["current_week"],
            "theme": cal["current_theme"],
            "next_post": cal["next_post"],
        },
        "ready_for": {
            "organic_posts": fb_status["valid"],
            "stories": fb_status["valid"],
            "reels": fb_status["valid"],
            "video_generation": fal_configured,
            "paid_ads": False,  # Requires META_AD_ACCOUNT_ID
        }
    }
