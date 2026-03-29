"""
INTERNAL LINKING - Maillage interne SEO automatique
Version: 1.0
Date: 2026-03-29

Fonctionnalités:
- Détection du type d'article
- Sélection contextuelle de 3-5 liens
- Injection dans le corps de l'article
- Bloc final structuré
- Ancres naturelles
"""

import re
import random
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION DES LIENS LUXURA
# =====================================================

# URLs des pages Luxura (à ajuster selon le site réel)
LUXURA_BASE_URL = "https://www.luxuradistribution.com"

# Collections produits
PRODUCT_COLLECTIONS = {
    "halo": {
        "url": f"{LUXURA_BASE_URL}/halo-extensions",
        "name": "Extensions Halo Everly",
        "anchors": [
            "extensions Halo",
            "Halo Everly",
            "fil invisible Halo",
            "extensions à fil invisible"
        ],
        "keywords": ["halo", "everly", "fil invisible", "sans attache", "débutante"]
    },
    "genius": {
        "url": f"{LUXURA_BASE_URL}/genius-weft",
        "name": "Genius Weft Vivian",
        "anchors": [
            "Genius Weft",
            "extensions Genius",
            "trame ultra-fine",
            "Genius Weft Vivian"
        ],
        "keywords": ["genius", "weft", "trame", "vivian", "ultra-fine", "discrète"]
    },
    "tape": {
        "url": f"{LUXURA_BASE_URL}/tape-in-extensions",
        "name": "Tape-in Aurora",
        "anchors": [
            "extensions Tape-in",
            "Tape Aurora",
            "extensions adhésives",
            "bandes adhésives"
        ],
        "keywords": ["tape", "adhésive", "bande", "aurora", "sandwich", "réutilisable"]
    },
    "itip": {
        "url": f"{LUXURA_BASE_URL}/i-tip-extensions",
        "name": "I-Tip Eleanor",
        "anchors": [
            "extensions I-Tip",
            "I-Tip Eleanor",
            "extensions à froid",
            "pose mèche par mèche"
        ],
        "keywords": ["itip", "i-tip", "froid", "eleanor", "kératine", "mèche"]
    }
}

# Pages business stratégiques (PRIORITÉ HAUTE)
BUSINESS_PAGES = {
    "revendeur": {
        "url": f"{LUXURA_BASE_URL}/devenir-revendeur",
        "name": "Devenir revendeur Luxura",
        "anchors": [
            "devenir revendeur",
            "partenariat Luxura",
            "distribuer nos extensions",
            "rejoindre notre réseau"
        ],
        "keywords": ["revendeur", "partenaire", "distribuer", "réseau", "salon affilié"],
        "priority": "high"
    },
    "salons": {
        "url": f"{LUXURA_BASE_URL}/salons-partenaires",
        "name": "Salons partenaires",
        "anchors": [
            "salons partenaires",
            "nos salons affiliés",
            "trouver un salon",
            "réseau de salons"
        ],
        "keywords": ["salon", "partenaire", "affilié", "coiffeur", "professionnel"],
        "priority": "high"
    },
    "depot": {
        "url": f"{LUXURA_BASE_URL}/depot-inventaire",
        "name": "Dépôt d'inventaire",
        "anchors": [
            "dépôt d'inventaire",
            "stock en consignation",
            "inventaire salon",
            "dépôt sans frais"
        ],
        "keywords": ["dépôt", "inventaire", "consignation", "stock", "sans investissement"],
        "priority": "high"
    },
    "boutique": {
        "url": f"{LUXURA_BASE_URL}/boutique",
        "name": "Boutique Luxura",
        "anchors": [
            "notre boutique",
            "tous nos produits",
            "collection complète",
            "acheter en ligne"
        ],
        "keywords": ["boutique", "acheter", "commander", "produits", "collection"],
        "priority": "medium"
    }
}

# Mapping catégorie → liens recommandés
CATEGORY_LINK_STRATEGY = {
    "cheveux_fins": {
        "products": ["halo", "tape"],  # Halo et Tape sont légers
        "business": ["boutique"],
        "max_links": 4
    },
    "entretien": {
        "products": [],  # Pas de produit spécifique
        "business": ["boutique"],
        "max_links": 3
    },
    "comparatif": {
        "products": ["halo", "genius", "tape", "itip"],  # Tous les produits
        "business": ["boutique"],
        "max_links": 5
    },
    "b2b_salon": {
        "products": ["genius", "tape"],
        "business": ["revendeur", "salons", "depot"],  # Priorité business
        "max_links": 5
    },
    "guide": {
        "products": ["halo", "genius", "tape", "itip"],
        "business": ["boutique", "salons"],
        "max_links": 5
    },
    "achat_en_ligne": {
        "products": ["halo", "genius", "tape", "itip"],
        "business": ["boutique"],
        "max_links": 4
    },
    "halo": {
        "products": ["halo"],
        "business": ["boutique", "salons"],
        "max_links": 4
    },
    "genius": {
        "products": ["genius"],
        "business": ["boutique", "revendeur"],
        "max_links": 4
    },
    "tape": {
        "products": ["tape"],
        "business": ["boutique", "salons"],
        "max_links": 4
    },
    "itip": {
        "products": ["itip"],
        "business": ["boutique", "salons"],
        "max_links": 4
    },
    "general": {
        "products": ["halo", "genius"],
        "business": ["boutique"],
        "max_links": 4
    }
}


# =====================================================
# FONCTIONS DE DÉTECTION
# =====================================================

def detect_article_context(content: str, title: str, category: str) -> Dict:
    """
    Analyse le contenu pour détecter le contexte de l'article.
    Retourne les produits et pages business pertinents.
    
    IMPORTANT: La catégorie déclarée a priorité sur la détection par mots-clés.
    """
    content_lower = (content + " " + title).lower()
    
    context = {
        "detected_products": [],
        "is_b2b": False,
        "is_consumer": False,
        "is_comparison": False,
        "is_maintenance": False
    }
    
    # Détecter les produits mentionnés
    for product_key, product_data in PRODUCT_COLLECTIONS.items():
        for keyword in product_data["keywords"]:
            if keyword in content_lower:
                if product_key not in context["detected_products"]:
                    context["detected_products"].append(product_key)
                break
    
    # PRIORITÉ À LA CATÉGORIE DÉCLARÉE
    # Catégories B2B explicites
    if category == "b2b_salon":
        context["is_b2b"] = True
    # Catégories consommateur explicites
    elif category in ["cheveux_fins", "guide", "achat_en_ligne", "entretien"]:
        context["is_consumer"] = True
    # Comparatif
    elif category == "comparatif":
        context["is_comparison"] = True
    else:
        # Fallback: détection par mots-clés (moins fiable)
        # B2B: termes TRÈS spécifiques pour éviter les faux positifs
        b2b_strong_keywords = ["revendeur", "partenaire luxura", "dépôt d'inventaire", "salon affilié", "devenir partenaire"]
        context["is_b2b"] = any(kw in content_lower for kw in b2b_strong_keywords)
        
        # Consommateur
        consumer_keywords = ["cheveux fins", "volume naturel", "transformation", "mariage", "occasion spéciale"]
        context["is_consumer"] = any(kw in content_lower for kw in consumer_keywords)
    
    # Détection maintenance (peut coexister avec d'autres)
    maintenance_keywords = ["entretien", "soins quotidiens", "durée de vie", "prolonger", "lavage", "brossage"]
    context["is_maintenance"] = any(kw in content_lower for kw in maintenance_keywords) or category == "entretien"
    
    # Détection comparaison
    comparison_keywords = ["vs", "versus", "comparatif", "différence entre", "choisir entre"]
    context["is_comparison"] = context["is_comparison"] or any(kw in content_lower for kw in comparison_keywords)
    
    return context


def select_links_for_article(
    category: str,
    context: Dict,
    max_links: int = 5
) -> List[Dict]:
    """
    Sélectionne les liens les plus pertinents pour l'article.
    Priorité: pages business > produits détectés > produits par catégorie
    """
    selected_links = []
    
    strategy = CATEGORY_LINK_STRATEGY.get(category, CATEGORY_LINK_STRATEGY["general"])
    
    # 1. PRIORITÉ HAUTE: Pages business pour articles B2B
    if context["is_b2b"]:
        for biz_key in ["revendeur", "depot", "salons"]:
            if biz_key in strategy["business"] or context["is_b2b"]:
                biz_page = BUSINESS_PAGES.get(biz_key)
                if biz_page and len(selected_links) < max_links:
                    selected_links.append({
                        "type": "business",
                        "key": biz_key,
                        "url": biz_page["url"],
                        "name": biz_page["name"],
                        "anchor": random.choice(biz_page["anchors"]),
                        "priority": "high"
                    })
    
    # 2. Produits détectés dans le contenu
    for product_key in context["detected_products"]:
        if len(selected_links) >= max_links:
            break
        product = PRODUCT_COLLECTIONS.get(product_key)
        if product:
            selected_links.append({
                "type": "product",
                "key": product_key,
                "url": product["url"],
                "name": product["name"],
                "anchor": random.choice(product["anchors"]),
                "priority": "medium"
            })
    
    # 3. Produits recommandés par catégorie (si pas assez de liens)
    for product_key in strategy["products"]:
        if len(selected_links) >= max_links:
            break
        # Éviter les doublons
        if any(l["key"] == product_key for l in selected_links):
            continue
        product = PRODUCT_COLLECTIONS.get(product_key)
        if product:
            selected_links.append({
                "type": "product",
                "key": product_key,
                "url": product["url"],
                "name": product["name"],
                "anchor": random.choice(product["anchors"]),
                "priority": "low"
            })
    
    # 4. Pages business restantes
    for biz_key in strategy["business"]:
        if len(selected_links) >= max_links:
            break
        if any(l["key"] == biz_key for l in selected_links):
            continue
        biz_page = BUSINESS_PAGES.get(biz_key)
        if biz_page:
            selected_links.append({
                "type": "business",
                "key": biz_key,
                "url": biz_page["url"],
                "name": biz_page["name"],
                "anchor": random.choice(biz_page["anchors"]),
                "priority": "low"
            })
    
    return selected_links[:max_links]


# =====================================================
# INJECTION DE LIENS
# =====================================================

def inject_contextual_links(content: str, links: List[Dict], max_inline: int = 2) -> str:
    """
    Injecte des liens contextuels dans le corps de l'article.
    Maximum 2 liens inline pour ne pas surcharger.
    """
    if not links:
        return content
    
    modified_content = content
    injected_count = 0
    
    # Trier par priorité
    priority_links = [l for l in links if l["priority"] == "high"][:max_inline]
    
    for link in priority_links:
        if injected_count >= max_inline:
            break
        
        # Chercher une mention naturelle dans le contenu
        anchor = link["anchor"]
        url = link["url"]
        
        # Patterns de recherche (texte sans lien existant)
        patterns = [
            (anchor, f'<a href="{url}">{anchor}</a>'),
            (anchor.title(), f'<a href="{url}">{anchor.title()}</a>'),
            (anchor.lower(), f'<a href="{url}">{anchor}</a>')
        ]
        
        for pattern, replacement in patterns:
            # Vérifier que le texte existe et n'est pas déjà un lien
            if pattern in modified_content and f'>{pattern}<' not in modified_content:
                # Remplacer seulement la première occurrence
                modified_content = modified_content.replace(pattern, replacement, 1)
                injected_count += 1
                logger.info(f"🔗 Lien contextuel injecté: {anchor} → {url}")
                break
    
    return modified_content


def generate_footer_block(links: List[Dict], category: str) -> str:
    """
    Génère le bloc de liens en fin d'article.
    Structure propre avec sections.
    """
    if not links:
        return ""
    
    product_links = [l for l in links if l["type"] == "product"]
    business_links = [l for l in links if l["type"] == "business"]
    
    html_parts = []
    
    # Section produits
    if product_links:
        html_parts.append('<h3>Découvrez nos collections</h3>')
        html_parts.append('<ul>')
        for link in product_links:
            html_parts.append(f'<li><a href="{link["url"]}">{link["name"]}</a></li>')
        html_parts.append('</ul>')
    
    # Section business (plus subtile)
    if business_links:
        html_parts.append('<h3>Ressources utiles</h3>')
        html_parts.append('<ul>')
        for link in business_links:
            html_parts.append(f'<li><a href="{link["url"]}">{link["name"]}</a></li>')
        html_parts.append('</ul>')
    
    # Call-to-action pour B2B
    if category in ["b2b_salon", "depot"]:
        cta = BUSINESS_PAGES.get("revendeur", {})
        if cta:
            html_parts.append(f'<p><strong>Vous êtes professionnel?</strong> <a href="{cta["url"]}">Découvrez notre programme partenaires</a>.</p>')
    
    return '\n'.join(html_parts)


# =====================================================
# FONCTION PRINCIPALE
# =====================================================

def apply_internal_linking(
    content: str,
    title: str,
    category: str,
    max_links: int = 5,
    max_inline: int = 2
) -> Tuple[str, List[Dict]]:
    """
    Applique le maillage interne complet à un article.
    
    Args:
        content: Contenu HTML de l'article
        title: Titre de l'article
        category: Catégorie de l'article
        max_links: Nombre max de liens total
        max_inline: Nombre max de liens dans le corps
    
    Returns:
        (content_with_links, links_used)
    """
    # 1. Analyser le contexte
    context = detect_article_context(content, title, category)
    logger.info(f"📊 Contexte détecté: produits={context['detected_products']}, b2b={context['is_b2b']}")
    
    # 2. Sélectionner les liens
    links = select_links_for_article(category, context, max_links)
    logger.info(f"🔗 Liens sélectionnés: {[l['key'] for l in links]}")
    
    if not links:
        return content, []
    
    # 3. Injecter les liens contextuels dans le corps
    content_with_inline = inject_contextual_links(content, links, max_inline)
    
    # 4. Ajouter le bloc final
    footer_block = generate_footer_block(links, category)
    
    # 5. Assembler
    final_content = content_with_inline
    if footer_block:
        # Ajouter avant la dernière balise </p> ou à la fin
        if '</p>' in final_content:
            # Trouver le dernier paragraphe
            last_p_index = final_content.rfind('</p>')
            final_content = final_content[:last_p_index + 4] + '\n\n' + footer_block
        else:
            final_content += '\n\n' + footer_block
    
    logger.info(f"✅ Maillage interne appliqué: {len(links)} liens")
    
    return final_content, links


# =====================================================
# FONCTION D'INTÉGRATION AVEC LE GÉNÉRATEUR
# =====================================================

async def enhance_blog_with_links(blog_data: Dict) -> Dict:
    """
    Enrichit un blog généré avec le maillage interne.
    À appeler après la génération du contenu.
    """
    content = blog_data.get("content", "")
    title = blog_data.get("title", "")
    category = blog_data.get("category", "general")
    
    if not content:
        return blog_data
    
    # Appliquer le maillage
    enhanced_content, links_used = apply_internal_linking(
        content=content,
        title=title,
        category=category,
        max_links=5,
        max_inline=2
    )
    
    # Mettre à jour le blog
    blog_data["content"] = enhanced_content
    blog_data["internal_links"] = [
        {"key": l["key"], "url": l["url"], "type": l["type"]} 
        for l in links_used
    ]
    blog_data["internal_links_count"] = len(links_used)
    
    return blog_data
