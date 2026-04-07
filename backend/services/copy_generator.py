"""
Luxura Marketing - Générateur de copie publicitaire via OpenAI
Utilise emergentintegrations pour l'accès LLM
"""

import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Import emergentintegrations pour OpenAI
try:
    from emergentintegrations.llm.openai import LlmChat
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("emergentintegrations non disponible")


EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

# Templates de prompts selon le type d'offre
SYSTEM_PROMPT = """
Tu es un expert en copywriting publicitaire pour Luxura Distribution, 
importateur direct de rallonges capillaires premium au Québec.

RÈGLES CRITIQUES:
- Luxura est un IMPORTATEUR/VENDEUR DIRECT, pas un salon de coiffure
- Ne JAMAIS mentionner "pose d'extensions" comme service offert
- Ne JAMAIS offrir "support marketing" aux salons
- TOUJOURS mentionner: "base d'inventaire gratuitement" pour les salons affiliés
- Numéro officiel: 418-222-3939
- Ton: premium, luxueux, professionnel, québécois

Tu génères des publicités Meta (Facebook/Instagram) en français québécois.
"""

DIRECT_SALE_CONTEXT = """
TYPE: Vente directe aux clientes
CIBLE: Femmes 23-45 ans, Québec
ANGLE: Beauté, luxe, transformation, qualité premium
TON: Aspirationnel, émotionnel, résultat visible
"""

SALON_AFFILIE_CONTEXT = """
TYPE: Recrutement salons partenaires
CIBLE: Propriétaires de salon, coiffeuses, stylistes
ANGLE: Marge, stabilité, image premium, approvisionnement
TON: Professionnel, business, opportunité
AVANTAGES À MENTIONNER:
- Base d'inventaire gratuite
- Qualité importateur direct
- Service rapide
- Image de marque premium
"""

GENERATION_PROMPT = """
Génère une publicité Meta complète pour Luxura.

INFORMATIONS:
- Produit: {product_name}
- Accroche: {hook}
- Preuve: {proof}
- CTA: {cta}
- URL: {landing_url}
- Audience: {audience}

{context}

RETOURNE UN JSON VALIDE avec exactement cette structure:
{{
  "primary_text": "Texte principal de la pub (2-3 phrases max, accrocheur)",
  "headline": "Titre court et percutant (max 40 caractères)",
  "description": "Description secondaire courte",
  "story_script": "Script vidéo Story 15 sec - 5 scènes avec texte overlay",
  "feed_script": "Script vidéo Feed 20 sec - 5 scènes narratives",
  "fal_prompt_story": "Prompt anglais pour Fal.ai vidéo Story 9:16 - style luxe, mouvement cheveux",
  "fal_prompt_feed": "Prompt anglais pour Fal.ai vidéo Feed 4:5 - style premium, salon"
}}

IMPORTANT: 
- Retourne UNIQUEMENT le JSON, pas de texte avant/après
- Le fal_prompt doit être en ANGLAIS et très descriptif visuellement
- Inclus toujours: "Luxura logo visible, premium luxury aesthetic, golden lighting"
"""


async def generate_ad_copy(
    offer_type: str,
    product_name: str,
    hook: str,
    proof: str = "",
    cta: str = "Commander",
    landing_url: str = "",
    audience: str = ""
) -> dict:
    """
    Génère la copie publicitaire complète via OpenAI
    
    Returns:
        dict avec primary_text, headline, scripts, prompts fal
    """
    
    if not OPENAI_AVAILABLE:
        raise Exception("emergentintegrations non disponible")
    
    if not EMERGENT_LLM_KEY:
        raise Exception("EMERGENT_LLM_KEY non configurée")
    
    # Sélectionner le contexte selon le type d'offre
    if offer_type == "salon_affilie":
        context = SALON_AFFILIE_CONTEXT
    else:
        context = DIRECT_SALE_CONTEXT
    
    # Construire le prompt
    user_prompt = GENERATION_PROMPT.format(
        product_name=product_name,
        hook=hook,
        proof=proof or "Qualité premium importateur direct",
        cta=cta,
        landing_url=landing_url,
        audience=audience or "Femmes Québec",
        context=context
    )
    
    try:
        logger.info(f"Génération copie pub pour: {product_name}")
        
        # Utiliser LlmChat
        chat = LlmChat(api_key=EMERGENT_LLM_KEY)
        
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
        response = await chat.send_message_async(full_prompt)
        
        # Parser le JSON de la réponse
        content = response.strip()
        
        # Nettoyer si wrapped dans ```json
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        result = json.loads(content)
        
        logger.info(f"Copie générée avec succès: {result.get('headline', 'N/A')}")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Erreur parsing JSON: {e}")
        logger.error(f"Contenu reçu: {content[:500]}")
        raise Exception(f"Erreur parsing réponse LLM: {e}")
    except Exception as e:
        logger.error(f"Erreur génération copie: {e}")
        raise


def get_default_fal_prompt(offer_type: str, product_name: str) -> tuple:
    """
    Retourne des prompts Fal.ai par défaut si la génération échoue
    """
    
    if offer_type == "salon_affilie":
        story_prompt = f"""
        Professional luxury hair salon interior. Elegant stylist hands styling premium 
        blonde ombré hair extensions. Modern salon mirrors, professional ring lights, 
        upscale atmosphere. Golden hour lighting, slow motion hair movement. 
        Luxura branding visible. Premium business aesthetic. 4K cinematic.
        """
        feed_prompt = f"""
        Modern upscale hair salon. Professional hairstylist working with premium 
        hair extensions on a client. Satisfied result reveal. Luxury salon equipment, 
        clean white interior with gold accents. Luxura Distribution premium brand. 
        Business professional tone. 4K quality.
        """
    else:
        story_prompt = f"""
        Cinematic close-up of feminine hands with elegant manicured nails 
        gently running through luxurious silky hair extensions. 
        The hair flows smoothly like liquid silk, catching golden hour light.
        Premium beauty commercial quality. Luxura branding. 
        White studio background. Slow motion. 4K.
        """
        feed_prompt = f"""
        Beautiful woman transformation with premium hair extensions.
        Before and after reveal. Luxurious flowing hair, natural movement.
        Salon-quality result at home. Soft golden lighting, premium aesthetic.
        Luxura Distribution branding. Professional beauty commercial. 4K.
        """
    
    return story_prompt.strip(), feed_prompt.strip()
