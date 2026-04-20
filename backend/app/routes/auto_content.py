"""
🔵 FACEBOOK AUTO-POST AVEC APPROBATION EMAIL
=============================================
Génère du contenu et l'envoie par email pour approbation
avant publication sur Facebook.

Types de contenu:
- product: Posts produits (Genius, Tape-in, Halo, etc.)
- educational: Conseils, tutoriels, erreurs à éviter
- testimonial: Témoignages de salons
- b2b: Posts pour professionnels
- weekend: Inspiration weekend, lifestyle
- magazine: Articles style magazine (tendances internationales)

Flow:
1. Cron déclenche la génération
2. Email envoyé pour approbation
3. Clic sur Approuver → Publication Facebook
"""

import os
import logging
import random
import httpx
from datetime import datetime
from typing import Dict, Optional, List
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auto-content", tags=["Auto Content with Approval"])

# Configuration
API_URL = os.getenv("API_URL", "https://luxura-inventory-api.onrender.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ==================== TEMPLATES PAR TYPE ====================

CONTENT_TYPES = {
    "product": {
        "name": "Produit Vedette",
        "description": "Post mettant en avant un produit spécifique",
        "themes": ["genius", "tape", "halo", "i-tip", "ponytail", "clip-in"],
        "emoji": "✨"
    },
    "educational": {
        "name": "Éducatif",
        "description": "Conseils, tutoriels, erreurs à éviter",
        "themes": ["entretien", "pose", "erreurs", "comparatif", "choix_couleur", "duree_vie"],
        "emoji": "📚"
    },
    "testimonial": {
        "name": "Témoignage",
        "description": "Témoignages de salons partenaires",
        "themes": ["satisfaction", "transformation", "resultats"],
        "emoji": "💬"
    },
    "b2b": {
        "name": "Professionnel B2B",
        "description": "Contenu pour salons et coiffeurs",
        "themes": ["offre_salon", "formation", "partenariat", "marge"],
        "emoji": "💼"
    },
    "weekend": {
        "name": "Weekend & Inspiration",
        "description": "Contenu lifestyle et inspiration",
        "themes": ["mariage", "event", "lifestyle", "avant_apres", "motivation"],
        "emoji": "🌟"
    },
    "magazine": {
        "name": "Magazine Tendances",
        "description": "Articles style magazine sur les tendances coiffure",
        "themes": ["tendance_coupe", "comparatif_extensions", "conseils_erreurs", "quiet_luxury", "inspiration_internationale"],
        "emoji": "📰"
    }
}


# ==================== PROMPTS DE GÉNÉRATION ====================

GENERATION_PROMPTS = {
    "product": """Tu es la social media manager de Luxura Distribution, distributeur d'extensions capillaires premium au Québec.

Crée un post Facebook pour mettre en avant le produit: {theme}

PRODUITS LUXURA:
- Genius Weft: Extensions sans colle, ultra-plates, réutilisables
- Tape-In: Bandes adhésives 4cm, pose rapide, 6-8 semaines
- Halo: Fil invisible, pose 2 min, parfait pour essayer
- I-Tip: Micro-anneaux, très discret, idéal cheveux fins
- Ponytail: Queue de cheval clip-on, volume instantané
- Clip-In: Extensions amovibles, pose quotidienne facile

RÈGLES:
1. Titre accrocheur avec emoji
2. 3 points forts du produit
3. Prix à partir de X$ (estimé)
4. CTA vers luxuradistribution.com
5. 100% en français québécois
6. Pas de ton trop commercial, rester authentique

Retourne UNIQUEMENT le post prêt à publier.""",

    "educational": """Tu es la social media manager de Luxura Distribution.

Crée un post Facebook ÉDUCATIF sur le thème: {theme}

THÈMES POSSIBLES:
- entretien: Comment prendre soin de ses extensions
- pose: Techniques de pose professionnelles
- erreurs: Erreurs à éviter avec les extensions
- comparatif: Différences entre types d'extensions
- choix_couleur: Comment choisir sa teinte
- duree_vie: Maximiser la durée de vie des extensions

RÈGLES:
1. Titre accrocheur avec emoji éducatif (💡📚✨)
2. 3-5 conseils concrets
3. Ton expert mais accessible
4. Question engageante à la fin
5. 100% en français québécois
6. Lien subtil vers Luxura

Retourne UNIQUEMENT le post prêt à publier.""",

    "testimonial": """Tu es la social media manager de Luxura Distribution.

Crée un post Facebook TÉMOIGNAGE fictif mais réaliste.

CONTEXTE:
- Salons partenaires au Québec (Beauce, Lévis, Montréal, Laval)
- Stylistes qui utilisent nos extensions Remy russes
- Clientes satisfaites

RÈGLES:
1. Nom de salon québécois réaliste
2. Citation authentique (pas trop parfaite)
3. Ville québécoise
4. Résultats concrets mentionnés
5. Emoji 💬 ou ⭐
6. Remerciment sincère

Retourne UNIQUEMENT le post prêt à publier.""",

    "b2b": """Tu es la social media manager de Luxura Distribution.

Crée un post Facebook B2B pour les SALONS ET COIFFEURS sur le thème: {theme}

THÈMES:
- offre_salon: Offres spéciales pour professionnels
- formation: Formation pose d'extensions
- partenariat: Devenir partenaire Luxura
- marge: Rentabilité des extensions pour salons

RÈGLES:
1. Ton professionnel mais chaleureux
2. Avantages business clairs (marges, clientèle, qualité)
3. CTA spécifique (contactez-nous, formulaire pro)
4. 100% en français québécois
5. Pas de prix publics, focus partenariat

Retourne UNIQUEMENT le post prêt à publier.""",

    "weekend": """Tu es la social media manager de Luxura Distribution.

Crée un post Facebook WEEKEND/INSPIRATION sur le thème: {theme}

THÈMES:
- mariage: Coiffures de mariée avec extensions
- event: Looks pour événements spéciaux
- lifestyle: Beauté au quotidien
- avant_apres: Transformations inspirantes
- motivation: Citations beauté/confiance

RÈGLES:
1. Ton léger, inspirant, feel-good
2. Visuellement évocateur (décrire le look)
3. Emoji appropriés (🌟💫✨👰💃)
4. Question ou invitation à partager
5. 100% en français québécois
6. Hashtags tendance

Retourne UNIQUEMENT le post prêt à publier.""",
}


# ==================== IMAGES PAR TYPE ====================

STOCK_IMAGES = {
    "product": [
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e",  # Hair styling
        "https://images.unsplash.com/photo-1560066984-138dadb4c035",  # Salon
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e",  # Beautiful hair
    ],
    "educational": [
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e",
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f",
        "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91",
    ],
    "testimonial": [
        "https://images.unsplash.com/photo-1560066984-138dadb4c035",  # Salon
        "https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f",  # Stylist
    ],
    "b2b": [
        "https://images.unsplash.com/photo-1560066984-138dadb4c035",
        "https://images.unsplash.com/photo-1633681926022-84c23e8cb2d6",
    ],
    "weekend": [
        "https://images.unsplash.com/photo-1496440737103-cd596325d314",  # Flowing hair
        "https://images.unsplash.com/photo-1503830232159-4b417691001e",  # Lifestyle
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e",
    ],
    "magazine": [
        "https://images.unsplash.com/photo-1496440737103-cd596325d314",
        "https://images.pexels.com/photos/113042/pexels-photo-113042.jpeg",
        "https://images.unsplash.com/photo-1503830232159-4b417691001e",
    ],
}


# ==================== GÉNÉRATION DE CONTENU ====================

async def generate_content(content_type: str, theme: str = None) -> Dict:
    """
    Génère du contenu avec GPT-4o
    """
    if content_type not in CONTENT_TYPES:
        raise ValueError(f"Type de contenu invalide: {content_type}")
    
    type_config = CONTENT_TYPES[content_type]
    
    # Sélectionner un thème aléatoire si non spécifié
    if not theme:
        theme = random.choice(type_config["themes"])
    
    # Pour le type magazine, utiliser le générateur spécialisé
    if content_type == "magazine":
        from app.services.magazine_content_generator import MagazineContentGenerator
        generator = MagazineContentGenerator()
        result = await generator.generate_magazine_post(theme=theme, country_inspiration="auto")
        return {
            "content_type": "magazine",
            "theme": theme,
            "text": result["full_text"],
            "hashtags": result["hashtags"],
            "image_url": result["fallback_image_url"],
            "image_prompt": result["image_prompt"],
        }
    
    # Génération standard avec GPT-4o
    prompt_template = GENERATION_PROMPTS.get(content_type, GENERATION_PROMPTS["product"])
    prompt = prompt_template.format(theme=theme)
    
    if not OPENAI_API_KEY:
        # Fallback si pas de clé OpenAI
        return _generate_fallback_content(content_type, theme)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": "Tu es une experte en marketing beauté pour Luxura Distribution au Québec. Tu écris en français québécois naturel."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.8
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result["choices"][0]["message"]["content"].strip()
                
                # Sélectionner une image
                images = STOCK_IMAGES.get(content_type, STOCK_IMAGES["product"])
                image_url = random.choice(images)
                
                # Extraire ou générer des hashtags
                hashtags = _extract_hashtags(text, content_type)
                
                return {
                    "content_type": content_type,
                    "theme": theme,
                    "text": text,
                    "hashtags": hashtags,
                    "image_url": image_url,
                }
            else:
                logger.error(f"Erreur OpenAI: {response.status_code}")
                return _generate_fallback_content(content_type, theme)
                
    except Exception as e:
        logger.error(f"Erreur génération: {e}")
        return _generate_fallback_content(content_type, theme)


def _generate_fallback_content(content_type: str, theme: str) -> Dict:
    """Génère du contenu de secours si l'API échoue"""
    
    fallback_texts = {
        "product": f"""✨ **PRODUIT VEDETTE | Extensions {theme.title()}**

Découvrez nos extensions {theme} de qualité professionnelle!

🎯 Pourquoi nos clientes les adorent:
• Cheveux 100% Remy russes
• Cuticules alignées pour un look naturel
• Durée de vie exceptionnelle

💰 À partir de 199$
🚚 Livraison rapide au Québec

👉 luxuradistribution.com

#LuxuraDistribution #ExtensionsCheveux #Quebec""",

        "educational": f"""📚 **CONSEIL PRO | {theme.replace('_', ' ').title()}**

Saviez-vous que prendre soin de vos extensions peut doubler leur durée de vie?

Voici 3 conseils essentiels:
1. Brossez délicatement, des pointes vers les racines
2. Utilisez des produits sans sulfate
3. Évitez la chaleur excessive

Une question? On est là pour vous! 💬

👉 luxuradistribution.com

#ConseilsCoiffure #Extensions #Luxura""",

        "weekend": f"""🌟 **INSPIRATION WEEKEND**

Parce que chaque femme mérite de se sentir belle et confiante.

Nos extensions vous permettent de réaliser tous vos rêves capillaires, que ce soit pour un mariage, une soirée, ou simplement pour le plaisir!

Quel look rêvez-vous d'essayer? 💫

👉 luxuradistribution.com

#WeekendVibes #BeautéQuébec #Luxura"""
    }
    
    images = STOCK_IMAGES.get(content_type, STOCK_IMAGES["product"])
    
    return {
        "content_type": content_type,
        "theme": theme,
        "text": fallback_texts.get(content_type, fallback_texts["product"]),
        "hashtags": ["#Luxura", "#ExtensionsCheveux", "#Quebec"],
        "image_url": random.choice(images),
    }


def _extract_hashtags(text: str, content_type: str) -> List[str]:
    """Extrait les hashtags du texte ou en génère"""
    import re
    hashtags = re.findall(r'#\w+', text)
    
    if hashtags:
        return hashtags[:7]
    
    # Hashtags par défaut selon le type
    default_hashtags = {
        "product": ["#LuxuraDistribution", "#ExtensionsCheveux", "#Quebec", "#Coiffure"],
        "educational": ["#ConseilsCoiffure", "#Extensions", "#Luxura", "#TutorielBeauté"],
        "testimonial": ["#Témoignage", "#SalonPartenaire", "#Luxura", "#Satisfaction"],
        "b2b": ["#CoiffeurQuébec", "#SalonCoiffure", "#Luxura", "#Professionnel"],
        "weekend": ["#WeekendVibes", "#Inspiration", "#Luxura", "#BeautéQuébec"],
        "magazine": ["#Tendances2026", "#Coiffure", "#Luxura", "#StyleFéminin"],
    }
    
    return default_hashtags.get(content_type, ["#Luxura", "#Quebec"])


# ==================== ENDPOINTS ====================

@router.post("/generate/{content_type}")
async def generate_and_send_for_approval(
    content_type: str,
    theme: str = Query(default=None, description="Thème spécifique (optionnel)"),
    send_email: bool = Query(default=True, description="Envoyer l'email d'approbation")
):
    """
    🎨 Génère du contenu et l'envoie pour approbation par email
    
    Types disponibles:
    - product: Posts produits
    - educational: Conseils et tutoriels
    - testimonial: Témoignages
    - b2b: Contenu professionnel
    - weekend: Inspiration weekend
    - magazine: Articles tendances
    """
    if content_type not in CONTENT_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Type invalide. Valides: {list(CONTENT_TYPES.keys())}"
        )
    
    logger.info(f"🎨 Génération contenu: {content_type} | theme={theme}")
    
    # Générer le contenu
    content = await generate_content(content_type, theme)
    
    if send_email:
        # Envoyer pour approbation
        from app.services.email_approval import send_approval_email
        from app.routes.content import add_pending_post
        
        post_data = {
            "text": content["text"],
            "full_text": content["text"],
            "hashtags": content["hashtags"],
            "image_url": content["image_url"],
            "fallback_image_url": content["image_url"],
            "content_type": content_type,
            "theme": content.get("theme"),
            "source_title": f"Auto-génération {CONTENT_TYPES[content_type]['name']}",
            "source_url": "https://luxuradistribution.com"
        }
        
        result = await send_approval_email(post_data)
        
        if result.get("success"):
            post_id = result.get("post_id")
            add_pending_post(post_id, post_data)
            
            return {
                "success": True,
                "content_type": content_type,
                "theme": content.get("theme"),
                "post_id": post_id,
                "message": "📧 Email d'approbation envoyé!",
                "approve_url": f"{API_URL}/api/content/approve/{post_id}",
                "reject_url": f"{API_URL}/api/content/reject/{post_id}",
                "preview": content["text"][:200] + "..."
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "Erreur envoi email"))
    
    # Sans email, retourner juste le contenu
    return {
        "success": True,
        "content_type": content_type,
        "theme": content.get("theme"),
        "content": content,
        "message": "Contenu généré (email non envoyé)"
    }


@router.get("/types")
async def list_content_types():
    """
    📋 Liste tous les types de contenu disponibles
    """
    return {
        "content_types": CONTENT_TYPES,
        "total": len(CONTENT_TYPES)
    }


@router.post("/daily-batch")
async def generate_daily_batch(
    types: List[str] = Query(default=["product", "educational", "weekend"], description="Types à générer")
):
    """
    📦 Génère un lot quotidien de contenu pour approbation
    
    Par défaut: 1 product + 1 educational + 1 weekend
    """
    results = []
    
    for content_type in types:
        if content_type not in CONTENT_TYPES:
            results.append({"type": content_type, "error": "Type invalide"})
            continue
        
        try:
            content = await generate_content(content_type)
            
            # Envoyer pour approbation
            from app.services.email_approval import send_approval_email
            from app.routes.content import add_pending_post
            
            post_data = {
                "text": content["text"],
                "full_text": content["text"],
                "hashtags": content["hashtags"],
                "image_url": content["image_url"],
                "content_type": content_type,
                "theme": content.get("theme"),
            }
            
            result = await send_approval_email(post_data)
            
            if result.get("success"):
                post_id = result.get("post_id")
                add_pending_post(post_id, post_data)
                
                results.append({
                    "type": content_type,
                    "theme": content.get("theme"),
                    "post_id": post_id,
                    "status": "email_sent"
                })
            else:
                results.append({
                    "type": content_type,
                    "error": result.get("message")
                })
                
        except Exception as e:
            results.append({
                "type": content_type,
                "error": str(e)
            })
    
    return {
        "success": True,
        "generated": len([r for r in results if "post_id" in r]),
        "failed": len([r for r in results if "error" in r]),
        "results": results,
        "message": "📧 Vérifiez votre email pour approuver les posts!"
    }


@router.post("/schedule-week")
async def schedule_week_content():
    """
    📅 Génère le contenu pour une semaine complète
    
    Calendrier:
    - Lundi: Product
    - Mardi: Educational
    - Mercredi: B2B
    - Jeudi: Product
    - Vendredi: Educational
    - Samedi: Weekend
    - Dimanche: Magazine
    """
    week_schedule = [
        ("Lundi", "product"),
        ("Mardi", "educational"),
        ("Mercredi", "b2b"),
        ("Jeudi", "product"),
        ("Vendredi", "educational"),
        ("Samedi", "weekend"),
        ("Dimanche", "magazine"),
    ]
    
    results = []
    
    for day, content_type in week_schedule:
        try:
            content = await generate_content(content_type)
            
            from app.services.email_approval import send_approval_email
            from app.routes.content import add_pending_post
            
            post_data = {
                "text": content["text"],
                "full_text": content["text"],
                "hashtags": content["hashtags"],
                "image_url": content["image_url"],
                "content_type": content_type,
                "scheduled_day": day,
            }
            
            result = await send_approval_email(post_data)
            
            if result.get("success"):
                post_id = result.get("post_id")
                add_pending_post(post_id, post_data)
                results.append({
                    "day": day,
                    "type": content_type,
                    "post_id": post_id,
                    "status": "pending_approval"
                })
            else:
                results.append({
                    "day": day,
                    "type": content_type,
                    "error": result.get("message")
                })
                
        except Exception as e:
            results.append({
                "day": day,
                "type": content_type,
                "error": str(e)
            })
    
    return {
        "success": True,
        "week_content": results,
        "total_generated": len([r for r in results if "post_id" in r]),
        "message": "📧 7 emails envoyés! Approuvez ceux que vous voulez publier."
    }
