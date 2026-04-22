"""
Service de découverte de contenu
Scrape, filtre, traduit et génère les posts
UNIQUEMENT sur les extensions capillaires
Adapte automatiquement le contenu selon la saison et les événements
"""

import os
import logging
import httpx
import hashlib
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from .content_sources import (
    SEARCH_QUERIES, TRUSTED_SOURCES,
    REQUIRED_EXTENSION_KEYWORDS, INCLUDE_KEYWORDS, 
    EXCLUDE_KEYWORDS, CANADA_KEYWORDS,
    LUXURA_TONE, POST_TEMPLATES
)
from .seasonal_context import (
    get_seasonal_context, get_image_prompt_context, 
    get_post_intro, get_current_season
)

logger = logging.getLogger(__name__)


class ContentDiscoveryService:
    """
    Service principal de découverte et génération de contenu
    """
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.google_news_url = "https://news.google.com/rss/search"
    
    # ============================================
    # COLLECTE
    # ============================================
    
    async def discover_canada_hair_news(self, max_items: int = 20) -> List[Dict]:
        """
        Collecte les actualités sur les extensions capillaires au Canada
        """
        all_items = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Limiter à 5 requêtes pour éviter le rate limiting
            for query in SEARCH_QUERIES[:5]:
                try:
                    items = await self._fetch_google_news(client, query)
                    all_items.extend(items)
                    logger.info(f"Collecté {len(items)} articles pour '{query}'")
                except Exception as e:
                    logger.error(f"Erreur collecte '{query}': {e}")
                    continue
        
        # Dédupliquer par URL
        seen_urls = set()
        unique_items = []
        for item in all_items:
            if item["source_url"] not in seen_urls:
                seen_urls.add(item["source_url"])
                unique_items.append(item)
        
        logger.info(f"Total unique: {len(unique_items)} articles")
        return unique_items[:max_items]
    
    async def _fetch_google_news(self, client: httpx.AsyncClient, query: str) -> List[Dict]:
        """
        Récupère les actualités Google News pour une requête
        """
        params = {
            "q": query,
            "hl": "en-CA",
            "gl": "CA",
            "ceid": "CA:en"
        }
        
        response = await client.get(self.google_news_url, params=params)
        
        if response.status_code != 200:
            logger.warning(f"Google News erreur: {response.status_code}")
            return []
        
        return self._parse_rss(response.text, query)
    
    def _parse_rss(self, xml_content: str, query: str) -> List[Dict]:
        """
        Parse le flux RSS Google News
        """
        items = []
        
        try:
            soup = BeautifulSoup(xml_content, 'xml')
            
            for item in soup.find_all('item'):
                title_tag = item.find('title')
                link_tag = item.find('link')
                pub_date_tag = item.find('pubDate')
                source_tag = item.find('source')
                desc_tag = item.find('description')
                
                if not title_tag or not link_tag:
                    continue
                
                title = title_tag.text.strip()
                url = link_tag.text.strip()
                
                # Hash pour dédoublonnage
                url_hash = hashlib.md5(url.encode()).hexdigest()
                title_hash = hashlib.md5(self._normalize_text(title).encode()).hexdigest()
                
                # Date de publication
                published_at = None
                if pub_date_tag:
                    try:
                        published_at = datetime.strptime(
                            pub_date_tag.text, "%a, %d %b %Y %H:%M:%S %Z"
                        )
                    except:
                        published_at = datetime.now()
                
                # Source fiable?
                source_name = source_tag.text if source_tag else "Unknown"
                is_trusted = any(ts in url.lower() for ts in TRUSTED_SOURCES)
                
                items.append({
                    "source_name": source_name,
                    "source_url": url,
                    "title": title,
                    "summary": desc_tag.text if desc_tag else None,
                    "published_at": published_at,
                    "country": "CA",
                    "language": "en",
                    "url_hash": url_hash,
                    "title_hash": title_hash,
                    "is_trusted": is_trusted,
                    "search_query": query,
                })
                
        except Exception as e:
            logger.error(f"Erreur parsing RSS: {e}")
        
        return items
    
    def _normalize_text(self, text: str) -> str:
        """Normalise le texte pour comparaison"""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    # ============================================
    # FILTRAGE
    # ============================================
    
    def filter_relevant_items(self, items: List[Dict]) -> List[Dict]:
        """
        Filtre les articles pertinents pour Luxura
        """
        relevant_items = []
        
        for item in items:
            score, keywords = self._calculate_relevance(item)
            
            if score >= 0.3:  # Seuil minimum
                item["relevance_score"] = score
                item["keywords_matched"] = keywords
                item["is_relevant"] = True
                relevant_items.append(item)
                logger.debug(f"✅ Pertinent ({score:.2f}): {item['title'][:50]}")
            else:
                logger.debug(f"❌ Rejeté ({score:.2f}): {item['title'][:50]}")
        
        # Trier par pertinence
        relevant_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        logger.info(f"Filtré: {len(relevant_items)}/{len(items)} pertinents")
        return relevant_items
    
    def _calculate_relevance(self, item: Dict) -> Tuple[float, List[str]]:
        """
        Calcule le score de pertinence
        OBLIGATOIRE: L'article DOIT parler d'extensions capillaires
        """
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        
        # =============================================
        # ÉTAPE 1: Exclusions (rejette immédiatement)
        # =============================================
        for keyword in EXCLUDE_KEYWORDS:
            if keyword in text:
                logger.debug(f"❌ Exclu (mot interdit '{keyword}'): {item.get('title', '')[:40]}")
                return 0.0, []
        
        # =============================================
        # ÉTAPE 2: OBLIGATOIRE - Doit contenir un mot d'extension
        # =============================================
        has_extension_keyword = False
        extension_matched = []
        
        for keyword in REQUIRED_EXTENSION_KEYWORDS:
            if keyword in text:
                has_extension_keyword = True
                extension_matched.append(keyword)
        
        # Si aucun mot d'extension trouvé, rejeter l'article
        if not has_extension_keyword:
            logger.debug(f"❌ Rejeté (pas d'extension): {item.get('title', '')[:40]}")
            return 0.0, []
        
        # =============================================
        # ÉTAPE 3: Score de base + bonus
        # =============================================
        matched_keywords = extension_matched.copy()
        score = 0.5  # Score de base car contient un mot d'extension
        
        # Bonus pour chaque mot d'extension supplémentaire
        score += len(extension_matched) * 0.1
        
        # Bonus pour mots-clés secondaires
        for keyword in INCLUDE_KEYWORDS:
            if keyword in text:
                matched_keywords.append(keyword)
                score += 0.05
        
        # Bonus Canada
        for keyword in CANADA_KEYWORDS:
            if keyword in text:
                score += 0.1
                matched_keywords.append(f"canada:{keyword}")
        
        # Bonus source fiable
        if item.get("is_trusted"):
            score += 0.15
        
        logger.debug(f"✅ Pertinent ({score:.2f}): {item.get('title', '')[:40]}")
        return min(score, 1.0), matched_keywords
    
    # ============================================
    # TRADUCTION
    # ============================================
    
    async def translate_to_french(self, text: str) -> str:
        """
        Traduit un texte en français avec GPT-4o
        """
        if not self.openai_key:
            logger.warning("OPENAI_API_KEY non configurée")
            return text
        
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
                            {
                                "role": "system",
                                "content": "Tu es un traducteur professionnel. Traduis le texte suivant en français canadien (québécois). Garde un ton professionnel et naturel. Ne traduis pas les noms propres."
                            },
                            {
                                "role": "user",
                                "content": text
                            }
                        ],
                        "max_tokens": 500,
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"Erreur traduction: {response.status_code}")
                    return text
                    
        except Exception as e:
            logger.error(f"Erreur traduction: {e}")
            return text
    
    # ============================================
    # GÉNÉRATION DE POST
    # ============================================
    
    async def generate_facebook_post(self, item: Dict) -> Dict:
        """
        Génère un post Facebook à partir d'un article
        """
        # Traduire si nécessaire
        title_fr = item.get("title_fr")
        if not title_fr and item.get("language") == "en":
            title_fr = await self.translate_to_french(item["title"])
            item["title_fr"] = title_fr
        
        summary_fr = item.get("summary_fr")
        if not summary_fr and item.get("summary") and item.get("language") == "en":
            summary_fr = await self.translate_to_french(item["summary"][:500])
            item["summary_fr"] = summary_fr
        
        # Générer le texte marketing avec GPT-4o
        post_text, confidence_score = await self._generate_marketing_text(item)
        
        # Générer le prompt DALL-E
        image_prompt = await self._generate_image_prompt(item)
        
        # Hashtags
        hashtags = self._select_hashtags(item)
        
        return {
            "source_item_id": item.get("id"),
            "source_url": item["source_url"],
            "platform": "facebook",
            "language": "fr",
            "tone": "luxura",
            "post_title": title_fr or item["title"],
            "post_text": post_text,
            "hashtags": hashtags,
            "image_prompt": image_prompt,
            "confidence_score": confidence_score,
            "status": "draft" if confidence_score < 0.85 else "approved",
        }
    
    async def _generate_marketing_text(self, item: Dict) -> Tuple[str, float]:
        """
        Génère le texte marketing pour Facebook
        """
        if not self.openai_key:
            # Fallback simple
            title = item.get("title_fr") or item["title"]
            return f"✨ {title}\n\nDécouvrez cette tendance sur luxuradistribution.com", 0.5
        
        title = item.get("title_fr") or item["title"]
        summary = item.get("summary_fr") or item.get("summary") or ""
        
        prompt = f"""Tu es le community manager de Luxura Distribution, importateur et distributeur d'extensions capillaires premium au Québec.

Voici un article d'actualité:
Titre: {title}
Résumé: {summary[:300]}

Écris un post Facebook engageant en français québécois basé sur cette actualité.

Le post doit:
- Commencer par un emoji accrocheur
- Être informatif et intéressant pour les femmes québécoises
- Mettre en valeur l'expertise de Luxura
- Avoir un ton féminin, professionnel et chaleureux
- Faire 100-150 mots maximum
- Terminer par un appel à l'action vers luxuradistribution.com
- NE PAS inclure de hashtags (je les ajouterai après)

Écris UNIQUEMENT le texte du post."""
        
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
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 400,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result["choices"][0]["message"]["content"].strip()
                    # Score basé sur la longueur et la présence d'éléments clés
                    score = self._calculate_post_quality(text)
                    return text, score
                else:
                    logger.error(f"Erreur GPT: {response.status_code}")
                    return f"✨ {title}\n\nDécouvrez-en plus sur luxuradistribution.com", 0.5
                    
        except Exception as e:
            logger.error(f"Erreur génération: {e}")
            return f"✨ {title}\n\nDécouvrez-en plus sur luxuradistribution.com", 0.5
    
    def _calculate_post_quality(self, text: str) -> float:
        """
        Calcule un score de qualité pour le post
        """
        score = 0.5
        
        # Longueur adéquate
        if 80 <= len(text) <= 500:
            score += 0.1
        
        # Contient un emoji
        if any(ord(c) > 127 for c in text):
            score += 0.1
        
        # Contient Luxura ou luxuradistribution
        if "luxura" in text.lower():
            score += 0.15
        
        # Contient un CTA
        cta_words = ["découvrez", "visitez", "contactez", "commandez"]
        if any(w in text.lower() for w in cta_words):
            score += 0.1
        
        return min(score, 1.0)
    
    async def _generate_image_prompt(self, item: Dict, post_text: str = "") -> str:
        """
        Génère un prompt pour l'image en utilisant les règles Luxura v3 Ultra-Glamour.
        
        UTILISE: luxura_image_prompts.py v3
        - Cheveux 3/4 du dos (JAMAIS courts)
        - Plusieurs femmes parfois
        - Salons haut de gamme
        - Décors luxueux (yachts, plages italiennes, etc.)
        """
        title = item.get("title_fr") or item["title"]
        
        try:
            # Import des prompts Luxura v3 Ultra-Glamour
            from app.services.luxura_image_prompts import (
                get_contextual_prompt,
                get_preset_prompt,
                LUXURA_CRITICAL_RULES
            )
            
            # Utiliser le générateur contextuel v3 qui analyse le titre
            prompt = get_contextual_prompt(title, post_text)
            
            logger.info(f"📝 Prompt Luxura v3 généré pour '{title[:50]}...'")
            return prompt
            
        except Exception as e:
            logger.error(f"Erreur import luxura_image_prompts: {e}")
        
        # Fallback Luxura style v3 (si import échoue)
        return "Real photograph of a glamorous woman at an exclusive Beverly Hills hair salon, with incredibly voluminous thick hair extensions reaching three-quarters down her back with dramatic body and natural movement. Shot from 3/4 back angle showcasing the incredible hair length. Soft professional lighting highlighting the hair shine and volume. Ultra-realistic luxury beauty photography. No text, no watermarks."
    
    def _select_hashtags(self, item: Dict) -> List[str]:
        """
        Sélectionne les hashtags pertinents
        """
        base_hashtags = [
            "#ExtensionsCapillaires",
            "#Luxura",
            "#CheveuxPremium",
            "#BeautéQuébec",
        ]
        
        # Ajouter des hashtags basés sur les mots-clés trouvés
        keywords = item.get("keywords_matched", [])
        
        if any("tape" in k for k in keywords):
            base_hashtags.append("#TapeInExtensions")
        if any("clip" in k for k in keywords):
            base_hashtags.append("#ClipInExtensions")
        if any("trend" in k or "tendance" in k for k in keywords):
            base_hashtags.append("#TendancesCoiffure")
        if any("canada" in k for k in keywords):
            base_hashtags.append("#BeautéCanada")
        
        return base_hashtags[:7]  # Max 7 hashtags
