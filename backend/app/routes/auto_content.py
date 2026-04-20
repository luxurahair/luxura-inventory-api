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
    "product": """Tu es une amie passionnée de beauté qui partage sur Facebook. 
Tu parles naturellement, comme à une copine, pas comme une pub.

Écris un post Facebook NATUREL pour parler du produit: {theme}

PRODUITS LUXURA:
- Genius Weft: Extensions sans colle, ultra-plates, réutilisables
- Tape-In: Bandes adhésives 4cm, pose rapide, 6-8 semaines
- Halo: Fil invisible, pose 2 min, parfait pour essayer
- I-Tip: Micro-anneaux, très discret, idéal cheveux fins
- Ponytail: Queue de cheval clip-on, volume instantané
- Clip-In: Extensions amovibles, pose quotidienne facile

TON NATUREL À UTILISER:
- Parle comme à une amie ("T'as vu ces extensions?", "Sérieux, ça change tout!")
- Partage une vraie expérience ou observation
- Pose une question authentique
- Pas de "découvrez nos produits" ou "commandez maintenant"
- Utilise des expressions québécoises naturelles

Retourne UNIQUEMENT le post prêt à publier (100-150 mots max).""",

    "educational": """Tu es une coiffeuse passionnée qui partage ses conseils sur Facebook.
Tu parles naturellement, comme à une cliente que t'aimes bien.

Écris un post Facebook CONSEILS sur le thème: {theme}

THÈMES:
- entretien: Comment prendre soin de ses extensions
- pose: Techniques de pose professionnelles
- erreurs: Erreurs à éviter avec les extensions
- comparatif: Différences entre types d'extensions
- choix_couleur: Comment choisir sa teinte
- duree_vie: Maximiser la durée de vie des extensions

TON NATUREL:
- "Bon, je vais te dire un truc que personne explique..."
- "Sérieux, arrêtez de faire cette erreur!"
- "La vraie question c'est..."
- Partage des trucs concrets, pas du blabla marketing
- Utilise "tu" pas "vous"

Retourne UNIQUEMENT le post prêt à publier (100-150 mots max).""",

    "testimonial": """Tu partages l'expérience d'une vraie cliente satisfaite.
Le ton doit être AUTHENTIQUE, pas une pub.

Écris un post Facebook TÉMOIGNAGE fictif mais réaliste.

CONTEXTE:
- Salons partenaires au Québec
- Clientes vraies avec leurs mots à elles
- Résultats concrets, pas de superlatifs

TON NATUREL:
- Citation avec les mots de la cliente (pas parfaite, naturelle)
- "Elle m'a dit: 'Ça fait 3 mois pis sont encore belles!'"
- Mentionner le nom du salon et la ville
- Une vraie réaction, pas du marketing

Retourne UNIQUEMENT le post prêt à publier (80-120 mots max).""",

    "b2b": """Tu parles à des coiffeuses professionnelles, de pro à pro.
Pas de blabla corporate, du concret.

Écris un post Facebook B2B pour les SALONS sur le thème: {theme}

THÈMES:
- offre_salon: Avantages pour les pros
- formation: Formation pose d'extensions
- partenariat: Devenir partenaire
- marge: Rentabilité des extensions

TON PRO MAIS HUMAIN:
- "Entre nous, les extensions c'est la meilleure marge du salon"
- "On forme les coiffeuses qui veulent se spécialiser"
- Chiffres concrets si possible
- Pas de "nous sommes fiers de..."

Retourne UNIQUEMENT le post prêt à publier (100-150 mots max).""",

    "weekend": """Tu partages de l'inspiration beauté le weekend.
Ton détendu, feel-good, pas de vente.

Écris un post Facebook INSPIRATION sur le thème: {theme}

THÈMES:
- mariage: Coiffures de mariée
- event: Looks pour événements
- lifestyle: Beauté au quotidien
- avant_apres: Transformations
- motivation: Confiance en soi

TON WEEKEND:
- "Le samedi c'est fait pour se sentir belle"
- "Qui d'autre rêve de cheveux comme ça?"
- Question engageante naturelle
- Partage d'inspiration, pas de pitch

Retourne UNIQUEMENT le post prêt à publier (80-120 mots max).""",
}


# ==================== IMAGES - VRAIES PHOTOS STOCK HAUTE QUALITÉ ====================
# Photos réelles de femmes avec beaux cheveux (Unsplash/Pexels)
# Plus naturelles que les images générées par AI

REAL_PHOTO_URLS = {
    "product": [
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=1200&fit=crop",  # Femme cheveux longs naturels
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=1200&fit=crop",  # Cheveux brillants
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=1200&fit=crop",  # Portrait beauté
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=1200&h=1200&fit=crop",  # Femme souriante cheveux
        "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=1200&h=1200&fit=crop",  # Beauté naturelle
    ],
    "educational": [
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1200&h=1200&fit=crop",  # Salon coiffure
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=1200&fit=crop",  # Styling cheveux
        "https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=1200&h=1200&fit=crop",  # Coiffeuse au travail
        "https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?w=1200&h=1200&fit=crop",  # Salon pro
    ],
    "testimonial": [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=1200&fit=crop",  # Portrait femme heureuse
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=1200&fit=crop",  # Femme naturelle
        "https://images.unsplash.com/photo-1524250502761-1ac6f2e30d43?w=1200&h=1200&fit=crop",  # Beauté authentique
    ],
    "b2b": [
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1200&h=1200&fit=crop",  # Salon moderne
        "https://images.unsplash.com/photo-1633681926022-84c23e8cb2d6?w=1200&h=1200&fit=crop",  # Équipement pro
        "https://images.unsplash.com/photo-1562322140-8baeececf3df?w=1200&h=1200&fit=crop",  # Coiffeuse pro
    ],
    "weekend": [
        "https://images.unsplash.com/photo-1496440737103-cd596325d314?w=1200&h=1200&fit=crop",  # Cheveux au vent
        "https://images.unsplash.com/photo-1503830232159-4b417691001e?w=1200&h=1200&fit=crop",  # Lifestyle
        "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=1200&h=1200&fit=crop",  # Femme glamour
        "https://images.unsplash.com/photo-1513379733131-47fc74b45fc7?w=1200&h=1200&fit=crop",  # Mariée
    ],
    "magazine": [
        "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=1200&h=1200&fit=crop",  # Editorial
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=1200&h=1200&fit=crop",  # Fashion
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=1200&fit=crop",  # Model beauté
    ],
}

# Garder les anciennes pour fallback
STOCK_IMAGES = REAL_PHOTO_URLS

# Prompts d'image par type de contenu
IMAGE_PROMPTS = {
    "product": "Professional product photography of premium hair extensions, elegant display, soft lighting, luxury beauty product, white background, high-end cosmetics style",
    "educational": "Woman with beautiful healthy hair in a salon setting, professional lighting, educational beauty content style, clean aesthetic",
    "testimonial": "Happy woman in a professional hair salon, natural smile, beautiful hair transformation, authentic moment",
    "b2b": "Professional hair salon interior, modern equipment, elegant atmosphere, business professional setting",
    "weekend": "Elegant woman with gorgeous flowing hair, lifestyle photography, golden hour lighting, aspirational beauty, natural movement",
    "magazine": "Fashion editorial style, woman with trendy hairstyle, magazine cover quality, high fashion beauty photography",
}


async def generate_ai_image(content_type: str, text: str = "") -> Dict:
    """
    Génère une image avec Grok (priorité) ou DALL-E 3
    
    Flow:
    1. Utilise Grok pour créer un prompt contextuel basé sur le texte
    2. Génère l'image avec Grok
    3. Fallback DALL-E si Grok échoue
    4. Fallback Stock si tout échoue
    
    Returns:
        Dict avec url et source (grok/dalle/stock)
    """
    grok_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    dalle_key = os.getenv("OPENAI_API_KEY")
    
    base_prompt = IMAGE_PROMPTS.get(content_type, IMAGE_PROMPTS["product"])
    
    # ==================== ÉTAPE 1: GÉNÉRER LE PROMPT AVEC GROK ====================
    contextual_prompt = base_prompt
    
    if grok_key and text:
        try:
            logger.info(f"🤖 Génération du prompt image avec Grok...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {grok_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-3-mini",
                        "messages": [
                            {
                                "role": "system", 
                                "content": """Tu es un expert en création de prompts pour Grok Imagine, spécialisé en photographie beauté/coiffure haut de gamme.

Crée un prompt DÉTAILLÉ en ANGLAIS pour générer une image EXCEPTIONNELLE de qualité magazine.

ÉLÉMENTS OBLIGATOIRES dans le prompt:
1. SUJET: Femme élégante avec cheveux magnifiques (mi-longs à longs, jamais courts)
2. CHEVEUX: Brillants, soyeux, mouvement naturel, volume, texture visible
3. ÉCLAIRAGE: Lumière naturelle douce, golden hour, rim lighting subtil
4. COMPOSITION: Portrait ou demi-corps, regard engageant ou profil élégant
5. STYLE: Editorial magazine, Vogue quality, high fashion beauty
6. TECHNIQUE: Shot on Hasselblad, 85mm f/1.4, shallow depth of field, bokeh
7. AMBIANCE: Luxueuse, aspirationnelle, féminine, sophistiquée
8. COULEURS: Tons chauds, palette harmonieuse

INTERDITS:
- Texte, logos, watermarks
- Visages déformés ou irréalistes
- Cheveux courts ou abîmés
- Poses rigides ou artificielles

Retourne UNIQUEMENT le prompt en anglais (250 mots max), rien d'autre."""
                            },
                            {
                                "role": "user",
                                "content": f"Crée un prompt image PREMIUM pour ce post Facebook de Luxura Distribution (extensions capillaires):\n\n{text[:600]}"
                            }
                        ],
                        "max_tokens": 350,
                        "temperature": 0.8
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    contextual_prompt = result["choices"][0]["message"]["content"].strip()
                    logger.info(f"✅ Prompt Grok généré: {contextual_prompt[:150]}...")
                else:
                    logger.warning(f"Grok prompt failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"Grok prompt error: {e}")
    
    # ==================== ÉTAPE 2: GÉNÉRER L'IMAGE AVEC GROK (PRIORITÉ) ====================
    if grok_key:
        # Essayer plusieurs modèles Grok
        grok_models = ["grok-imagine-image", "grok-2-image", "grok-2-image-1212"]
        
        for model_name in grok_models:
            try:
                logger.info(f"🤖 Génération image avec Grok ({model_name}) - 2K quality...")
                async with httpx.AsyncClient(timeout=120.0) as client:
                    # Améliorer le prompt pour meilleure qualité
                    enhanced_prompt = f"""{contextual_prompt}

STYLE: Ultra high quality professional beauty photography, magazine editorial quality, 
sharp focus, natural soft lighting, warm color tones, elegant and aspirational mood,
shot with professional DSLR camera, shallow depth of field, bokeh background,
skin texture visible but flattering, hair looks silky and healthy with natural shine,
NO text, NO watermarks, NO logos, photorealistic, 8K quality render."""

                    response = await client.post(
                        "https://api.x.ai/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {grok_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_name,
                            "prompt": enhanced_prompt,
                            "n": 1,
                            "resolution": "2k",  # Haute résolution
                            "aspect_ratio": "1:1"  # Carré pour Facebook/Instagram
                        }
                    )
                    
                    logger.info(f"Grok ({model_name}) response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"Grok response: {result}")
                        
                        # Grok peut retourner l'URL dans différents formats
                        image_url = None
                        if "data" in result and len(result["data"]) > 0:
                            image_url = result["data"][0].get("url") or result["data"][0].get("b64_json")
                        
                        if image_url:
                            logger.info(f"🤖 Image Grok ({model_name}) 2K générée avec succès!")
                            return {
                                "url": image_url, 
                                "source": "grok",
                                "model": model_name,
                                "resolution": "2k",
                                "prompt_used": contextual_prompt
                            }
                        else:
                            logger.warning(f"Grok ({model_name}): pas d'URL dans la réponse: {result}")
                    elif response.status_code == 404:
                        # Modèle non disponible, essayer le suivant
                        logger.info(f"Grok ({model_name}): modèle non disponible, essai suivant...")
                        continue
                    else:
                        error_text = response.text[:500] if response.text else "No error text"
                        logger.warning(f"Grok ({model_name}) failed: {response.status_code} - {error_text}")
                        
            except Exception as e:
                logger.warning(f"Grok ({model_name}) error: {e}")
                continue
    
    # ==================== ÉTAPE 3: FALLBACK DALL-E 3 ====================
    if dalle_key:
        try:
            logger.info(f"🎨 Fallback vers DALL-E 3...")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {dalle_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": f"{contextual_prompt}. Style: premium beauty brand, no text in image.",
                        "n": 1,
                        "size": "1024x1024",
                        "quality": "standard"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    image_url = result["data"][0]["url"]
                    logger.info(f"🎨 Image DALL-E 3 générée pour {content_type}")
                    return {
                        "url": image_url, 
                        "source": "dalle",
                        "prompt_used": contextual_prompt
                    }
                else:
                    logger.warning(f"DALL-E failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"DALL-E error: {e}")
    
    # ==================== ÉTAPE 4: FALLBACK STOCK ====================
    logger.info(f"📷 Fallback vers images stock")
    images = STOCK_IMAGES.get(content_type, STOCK_IMAGES["product"])
    return {
        "url": random.choice(images), 
        "source": "stock",
        "prompt_used": None
    }


# ==================== GÉNÉRATION DE CONTENU ====================

async def generate_content(content_type: str, theme: str = None, generate_ai_images: bool = True) -> Dict:
    """
    Génère du contenu avec GPT-4o
    
    Args:
        content_type: Type de contenu
        theme: Thème spécifique (optionnel)
        generate_ai_images: Si True, essaie de générer des images avec DALL-E/Grok
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
        
        # Générer image AI si demandé
        if generate_ai_images:
            image_result = await generate_ai_image(content_type, result["full_text"])
        else:
            images = STOCK_IMAGES.get(content_type, STOCK_IMAGES["product"])
            image_result = {"url": random.choice(images), "source": "stock"}
        
        return {
            "content_type": "magazine",
            "theme": theme,
            "text": result["full_text"],
            "hashtags": result["hashtags"],
            "image_url": image_result["url"],
            "image_source": image_result["source"],
            "image_prompt": result.get("image_prompt", ""),
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
                
                # Générer image AI si demandé
                if generate_ai_images:
                    image_result = await generate_ai_image(content_type, text)
                else:
                    images = STOCK_IMAGES.get(content_type, STOCK_IMAGES["product"])
                    image_result = {"url": random.choice(images), "source": "stock"}
                
                # Extraire ou générer des hashtags
                hashtags = _extract_hashtags(text, content_type)
                
                return {
                    "content_type": content_type,
                    "theme": theme,
                    "text": text,
                    "hashtags": hashtags,
                    "image_url": image_result["url"],
                    "image_source": image_result["source"],
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
    send_email: bool = Query(default=True, description="Envoyer l'email d'approbation"),
    ai_images: bool = Query(default=False, description="Utiliser Grok AI pour images (défaut: vraies photos stock)"),
    real_photos: bool = Query(default=True, description="Utiliser vraies photos Unsplash (plus naturel)")
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
    
    Images:
    - real_photos=true (DÉFAUT): Vraies photos Unsplash/Pexels (plus naturel!)
    - ai_images=true: Génère avec Grok AI (moins naturel)
    """
    if content_type not in CONTENT_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Type invalide. Valides: {list(CONTENT_TYPES.keys())}"
        )
    
    # Si real_photos est True, désactiver ai_images
    use_ai = ai_images and not real_photos
    
    logger.info(f"🎨 Génération contenu: {content_type} | theme={theme} | real_photos={real_photos}")
    
    # Générer le contenu
    content = await generate_content(content_type, theme, generate_ai_images=use_ai)
    
    if send_email:
        # Envoyer pour approbation
        from app.services.email_approval import send_approval_email
        from app.routes.content import add_pending_post
        
        post_data = {
            "text": content["text"],
            "full_text": content["text"],
            "hashtags": content["hashtags"],
            "image_url": content["image_url"],
            "image_source": content.get("image_source", "stock"),
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
                "image_source": content.get("image_source", "stock"),
                "image_type": "Vraie photo Unsplash" if not use_ai else "Grok AI",
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
        "image_source": content.get("image_source", "stock"),
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
