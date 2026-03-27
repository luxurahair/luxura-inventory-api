# services/blog_content_generator.py
"""
Génération du contenu texte des blogs avec GPT-4o
Version V8 - Compatible avec le nouveau brief technique
"""

import os
import random
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Import des topics depuis blog_automation existant
try:
    from blog_automation import BLOG_TOPICS_EXTENDED, LUXURA_ANECDOTES, get_random_anecdote, get_luxura_recommendation, CITIES_SEO
except ImportError:
    logger.warning("Could not import BLOG_TOPICS_EXTENDED, using minimal fallback")
    BLOG_TOPICS_EXTENDED = []
    LUXURA_ANECDOTES = {}
    CITIES_SEO = {}
    def get_random_anecdote(cat): return ""
    def get_luxura_recommendation(cat): return ""


def select_topics(count: int = 2, existing_titles: List[str] = None) -> List[Dict]:
    """
    Sélectionne des sujets de blog en évitant les doublons.
    Priorise la diversité des catégories.
    """
    if existing_titles is None:
        existing_titles = []
    
    existing_lower = [t.lower() for t in existing_titles]
    
    # Filtrer les topics déjà utilisés
    available = [t for t in BLOG_TOPICS_EXTENDED if t["topic"].lower() not in existing_lower]
    
    # Si pas assez de topics disponibles, réutiliser tout
    if len(available) < count:
        available = BLOG_TOPICS_EXTENDED.copy()
        random.shuffle(available)
    
    selected = []
    categories_used = []
    
    # Sélectionner en diversifiant les catégories
    for topic in available:
        if len(selected) >= count:
            break
        # Prioriser les catégories pas encore utilisées
        if topic["category"] not in categories_used or len(categories_used) >= 4:
            selected.append(topic)
            categories_used.append(topic["category"])
    
    # Compléter si nécessaire
    while len(selected) < count and available:
        remaining = [t for t in available if t not in selected]
        if remaining:
            selected.append(random.choice(remaining))
    
    logger.info(f"🎯 Selected {len(selected)} topics: {[t['topic'][:40] for t in selected]}")
    return selected


# Alias pour compatibilité
select_random_topics = select_topics


async def generate_blog_content(topic_data: Dict, openai_key: str) -> Optional[Dict]:
    """
    Génère le contenu texte d'un blog avec GPT-4o.
    Retourne un dict avec title, excerpt, content.
    """
    try:
        # Utiliser emergentintegrations si disponible
        try:
            from emergentintegrations.llm.openai import OpenAIChatBot
            
            chatbot = OpenAIChatBot(
                api_key=openai_key,
                model="gpt-4o"
            )
            use_emergent = True
        except ImportError:
            import openai
            client = openai.AsyncOpenAI(api_key=openai_key)
            use_emergent = False
        
        topic = topic_data.get('topic', 'Extensions capillaires')
        category = topic_data.get('category', 'general')
        keywords = topic_data.get('keywords', [])
        focus_product = topic_data.get('focus_product', '')
        city = topic_data.get('city', '')
        content_type = topic_data.get('content_type', 'guide')
        installation_steps = topic_data.get('installation_steps', [])
        
        # Obtenir anecdote et recommandation
        anecdote = get_random_anecdote(category)
        recommendation = get_luxura_recommendation(category)
        
        # Info ville si applicable
        city_info = ""
        if city and city in CITIES_SEO:
            city_data = CITIES_SEO[city]
            city_info = f"\nVille ciblée: {city_data['name']} - Angle: {city_data['angle']}"
        
        # Étapes d'installation si applicable
        steps_info = ""
        if installation_steps:
            steps_info = f"\n\nÉTAPES D'INSTALLATION À DÉCRIRE (dans l'ordre):\n" + "\n".join([f"- {step}" for step in installation_steps])
        
        system_message = f"""Tu es un expert SEO francophone spécialisé dans les extensions capillaires au Québec.
Tu écris pour Luxura Distribution, le distributeur #1 d'extensions de cheveux professionnelles.

TON STYLE:
- Français québécois naturel (utilise "magasiner", "pogner", "génial")
- Expertise technique mais accessible
- Mentions authentiques de Luxura (salle d'exposition Saint-Georges, service personnalisé)
- Toujours parler de cheveux TRÈS LONGS (jusqu'à la taille ou aux hanches)
- JAMAIS de tons condescendants

ANECDOTE LUXURA À INTÉGRER (rends-la naturelle):
"{anecdote}"

RECOMMANDATION LUXURA:
"{recommendation}"
{city_info}
{steps_info}

RÈGLES SEO:
- Titre: max 60 caractères, avec mot-clé principal
- Meta description (excerpt): 155 caractères max
- Structure H2/H3 claire
- Mots-clés intégrés naturellement
- Min 800 mots, max 1500 mots
- Lien vers luxuradistribution.com

RÉPONDS UNIQUEMENT EN JSON VALIDE:
{{
  "title": "...",
  "excerpt": "...",
  "content": "<h2>...</h2><p>...</p>..."
}}"""

        user_prompt = f"""Rédige un article de blog SEO optimisé sur:

SUJET: {topic}
CATÉGORIE: {category}
MOTS-CLÉS: {', '.join(keywords)}
PRODUIT VEDETTE: {focus_product or 'Extensions Luxura'}
TYPE: {content_type}

L'article doit être:
- Informatif et utile
- Optimisé SEO local Québec
- Authentique (intègre l'anecdote Luxura)
- Bien structuré avec H2/H3
- Min 800 mots

RÉPONDS EN JSON UNIQUEMENT."""

        logger.info(f"📝 Generating content for: {topic[:50]}...")
        
        if use_emergent:
            response_text = await chatbot.chat(
                user_prompt,
                system_message=system_message
            )
        else:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.75,
                max_tokens=4000
            )
            response_text = response.choices[0].message.content.strip()
        
        # Nettoyer le JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        blog_data = json.loads(response_text.strip())
        
        # Enrichir avec les métadonnées
        blog_data["category"] = category
        blog_data["focus_product"] = focus_product
        blog_data["keywords"] = keywords
        
        logger.info(f"✅ Content generated: {blog_data.get('title', 'No title')[:50]}...")
        return blog_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.error(f"Response was: {response_text[:500]}...")
        return None
    except Exception as e:
        logger.error(f"Blog content generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def send_summary_email(results: List[Dict]):
    """
    Envoie un email récapitulatif des blogs générés.
    Utilise la fonction existante de blog_automation.
    """
    try:
        from blog_automation import send_blog_images_email
        await send_blog_images_email(results)
    except Exception as e:
        logger.warning(f"Email summary skipped: {e}")
