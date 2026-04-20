"""
🌍 LUXURA INTERNATIONAL CONTENT SCANNER v2
==========================================
Scrute les tendances mode féminine internationales:
- 🇫🇷 France (Paris, Elle, Vogue)
- 🇮🇹 Italie (Milan, Grazia)
- 🇺🇸 USA (New York, Allure, Glamour)
- 🇬🇧 UK (Londres, Harper's Bazaar)
- 🇨🇦 Canada (Montréal, Fashion Magazine)

Flux:
1. Scrutation Google News par pays (rotation quotidienne)
2. Filtrage articles mode féminine/coiffure
3. Dédoublonnage avec historique persistant (30 jours)
4. Traduction française (GPT-4o)
5. Génération image contextuelle (Grok)
6. Ajout watermark LUXURA doré
7. Email approbation → Publication Facebook
"""

import os
import logging
import httpx
import hashlib
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ============================================
# HISTORIQUE DES ARTICLES PUBLIÉS (Anti-répétition)
# ============================================

HISTORY_FILE = Path("/tmp/luxura_international_history.json")
HISTORY_MAX_DAYS = 30  # Garder l'historique 30 jours


def load_article_history() -> Dict:
    """Charge l'historique des articles déjà traités"""
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
                # Nettoyer les vieux articles (> 30 jours)
                cutoff = (datetime.now() - timedelta(days=HISTORY_MAX_DAYS)).isoformat()
                history["articles"] = {
                    k: v for k, v in history.get("articles", {}).items()
                    if v.get("published_at", "") > cutoff
                }
                return history
    except Exception as e:
        logger.error(f"Erreur chargement historique: {e}")
    return {"articles": {}, "last_run": None}


def save_article_history(history: Dict):
    """Sauvegarde l'historique"""
    try:
        history["last_run"] = datetime.now().isoformat()
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur sauvegarde historique: {e}")


def is_article_already_published(title: str, url: str) -> bool:
    """Vérifie si un article a déjà été publié"""
    history = load_article_history()
    
    # Hash du titre normalisé
    title_hash = hashlib.md5(title.lower()[:100].encode()).hexdigest()
    
    # Hash de l'URL
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    articles = history.get("articles", {})
    
    # Vérifier si le titre ou l'URL existe déjà
    if title_hash in articles or url_hash in articles:
        return True
    
    return False


def mark_article_as_published(title: str, url: str, country: str):
    """Marque un article comme publié dans l'historique"""
    history = load_article_history()
    
    title_hash = hashlib.md5(title.lower()[:100].encode()).hexdigest()
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    now = datetime.now().isoformat()
    
    history["articles"][title_hash] = {
        "title": title[:100],
        "country": country,
        "published_at": now
    }
    history["articles"][url_hash] = {
        "url": url,
        "country": country,
        "published_at": now
    }
    
    save_article_history(history)
    logger.info(f"📝 Article ajouté à l'historique: {title[:50]}...")


# ============================================
# CONFIGURATION PAR PAYS
# ============================================

COUNTRY_CONFIG = {
    "france": {
        "name": "France",
        "flag": "🇫🇷",
        "city": "Paris",
        "language": "fr",
        "google_params": {"hl": "fr", "gl": "FR", "ceid": "FR:fr"},
        "queries": [
            "tendances coiffure femme 2026",
            "coupe bob carré tendance",
            "extensions cheveux naturels",
            "cheveux brillants glossy",
            "frange rideau tendance",
            "coiffure mariage 2026",
            "soins cheveux luxe",
        ],
        "sources": ["elle.fr", "vogue.fr", "marieclaire.fr", "grazia.fr", "glamourparis.com"],
    },
    "italy": {
        "name": "Italie",
        "flag": "🇮🇹",
        "city": "Milan",
        "language": "it",
        "google_params": {"hl": "it", "gl": "IT", "ceid": "IT:it"},
        "queries": [
            "tendenze capelli 2026",
            "extension capelli naturali",
            "milan fashion week hair",
            "capelli lucidi glossy",
            "acconciature eleganti",
            "taglio bob italiano",
        ],
        "sources": ["vogue.it", "elle.it", "grazia.it", "vanityfair.it", "marieclaire.it"],
    },
    "usa": {
        "name": "États-Unis",
        "flag": "🇺🇸",
        "city": "New York",
        "language": "en",
        "google_params": {"hl": "en-US", "gl": "US", "ceid": "US:en"},
        "queries": [
            "hair trends 2026 women",
            "hair extensions celebrity",
            "bob haircut trends",
            "glossy hair trend",
            "new york fashion week hair",
            "bridal hairstyles 2026",
            "volume hair tips",
        ],
        "sources": ["allure.com", "elle.com", "glamour.com", "byrdie.com", "refinery29.com", "instyle.com"],
    },
    "uk": {
        "name": "Royaume-Uni",
        "flag": "🇬🇧",
        "city": "Londres",
        "language": "en",
        "google_params": {"hl": "en-GB", "gl": "GB", "ceid": "GB:en"},
        "queries": [
            "hair trends london 2026",
            "british women hairstyles",
            "hair extensions uk",
            "glossy hair tips",
            "wedding hair 2026",
        ],
        "sources": ["glamourmagazine.co.uk", "harpersbazaar.com/uk", "marieclaire.co.uk"],
    },
    "canada": {
        "name": "Canada",
        "flag": "🇨🇦",
        "city": "Montréal",
        "language": "en",
        "google_params": {"hl": "en-CA", "gl": "CA", "ceid": "CA:en"},
        "queries": [
            "hair extensions Canada",
            "coiffure tendance Montréal",
            "extensions cheveux Québec",
            "salon coiffure premium",
        ],
        "sources": ["fashionmagazine.com", "thekit.ca", "salonmagazine.ca"],
    },
}

# Rotation des pays par jour de la semaine
DAILY_COUNTRY_ROTATION = {
    0: ["france", "italy"],      # Lundi: Europe
    1: ["usa", "uk"],            # Mardi: Anglophone
    2: ["france", "canada"],     # Mercredi: Francophone
    3: ["italy", "usa"],         # Jeudi: Mode
    4: ["uk", "france"],         # Vendredi: Élégance
    5: ["usa", "italy"],         # Samedi: Lifestyle
    6: ["france", "uk"],         # Dimanche: Classique
}


# ============================================
# MOTS-CLÉS FÉMININS MODE/COIFFURE
# ============================================

FEMININE_KEYWORDS = [
    # Coiffure
    "hair", "cheveux", "capelli", "coiffure", "hairstyle", "acconciatura",
    "bob", "lob", "fringe", "frange", "bangs", "frangia",
    "extensions", "rallonges", "extension",
    "glossy", "brillant", "lucido", "shiny",
    "volume", "volumineux",
    "long hair", "cheveux longs", "capelli lunghi",
    
    # Mode féminine
    "women", "femme", "donna", "feminine", "féminin", "femminile",
    "beauty", "beauté", "bellezza",
    "style", "tendance", "trend", "tendenza",
    "fashion", "mode", "moda",
    "elegant", "élégant", "elegante",
    "chic", "glamour", "luxe", "luxury",
    
    # Occasions
    "wedding", "mariage", "matrimonio", "bridal",
    "celebrity", "célébrité",
    "red carpet", "tapis rouge",
]

EXCLUDE_KEYWORDS = [
    "men", "homme", "uomo", "masculine", "masculin",
    "beard", "barbe", "barba",
    "bald", "chauve", "calvo",
    "hair loss", "perte cheveux", "perdita capelli",
    "wig", "perruque", "parrucca",
    "casino", "crypto", "bitcoin", "forex",
]


class InternationalContentScanner:
    """
    Scanner de contenu international pour Luxura
    """
    
    def __init__(self):
        self.google_news_url = "https://news.google.com/rss/search"
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.grok_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    
    def get_todays_countries(self) -> List[str]:
        """Retourne les pays à scanner aujourd'hui (rotation)"""
        day_of_week = datetime.now().weekday()
        return DAILY_COUNTRY_ROTATION.get(day_of_week, ["france", "usa"])
    
    async def scan_international_news(self, max_per_country: int = 5) -> List[Dict]:
        """
        Scrute les actualités mode féminine de tous les pays du jour
        """
        countries = self.get_todays_countries()
        all_articles = []
        
        logger.info(f"🌍 Scrutation internationale: {', '.join([COUNTRY_CONFIG[c]['flag'] + ' ' + COUNTRY_CONFIG[c]['name'] for c in countries])}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for country_code in countries:
                config = COUNTRY_CONFIG.get(country_code)
                if not config:
                    continue
                
                logger.info(f"\n{config['flag']} Scrutation {config['name']} ({config['city']})...")
                
                # Sélectionner 3 requêtes aléatoires pour ce pays
                queries = random.sample(config["queries"], min(3, len(config["queries"])))
                
                for query in queries:
                    try:
                        articles = await self._fetch_google_news(
                            client, 
                            query, 
                            config["google_params"],
                            country_code,
                            config["language"]
                        )
                        
                        # Filtrer les articles pertinents
                        filtered = self._filter_feminine_articles(articles)
                        all_articles.extend(filtered[:max_per_country])
                        
                        logger.info(f"   ✅ '{query}': {len(filtered)} articles féminins trouvés")
                        
                    except Exception as e:
                        logger.error(f"   ❌ Erreur '{query}': {e}")
                        continue
        
        # Dédupliquer par titre
        unique_articles = self._deduplicate_articles(all_articles)
        
        logger.info(f"\n📊 Total: {len(unique_articles)} articles uniques collectés")
        return unique_articles
    
    async def _fetch_google_news(
        self, 
        client: httpx.AsyncClient, 
        query: str,
        google_params: Dict,
        country: str,
        language: str
    ) -> List[Dict]:
        """Récupère les articles Google News pour une requête"""
        
        params = {
            "q": query,
            **google_params
        }
        
        response = await client.get(self.google_news_url, params=params)
        
        if response.status_code != 200:
            return []
        
        return self._parse_rss(response.text, country, language)
    
    def _parse_rss(self, xml_content: str, country: str, language: str) -> List[Dict]:
        """Parse le flux RSS Google News"""
        articles = []
        
        try:
            soup = BeautifulSoup(xml_content, 'html.parser')
            
            for item in soup.find_all('item')[:10]:  # Max 10 par requête
                title_tag = item.find('title')
                link_tag = item.find('link')
                pub_date_tag = item.find('pubdate')
                source_tag = item.find('source')
                desc_tag = item.find('description')
                
                if not title_tag or not link_tag:
                    continue
                
                title = title_tag.text.strip()
                url = link_tag.text.strip()
                source = source_tag.text if source_tag else "Unknown"
                
                # Vérifier si source fiable
                config = COUNTRY_CONFIG.get(country, {})
                trusted_sources = config.get("sources", [])
                is_trusted = any(ts in url.lower() for ts in trusted_sources)
                
                articles.append({
                    "title": title,
                    "url": url,
                    "source": source,
                    "summary": desc_tag.text if desc_tag else "",
                    "country": country,
                    "country_name": config.get("name", country),
                    "country_flag": config.get("flag", "🌍"),
                    "city": config.get("city", ""),
                    "language": language,
                    "is_trusted": is_trusted,
                    "collected_at": datetime.now().isoformat(),
                })
                
        except Exception as e:
            logger.error(f"Erreur parsing RSS: {e}")
        
        return articles
    
    def _filter_feminine_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filtre les articles pour ne garder que le contenu féminin mode/coiffure"""
        filtered = []
        
        for article in articles:
            text = f"{article['title']} {article.get('summary', '')}".lower()
            
            # Vérifier exclusions
            if any(kw in text for kw in EXCLUDE_KEYWORDS):
                continue
            
            # Doit contenir au moins un mot-clé féminin
            if any(kw in text for kw in FEMININE_KEYWORDS):
                # Calculer score de pertinence
                score = sum(1 for kw in FEMININE_KEYWORDS if kw in text)
                article["relevance_score"] = min(score / 5, 1.0)
                filtered.append(article)
        
        # Trier par pertinence
        filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return filtered
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Dédoublonne par titre similaire ET vérifie l'historique des 30 derniers jours"""
        seen_titles = set()
        unique = []
        skipped_history = 0
        
        for article in articles:
            title = article["title"]
            url = article.get("url", "")
            title_normalized = title.lower()[:50]
            title_hash = hashlib.md5(title_normalized.encode()).hexdigest()
            
            # Vérifier si déjà vu dans cette session
            if title_hash in seen_titles:
                continue
            
            # Vérifier l'historique persistant (30 jours)
            if is_article_already_published(title, url):
                skipped_history += 1
                logger.debug(f"⏭️ Article déjà publié: {title[:40]}...")
                continue
            
            seen_titles.add(title_hash)
            unique.append(article)
        
        if skipped_history > 0:
            logger.info(f"⏭️ {skipped_history} articles ignorés (déjà publiés)")
        
        return unique
    
    # ============================================
    # TRADUCTION EN FRANÇAIS
    # ============================================
    
    async def translate_to_french(self, text: str, source_language: str) -> str:
        """Traduit un texte en français québécois"""
        
        if source_language == "fr":
            return text  # Déjà en français
        
        if not self.openai_key:
            logger.warning("OPENAI_API_KEY non configurée - pas de traduction")
            return text
        
        language_names = {
            "en": "anglais",
            "it": "italien",
            "es": "espagnol",
            "de": "allemand",
        }
        
        source_lang_name = language_names.get(source_language, source_language)
        
        prompt = f"""Traduis ce texte de {source_lang_name} vers le français québécois.
Garde un ton naturel, féminin et élégant. Ne traduis pas les noms propres ou marques.

Texte à traduire:
{text}

Retourne UNIQUEMENT la traduction, sans explication."""
        
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
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                    
        except Exception as e:
            logger.error(f"Erreur traduction: {e}")
        
        return text
    
    # ============================================
    # GÉNÉRATION POST FACEBOOK
    # ============================================
    
    async def generate_luxura_post(self, article: Dict) -> Dict:
        """
        Génère un post Facebook complet à partir d'un article international
        """
        # 1. Traduire le titre et résumé en français
        title_fr = await self.translate_to_french(article["title"], article["language"])
        summary_fr = await self.translate_to_french(article.get("summary", ""), article["language"])
        
        # 2. Générer le texte du post avec GPT-4o
        post_text = await self._generate_post_text(article, title_fr, summary_fr)
        
        # 3. Générer le prompt image contextuel
        image_prompt = await self._generate_image_prompt(article, title_fr, post_text)
        
        # 4. Générer l'image avec Grok
        image_url = await self._generate_grok_image(image_prompt)
        
        return {
            "title_original": article["title"],
            "title_fr": title_fr,
            "summary_fr": summary_fr,
            "post_text": post_text,
            "image_prompt": image_prompt,
            "image_url": image_url,
            "source_url": article["url"],
            "source_name": article["source"],
            "country": article["country"],
            "country_flag": article["country_flag"],
            "city": article["city"],
            "hashtags": self._generate_hashtags(article),
            "generated_at": datetime.now().isoformat(),
        }
    
    async def _generate_post_text(self, article: Dict, title_fr: str, summary_fr: str) -> str:
        """Génère le texte du post Facebook style Luxura"""
        
        if not self.openai_key:
            return f"✨ {title_fr}\n\nDécouvrez cette tendance sur luxuradistribution.com"
        
        prompt = f"""Tu es la community manager de Luxura Distribution, importateur d'extensions capillaires premium au Québec.
Tu as un ton SENSUEL, FÉMININ et CHALEUREUX, comme une amie passionnée de beauté.

Voici un article de mode/coiffure venant de {article['country_flag']} {article['city']}:
Titre: {title_fr}
Résumé: {summary_fr[:300]}

Écris un post Facebook ENGAGEANT en français québécois.

STYLE LUXURA:
- Commence par un emoji accrocheur
- Ton sensuel et féminin, pas corporate
- Parle de la séduction, de la confiance, du pouvoir de beaux cheveux
- Mentionne l'inspiration de {article['city']} si pertinent
- 100-150 mots maximum
- Termine par luxuradistribution.com
- PAS de hashtags (je les ajoute après)

Exemples de ton:
- "Des cheveux qui font tourner les têtes..."
- "Se sentir irrésistible et confiante..."
- "Le secret des {article['city'].lower()}es pour des cheveux de rêve..."

Écris UNIQUEMENT le post."""

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
                        "temperature": 0.8
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                    
        except Exception as e:
            logger.error(f"Erreur génération post: {e}")
        
        return f"✨ {title_fr}\n\nDécouvrez cette tendance venue de {article['city']} sur luxuradistribution.com"
    
    async def _generate_image_prompt(self, article: Dict, title_fr: str, post_text: str) -> str:
        """Génère un prompt image contextuel basé sur l'article"""
        
        if not self.openai_key:
            return f"Real photograph of glamorous woman from 3/4 back angle, long voluminous flowing hair extensions, {article['city']} style, seductive elegant, natural daylight"
        
        prompt = f"""Tu es expert en création de prompts pour générer des VRAIES PHOTOS GLAMOUR de femmes avec EXTENSIONS CAPILLAIRES LUXURA.

ARTICLE SOURCE:
- Titre: {title_fr}
- Ville: {article['city']}
- Pays: {article['country_flag']} {article['country_name']}

POST FACEBOOK:
{post_text[:400]}

Crée un prompt image EN ANGLAIS pour une photo GLAMOUR, SENSUELLE et ASPIRATIONNELLE.

RÈGLES CRITIQUES - STYLE LUXURA EXTENSIONS:
1. Commence TOUJOURS par "Real photograph of a glamorous woman"
2. ANGLE: 3/4 back view OU semi-profile OU looking over shoulder - pour montrer les cheveux
3. CHEVEUX LUXURA: Long (past shoulders to mid-back), voluminous, flowing, silky hair extensions
4. Les cheveux doivent être LE FOCUS principal - en mouvement naturel
5. LUMIÈRE: Golden hour, sunset, natural sunlight highlighting the hair shine

DÉCORS LUXUEUX À VARIER (choisis selon le contexte de l'article):
- 🏖️ PLAGE: Amalfi Coast Italy, Santorini Greece, Maldives, Monaco beach club
- 🌅 SUNSET: Luxury yacht deck, rooftop bar with city view, infinity pool edge
- 🏛️ VILLE: Paris balcony with Eiffel view, Milan fashion district, Monaco harbor
- 🌸 NATURE: Lavender fields Provence, Tuscan vineyard, tropical garden
- ✨ SOIRÉE: Grand hotel terrace, luxury restaurant, gala event entrance

TENUES GLAMOUR À VARIER:
- 👙 Plage/Piscine: Elegant one-piece swimsuit, chic bikini with sarong, resort wear
- 👗 Soirée: Flowing evening gown, elegant cocktail dress, silk maxi dress
- 🌞 Jour: Chic sundress, elegant linen outfit, sophisticated casual
- 💎 Luxe: Designer outfit, haute couture inspired, red carpet style

AMBIANCE:
- Sensuelle mais élégante (jamais vulgaire)
- Aspirationnelle - vie de rêve
- Cheveux qui bougent au vent ou en mouvement
- Femme confiante, séductrice naturelle
- Maximum 200 caractères

EXEMPLES BONS PROMPTS:
- "Real photograph of glamorous woman from 3/4 back on Amalfi Coast beach, long voluminous hair flowing in sea breeze, elegant white swimsuit, golden sunset light, Mediterranean luxury"
- "Real photo of sensual woman looking over shoulder on Monaco yacht deck, luxurious thick hair cascading down her back, silk evening dress, champagne sunset glow"
- "Real photograph of elegant woman on Paris balcony with Eiffel Tower view, long flowing hair extensions catching golden hour light, chic black dress, glamorous Parisian mood"
- "Real photo of glamorous woman walking through Santorini streets, voluminous wavy hair in motion, flowing white summer dress, stunning ocean backdrop"

Retourne UNIQUEMENT le prompt en anglais. Sois créatif avec les décors!"""

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
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 250,
                        "temperature": 0.9  # Plus créatif pour varier les décors
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                    
        except Exception as e:
            logger.error(f"Erreur prompt image: {e}")
        
        # Fallback avec décors variés luxueux
        import random
        luxury_scenes = [
            "Real photograph of glamorous woman from 3/4 back on Amalfi Coast beach, long voluminous silky hair flowing in Mediterranean breeze, elegant white swimsuit, golden sunset, Italian Riviera luxury",
            "Real photo of sensual woman looking over shoulder on luxury yacht Monaco, thick flowing hair extensions cascading down bare back, silk champagne dress, sunset glow on water",
            "Real photograph of elegant woman on Paris hotel balcony with Eiffel Tower, long gorgeous hair catching golden hour light, black evening gown, romantic Parisian glamour",
            "Real photo of glamorous woman walking Santorini white streets, voluminous wavy hair in motion, flowing cream maxi dress, stunning blue ocean backdrop, Greek island luxury",
            "Real photograph of sensual woman by infinity pool Maldives, long silky hair extensions wet and flowing, chic one-piece swimsuit, tropical sunset paradise",
            "Real photo of elegant woman in Tuscan vineyard golden hour, luxurious thick hair blowing gently, sundress, rolling hills backdrop, Italian countryside glamour",
            "Real photograph of glamorous woman on Monaco rooftop terrace, long flowing hair extensions in evening breeze, red silk gown, city lights and harbor view",
            "Real photo of sensual woman at lavender fields Provence, voluminous hair catching sunset light, elegant linen dress, purple flower sea backdrop, French countryside luxury",
        ]
        return random.choice(luxury_scenes)
    
    async def _generate_grok_image(self, prompt: str) -> Optional[str]:
        """Génère une image avec Grok (xAI)"""
        
        if not self.grok_key:
            logger.warning("XAI_API_KEY non configurée - pas d'image Grok")
            return None
        
        logger.info(f"🎨 Génération image Grok...")
        logger.info(f"   Prompt: {prompt[:80]}...")
        
        # NOUVEAU PROMPT ULTRA-RÉALISTE - Style photo magazine
        enhanced_prompt = f"""REAL PHOTOGRAPH, NOT AI ART. {prompt}

CRITICAL REQUIREMENTS FOR REALISM:
- Real candid photograph of a real woman, NOT illustration, NOT digital art, NOT 3D render
- Shot on Canon EOS R5 or Sony A7R IV with 85mm f/1.4 portrait lens
- Natural daylight, golden hour or soft window light - NO dramatic lighting
- Bright, well-lit scene - NOT dark or moody
- Hair should look natural with flyaways and natural texture, NOT perfect CGI hair
- Skin with natural texture, pores visible, NOT airbrushed plastic skin
- Natural makeup, NOT heavy editorial makeup
- Candid lifestyle moment, woman NOT posing directly at camera
- Background should be real environment (cafe, street, park) with natural blur
- Colors should be warm but natural, NOT oversaturated
- Style: Vogue Paris editorial, Harper's Bazaar lifestyle shoot
- The woman should look like a real person you'd see on the street, NOT a perfect AI model
- NO text, NO watermarks, NO logos, NO borders

OUTPUT: Hyper-realistic photograph indistinguishable from a real camera photo."""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.grok_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-imagine-image",
                        "prompt": enhanced_prompt,
                        "n": 1,
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("data") and len(result["data"]) > 0:
                        image_url = result["data"][0].get("url")
                        if image_url:
                            logger.info(f"   ✅ Image Grok générée!")
                            return image_url
                
                logger.warning(f"   ⚠️ Grok: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            logger.error(f"   ❌ Erreur Grok: {e}")
        
        return None
    
    def _generate_hashtags(self, article: Dict) -> List[str]:
        """Génère les hashtags basés sur le pays et le contenu"""
        
        base_hashtags = ["#LuxuraDistribution", "#ExtensionsCheveux", "#Québec"]
        
        country_hashtags = {
            "france": ["#TendancesParis", "#StyleFrançais", "#ModeFéminine"],
            "italy": ["#StyleMilan", "#ModeItalienne", "#Eleganza"],
            "usa": ["#TrendingNYC", "#AmericanStyle", "#GlamourUSA"],
            "uk": ["#LondonStyle", "#BritishElegance", "#UKBeauty"],
            "canada": ["#BeautéQuébec", "#MontréalStyle", "#CanadianBeauty"],
        }
        
        country_tags = country_hashtags.get(article["country"], [])
        
        return (base_hashtags + country_tags)[:7]


# ============================================
# FONCTION PRINCIPALE POUR LE CRON
# ============================================

async def run_international_content_scan(max_posts: int = 3, send_email: bool = True) -> Dict:
    """
    Exécute le scan international complet
    
    Returns:
        Dict avec les résultats du scan
    """
    from app.services.email_approval import send_approval_email
    from app.services.watermark import process_image_with_watermark
    from app.routes.content import add_pending_post
    
    scanner = InternationalContentScanner()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "countries_scanned": scanner.get_todays_countries(),
        "articles_found": 0,
        "posts_generated": 0,
        "posts": [],
        "errors": []
    }
    
    logger.info("=" * 60)
    logger.info("🌍 LUXURA INTERNATIONAL CONTENT SCAN")
    logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 60)
    
    try:
        # 1. Scanner les actualités internationales
        articles = await scanner.scan_international_news(max_per_country=5)
        results["articles_found"] = len(articles)
        
        if not articles:
            logger.warning("Aucun article trouvé")
            return results
        
        # 2. Générer les posts (max 3)
        for article in articles[:max_posts]:
            try:
                logger.info(f"\n📝 Génération post: {article['title'][:50]}...")
                
                # Générer le post complet
                post = await scanner.generate_luxura_post(article)
                
                # 3. Ajouter watermark si image générée
                if post.get("image_url"):
                    logger.info(f"🏷️ Ajout watermark LUXURA...")
                    watermarked_bytes = await process_image_with_watermark(post["image_url"])
                    if watermarked_bytes:
                        post["watermarked_image_bytes"] = watermarked_bytes
                        post["has_watermark"] = True
                        logger.info(f"   ✅ Watermark ajouté! ({len(watermarked_bytes)} bytes)")
                
                results["posts"].append(post)
                results["posts_generated"] += 1
                
                # 4. Envoyer email d'approbation
                if send_email:
                    post_data = {
                        "text": post["post_text"],
                        "full_text": post["post_text"],
                        "hashtags": post["hashtags"],
                        "image_url": post.get("image_url"),
                        "source_title": f"{post['country_flag']} {post['title_fr'][:50]}",
                        "source_url": post["source_url"],
                        "country": post["country"],
                    }
                    
                    email_result = await send_approval_email(post_data)
                    
                    if email_result.get("success"):
                        post_id = email_result.get("post_id")
                        add_pending_post(post_id, {
                            **post_data,
                            "watermarked_image_bytes": post.get("watermarked_image_bytes"),
                        })
                        post["post_id"] = post_id
                        post["email_sent"] = True
                        logger.info(f"   📧 Email envoyé! ID: {post_id}")
                
                logger.info(f"   ✅ Post généré: {post['country_flag']} {post['title_fr'][:40]}...")
                
            except Exception as e:
                logger.error(f"   ❌ Erreur: {e}")
                results["errors"].append(str(e))
    
    except Exception as e:
        logger.error(f"Erreur scan: {e}")
        results["errors"].append(str(e))
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ SCAN TERMINÉ: {results['posts_generated']} posts générés")
    logger.info("=" * 60)
    
    return results
