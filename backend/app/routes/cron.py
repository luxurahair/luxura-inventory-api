"""
Luxura Marketing CRON - Automated Content Posting
Endpoints for scheduled marketing automation on Render

CRON Schedule Recommendations:
- Blog: Every day at 6:00 AM EST (11:00 UTC)
- Facebook Post: Mon/Wed/Fri at 10:00 AM EST (15:00 UTC)
- Instagram Reel idea: Tue/Thu at 7:00 PM EST (00:00 UTC next day)
"""

import os
import json
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import requests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cron", tags=["CRON Jobs"])

# ============ CONFIGURATION ============

BRAND_INFO = {
    "name": "Luxura Distribution",
    "tagline": "Importateur direct d'extensions capillaires premium au Québec",
    "phone": "418-222-3939",
    "website": "luxuradistribution.com",
    "location": "St-Georges, Québec",
}

# Facebook API
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "me")

# Content templates
DAILY_POST_TEMPLATES = [
    # Product posts
    {
        "category": "product",
        "templates": [
            """✨ **Genius Weft Série Vivian** - La trame invisible la plus discrète du marché !

Ultra-légère, couture invisible, 100% cheveux naturels Remy.
Idéale pour un volume naturel sans démarcation.

📦 En stock à St-Georges
🚚 Livraison rapide partout au Québec

👉 luxuradistribution.com
📞 418-222-3939

#GeniusWeft #ExtensionsQuebec #LuxuraDistribution""",

            """💎 **Bandes Adhésives Premium** - La méthode la plus populaire !

✅ Pose rapide (30-45 min)
✅ Réutilisable 2-3 fois
✅ Confort au quotidien
✅ Excellent rapport qualité/prix

En stock maintenant !
👉 luxuradistribution.com

#TapeIn #ExtensionsPremium #LuxuraDistribution""",

            """⏱️ **Halo Luxura** - Volume en 5 minutes !

Parfait pour :
✨ Événements spéciaux
✨ Mamans occupées  
✨ Essayer sans engagement

Aucune colle, aucune chaleur, zéro dommage !

👉 luxuradistribution.com
📞 418-222-3939

#HaloExtensions #VolumeInstant #LuxuraDistribution""",
        ]
    },
    # Educational posts
    {
        "category": "educational",
        "templates": [
            """📚 **Remy vs Non-Remy : C'est quoi la différence ?**

**Cheveux Remy :**
✅ Cuticules alignées = moins d'emmêlement
✅ Brillance naturelle
✅ Durée de vie plus longue

**Non-Remy :**
❌ Cuticules enlevées chimiquement
❌ S'emmêlent plus vite

Chez Luxura, on vend UNIQUEMENT du Remy/Vierge ! 💎

#CheveuxRemy #QualitePremium #LuxuraDistribution""",

            """💡 **5 conseils pour entretenir vos extensions**

1️⃣ Brossez délicatement de bas en haut
2️⃣ Utilisez des produits sans sulfate
3️⃣ Évitez la chaleur excessive
4️⃣ Dormez avec une tresse loose
5️⃣ Masque hydratant 1x/semaine

Vos extensions dureront 2x plus longtemps ! ✨

Questions ? 418-222-3939

#ConseilsExtensions #Entretien #LuxuraDistribution""",

            """🤔 **Quelle méthode d'extensions choisir ?**

➡️ **Genius Weft** : Invisible, ultra-légère
➡️ **Tape-In** : Populaire, bon rapport qualité/prix
➡️ **I-Tips** : Look très naturel
➡️ **Halo** : Sans engagement, pose 5 min

On vous aide à choisir ! 
📞 418-222-3939

#GuideExtensions #ConseilsBeaute #LuxuraDistribution""",
        ]
    },
    # Local/Trust posts
    {
        "category": "local_trust",
        "templates": [
            """🍁 **Fier d'être 100% québécois !**

Luxura Distribution, c'est :
✅ Inventaire réel à St-Georges
✅ Support en français
✅ Livraison rapide sans douane
✅ Service personnalisé

Merci à toutes les clientes et salons qui nous font confiance ! 🙏💛

#MadeInQuebec #SupportLocal #LuxuraDistribution""",

            """📍 **Pourquoi commander local ?**

Chez Luxura à St-Georges :
🚚 Livraison 1-2 jours au Québec
📞 Support téléphonique en français
🏪 Ramassage possible sur place
💰 Pas de frais de douane

Importateur direct = meilleurs prix ! 💎

#AchetezLocal #Quebec #LuxuraDistribution""",
        ]
    },
    # B2B posts
    {
        "category": "b2b_salon",
        "templates": [
            """💼 **Salons : Devenez partenaire Luxura !**

Avantages exclusifs :
✅ Prix distributeur avantageux
✅ Inventaire dédié
✅ Support technique & formation
✅ Livraison prioritaire

Intéressé(e) ? 
📞 418-222-3939
📩 Message privé

#PartenariatSalon #B2B #LuxuraDistribution""",

            """👩‍💼 **Stylistes : On a tout en stock !**

Genius Weft, Tape-In, I-Tips, Micro-billes, Halo...
Toutes les couleurs, toutes les longueurs.

Prix pro disponibles !
📞 418-222-3939

Venez visiter notre showroom au Salon Carouso, St-Georges.

#SalonCoiffure #ExtensionsPro #LuxuraDistribution""",
        ]
    },
]

# ============ MODELS ============

class CronJobResult(BaseModel):
    success: bool
    job_type: str
    timestamp: str
    message: str
    data: Optional[dict] = None

class ScheduledPost(BaseModel):
    category: str
    content: str
    scheduled_time: Optional[str] = None
    posted: bool = False
    post_id: Optional[str] = None

# ============ HELPER FUNCTIONS ============

def get_random_post(category: Optional[str] = None) -> dict:
    """Get a random post from templates"""
    
    if category:
        # Filter by category
        category_templates = [t for t in DAILY_POST_TEMPLATES if t["category"] == category]
        if not category_templates:
            category_templates = DAILY_POST_TEMPLATES
    else:
        # Weighted random selection based on day of week
        day = datetime.now().weekday()
        if day in [0, 2, 4]:  # Mon, Wed, Fri - Product focus
            weights = {"product": 0.5, "educational": 0.3, "local_trust": 0.1, "b2b_salon": 0.1}
        elif day in [1, 3]:  # Tue, Thu - Educational focus
            weights = {"product": 0.2, "educational": 0.5, "local_trust": 0.2, "b2b_salon": 0.1}
        else:  # Sat, Sun - Local/casual
            weights = {"product": 0.3, "educational": 0.2, "local_trust": 0.4, "b2b_salon": 0.1}
        
        # Select category based on weights
        categories = list(weights.keys())
        selected_category = random.choices(categories, weights=list(weights.values()))[0]
        category_templates = [t for t in DAILY_POST_TEMPLATES if t["category"] == selected_category]
    
    template_group = random.choice(category_templates)
    content = random.choice(template_group["templates"])
    
    return {
        "category": template_group["category"],
        "content": content
    }


def post_to_facebook(message: str, link: Optional[str] = None) -> dict:
    """Post to Facebook page"""
    
    if not FB_PAGE_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="FB_PAGE_ACCESS_TOKEN not configured")
    
    url = f"https://graph.facebook.com/v25.0/{FB_PAGE_ID}/feed"
    
    payload = {
        "message": message,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    
    if link:
        payload["link"] = link
    
    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Facebook post error: {e}")
        raise HTTPException(status_code=500, detail=f"Facebook API error: {str(e)}")


def log_cron_execution(job_type: str, success: bool, details: dict):
    """Log CRON execution for monitoring"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "job_type": job_type,
        "success": success,
        "details": details
    }
    logger.info(f"CRON Execution: {json.dumps(log_entry)}")
    return log_entry


# ============ CRON ENDPOINTS ============

@router.get("/status")
async def cron_status():
    """Check CRON system status"""
    return {
        "status": "ok",
        "service": "Luxura Marketing CRON",
        "facebook_configured": bool(FB_PAGE_ACCESS_TOKEN),
        "current_time_utc": datetime.utcnow().isoformat(),
        "templates_loaded": len(DAILY_POST_TEMPLATES),
        "available_jobs": [
            "POST /cron/facebook/auto-post",
            "POST /cron/facebook/scheduled-post",
            "GET /cron/preview-post",
            "POST /cron/weekly-schedule"
        ]
    }


@router.get("/preview-post")
async def preview_random_post(category: Optional[str] = None):
    """
    Preview a random post without posting
    
    Categories: product, educational, local_trust, b2b_salon
    """
    post = get_random_post(category)
    return {
        "preview": True,
        "category": post["category"],
        "content": post["content"],
        "character_count": len(post["content"]),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/facebook/auto-post")
async def auto_post_to_facebook(
    category: Optional[str] = None,
    dry_run: bool = False
):
    """
    🤖 AUTO POST - Main CRON endpoint
    
    Call this endpoint from Render Cron Job to auto-post to Facebook.
    
    Render Cron Examples:
    - Daily at 10 AM EST: 0 15 * * *
    - Mon/Wed/Fri at 10 AM EST: 0 15 * * 1,3,5
    - Tue/Thu at 7 PM EST: 0 0 * * 2,4
    
    Parameters:
    - category: Optional filter (product, educational, local_trust, b2b_salon)
    - dry_run: If true, preview only without posting
    """
    
    try:
        # Get random post
        post = get_random_post(category)
        
        if dry_run:
            return CronJobResult(
                success=True,
                job_type="facebook_auto_post_preview",
                timestamp=datetime.utcnow().isoformat(),
                message="Preview only - not posted",
                data=post
            )
        
        # Post to Facebook
        fb_response = post_to_facebook(post["content"])
        
        # Log success
        log_cron_execution("facebook_auto_post", True, {
            "category": post["category"],
            "post_id": fb_response.get("id"),
            "content_preview": post["content"][:100] + "..."
        })
        
        return CronJobResult(
            success=True,
            job_type="facebook_auto_post",
            timestamp=datetime.utcnow().isoformat(),
            message=f"Posted successfully to Facebook!",
            data={
                "facebook_post_id": fb_response.get("id"),
                "category": post["category"],
                "content_preview": post["content"][:200] + "..."
            }
        )
        
    except Exception as e:
        log_cron_execution("facebook_auto_post", False, {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/facebook/scheduled-post")
async def post_specific_content(
    content: str,
    link: Optional[str] = None
):
    """
    Post specific content to Facebook
    
    Use this for custom scheduled posts from n8n or other automation tools.
    """
    
    try:
        fb_response = post_to_facebook(content, link)
        
        log_cron_execution("facebook_scheduled_post", True, {
            "post_id": fb_response.get("id"),
            "content_preview": content[:100] + "..."
        })
        
        return CronJobResult(
            success=True,
            job_type="facebook_scheduled_post",
            timestamp=datetime.utcnow().isoformat(),
            message="Custom content posted successfully!",
            data={
                "facebook_post_id": fb_response.get("id"),
                "content_length": len(content)
            }
        )
        
    except Exception as e:
        log_cron_execution("facebook_scheduled_post", False, {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weekly-schedule")
async def generate_weekly_schedule():
    """
    Generate a weekly content schedule
    
    Returns 7 days of planned posts with recommended posting times.
    """
    
    schedule = []
    
    # Schedule configuration
    posting_times = {
        0: {"time": "10:00", "category": "product"},      # Monday
        1: {"time": "19:00", "category": "educational"},  # Tuesday
        2: {"time": "10:00", "category": "product"},      # Wednesday
        3: {"time": "19:00", "category": "educational"},  # Thursday
        4: {"time": "10:00", "category": "product"},      # Friday
        5: {"time": "12:00", "category": "local_trust"},  # Saturday
        6: {"time": "15:00", "category": "b2b_salon"},    # Sunday
    }
    
    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    
    today = datetime.now()
    
    for i in range(7):
        target_date = today + timedelta(days=i)
        day_of_week = target_date.weekday()
        config = posting_times[day_of_week]
        
        post = get_random_post(config["category"])
        
        schedule.append({
            "day": i + 1,
            "day_name": day_names[day_of_week],
            "date": target_date.strftime("%Y-%m-%d"),
            "recommended_time": config["time"] + " EST",
            "category": post["category"],
            "content": post["content"],
            "cron_expression": f"0 {int(config['time'].split(':')[0]) + 5} * * {day_of_week}"  # UTC adjustment
        })
    
    return {
        "success": True,
        "generated_at": datetime.utcnow().isoformat(),
        "timezone_note": "Times are in EST. CRON expressions are in UTC.",
        "schedule": schedule
    }


@router.get("/render-cron-config")
async def get_render_cron_config():
    """
    Get recommended Render Cron Job configuration
    
    Copy these settings to your Render dashboard.
    """
    
    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://your-api.onrender.com")
    
    return {
        "instructions": "Add these as Cron Jobs in your Render dashboard",
        "cron_jobs": [
            {
                "name": "Facebook Daily Post",
                "schedule": "0 15 * * 1,3,5",  # Mon/Wed/Fri at 10 AM EST
                "command": f"curl -X POST {base_url}/cron/facebook/auto-post",
                "description": "Auto-post produit 3x/semaine"
            },
            {
                "name": "Facebook Educational Post",
                "schedule": "0 0 * * 2,4",  # Tue/Thu at 7 PM EST
                "command": f"curl -X POST '{base_url}/cron/facebook/auto-post?category=educational'",
                "description": "Post éducatif 2x/semaine"
            },
            {
                "name": "Weekend Engagement Post",
                "schedule": "0 17 * * 6",  # Saturday at 12 PM EST
                "command": f"curl -X POST '{base_url}/cron/facebook/auto-post?category=local_trust'",
                "description": "Post engagement weekend"
            }
        ],
        "environment_variables_required": [
            "FB_PAGE_ACCESS_TOKEN",
            "FB_PAGE_ID (optional, defaults to 'me')"
        ]
    }


# ============ HEALTH CHECK FOR CRON ============

@router.head("/ping")
@router.get("/ping")
async def cron_ping():
    """Simple ping for uptime monitoring"""
    return {"pong": True, "timestamp": datetime.utcnow().isoformat()}
