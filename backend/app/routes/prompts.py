"""
📝 API PROMPTS - Accès direct aux prompts de chaque cron
=========================================================
Permet de visualiser et copier tous les prompts utilisés
pour la génération d'images AI.
"""

from fastapi import APIRouter
from typing import Dict, List
from datetime import datetime

router = APIRouter(prefix="/api/prompts", tags=["Prompts"])


# ============================================
# 📋 DÉFINITION DE TOUS LES PROMPTS PAR CRON
# ============================================

CRON_PROMPTS = {
    "LUX-HALO-12H": {
        "name": "Halo - 12h00",
        "fichier": "scripts/multi_category_cron.py",
        "lignes": "282-315",
        "description": "Publications produits Halo à midi",
        "frequence": "Tous les jours à 12h00 (Montréal)",
        "scenes": [
            {"name": "Cocktail Bar", "desc": "with her best girlfriend at a trendy Montreal cocktail bar, both holding fancy drinks, dim romantic lighting, chic lounge atmosphere"},
            {"name": "5 à 7 Copines", "desc": "at happy hour (5 à 7) with two girlfriends at a stylish downtown bar, laughing together, cocktails on table, warm ambient lighting"},
            {"name": "Rooftop Lounge", "desc": "with her friend at a glamorous Montreal rooftop lounge at sunset, champagne glasses, city skyline backdrop, VIP atmosphere"},
            {"name": "Wine Bar", "desc": "at an upscale wine bar with a close friend, elegant wine glasses, sophisticated decor, intimate conversation moment"},
            {"name": "Sushi Bar", "desc": "at a trendy Montreal sushi restaurant with friends, modern Japanese decor, enjoying omakase experience, elegant ambiance"},
            {"name": "Steakhouse", "desc": "at a high-end Quebec steakhouse with her girlfriend, leather booths, warm lighting, celebrating a special occasion"},
            {"name": "Terrasse Restaurant", "desc": "at an upscale Old Montreal restaurant terrace with friends, al fresco dining, string lights, evening atmosphere"},
            {"name": "Brunch Chic", "desc": "at a trendy brunch spot with girlfriends, mimosas on table, bright modern interior, weekend vibes"},
            {"name": "Girls Night", "desc": "on a girls night out with two friends at a chic Montreal nightclub lounge, VIP booth, glamorous setting"},
            {"name": "Bachelorette", "desc": "at a bachelorette party with friends, festive atmosphere, champagne toast, stylish venue"},
            {"name": "Birthday Dinner", "desc": "celebrating a birthday dinner with close friends at an elegant restaurant, candles, joyful moment"},
            {"name": "After Work", "desc": "at an after-work gathering with colleagues at a trendy bar, relaxed professional atmosphere, end of day drinks"},
        ],
        "prompt_template": """Real photograph of glamorous Québec women in their early 30s {scene_desc}.

SCENE REQUIREMENT:
- Show 2-3 girlfriends together enjoying the moment
- Social, fun, luxurious atmosphere
- Natural interaction between friends

DIVERSITY REQUIREMENT - VERY IMPORTANT:
⚠️ Each woman MUST look like a DIFFERENT PERSON ⚠️
- Different face shapes (oval, round, square, heart)
- Different nose shapes and sizes
- Different eye shapes and colors
- Mix of ethnicities is welcome (Québécoise can be diverse)
- NOT clones or twins - they are DIFFERENT individuals
- Variety in body types is natural

HAIR COLOR FOR MAIN SUBJECT:
{product_color}
- Other women should have DIFFERENT hair colors (variety!)

HAIR LENGTH - STRICT RULE:
⚠️ ALL WOMEN: HAIR MUST BE MID-BACK MAXIMUM ⚠️
- Hair ends at BRA-STRAP level
- Hair is ABOVE the waist
- DO NOT generate hair past the waist

Hair style: Soft waves, voluminous, glamorous

Setting: Upscale, trendy, Quebec nightlife/restaurant
Lighting: Warm ambient, flattering
Mood: Fun, confident, aspirational

Professional lifestyle photography.
No text, no watermarks."""
    },
    
    "LUX-GENIUS-18H": {
        "name": "Genius Weft - 18h00",
        "fichier": "scripts/multi_category_cron.py",
        "lignes": "282-315",
        "description": "Publications produits Genius Weft à 18h",
        "frequence": "Tous les jours à 18h00 (Montréal)",
        "scenes": "Mêmes scènes que LUX-HALO-12H",
        "prompt_template": "Même prompt que LUX-HALO-12H (multi_category_cron.py)"
    },
    
    "LUX-ITIP-2030": {
        "name": "I-Tip - 20h30",
        "fichier": "scripts/multi_category_cron.py",
        "lignes": "282-315",
        "description": "Publications produits I-Tip à 20h30",
        "frequence": "Tous les jours à 20h30 (Montréal)",
        "scenes": "Mêmes scènes que LUX-HALO-12H",
        "prompt_template": "Même prompt que LUX-HALO-12H (multi_category_cron.py)"
    },
    
    "LUX-TAPE-0730": {
        "name": "Tape-In - 07h30",
        "fichier": "scripts/multi_category_cron.py",
        "lignes": "282-315",
        "description": "Publications produits Tape-In à 7h30",
        "frequence": "Tous les jours à 07h30 (Montréal)",
        "scenes": "Mêmes scènes que LUX-HALO-12H",
        "prompt_template": "Même prompt que LUX-HALO-12H (multi_category_cron.py)"
    },
    
    "LUX-DAILY-18H": {
        "name": "Produit Quotidien - 18h00",
        "fichier": "scripts/daily_product_cron.py",
        "lignes": "654-678",
        "description": "1 produit mis en vedette par jour",
        "frequence": "Tous les jours à 18h00 (Montréal)",
        "scenes": [
            {"name": "Lifestyle varié", "desc": "Scènes lifestyle québécoises variées"}
        ],
        "prompt_template": """Real photograph of a glamorous Québec woman in her early 30s {scene_desc}.

HAIR COLOR (MANDATORY - MUST MATCH EXACTLY):
{product_color}

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

The hair showcases {product_name} shade. Professional photography.
No text, no watermarks."""
    },
    
    "LUX-EDITORIAL": {
        "name": "Éditorial / Weekend",
        "fichier": "scripts/facebook_cron.py",
        "lignes": "509-567",
        "description": "Posts éducatifs, comparatifs, weekend",
        "frequence": "Selon calendrier éditorial",
        "scenes": [
            {"name": "Grande Allée", "desc": "walking down Grande Allée Quebec City at golden hour, stunning mid-back hair flowing behind her, chic summer dress, historic architecture backdrop"},
            {"name": "Café Montréal", "desc": "at a trendy Montreal cafe terrace, beautiful mid-back hair extensions, enjoying coffee alone, European city vibes, soft natural lighting"},
            {"name": "Shopping St-Denis", "desc": "shopping on Rue Saint-Denis Montreal, beautiful mid-back hair, casual chic outfit, authentic urban lifestyle moment"},
            {"name": "Mont-Tremblant", "desc": "at Mont-Tremblant lookout point, mid-back hair caught in mountain breeze, athletic casual wear, stunning autumn foliage backdrop"},
            {"name": "Vieux-Port", "desc": "on a peaceful morning walk along Vieux-Port Montreal, mid-back hair gently moving, casual elegant style, water and city skyline"},
            {"name": "Yoga Parc", "desc": "doing yoga in a Quebec park at sunrise, mid-back ponytail, athletic wear, serene peaceful atmosphere"},
            {"name": "Spa Charlevoix", "desc": "at a luxury Charlevoix spa, white robe, touching her beautiful mid-back hair, mountain view through window, serene atmosphere"},
            {"name": "Cozy Home", "desc": "in cozy home setting brushing her mid-back hair near window, Sunday morning vibes, soft natural light, peaceful moment"},
            {"name": "Wine Tasting", "desc": "at an outdoor wine tasting in Quebec wine country, gorgeous mid-back hair, sophisticated casual style, warm afternoon light"},
            {"name": "Art Gallery", "desc": "at a Montreal art gallery opening, stunning mid-back hair, elegant black dress, modern art backdrop"},
            {"name": "Autumn Leaves", "desc": "walking through autumn leaves in Parc Mont-Royal, mid-back hair flowing, cozy fall fashion, golden hour lighting"},
            {"name": "Summer Terrasse", "desc": "at a summer terrasse in Old Montreal, mid-back hair catching sunset light, relaxed elegant style, cobblestone street visible"},
        ],
        "prompt_template": """{scene_prompt}

HAIR LENGTH - THIS IS THE MOST IMPORTANT RULE:
⚠️ HAIR MUST BE SHOULDER-LENGTH TO MID-BACK MAXIMUM ⚠️
Hair ends at BRA-STRAP level (middle of back).
Hair is ABOVE the waist - NOT touching waist.
Hair is SHORT OF the hips - nowhere near hips.
DO NOT generate long mermaid hair.
DO NOT generate hair past the waist.
DO NOT generate hair reaching hips or thighs.
CORRECT: Hair tips end between shoulder blades and waist.
WRONG: Hair going to waist, hips, thighs, or knees.

No text, no watermarks, no logos."""
    },
    
    "LUX-PROMO": {
        "name": "Promotions Produits",
        "fichier": "scripts/product_promo_cron.py",
        "lignes": "213-237",
        "description": "Promotions et mises en vedette",
        "frequence": "Variable",
        "scenes": [
            {"name": "Quebec Settings variés", "desc": "Décors québécois variés (terrasses, spas, événements)"}
        ],
        "prompt_template": """Real photograph of a glamorous Québec woman in her early 30s {setting_desc}.

HAIR COLOR (MANDATORY - MUST MATCH EXACTLY):
{product_color} - {color_description}

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

The hair showcases {product_name} shade. Professional photography.
No text, no watermarks."""
    },
    
    "LUX-MAGAZINE": {
        "name": "Magazine Style",
        "fichier": "scripts/magazine_cron.py",
        "lignes": "62-72",
        "description": "Posts style magazine haut de gamme",
        "frequence": "Variable",
        "scenes": [
            {"name": "Yacht Sunset", "desc": "glamorous woman on luxury yacht deck at sunset"},
            {"name": "Rooftop Bar", "desc": "two elegant women at exclusive rooftop bar"},
            {"name": "Fashion Week", "desc": "glamorous woman at fashion week backstage"},
        ],
        "prompt_template": """Real photograph of glamorous woman on luxury yacht deck at sunset.
HAIR LENGTH RULE: Hair MUST end at BRA-STRAP level (middle of back). Hair is ABOVE waist, NOT touching waist. Hair does NOT reach hips or thighs. Think medium-long NOT ultra-long.
Soft flowing waves with volume. Elegant white designer dress. Shot from 3/4 back angle. Golden hour lighting. No text, no watermarks.

--- OU ---

Real photograph of two elegant women at exclusive rooftop bar.
HAIR LENGTH RULE: Both have hair ending at MID-BACK level only. Hair ABOVE waist, NOT at hips. BRA-STRAP length maximum.
Chic evening wear. Golden hour lighting. No text.

--- OU ---

Real photograph of glamorous woman at fashion week backstage.
HAIR LENGTH RULE: Hair MUST end at BRA-STRAP level. Hair does NOT reach waist or hips. MEDIUM-LONG only, not ultra-long.
Soft professional lighting. No text."""
    },
}


# ============================================
# 🔌 ENDPOINTS API
# ============================================

@router.get("/")
async def get_all_prompts():
    """Retourne tous les prompts organisés par cron."""
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "total_crons": len(CRON_PROMPTS),
        "crons": CRON_PROMPTS
    }


@router.get("/list")
async def get_prompts_list():
    """Retourne une liste simplifiée des crons disponibles."""
    return {
        "success": True,
        "crons": [
            {
                "id": cron_id,
                "name": data["name"],
                "fichier": data["fichier"],
                "frequence": data["frequence"],
                "description": data["description"]
            }
            for cron_id, data in CRON_PROMPTS.items()
        ]
    }


@router.get("/{cron_id}")
async def get_prompt_by_cron(cron_id: str):
    """Retourne le prompt d'un cron spécifique."""
    cron_id_upper = cron_id.upper()
    
    if cron_id_upper not in CRON_PROMPTS:
        return {
            "success": False,
            "error": f"Cron '{cron_id}' non trouvé",
            "available_crons": list(CRON_PROMPTS.keys())
        }
    
    return {
        "success": True,
        "cron_id": cron_id_upper,
        "data": CRON_PROMPTS[cron_id_upper]
    }


@router.get("/rules/hair-length")
async def get_hair_length_rules():
    """Retourne les règles de longueur de cheveux utilisées."""
    return {
        "success": True,
        "rule_name": "HAIR LENGTH - STRICT RULE",
        "summary": "Cheveux au niveau BRA-STRAP / MID-BACK (3/4 du dos)",
        "rules": [
            "Hair ends at BRA-STRAP level (middle of back)",
            "Hair is ABOVE the waist - NOT touching waist",
            "Hair is SHORT OF the hips - nowhere near hips",
            "Hair length is approximately 18-20 inches from scalp",
            "DO NOT generate long mermaid hair",
            "DO NOT generate hair past the waist",
            "DO NOT generate hair reaching hips or thighs",
            "Think 'medium-long' NOT 'ultra-long'"
        ],
        "correct": "Hair tips end between shoulder blades and waist",
        "wrong": "Hair going to waist, hips, thighs, or knees"
    }


@router.get("/rules/diversity")
async def get_diversity_rules():
    """Retourne les règles de diversité utilisées."""
    return {
        "success": True,
        "rule_name": "DIVERSITY REQUIREMENT",
        "summary": "Chaque femme doit avoir un visage DIFFÉRENT",
        "rules": [
            "Different face shapes (oval, round, square, heart)",
            "Different nose shapes and sizes",
            "Different eye shapes and colors",
            "Mix of ethnicities is welcome (Québécoise can be diverse)",
            "NOT clones or twins - they are DIFFERENT individuals",
            "Variety in body types is natural",
            "Other women should have DIFFERENT hair colors"
        ]
    }
