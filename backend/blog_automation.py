# =====================================================
# BLOG AUTOMATION SYSTEM - Luxura Distribution
# Génération automatique + Publication Wix + Images libres
# =====================================================

import os
import random
import uuid
import httpx
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

# =====================================================
# UNSPLASH FREE IMAGES - Catégorisées par sujet
# =====================================================

UNSPLASH_IMAGES = {
    "halo": [
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",  # Femme cheveux longs
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=800",  # Salon coiffure
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800",  # Cheveux brillants
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=800",  # Femme blonde
        "https://images.unsplash.com/photo-1605497788044-5a32c7078486?w=800",  # Cheveux wavy
    ],
    "genius": [
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=800",  # Cheveux parfaits
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=800",  # Femme professionnelle
        "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=800",  # Salon luxe
        "https://images.unsplash.com/photo-1616683693504-3ea7e9ad6fec?w=800",  # Extensions visibles
        "https://images.unsplash.com/photo-1559599101-f09722fb4948?w=800",  # Coiffeuse travail
    ],
    "tape": [
        "https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=800",  # Pose extensions
        "https://images.unsplash.com/photo-1562322140-8baeececf3df?w=800",  # Salon coiffure
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800",  # Application
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",  # Résultat
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=800",  # Outils salon
    ],
    "itip": [
        "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=800",  # Détail cheveux
        "https://images.unsplash.com/photo-1559599101-f09722fb4948?w=800",  # Application pro
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=800",  # Salon
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=800",  # Cheveux naturels
        "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=800",  # Portrait femme
    ],
    "entretien": [
        "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=800",  # Brossage
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=800",  # Soins
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=800",  # Cheveux sains
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800",  # Brillance
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=800",  # Produits
    ],
    "tendances": [
        "https://images.unsplash.com/photo-1605497788044-5a32c7078486?w=800",  # Style moderne
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=800",  # Blonde tendance
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=800",  # Look pro
        "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=800",  # Style 2025
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=800",  # Salon tendance
    ],
    "general": [
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800",
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=800",
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=800",
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=800",
    ]
}

# =====================================================
# SUJETS DE BLOG - Focus Halo, Genius, Tape, I-Tip
# =====================================================

BLOG_TOPICS_EXTENDED = [
    # === HALO EXTENSIONS ===
    {
        "topic": "Extensions Halo : La révolution du volume instantané sans engagement",
        "category": "halo",
        "keywords": ["extensions halo Québec", "volume instantané", "fil invisible", "extensions sans colle"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Halo vs autres extensions : Pourquoi le fil invisible conquiert le Québec",
        "category": "halo", 
        "keywords": ["halo vs clip-in", "extensions fil invisible", "comparatif extensions"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Comment porter des extensions Halo pour un look naturel parfait",
        "category": "halo",
        "keywords": ["tutoriel halo", "porter extensions halo", "look naturel extensions"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Extensions Halo pour cheveux fins : La solution idéale au Québec",
        "category": "halo",
        "keywords": ["cheveux fins solution", "halo cheveux fins", "volume cheveux fins"],
        "focus_product": "Halo Everly"
    },
    
    # === GENIUS WEFT ===
    {
        "topic": "Genius Weft : La technologie révolutionnaire de trame invisible 0.78mm",
        "category": "genius",
        "keywords": ["genius weft Québec", "trame invisible", "extensions professionnelles"],
        "focus_product": "Genius Vivian"
    },
    {
        "topic": "Pourquoi les salons du Québec adoptent les extensions Genius Weft",
        "category": "genius",
        "keywords": ["genius weft salon", "extensions salon professionnel", "fournisseur extensions"],
        "focus_product": "Genius Vivian"
    },
    {
        "topic": "Installation Genius Weft : Guide complet pour professionnels",
        "category": "genius",
        "keywords": ["installer genius weft", "technique couture invisible", "formation extensions"],
        "focus_product": "Genius Vivian"
    },
    {
        "topic": "Genius Weft vs Tape-in : Quelle technique choisir pour votre cliente ?",
        "category": "genius",
        "keywords": ["genius vs tape", "comparatif extensions", "meilleure technique extensions"],
        "focus_product": "Genius Vivian"
    },
    
    # === TAPE-IN / BANDE ADHÉSIVE ===
    {
        "topic": "Extensions Bande Adhésive Aurora : Application sandwich professionnelle",
        "category": "tape",
        "keywords": ["tape-in extensions", "bande adhésive cheveux", "extensions sandwich"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Combien de temps durent les extensions Tape-in ? Guide complet",
        "category": "tape",
        "keywords": ["durée tape-in", "entretien tape extensions", "repose extensions"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Tape-in vs Genius Weft : Le match des extensions professionnelles",
        "category": "tape",
        "keywords": ["tape vs genius", "meilleures extensions salon", "comparatif technique"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Retrait et repositionnement des extensions Tape-in : Guide expert",
        "category": "tape",
        "keywords": ["retrait tape extensions", "repositionner extensions", "entretien tape-in"],
        "focus_product": "Tape Aurora"
    },
    
    # === I-TIP / KÉRATINE ===
    {
        "topic": "Extensions I-Tip kératine : La technique mèche par mèche ultime",
        "category": "itip",
        "keywords": ["i-tip extensions", "kératine cheveux", "extensions mèche par mèche"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "I-Tip vs Tape-in : Quelle méthode pour un résultat naturel ?",
        "category": "itip",
        "keywords": ["i-tip vs tape", "extensions naturelles", "kératine vs adhésive"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "Formation extensions I-Tip : Maîtriser la fusion kératine",
        "category": "itip",
        "keywords": ["formation i-tip", "technique kératine", "apprendre extensions"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "Entretien extensions I-Tip : Prolonger la durée de vie jusqu'à 6 mois",
        "category": "itip",
        "keywords": ["entretien i-tip", "durée extensions kératine", "soins extensions"],
        "focus_product": "I-Tip Eleanor"
    },
    
    # === SUJETS GÉNÉRAUX ===
    {
        "topic": "Tendances extensions cheveux 2025 : Balayage, ombré et couleurs naturelles",
        "category": "tendances",
        "keywords": ["tendances extensions 2025", "couleurs cheveux tendance", "balayage extensions"],
        "focus_product": None
    },
    {
        "topic": "Comment entretenir ses extensions cheveux : Guide professionnel complet",
        "category": "entretien",
        "keywords": ["entretien extensions", "soins extensions cheveux", "durée vie extensions"],
        "focus_product": None
    },
    {
        "topic": "Devenir partenaire Luxura : Programme salon extensions cheveux Québec",
        "category": "general",
        "keywords": ["partenaire salon extensions", "distributeur extensions Québec", "grossiste cheveux"],
        "focus_product": None
    },
    {
        "topic": "Extensions cheveux naturel vs synthétique : Le guide définitif",
        "category": "general",
        "keywords": ["extensions naturel vs synthétique", "cheveux remy", "qualité extensions"],
        "focus_product": None
    },
]

def get_blog_image_by_category(category: str) -> str:
    """Retourne une image libre de droits selon la catégorie"""
    images = UNSPLASH_IMAGES.get(category, UNSPLASH_IMAGES["general"])
    return random.choice(images)

# =====================================================
# WIX BLOG INTEGRATION
# =====================================================

async def get_wix_member_id(api_key: str, site_id: str) -> Optional[str]:
    """Récupère le member ID du propriétaire du site pour la publication"""
    try:
        async with httpx.AsyncClient() as client:
            # Try to get site members
            response = await client.get(
                "https://www.wixapis.com/members/v1/members/query",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                members = data.get("members", [])
                if members:
                    return members[0].get("id")
    except Exception as e:
        logger.error(f"Error getting Wix member ID: {e}")
    return None

async def get_wix_blog_categories(api_key: str, site_id: str) -> List[Dict]:
    """Récupère les catégories de blog Wix existantes"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.wixapis.com/blog/v3/categories",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("categories", [])
    except Exception as e:
        logger.error(f"Error getting Wix blog categories: {e}")
    return []

async def create_wix_draft_post(
    api_key: str,
    site_id: str,
    title: str,
    content: str,
    excerpt: str,
    cover_image: str,
    tags: List[str] = None
) -> Optional[Dict]:
    """Crée un brouillon de post sur Wix Blog"""
    try:
        async with httpx.AsyncClient() as client:
            # Convertir le contenu HTML en format Ricos (Wix rich content)
            rich_content = html_to_ricos(content)
            
            payload = {
                "draftPost": {
                    "title": title,
                    "excerpt": excerpt,
                    "richContent": rich_content,
                    "coverMedia": {
                        "image": cover_image,
                        "displayed": True
                    },
                    "tags": tags or []
                }
            }
            
            response = await client.post(
                "https://www.wixapis.com/blog/v3/draft-posts",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Wix draft creation failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error creating Wix draft: {e}")
        return None

async def publish_wix_draft(api_key: str, site_id: str, draft_id: str) -> bool:
    """Publie un brouillon de post Wix"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}/publish",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Error publishing Wix draft: {e}")
        return False

def html_to_ricos(html_content: str) -> Dict:
    """Convertit le HTML en format Ricos (Wix rich content format)"""
    import re
    
    nodes = []
    
    # Nettoyer le HTML
    content = html_content.strip()
    
    # Parser les balises principales
    # H1
    for match in re.finditer(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL):
        nodes.append({
            "type": "HEADING",
            "headingData": {"level": 1},
            "nodes": [{"type": "TEXT", "textData": {"text": match.group(1).strip()}}]
        })
    
    # H2
    for match in re.finditer(r'<h2[^>]*>(.*?)</h2>', content, re.DOTALL):
        nodes.append({
            "type": "HEADING",
            "headingData": {"level": 2},
            "nodes": [{"type": "TEXT", "textData": {"text": match.group(1).strip()}}]
        })
    
    # H3
    for match in re.finditer(r'<h3[^>]*>(.*?)</h3>', content, re.DOTALL):
        nodes.append({
            "type": "HEADING", 
            "headingData": {"level": 3},
            "nodes": [{"type": "TEXT", "textData": {"text": match.group(1).strip()}}]
        })
    
    # Paragraphes
    for match in re.finditer(r'<p[^>]*>(.*?)</p>', content, re.DOTALL):
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        if text:
            nodes.append({
                "type": "PARAGRAPH",
                "nodes": [{"type": "TEXT", "textData": {"text": text}}]
            })
    
    # Listes
    for ul_match in re.finditer(r'<ul[^>]*>(.*?)</ul>', content, re.DOTALL):
        list_items = []
        for li_match in re.finditer(r'<li[^>]*>(.*?)</li>', ul_match.group(1), re.DOTALL):
            text = re.sub(r'<[^>]+>', '', li_match.group(1)).strip()
            list_items.append({
                "type": "LIST_ITEM",
                "nodes": [{"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "textData": {"text": text}}]}]
            })
        if list_items:
            nodes.append({
                "type": "BULLETED_LIST",
                "nodes": list_items
            })
    
    # Si aucun node, créer un paragraphe avec le contenu brut
    if not nodes:
        clean_text = re.sub(r'<[^>]+>', '\n', content).strip()
        for para in clean_text.split('\n\n'):
            if para.strip():
                nodes.append({
                    "type": "PARAGRAPH",
                    "nodes": [{"type": "TEXT", "textData": {"text": para.strip()}}]
                })
    
    return {
        "nodes": nodes,
        "metadata": {
            "version": 1,
            "createdTimestamp": datetime.now(timezone.utc).isoformat(),
            "updatedTimestamp": datetime.now(timezone.utc).isoformat()
        }
    }

# =====================================================
# GÉNÉRATION DE BLOG AVEC IA
# =====================================================

async def generate_blog_with_ai(
    topic_data: Dict,
    emergent_key: str,
    existing_titles: List[str] = None
) -> Optional[Dict]:
    """Génère un article de blog SEO optimisé avec l'IA"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        topic = topic_data["topic"]
        category = topic_data["category"]
        keywords = topic_data["keywords"]
        focus_product = topic_data.get("focus_product")
        
        # System message optimisé SEO Québec
        system_message = f"""Tu es un expert SEO francophone spécialisé dans les extensions capillaires au Québec.
Tu écris pour Luxura Distribution, le leader des extensions cheveux haut de gamme au Canada.

STYLE:
- Professionnel mais accessible
- Informatif et engageant
- Français québécois naturel
- SEO optimisé avec mots-clés intégrés naturellement

PRODUITS LUXURA:
- Genius Weft Vivian: Trame ultra-fine 0.78mm révolutionnaire, découpable, couture invisible
- Halo Everly: Fil invisible ajustable, volume instantané, aucune fixation permanente
- Tape Aurora: Bande adhésive médicale, pose sandwich, réutilisable 3-4 fois
- I-Tip Eleanor: Kératine italienne, fusion mèche par mèche, invisible

LOCALISATION: Québec, Montréal, Canada
LANGUE: Français québécois UNIQUEMENT"""

        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"blog-{uuid.uuid4().hex[:8]}",
            system_message=system_message
        ).with_model("openai", "gpt-4.1-mini")
        
        product_mention = f"\nMentionne particulièrement le produit: {focus_product}" if focus_product else ""
        
        prompt = f"""Écris un article de blog SEO complet sur le sujet suivant:

SUJET: {topic}
CATÉGORIE: {category}
MOTS-CLÉS À INTÉGRER: {', '.join(keywords)}
{product_mention}

STRUCTURE:
1. Titre H1 accrocheur avec mot-clé principal
2. Introduction engageante (100-150 mots)
3. Section 1 avec H2 + contenu détaillé
4. Section 2 avec H2 + contenu détaillé
5. Section 3 avec H2 + liste à puces des avantages
6. Conclusion avec appel à l'action Luxura Distribution

CONSIGNES:
- 800-1200 mots total
- Intégrer chaque mot-clé 2-3 fois naturellement
- Utiliser des balises HTML: <h1>, <h2>, <p>, <ul>, <li>, <strong>
- Mentionner Luxura Distribution comme expert
- Inclure des statistiques ou faits si pertinent
- Ton professionnel mais chaleureux

FORMAT JSON STRICT:
{{
  "title": "Titre SEO optimisé",
  "excerpt": "Résumé accrocheur de 150 caractères max",
  "content": "Contenu HTML complet",
  "meta_description": "Description meta de 155 caractères max",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parser la réponse JSON
        import json
        response_text = response.strip()
        
        # Nettoyer les balises markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        try:
            blog_data = json.loads(response_text.strip())
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                blog_data = json.loads(json_match.group())
            else:
                return None
        
        # Ajouter l'image et les métadonnées
        blog_data["image"] = get_blog_image_by_category(category)
        blog_data["category"] = category
        blog_data["keywords"] = keywords
        blog_data["focus_product"] = focus_product
        
        return blog_data
        
    except Exception as e:
        logger.error(f"Error generating blog with AI: {e}")
        return None

# =====================================================
# GÉNÉRATION AUTOMATIQUE 2x PAR JOUR
# =====================================================

async def generate_daily_blogs(
    db,
    emergent_key: str,
    wix_api_key: str = None,
    wix_site_id: str = None,
    publish_to_wix: bool = True,
    count: int = 2
) -> List[Dict]:
    """Génère automatiquement les blogs quotidiens"""
    results = []
    
    # Récupérer les titres existants pour éviter les doublons
    existing_posts = await db.blog_posts.find({}, {"title": 1}).to_list(1000)
    existing_titles = [p.get("title", "").lower() for p in existing_posts]
    
    # Sélectionner des sujets non couverts
    available_topics = [
        t for t in BLOG_TOPICS_EXTENDED 
        if t["topic"].lower() not in existing_titles
    ]
    
    # Si tous les sujets sont couverts, réutiliser avec rotation
    if len(available_topics) < count:
        # Ajouter des variations aux sujets existants
        available_topics = BLOG_TOPICS_EXTENDED.copy()
        random.shuffle(available_topics)
    
    # Sélectionner les sujets pour aujourd'hui (diversifier les catégories)
    categories_used = []
    selected_topics = []
    
    for topic in available_topics:
        if len(selected_topics) >= count:
            break
        if topic["category"] not in categories_used or len(categories_used) >= 4:
            selected_topics.append(topic)
            categories_used.append(topic["category"])
    
    # Générer chaque blog
    for topic_data in selected_topics:
        blog_data = await generate_blog_with_ai(topic_data, emergent_key, existing_titles)
        
        if not blog_data:
            continue
        
        # Créer l'entrée dans la base locale
        post_id = f"auto-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4]}"
        
        blog_post = {
            "id": post_id,
            "title": blog_data.get("title", topic_data["topic"]),
            "excerpt": blog_data.get("excerpt", ""),
            "content": blog_data.get("content", ""),
            "meta_description": blog_data.get("meta_description", ""),
            "tags": blog_data.get("tags", topic_data["keywords"]),
            "image": blog_data.get("image"),
            "category": topic_data["category"],
            "author": "Luxura Distribution",
            "created_at": datetime.now(timezone.utc),
            "auto_generated": True,
            "published_to_wix": False
        }
        
        await db.blog_posts.insert_one(blog_post)
        
        # Publier sur Wix si configuré
        if publish_to_wix and wix_api_key and wix_site_id:
            wix_result = await create_wix_draft_post(
                api_key=wix_api_key,
                site_id=wix_site_id,
                title=blog_post["title"],
                content=blog_post["content"],
                excerpt=blog_post["excerpt"],
                cover_image=blog_post["image"],
                tags=blog_post["tags"]
            )
            
            if wix_result:
                draft_id = wix_result.get("draftPost", {}).get("id")
                if draft_id:
                    # Publier le brouillon
                    published = await publish_wix_draft(wix_api_key, wix_site_id, draft_id)
                    if published:
                        await db.blog_posts.update_one(
                            {"id": post_id},
                            {"$set": {"published_to_wix": True, "wix_post_id": draft_id}}
                        )
                        blog_post["published_to_wix"] = True
        
        # Nettoyer pour la réponse
        blog_post.pop("_id", None)
        if isinstance(blog_post.get("created_at"), datetime):
            blog_post["created_at"] = blog_post["created_at"].isoformat()
        
        results.append(blog_post)
        existing_titles.append(blog_post["title"].lower())
    
    return results
