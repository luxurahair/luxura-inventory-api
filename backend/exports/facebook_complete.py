# app/routes/facebook.py
"""
🔵 FACEBOOK CONTENT AUTOMATION - Luxura Inventory API
======================================================
Système complet d'automatisation de contenu Facebook:
- Posts produits, témoignages, B2B
- Reels vidéo
- Stories
- Carrousels
- Calendrier éditorial intelligent

Endpoints:
- GET  /facebook/status       : Statut connexion
- GET  /facebook/test         : Test rapide
- POST /facebook/post         : Post basique
- POST /facebook/post-product : Post produit formaté
- POST /facebook/post-testimonial : Post témoignage
- POST /facebook/post-b2b     : Post professionnel
- POST /facebook/post-reel    : Publier un Reel vidéo
- POST /facebook/post-story   : Publier une Story
- GET  /facebook/calendar     : Voir le calendrier
- POST /facebook/auto-post    : Publication automatique selon calendrier
"""

import os
import requests
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/facebook", tags=["Facebook"])

# Configuration
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "1838415193042352")
FB_API_VERSION = "v25.0"
FB_BASE_URL = f"https://graph.facebook.com/{FB_API_VERSION}"

# ==================== MODELS ====================

class FacebookPostRequest(BaseModel):
    message: str
    link: Optional[str] = None
    image_url: Optional[str] = None

class ProductPostRequest(BaseModel):
    product_type: str  # genius, tape, halo, i-tip, ponytail, clip-in
    color_name: str    # Nom luxueux de la couleur
    color_code: str    # Code (60a, hps, etc.)
    price: Optional[float] = None
    image_url: Optional[str] = None
    template: str = "vedette"  # vedette, nouveau, promo

class TestimonialPostRequest(BaseModel):
    salon_name: str
    city: str
    quote: str
    stylist_name: Optional[str] = None
    image_url: Optional[str] = None

class B2BPostRequest(BaseModel):
    title: str
    benefits: List[str]
    cta: str = "Contactez-nous"
    image_url: Optional[str] = None

class ReelRequest(BaseModel):
    video_url: str
    description: str
    title: Optional[str] = None
    hashtags: List[str] = []

class StoryRequest(BaseModel):
    media_url: str
    media_type: str = "photo"  # photo ou video


# ==================== TEMPLATES ====================

TEMPLATES = {
    "product_vedette": """✨ PRODUIT VEDETTE | {product_name}

{type_description}

🎯 Pourquoi nos clientes l'adorent:
• Cheveux 100% Remy russes
• Cuticules alignées pour un look naturel
• Durée de vie exceptionnelle (12+ mois)

💰 À partir de {price}$
🚚 Livraison rapide partout au Québec

👉 Lien en bio ou DM pour commander

#LuxuraDistribution #ExtensionsCheveux #{product_type} #Quebec #Beauce #Coiffure""",

    "product_nouveau": """🆕 NOUVEAUTÉ | {product_name}

Découvrez notre nouvelle teinte {color_name}! 

{type_description}

✨ Disponible maintenant en:
• 16" | 18" | 20" | 22" | 24"

📦 Commandez aujourd'hui, recevez cette semaine!

#Nouveauté #ExtensionsCheveux #{product_type} #Quebec #LuxuraDistribution""",

    "product_promo": """🔥 PROMOTION | {product_name}

Offre spéciale sur nos {product_type}!

{type_description}

💰 Prix régulier: {regular_price}$
✨ Prix promo: {promo_price}$

⏰ Offre limitée - Ne manquez pas ça!

#Promo #ExtensionsCheveux #{product_type} #Quebec #LuxuraDistribution""",

    "testimonial": """💬 TÉMOIGNAGE | {salon_name}

"{quote}"

- {stylist_name}, {city}

Merci à nos incroyables partenaires! 💕

Vous aussi, offrez la qualité Luxura à vos clientes ✨

👉 Devenez salon partenaire: info@luxuradistribution.com

#Témoignage #SalonPartenaire #Quebec #Coiffure #LuxuraDistribution""",

    "b2b": """💼 OFFRE PROFESSIONNELS | {title}

Vous êtes propriétaire de salon? 

Luxura Distribution vous offre:
{benefits_list}

📍 Déjà 25+ salons partenaires au Québec!

📩 {cta}: info@luxuradistribution.com
📞 418-774-4315

#SalonPartenaire #B2B #ExtensionsPro #Quebec #CoiffeurQuebec""",

    "reel": """✨ {title}

{description}

👉 Réservez votre consultation!
📍 Salons partenaires partout au Québec

#LuxuraDistribution #Extensions #Reels #Quebec {hashtags}"""
}

TYPE_DESCRIPTIONS = {
    "genius": "Nos extensions Genius Trame Invisible offrent un confort inégalé - aucune colle, aucun dommage, réutilisables!",
    "tape": "Extensions Tape-In à pose rapide - le choix #1 des professionnels pour un résultat naturel et durable.",
    "halo": "Extensions Halo avec fil invisible - posez-les en 2 minutes, retirez-les quand vous voulez!",
    "i-tip": "Extensions I-Tip Kératine - fixation individuelle ultra-naturelle, durée 6+ mois.",
    "ponytail": "Queue de cheval Luxura - volume et longueur instantanés pour vos occasions spéciales!",
    "clip-in": "Extensions à Clips - parfaites pour un changement de look sans engagement!"
}


# ==================== HELPER FUNCTIONS ====================

def get_fb_token():
    token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="FB_PAGE_ACCESS_TOKEN non configuré")
    return token

def format_hashtags(tags: List[str]) -> str:
    return " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])


# ==================== ENDPOINTS ====================

@router.get("/status")
def facebook_status():
    """📊 Vérifier le statut de la connexion Facebook."""
    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    status = {"configured": bool(fb_token), "token_valid": False, "page_id": FB_PAGE_ID, "page_name": None}
    
    if not fb_token:
        return status
    
    try:
        response = requests.get(
            f"{FB_BASE_URL}/{FB_PAGE_ID}",
            params={"access_token": fb_token, "fields": "name,id"},
            timeout=10
        )
        result = response.json()
        
        if "error" not in result:
            status["token_valid"] = True
            status["page_name"] = result.get("name")
        else:
            status["error"] = result["error"].get("message")
    except Exception as e:
        status["error"] = str(e)
    
    return status


@router.get("/test")
def test_facebook():
    """🧪 Test rapide de la connexion."""
    status = facebook_status()
    if status.get("token_valid"):
        return {"ok": True, "message": f"✅ Connecté à: {status.get('page_name')}", "ready": True}
    return {"ok": False, "message": f"❌ {status.get('error', 'Token non configuré')}", "ready": False}


@router.post("/post")
def post_basic(request: FacebookPostRequest):
    """📘 Post basique (texte/image/lien)."""
    fb_token = get_fb_token()
    
    try:
        if request.image_url:
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/photos",
                data={"url": request.image_url, "caption": request.message, "access_token": fb_token},
                timeout=30
            )
        else:
            data = {"message": request.message, "access_token": fb_token}
            if request.link:
                data["link"] = request.link
            response = requests.post(f"{FB_BASE_URL}/{FB_PAGE_ID}/feed", data=data, timeout=30)
        
        result = response.json()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"].get("message"))
        
        return {"success": True, "post_id": result.get("id"), "page_url": f"https://www.facebook.com/{FB_PAGE_ID}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post-product")
def post_product(request: ProductPostRequest):
    """✨ Publier un post produit formaté."""
    fb_token = get_fb_token()
    
    template_key = f"product_{request.template}"
    template = TEMPLATES.get(template_key, TEMPLATES["product_vedette"])
    
    product_name = f"{request.product_type.title()} {request.color_name} ({request.color_code})"
    type_desc = TYPE_DESCRIPTIONS.get(request.product_type.lower(), "Extensions de qualité professionnelle.")
    
    message = template.format(
        product_name=product_name,
        product_type=request.product_type.title(),
        color_name=request.color_name,
        type_description=type_desc,
        price=request.price or "199",
        regular_price=request.price or "249",
        promo_price=int((request.price or 249) * 0.8)
    )
    
    try:
        if request.image_url:
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/photos",
                data={"url": request.image_url, "caption": message, "access_token": fb_token},
                timeout=30
            )
        else:
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/feed",
                data={"message": message, "access_token": fb_token},
                timeout=30
            )
        
        result = response.json()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"].get("message"))
        
        return {
            "success": True,
            "post_id": result.get("id"),
            "template_used": template_key,
            "message_preview": message[:200] + "..."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post-testimonial")
def post_testimonial(request: TestimonialPostRequest):
    """💬 Publier un témoignage de salon."""
    fb_token = get_fb_token()
    
    template = TEMPLATES["testimonial"]
    message = template.format(
        salon_name=request.salon_name,
        quote=request.quote,
        stylist_name=request.stylist_name or "L'équipe",
        city=request.city
    )
    
    try:
        if request.image_url:
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/photos",
                data={"url": request.image_url, "caption": message, "access_token": fb_token},
                timeout=30
            )
        else:
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/feed",
                data={"message": message, "access_token": fb_token},
                timeout=30
            )
        
        result = response.json()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"].get("message"))
        
        return {"success": True, "post_id": result.get("id"), "type": "testimonial"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post-b2b")
def post_b2b(request: B2BPostRequest):
    """💼 Publier un post B2B pour salons."""
    fb_token = get_fb_token()
    
    benefits_list = "\n".join([f"✅ {b}" for b in request.benefits])
    
    template = TEMPLATES["b2b"]
    message = template.format(
        title=request.title,
        benefits_list=benefits_list,
        cta=request.cta
    )
    
    try:
        if request.image_url:
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/photos",
                data={"url": request.image_url, "caption": message, "access_token": fb_token},
                timeout=30
            )
        else:
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/feed",
                data={"message": message, "access_token": fb_token},
                timeout=30
            )
        
        result = response.json()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"].get("message"))
        
        return {"success": True, "post_id": result.get("id"), "type": "b2b"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post-reel")
def post_reel(request: ReelRequest):
    """🎬 Publier un Reel vidéo."""
    fb_token = get_fb_token()
    
    hashtags_str = format_hashtags(request.hashtags)
    description = TEMPLATES["reel"].format(
        title=request.title or "Transformation Luxura",
        description=request.description,
        hashtags=hashtags_str
    )
    
    try:
        # Phase 1: Initialize upload
        init_response = requests.post(
            f"{FB_BASE_URL}/{FB_PAGE_ID}/video_reels",
            data={
                "upload_phase": "start",
                "access_token": fb_token
            },
            timeout=30
        )
        init_result = init_response.json()
        
        if "error" in init_result:
            raise HTTPException(status_code=400, detail=f"Init failed: {init_result['error'].get('message')}")
        
        video_id = init_result.get("video_id")
        upload_url = init_result.get("upload_url")
        
        # Phase 2: Upload video from URL
        video_response = requests.get(request.video_url, timeout=60)
        if video_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download video from URL")
        
        upload_response = requests.post(
            upload_url,
            headers={"Content-Type": "video/mp4"},
            data=video_response.content,
            timeout=120
        )
        
        # Phase 3: Finish and publish
        finish_response = requests.post(
            f"{FB_BASE_URL}/{FB_PAGE_ID}/video_reels",
            data={
                "upload_phase": "finish",
                "video_id": video_id,
                "video_state": "PUBLISHED",
                "description": description,
                "title": request.title or "Luxura Distribution",
                "access_token": fb_token
            },
            timeout=30
        )
        finish_result = finish_response.json()
        
        if "error" in finish_result:
            raise HTTPException(status_code=400, detail=f"Finish failed: {finish_result['error'].get('message')}")
        
        return {
            "success": True,
            "video_id": video_id,
            "type": "reel",
            "status": finish_result.get("success", True)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post-story")
def post_story(request: StoryRequest):
    """📱 Publier une Story."""
    fb_token = get_fb_token()
    
    try:
        if request.media_type == "photo":
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/photo_stories",
                data={
                    "photo_url": request.media_url,
                    "access_token": fb_token
                },
                timeout=30
            )
        else:  # video
            response = requests.post(
                f"{FB_BASE_URL}/{FB_PAGE_ID}/video_stories",
                data={
                    "video_url": request.media_url,
                    "access_token": fb_token
                },
                timeout=30
            )
        
        result = response.json()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"].get("message"))
        
        return {
            "success": True,
            "post_id": result.get("post_id"),
            "type": "story",
            "media_type": request.media_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar")
def get_calendar():
    """📅 Voir le calendrier de publication."""
    
    # Calendrier sur 4 semaines - TOUT EN FRANÇAIS
    calendar = {
        "semaine_1_produits": {
            "lundi_10h": {"type": "post_product", "template": "vedette", "product_type": "genius"},
            "mardi_12h": {"type": "reel", "theme": "transformation"},
            "mercredi_19h": {"type": "story", "theme": "coulisses"},
            "jeudi_08h": {"type": "post_b2b", "theme": "offre_salons"},
            "vendredi_14h": {"type": "carousel", "theme": "couleurs_tendance"},
            "samedi_11h": {"type": "reel", "theme": "tutoriel"},
            "dimanche_20h": {"type": "story", "theme": "temoignage"}
        },
        "semaine_2_education": {
            "lundi_10h": {"type": "post_product", "template": "vedette", "product_type": "tape"},
            "mardi_12h": {"type": "reel", "theme": "comparatif"},
            "mercredi_19h": {"type": "story", "theme": "qa"},
            "jeudi_08h": {"type": "post_b2b", "theme": "formation"},
            "vendredi_14h": {"type": "carousel", "theme": "erreurs_eviter"},
            "samedi_11h": {"type": "reel", "theme": "routine_entretien"},
            "dimanche_20h": {"type": "story", "theme": "avant_apres"}
        },
        "semaine_3_temoignages": {
            "lundi_10h": {"type": "post_testimonial", "salon": "Salon Carouso"},
            "mardi_12h": {"type": "reel", "theme": "reaction_wow"},
            "mercredi_19h": {"type": "story", "theme": "pose_salon"},
            "jeudi_08h": {"type": "post_b2b", "theme": "resultats"},
            "vendredi_14h": {"type": "carousel", "theme": "transformations"},
            "samedi_11h": {"type": "reel", "theme": "texture_cheveux"},
            "dimanche_20h": {"type": "story", "theme": "weekend"}
        },
        "semaine_4_inspiration": {
            "lundi_10h": {"type": "post_product", "template": "nouveau", "product_type": "halo"},
            "mardi_12h": {"type": "reel", "theme": "3_coiffures"},
            "mercredi_19h": {"type": "story", "theme": "photoshoot"},
            "jeudi_08h": {"type": "post_b2b", "theme": "nouvelle_collection"},
            "vendredi_14h": {"type": "carousel", "theme": "tendances_2026"},
            "samedi_11h": {"type": "reel", "theme": "mariage"},
            "dimanche_20h": {"type": "story", "theme": "preparation"}
        }
    }
    
    # Calculer la semaine actuelle dans le cycle
    week_number = ((datetime.now().isocalendar()[1] - 1) % 4) + 1
    week_key = list(calendar.keys())[week_number - 1]
    
    # Jours en français
    jours_fr = {0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi", 4: "vendredi", 5: "samedi", 6: "dimanche"}
    current_day = jours_fr[datetime.now().weekday()]
    current_hour = datetime.now().hour
    
    return {
        "semaine_actuelle": week_number,
        "theme_semaine": week_key.replace("semaine_", "").replace("_", " ").title(),
        "jour_actuel": current_day,
        "horaire": calendar[week_key],
        "calendrier_complet": calendar
    }


@router.post("/auto-post")
def auto_post():
    """🤖 Publication automatique selon le calendrier."""
    calendar = get_calendar()
    current_day = calendar["current_day"]
    schedule = calendar["schedule"]
    
    # Trouver le post actuel
    next_post = None
    for key, value in schedule.items():
        if key.startswith(current_day):
            next_post = value
            break
    
    if not next_post:
        return {"success": False, "message": "Aucun post prévu aujourd'hui", "schedule": schedule}
    
    return {
        "success": True,
        "next_post": next_post,
        "message": f"Prochain post: {next_post['type']}",
        "note": "Utilisez l'endpoint spécifique pour publier avec les données appropriées"
    }


@router.get("/templates")
def get_templates():
    """📝 Voir tous les templates disponibles."""
    return {
        "templates": list(TEMPLATES.keys()),
        "type_descriptions": TYPE_DESCRIPTIONS,
        "hashtags": {
            "marque": ["LuxuraDistribution", "Luxura", "ExtensionsLuxura"],
            "produit": ["ExtensionsCheveux", "RallongesCapillaires", "CheveuxRusses"],
            "type": ["GeniusWeft", "TapeIn", "HaloExtensions", "ITip", "ClipIn"],
            "geo": ["Quebec", "Beauce", "StGeorges", "Levis", "Montreal", "Laval"],
            "profession": ["Coiffure", "SalonCoiffure", "CoiffeurQuebec"],
            "engagement": ["AvantApres", "Transformation", "Reels", "Tutorial"]
        }
    }
