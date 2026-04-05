"""
🔍 LUXURA SEO IMAGE OPTIMIZER
================================
Optimise les noms d'images et métadonnées pour le SEO local Québec.

Mots-clés cibles:
- Luxura rallonge / Luxura extension
- Régions: Québec, Beauce, Lévis, Chaudière-Appalaches, Rive-Sud
- Types: Genius, Tape, Halo, I-Tip, Ponytail, Clip-in

Fonctionnalités:
1. Génère des noms de fichiers SEO-friendly
2. Génère des textes alt optimisés
3. Génère des méta-descriptions produits
4. Batch update via Wix API
"""

import os
import re
import httpx
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION SEO ====================

# Mots-clés géographiques ciblés (Québec francophone)
GEO_KEYWORDS = [
    "Québec",
    "Beauce", 
    "Lévis",
    "Chaudière-Appalaches",
    "Rive-Sud",
    "St-Georges",
    "Thetford",
    "Montmagny",
    "Trois-Rivières",
    "Montréal",
    "Sherbrooke",
    "Gatineau",
    "Saguenay"
]

# Synonymes SEO pour "extensions de cheveux"
EXTENSION_SYNONYMS = [
    "rallonge capillaire",
    "rallonges cheveux",
    "extension cheveux",
    "extensions capillaires",
    "rallonge naturelle",
    "cheveux naturels",
    "extensions humaines",
    "rallonges 100% naturelles"
]

# Types de produits avec variantes SEO
PRODUCT_TYPES_SEO = {
    "genius": {
        "name": "Genius Trame Invisible",
        "keywords": ["trame invisible", "genius weft", "hand-tied weft", "couture invisible"],
        "benefits": ["aucune colle", "sans dommage", "réutilisable", "confort maximal"]
    },
    "tape": {
        "name": "Bande Adhésive",
        "keywords": ["tape-in", "bande adhésive", "extensions à bandes", "tape extensions"],
        "benefits": ["pose rapide", "naturel", "discret", "longue durée"]
    },
    "halo": {
        "name": "Halo",
        "keywords": ["halo extensions", "fil invisible", "extensions sans clip", "halo wire"],
        "benefits": ["sans dommage", "pose en 2 minutes", "amovible", "aucun engagement"]
    },
    "i-tip": {
        "name": "I-Tip Kératine",
        "keywords": ["i-tip", "kératine", "micro-anneaux", "extensions individuelles"],
        "benefits": ["longue durée", "très naturel", "mouvement naturel", "6 mois+"]
    },
    "ponytail": {
        "name": "Queue de Cheval",
        "keywords": ["ponytail", "queue de cheval", "postiche", "clip ponytail"],
        "benefits": ["volume instant", "pose 30 secondes", "événements spéciaux"]
    },
    "clip-in": {
        "name": "Extensions à Clips",
        "keywords": ["clip-in", "extensions clips", "rallonges à clips", "clip extensions"],
        "benefits": ["pose maison", "réutilisable", "sans engagement", "occasionnel"]
    }
}

# Couleurs avec noms SEO-friendly
COLOR_SEO_MAP = {
    "1": {"name": "Noir Foncé", "keywords": ["noir", "jet black", "noir de jais"]},
    "1b": {"name": "Noir Naturel", "keywords": ["noir naturel", "off black", "brun très foncé"]},
    "2": {"name": "Brun Foncé", "keywords": ["brun foncé", "espresso", "châtain foncé"]},
    "3": {"name": "Châtain Moyen", "keywords": ["châtain", "brun moyen", "marron"]},
    "6": {"name": "Châtain Clair", "keywords": ["châtain clair", "caramel", "brun doré"]},
    "6/24": {"name": "Balayage Caramel", "keywords": ["balayage", "ombré", "caramel doré"]},
    "18/22": {"name": "Blond Cendré", "keywords": ["blond cendré", "dirty blonde", "blond naturel"]},
    "60a": {"name": "Blond Platine", "keywords": ["platine", "blond polaire", "blanc doré"]},
    "613/18a": {"name": "Blond Glacé", "keywords": ["blond glacé", "ice blonde", "blond froid"]},
    "hps": {"name": "Blond Cendré Foncé", "keywords": ["cendré", "ash blonde", "blond gris"]},
    "pha": {"name": "Blond Perle", "keywords": ["perle", "pearl blonde", "blond nacré"]},
    "cb": {"name": "Ombré Miel", "keywords": ["ombré", "honey balayage", "miel"]},
    "db": {"name": "Brun Nuit", "keywords": ["brun nuit", "dark brown", "chocolat foncé"]},
    "dc": {"name": "Chocolat Profond", "keywords": ["chocolat", "dark chocolate", "brun riche"]},
    "cacao": {"name": "Cacao", "keywords": ["cacao", "brun chaud", "chocolat au lait"]},
    "cinnamon": {"name": "Cannelle", "keywords": ["cannelle", "auburn", "roux doux"]},
    "foochow": {"name": "Cachemire Oriental", "keywords": ["oriental", "brun chaud", "asiatique"]},
    "chengtu": {"name": "Soie d'Orient", "keywords": ["soie", "brun naturel", "asiatique"]},
    "5at60": {"name": "Aurore Glaciale", "keywords": ["ombré glacé", "roots", "balayage froid"]},
    "5atp18b62": {"name": "Aurore Boréale", "keywords": ["aurore", "multitonal", "balayage complexe"]},
}

# ==================== FONCTIONS DE GÉNÉRATION SEO ====================

def generate_seo_filename(
    product_type: str,
    color_code: str,
    length: str = None,
    geo_variation: int = 0
) -> str:
    """
    Génère un nom de fichier SEO-friendly pour une image.
    
    Exemple: luxura-extension-genius-blond-platine-quebec-20po.jpg
    
    Args:
        product_type: genius, tape, halo, etc.
        color_code: 1, 6, 60a, hps, etc.
        length: 16, 18, 20, 22, 24 (pouces)
        geo_variation: Index pour alterner les régions (0=Québec, 1=Beauce, etc.)
    """
    # Base: luxura + type de rallonge
    parts = ["luxura"]
    
    # Alterner entre "rallonge" et "extension"
    if geo_variation % 2 == 0:
        parts.append("rallonge")
    else:
        parts.append("extension")
    
    # Type de produit - version courte pour le filename
    type_short = {
        "genius": "genius",
        "tape": "tape",
        "halo": "halo",
        "i-tip": "itip",
        "ponytail": "ponytail",
        "clip-in": "clip-in"
    }
    parts.append(type_short.get(product_type, product_type))
    
    # Couleur
    color_info = COLOR_SEO_MAP.get(color_code.lower(), {})
    color_name = color_info.get("name", color_code).lower()
    # Normaliser les caractères spéciaux pour les URLs
    color_name = color_name.replace("é", "e").replace("è", "e").replace("ê", "e")
    color_name = color_name.replace("â", "a").replace("à", "a")
    color_name = color_name.replace("î", "i").replace("ï", "i")
    color_name = color_name.replace("ô", "o").replace("û", "u").replace("ù", "u")
    color_name = color_name.replace("ç", "c")
    color_name = re.sub(r'[^a-z0-9-]', '-', color_name)
    color_name = re.sub(r'-+', '-', color_name).strip('-')
    parts.append(color_name)
    
    # Région géographique (rotation)
    geo_index = geo_variation % len(GEO_KEYWORDS)
    geo = GEO_KEYWORDS[geo_index].lower()
    geo = geo.replace("é", "e").replace("è", "e").replace("-", "")
    geo = geo.replace("'", "").replace(" ", "-")
    parts.append(geo)
    
    # Longueur si disponible
    if length:
        parts.append(f"{length}po")
    
    # Assembler le nom de fichier
    filename = "-".join(parts)
    filename = re.sub(r'-+', '-', filename)  # Nettoyer les doubles tirets
    
    return f"{filename}.jpg"


def generate_seo_alt_text(
    product_type: str,
    color_code: str,
    length: str = None,
    geo_variation: int = 0
) -> str:
    """
    Génère un texte alternatif optimisé SEO pour une image.
    
    Exemple: "Extension Genius trame invisible blond platine 20 pouces - Luxura Distribution Québec"
    """
    type_info = PRODUCT_TYPES_SEO.get(product_type, {})
    type_name = type_info.get("name", product_type.title())
    keywords = type_info.get("keywords", [])
    
    color_info = COLOR_SEO_MAP.get(color_code.lower(), {})
    color_name = color_info.get("name", color_code)
    
    # Construire le texte alt
    parts = []
    
    # Type de rallonge avec variation
    if geo_variation % 2 == 0:
        parts.append(f"Rallonge {type_name}")
    else:
        parts.append(f"Extension {type_name}")
    
    # Ajouter un mot-clé technique
    if keywords:
        parts.append(keywords[geo_variation % len(keywords)])
    
    # Couleur
    parts.append(color_name)
    
    # Longueur
    if length:
        parts.append(f"{length} pouces")
    
    # Marque et région
    geo = GEO_KEYWORDS[geo_variation % len(GEO_KEYWORDS)]
    parts.append(f"- Luxura Distribution {geo}")
    
    return " ".join(parts)


def generate_seo_meta_description(
    product_type: str,
    color_code: str,
    price: float = None
) -> str:
    """
    Génère une méta-description SEO pour un produit Wix.
    
    Max 160 caractères, inclut: type, couleur, bénéfice, CTA, région
    """
    type_info = PRODUCT_TYPES_SEO.get(product_type, {})
    type_name = type_info.get("name", product_type.title())
    benefits = type_info.get("benefits", ["qualité professionnelle"])
    
    color_info = COLOR_SEO_MAP.get(color_code.lower(), {})
    color_name = color_info.get("name", color_code)
    
    # Premier bénéfice
    benefit = benefits[0] if benefits else "qualité professionnelle"
    
    # Template avec variations
    templates = [
        f"Rallonge {type_name} {color_name} - {benefit}. Cheveux 100% Remy. Livraison rapide au Québec. Luxura Distribution",
        f"Extension {type_name} {color_name} - {benefit}. Importateur direct au Québec. Luxura Distribution St-Georges",
        f"{type_name} {color_name} - {benefit}. Extensions professionnelles Luxura. Livraison Québec, Beauce, Lévis",
    ]
    
    # Choisir un template (peut être rotatif)
    desc = templates[0]
    
    # Tronquer à 160 caractères si nécessaire
    if len(desc) > 160:
        desc = desc[:157] + "..."
    
    return desc


def generate_product_seo_data(
    product_type: str,
    color_code: str,
    length: str = None,
    price: float = None,
    variation_index: int = 0
) -> Dict:
    """
    Génère toutes les données SEO pour un produit.
    
    Returns:
        {
            "filename": "luxura-rallonge-genius-blond-platine-quebec-20po.jpg",
            "alt_text": "Rallonge Genius trame invisible blond platine 20 pouces - Luxura Distribution Québec",
            "meta_description": "Rallonge Genius blond platine - aucune colle...",
            "title_tag": "Genius Blond Platine | Extensions Luxura Québec",
            "keywords": ["luxura", "rallonge", "genius", ...]
        }
    """
    type_info = PRODUCT_TYPES_SEO.get(product_type, {})
    type_name = type_info.get("name", product_type.title())
    type_keywords = type_info.get("keywords", [])
    
    color_info = COLOR_SEO_MAP.get(color_code.lower(), {})
    color_name = color_info.get("name", color_code)
    color_keywords = color_info.get("keywords", [])
    
    geo = GEO_KEYWORDS[variation_index % len(GEO_KEYWORDS)]
    
    # Générer les données
    return {
        "filename": generate_seo_filename(product_type, color_code, length, variation_index),
        "alt_text": generate_seo_alt_text(product_type, color_code, length, variation_index),
        "meta_description": generate_seo_meta_description(product_type, color_code, price),
        "title_tag": f"{type_name} {color_name} | Extensions Luxura {geo}",
        "keywords": [
            "luxura",
            "luxura distribution",
            "rallonge",
            "extension",
            "cheveux naturels",
            product_type,
            type_name.lower(),
            color_name.lower(),
            geo.lower(),
            *type_keywords[:2],
            *color_keywords[:2]
        ],
        "geo_region": geo
    }


# ==================== WIX API INTEGRATION ====================

WIX_API_KEY = os.getenv("WIX_API_KEY", "")
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "")
WIX_API_BASE = "https://www.wixapis.com"


async def get_wix_products() -> List[Dict]:
    """Récupère tous les produits du catalogue Wix"""
    headers = {
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json"
    }
    
    products = []
    cursor = None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            payload = {"query": {"paging": {"limit": 100}}}
            if cursor:
                payload["query"]["paging"]["cursor"] = cursor
            
            response = await client.post(
                f"{WIX_API_BASE}/stores/v1/products/query",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Erreur Wix API: {response.status_code} - {response.text}")
                break
            
            data = response.json()
            products.extend(data.get("products", []))
            
            # Pagination
            paging = data.get("metadata", {}).get("cursors", {})
            cursor = paging.get("next")
            if not cursor:
                break
    
    return products


async def update_product_seo(product_id: str, seo_data: Dict) -> bool:
    """Met à jour les métadonnées SEO d'un produit Wix"""
    headers = {
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json"
    }
    
    # Wix Stores API - Update product
    payload = {
        "product": {
            "seoData": {
                "tags": [
                    {"type": "title", "props": {"content": seo_data.get("title_tag", "")}},
                    {"type": "meta", "props": {"name": "description", "content": seo_data.get("meta_description", "")}},
                    {"type": "meta", "props": {"name": "keywords", "content": ", ".join(seo_data.get("keywords", []))}}
                ]
            }
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.patch(
            f"{WIX_API_BASE}/stores/v1/products/{product_id}",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            logger.info(f"✅ SEO mis à jour pour produit {product_id}")
            return True
        else:
            logger.error(f"❌ Erreur SEO pour {product_id}: {response.status_code}")
            return False


def extract_product_info_from_handle(handle: str) -> Tuple[str, str]:
    """
    Extrait le type de produit et le code couleur depuis un handle Wix.
    
    Ex: "genius-trame-invisible-vivian-blond-platine-60a" → ("genius", "60a")
    """
    handle_lower = handle.lower()
    
    # Détecter le type
    product_type = "essentiels"
    for ptype in PRODUCT_TYPES_SEO.keys():
        if ptype in handle_lower:
            product_type = ptype
            break
    
    # Détecter le code couleur (à la fin du handle généralement)
    color_code = ""
    for code in COLOR_SEO_MAP.keys():
        if handle_lower.endswith(f"-{code}") or f"-{code}-" in handle_lower:
            color_code = code
            break
    
    return product_type, color_code


async def batch_update_catalog_seo(dry_run: bool = True) -> Dict:
    """
    Met à jour le SEO de tout le catalogue Wix.
    
    Args:
        dry_run: Si True, simule sans modifier (pour prévisualiser)
    
    Returns:
        Rapport avec les changements effectués/proposés
    """
    logger.info("🔍 Récupération du catalogue Wix...")
    products = await get_wix_products()
    
    report = {
        "total_products": len(products),
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "dry_run": dry_run,
        "changes": []
    }
    
    for i, product in enumerate(products):
        product_id = product.get("id")
        name = product.get("name", "")
        handle = product.get("slug", "")
        
        # Extraire les infos du handle
        product_type, color_code = extract_product_info_from_handle(handle)
        
        if not color_code:
            report["skipped"] += 1
            continue
        
        # Générer les données SEO avec variation géographique
        seo_data = generate_product_seo_data(
            product_type=product_type,
            color_code=color_code,
            variation_index=i  # Rotation des régions
        )
        
        change = {
            "product_id": product_id,
            "name": name,
            "handle": handle,
            "seo_data": seo_data
        }
        report["changes"].append(change)
        
        if not dry_run:
            success = await update_product_seo(product_id, seo_data)
            if success:
                report["updated"] += 1
            else:
                report["errors"] += 1
            
            # Rate limiting
            await asyncio.sleep(0.5)
        else:
            report["updated"] += 1
    
    return report


# ==================== CLI / STANDALONE USAGE ====================

async def main():
    """Exécution standalone pour tests"""
    print("=" * 60)
    print("🔍 LUXURA SEO IMAGE OPTIMIZER")
    print("=" * 60)
    
    # Test de génération
    print("\n📝 Exemples de génération SEO:\n")
    
    test_cases = [
        ("genius", "60a", "20"),
        ("tape", "6/24", "18"),
        ("halo", "1b", "22"),
        ("i-tip", "hps", "24"),
    ]
    
    for i, (ptype, color, length) in enumerate(test_cases):
        seo = generate_product_seo_data(ptype, color, length, variation_index=i)
        print(f"Produit: {ptype.upper()} #{color}")
        print(f"  📁 Fichier: {seo['filename']}")
        print(f"  🏷️ Alt: {seo['alt_text']}")
        print(f"  📄 Meta: {seo['meta_description'][:80]}...")
        print(f"  🌍 Région: {seo['geo_region']}")
        print()
    
    # Test batch (dry run)
    print("\n🔄 Simulation batch update (dry run)...")
    if WIX_API_KEY:
        report = await batch_update_catalog_seo(dry_run=True)
        print(f"  Total produits: {report['total_products']}")
        print(f"  À mettre à jour: {report['updated']}")
        print(f"  Ignorés: {report['skipped']}")
        
        # Afficher quelques exemples
        if report['changes']:
            print("\n  Exemples de changements proposés:")
            for change in report['changes'][:3]:
                print(f"    - {change['name']}")
                print(f"      → {change['seo_data']['filename']}")
    else:
        print("  ⚠️ WIX_API_KEY non configurée - test en mode local uniquement")


if __name__ == "__main__":
    asyncio.run(main())
