"""
Générateur de Contenu Magazine Luxura
=====================================
Génère des posts Facebook style magazine féminin
inspirés des tendances internationales (Europe, Italie, USA, UK)

Thèmes:
- Tendances coupe (bob, lob, frange)
- Comparatifs extensions
- Conseils / Erreurs à éviter
- Quiet Luxury cheveux
- Inspiration internationale
"""

import os
import logging
import httpx
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .content_sources import (
    MAGAZINE_THEMES, POST_TEMPLATES, LUXURA_TONE,
    NATURAL_HAIR_IMAGES, INTERNATIONAL_QUERIES
)

logger = logging.getLogger(__name__)


# ============================================
# JOURS DE LA SEMAINE EN FRANÇAIS
# ============================================
JOURS_FR = {
    "Monday": "Lundi",
    "Tuesday": "Mardi", 
    "Wednesday": "Mercredi",
    "Thursday": "Jeudi",
    "Friday": "Vendredi",
    "Saturday": "Samedi",
    "Sunday": "Dimanche",
}

MOIS_FR = {
    "January": "janvier",
    "February": "février",
    "March": "mars",
    "April": "avril",
    "May": "mai",
    "June": "juin",
    "July": "juillet",
    "August": "août",
    "September": "septembre",
    "October": "octobre",
    "November": "novembre",
    "December": "décembre",
}


def traduire_date_fr(date_str: str) -> str:
    """
    Traduit une date en français
    Ex: "Sunday, June 15" -> "Dimanche 15 juin"
    """
    result = date_str
    for en, fr in JOURS_FR.items():
        result = result.replace(en, fr)
    for en, fr in MOIS_FR.items():
        result = result.replace(en, fr)
    return result


def get_jour_semaine_fr() -> str:
    """Retourne le jour de la semaine en français"""
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    return jours[datetime.now().weekday()]


class MagazineContentGenerator:
    """
    Générateur de posts Facebook style magazine féminin
    """
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.grok_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    
    async def generate_magazine_post(
        self, 
        theme: str = "auto",
        country_inspiration: str = "auto"
    ) -> Dict:
        """
        Génère un post magazine complet
        
        Args:
            theme: Type de post (tendance_coupe, comparatif_extensions, etc.) ou "auto"
            country_inspiration: Pays d'inspiration (france, italy, usa, uk) ou "auto"
        
        Returns:
            Dict avec le post complet (texte, image_prompt, hashtags)
        """
        # Sélection automatique du thème si "auto"
        if theme == "auto":
            theme = self._select_theme_for_today()
        
        # Sélection automatique du pays si "auto"
        if country_inspiration == "auto":
            country_inspiration = random.choice(["france", "italy", "usa", "uk"])
        
        theme_config = MAGAZINE_THEMES.get(theme, MAGAZINE_THEMES["tendance_coupe"])
        
        logger.info(f"🎨 Génération post magazine: {theme} | Inspiration: {country_inspiration}")
        
        # Générer le contenu avec GPT-4o
        post_content = await self._generate_post_content(theme, theme_config, country_inspiration)
        
        # Générer le prompt image contextuel
        image_prompt = await self._generate_contextual_image_prompt(
            theme, 
            post_content.get("title", ""),
            post_content.get("content", "")
        )
        
        # Sélectionner les hashtags
        hashtags = self._select_hashtags(theme, country_inspiration)
        
        # Obtenir une image fallback si besoin
        fallback_image = random.choice(NATURAL_HAIR_IMAGES)
        
        return {
            "theme": theme,
            "theme_name": theme_config["name"],
            "country_inspiration": country_inspiration,
            "title": post_content.get("title", ""),
            "full_text": post_content.get("full_text", ""),
            "image_prompt": image_prompt,
            "fallback_image_url": fallback_image,
            "hashtags": hashtags,
            "day_fr": get_jour_semaine_fr(),
            "generated_at": datetime.now().isoformat(),
            "language": "fr",
            "tone": "magazine féminin",
        }
    
    def _select_theme_for_today(self) -> str:
        """
        Sélectionne le thème en fonction du jour de la semaine
        """
        day = datetime.now().weekday()
        themes_rotation = [
            "tendance_coupe",         # Lundi
            "comparatif_extensions",  # Mardi
            "conseils_erreurs",       # Mercredi
            "quiet_luxury",           # Jeudi
            "inspiration_internationale",  # Vendredi
            "tendance_coupe",         # Samedi
            "inspiration_internationale",  # Dimanche
        ]
        return themes_rotation[day]
    
    async def _generate_post_content(
        self, 
        theme: str, 
        theme_config: Dict,
        country: str
    ) -> Dict:
        """
        Génère le contenu du post avec GPT-4o
        """
        if not self.openai_key:
            return self._generate_fallback_content(theme, theme_config)
        
        country_names = {
            "france": "française/parisienne",
            "italy": "italienne/milanaise", 
            "usa": "américaine/new-yorkaise",
            "uk": "britannique/londonienne",
        }
        country_style = country_names.get(country, "internationale")
        
        # Exemple de titre pour guider le modèle
        example_title = random.choice(theme_config.get("example_titles", ["Tendance coiffure 2026"]))
        
        system_prompt = f"""Tu es la rédactrice en chef du magazine beauté de Luxura Distribution, 
distributeur d'extensions capillaires premium au Québec.

Tu écris des posts Facebook STYLE MAGAZINE FÉMININ - pas de la pub.

TON STYLE:
- Chic, expert mais accessible
- Québécois naturel (pas "parisien")
- Informatif avec une touche de personnalité
- Questions engageantes à la fin

RÈGLES:
1. TITRE ACCROCHEUR (avec emoji) - doit donner envie de lire
2. INTRODUCTION courte qui capte l'attention
3. CONTENU UTILE (conseils, comparatifs, infos) - 100-150 mots
4. Toujours terminer par une QUESTION pour l'engagement
5. Jamais de ton promotionnel direct
6. Jamais de "cliquez ici" ou "achetez maintenant"
7. TOUT EN FRANÇAIS (pas de mots anglais sauf noms de produits)
8. Les jours et mois doivent être en français (Dimanche, juin, etc.)

THÈME: {theme_config['name']}
DESCRIPTION: {theme_config['description']}
INSPIRATION: tendance {country_style}
TON: {theme_config['tone']}

EXEMPLE DE TITRE: "{example_title}"

Retourne UNIQUEMENT le post complet prêt à publier."""

        user_prompt = f"""Écris un post Facebook magazine sur le thème "{theme_config['name']}" 
avec une inspiration {country_style}.

Le post doit être:
- Informatif et intéressant pour les femmes québécoises
- Dans le ton d'un vrai magazine beauté
- Avec un lien subtil vers les extensions capillaires Luxura
- 100-150 mots maximum

Structure:
1. Emoji + Titre accrocheur (en gras avec **)
2. 2-3 paragraphes de contenu utile
3. Un conseil Luxura
4. Question engageante finale
5. Lien: luxuradistribution.com"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 600,
                        "temperature": 0.8
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    full_text = result["choices"][0]["message"]["content"].strip()
                    
                    # Extraire le titre (première ligne avec **)
                    lines = full_text.split("\n")
                    title = lines[0].replace("**", "").replace("*", "").strip()
                    
                    # Traduire les dates en français si nécessaire
                    full_text = traduire_date_fr(full_text)
                    
                    return {
                        "title": title,
                        "full_text": full_text,
                        "content": full_text,
                    }
                else:
                    logger.error(f"Erreur OpenAI: {response.status_code}")
                    return self._generate_fallback_content(theme, theme_config)
                    
        except Exception as e:
            logger.error(f"Erreur génération contenu: {e}")
            return self._generate_fallback_content(theme, theme_config)
    
    def _generate_fallback_content(self, theme: str, theme_config: Dict) -> Dict:
        """
        Génère un contenu de secours si l'API échoue
        """
        title = random.choice(theme_config.get("example_titles", ["Tendance beauté 2026"]))
        
        return {
            "title": title,
            "full_text": f"""✨ **{title}**

Les tendances évoluent, mais une chose reste constante: des cheveux sains et brillants font toujours la différence.

Chez Luxura, on croit que la beauté naturelle mérite d'être sublimée, pas masquée.

💡 **Notre conseil:** Avant d'investir dans un nouveau look, consultez nos experts pour trouver la solution parfaite pour vous.

Qu'est-ce qui compte le plus pour vous: la longueur ou la brillance?

👉 luxuradistribution.com""",
            "content": "Contenu généré automatiquement",
        }
    
    async def _generate_contextual_image_prompt(
        self, 
        theme: str, 
        title: str,
        content: str
    ) -> str:
        """
        Génère un prompt d'image contextuel basé sur le contenu du post
        """
        # Prompts de base par thème
        theme_image_contexts = {
            "tendance_coupe": "woman with stylish haircut, modern bob or lob hairstyle",
            "comparatif_extensions": "woman touching her long silky hair extensions",
            "conseils_erreurs": "woman with healthy shiny hair, natural beauty",
            "quiet_luxury": "elegant woman with glossy sophisticated hair, quiet luxury aesthetic",
            "inspiration_internationale": "fashionable woman with trendy hairstyle, european style",
        }
        
        base_context = theme_image_contexts.get(theme, "beautiful woman with gorgeous hair")
        
        if not self.openai_key:
            return f"{base_context}, natural lighting, lifestyle photography, warm tones, elegant mood, mid-back length hair"
        
        system_prompt = """Tu crées des prompts d'images pour DALL-E 3 / Grok.
Les images sont pour une marque d'extensions capillaires premium (Luxura Distribution).

RÈGLES CHEVEUX:
1. Longueur mi-dos à 3/4 dos (pas trop court, pas au sol)
2. Volume naturel et soyeux (pas exagéré)
3. Brillance naturelle
4. Peut tomber sur les épaules/poitrine

STYLE:
- Photos lifestyle naturelles, pas studio
- Lumière naturelle (golden hour idéal)
- Maximum 1-2 personnes
- Expressions naturelles, authentiques
- Mood élégant et aspirationnel

Retourne UNIQUEMENT le prompt en anglais (max 200 caractères)."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Crée un prompt image pour ce post:\nTitre: {title}\nThème: {theme}\nContenu: {content[:300]}"}
                        ],
                        "max_tokens": 100,
                        "temperature": 0.6
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                    
        except Exception as e:
            logger.error(f"Erreur prompt image: {e}")
        
        return f"{base_context}, natural lighting, lifestyle photography, warm tones, elegant mood"
    
    def _select_hashtags(self, theme: str, country: str) -> List[str]:
        """
        Sélectionne les hashtags pertinents
        """
        base_hashtags = ["#Luxura", "#BeautéQuébec", "#Tendances2026"]
        
        theme_hashtags = {
            "tendance_coupe": ["#BobHaircut", "#Lob2026", "#CoupeTendance"],
            "comparatif_extensions": ["#ExtensionsCapillaires", "#TapeIn", "#HaloExtensions"],
            "conseils_erreurs": ["#ConseilsCoiffure", "#CheveuxSains", "#HairTips"],
            "quiet_luxury": ["#QuietLuxury", "#CheveuxBrillants", "#GlossyHair"],
            "inspiration_internationale": ["#FashionHair", "#TendancesInternationales", "#StyleFéminin"],
        }
        
        country_hashtags = {
            "france": "#StyleParisien",
            "italy": "#MilanStyle",
            "usa": "#NYCStyle",
            "uk": "#LondonStyle",
        }
        
        hashtags = base_hashtags + theme_hashtags.get(theme, [])[:2]
        if country in country_hashtags:
            hashtags.append(country_hashtags[country])
        
        return hashtags[:7]  # Max 7 hashtags
    
    async def generate_week_content_plan(self) -> List[Dict]:
        """
        Génère un plan de contenu pour la semaine
        """
        week_plan = []
        themes = list(MAGAZINE_THEMES.keys())
        countries = ["france", "italy", "usa", "uk"]
        
        for i, day in enumerate(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]):
            theme = themes[i % len(themes)]
            country = countries[i % len(countries)]
            
            week_plan.append({
                "day": day,
                "theme": theme,
                "theme_name": MAGAZINE_THEMES[theme]["name"],
                "country_inspiration": country,
                "suggested_time": "10h" if i < 5 else "11h",
            })
        
        return week_plan


# Instance singleton
magazine_generator = MagazineContentGenerator()
