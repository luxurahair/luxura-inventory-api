"""
WIX SEO PUSH SCRIPT V2 - Pour backend Render (luxura-inventory-api)
====================================================================
Ce script met à jour les produits Wix avec:
1. SKUs Luxura standardisés pour chaque variante
2. Descriptions HTML structurées avec sections SEO
3. Sections d'informations supplémentaires

INSTRUCTIONS DE DÉPLOIEMENT:
1. Copier ce fichier dans votre repo GitHub: app/routes/wix_seo_push.py
2. Remplacer le contenu existant
3. Push vers GitHub → Render redéploie automatiquement
4. Tester avec: GET /wix/seo/preview/{product_id}
5. Appliquer avec: POST /wix/seo/push/{product_id}
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.product import Product

router = APIRouter(prefix="/wix", tags=["wix-seo-push"])

WIX_API_BASE = "https://www.wixapis.com"
DEFAULT_PUBLIC_BASE = "https://luxura-inventory-api.onrender.com"


# ════════════════════════════════════════════════════════════════════════════════
# SYSTÈME DE COULEURS LUXURA - Source de vérité pour noms et SKUs
# ════════════════════════════════════════════════════════════════════════════════

COLOR_LUXURA_MAP = {
    # ═══════════ NOIRS ═══════════
    "1": {"luxe": "Onyx Noir", "sku": "ONYX-NOIR", "type": "SOLID", "category": "noir"},
    "1B": {"luxe": "Noir Soie", "sku": "NOIR-SOIE", "type": "SOLID", "category": "noir"},
    
    # ═══════════ BRUNS FONCÉS ═══════════
    "2": {"luxe": "Espresso Intense", "sku": "ESPRESSO", "type": "SOLID", "category": "brun"},
    "DB": {"luxe": "Nuit Mystère", "sku": "NUIT-MYSTERE", "type": "SOLID", "category": "brun"},
    "DC": {"luxe": "Chocolat Profond", "sku": "CHOCOLAT-PROFOND", "type": "SOLID", "category": "brun"},
    "CACAO": {"luxe": "Cacao Velours", "sku": "CACAO-VELOURS", "type": "SOLID", "category": "brun"},
    "CHENGTU": {"luxe": "Soie d'Orient", "sku": "SOIE-ORIENT", "type": "SOLID", "category": "brun"},
    "FOOCHOW": {"luxe": "Cachemire Oriental", "sku": "CACHEMIRE-ORIENTAL", "type": "SOLID", "category": "brun"},
    
    # ═══════════ CHÂTAIGNES ═══════════
    "3": {"luxe": "Châtaigne Naturelle", "sku": "CHATAIGNE", "type": "SOLID", "category": "chataigne"},
    "CINNAMON": {"luxe": "Cannelle Épicée", "sku": "CANNELLE", "type": "SOLID", "category": "chataigne"},
    "3/3T24": {"luxe": "Châtaigne Lumière", "sku": "CHATAIGNE-LUMIERE", "type": "OMBRE-PIANO", "category": "chataigne"},
    
    # ═══════════ CARAMELS ═══════════
    "6": {"luxe": "Caramel Doré", "sku": "CARAMEL-DORE", "type": "SOLID", "category": "caramel"},
    "BM": {"luxe": "Miel Sauvage", "sku": "MIEL-SAUVAGE", "type": "SOLID", "category": "caramel"},
    "6/24": {"luxe": "Golden Hour", "sku": "GOLDEN-HOUR", "type": "BALAYAGE", "category": "caramel"},
    "6/6T24": {"luxe": "Caramel Soleil", "sku": "CARAMEL-SOLEIL", "type": "OMBRE-PIANO", "category": "caramel"},
    
    # ═══════════ BLONDS ═══════════
    "18/22": {"luxe": "Champagne Doré", "sku": "CHAMPAGNE-DORE", "type": "PIANO", "category": "blond"},
    "60A": {"luxe": "Platine Pur", "sku": "PLATINE-PUR", "type": "SOLID", "category": "blond"},
    "PHA": {"luxe": "Cendré Céleste", "sku": "CENDRE-CELESTE", "type": "SOLID", "category": "blond"},
    "613/18A": {"luxe": "Diamant Glacé", "sku": "DIAMANT-GLACE", "type": "BALAYAGE", "category": "blond"},
    
    # ═══════════ BLANCS ═══════════
    "IVORY": {"luxe": "Ivoire Précieux", "sku": "IVOIRE", "type": "SOLID", "category": "blanc"},
    "ICW": {"luxe": "Cristal Polaire", "sku": "CRISTAL-POLAIRE", "type": "SOLID", "category": "blanc"},
    
    # ═══════════ OMBRÉS ═══════════
    "CB": {"luxe": "Miel Sauvage Ombré", "sku": "MIEL-OMBRE", "type": "OMBRE", "category": "ombre"},
    "HPS": {"luxe": "Cendré Étoilé", "sku": "CENDRE-ETOILE", "type": "OMBRE", "category": "ombre"},
    "5AT60": {"luxe": "Aurore Glaciale", "sku": "AURORE-GLACIALE", "type": "OMBRE", "category": "ombre"},
    "5ATP18B62": {"luxe": "Aurore Boréale", "sku": "AURORE-BOREALE", "type": "OMBRE", "category": "ombre"},
    "2BTP18/1006": {"luxe": "Espresso Lumière", "sku": "ESPRESSO-LUMIERE", "type": "OMBRE-PIANO", "category": "ombre"},
    "T14/P14/24": {"luxe": "Venise Dorée", "sku": "VENISE-DOREE", "type": "OMBRE-PIANO", "category": "ombre"},
}

# Mapping des types de produits
PRODUCT_TYPE_MAP = {
    "halo": {"prefix": "H", "name": "Halo", "series": "Everly"},
    "genius": {"prefix": "G", "name": "Genius", "series": "Vivian"},
    "tape": {"prefix": "T", "name": "Bande Adhésive", "series": "Aurora"},
    "i-tip": {"prefix": "I", "name": "I-Tip", "series": "Eleanor"},
    "essentiels": {"prefix": "E", "name": "Essentiels", "series": ""},
}


def get_color_info(color_code: str) -> Dict[str, str]:
    """Obtenir les informations de couleur depuis le code"""
    if not color_code:
        return {"luxe": "Inconnu", "sku": "UNKNOWN", "type": "SOLID", "category": "autre"}
    
    clean = color_code.strip().upper()
    
    # Recherche exacte
    if clean in COLOR_LUXURA_MAP:
        return COLOR_LUXURA_MAP[clean]
    
    # Recherche avec variantes de formatage
    for code, info in COLOR_LUXURA_MAP.items():
        if code.replace("/", "-") == clean.replace("/", "-"):
            return info
        if code.replace("/", "") == clean.replace("/", ""):
            return info
    
    # Fallback intelligent
    return {"luxe": f"Teinte {color_code}", "sku": clean.replace("/", "-"), "type": "SOLID", "category": "autre"}


def detect_product_type(handle: str, name: str) -> str:
    """Détecter le type de produit depuis le handle Wix"""
    handle_lower = (handle or "").lower()
    name_lower = (name or "").lower()
    
    if "halo" in handle_lower or "everly" in handle_lower:
        return "halo"
    elif "genius" in handle_lower or "vivian" in handle_lower or "trame" in handle_lower:
        return "genius"
    elif "bande" in handle_lower or "aurora" in handle_lower or "tape" in handle_lower:
        return "tape"
    elif "i-tip" in handle_lower or "itip" in handle_lower or "eleanor" in handle_lower:
        return "i-tip"
    else:
        return "essentiels"


def extract_color_code_from_handle(handle: str) -> str:
    """Extraire le code couleur depuis le handle Wix"""
    if not handle:
        return ""
    
    # Patterns communs dans les handles
    patterns = [
        r"-(\d+[ab]?)$",  # -1, -1b, -2
        r"-([a-z]{2,})$",  # -dc, -db, -bm, -pha
        r"-(\d+-\d+)$",  # -6-24, -18-22
        r"-(\d+[a-z]+\d+)$",  # -5at60, -5atp18b62
    ]
    
    handle_lower = handle.lower()
    
    for pattern in patterns:
        match = re.search(pattern, handle_lower)
        if match:
            return match.group(1).upper()
    
    return ""


def generate_variant_sku(product_type: str, color_code: str, length: str, weight: str) -> str:
    """
    Générer un SKU Luxura standardisé pour une variante
    Format: {Prefix}{Longueur}{Poids}-{CodeCouleur}-{NomSKU}
    Exemple: H16120-1-ONYX-NOIR
    """
    type_info = PRODUCT_TYPE_MAP.get(product_type, PRODUCT_TYPE_MAP["essentiels"])
    color_info = get_color_info(color_code)
    
    prefix = type_info["prefix"]
    sku_name = color_info["sku"]
    clean_code = color_code.replace("/", "-")
    
    # Nettoyer longueur et poids
    length_num = re.sub(r'[^0-9]', '', length or "")
    weight_num = re.sub(r'[^0-9]', '', weight or "")
    
    if length_num and weight_num:
        return f"{prefix}{length_num}{weight_num}-{clean_code}-{sku_name}"
    elif length_num:
        return f"{prefix}{length_num}-{clean_code}-{sku_name}"
    else:
        return f"{prefix}-{clean_code}-{sku_name}"


def generate_seo_description(product_type: str, color_code: str, series: str) -> str:
    """
    Générer une description SEO structurée en HTML pour Wix
    """
    type_info = PRODUCT_TYPE_MAP.get(product_type, PRODUCT_TYPE_MAP["halo"])
    color_info = get_color_info(color_code)
    
    product_name = type_info["name"]
    series_name = series or type_info["series"]
    luxe_name = color_info["luxe"]
    color_type = color_info["type"]
    
    # Descriptions spécifiques par type de produit
    descriptions = {
        "halo": {
            "intro": f"Extensions {product_name} - Volume instantané sans engagement par Luxura.",
            "concept": [
                "Fil invisible ajustable qui repose sur votre tête",
                "Aucune fixation permanente - 100% réversible",
                "Application en moins de 2 minutes",
                "Retrait instantané sans aide professionnelle"
            ],
            "application": "Auto-application - Aucune aide requise"
        },
        "genius": {
            "intro": f"Extensions {product_name} - Trame invisible ultra-plate par Luxura.",
            "concept": [
                "Trame invisible qui disparaît dans vos cheveux",
                "Technique cousue pour une tenue longue durée",
                "Volume spectaculaire sans épaisseur visible",
                "Confort optimal toute la journée"
            ],
            "application": "Application professionnelle recommandée - Résultat salon"
        },
        "tape": {
            "intro": f"Extensions {product_name} - Adhésif médical invisible par Luxura.",
            "concept": [
                "Bandes adhésives ultra-fines médicales",
                "Pose rapide en 30-45 minutes",
                "Repositionnables jusqu'à 3 fois",
                "Zéro tension sur le cuir chevelu"
            ],
            "application": "Application professionnelle ou autonome avec tutoriel"
        },
        "i-tip": {
            "intro": f"Extensions {product_name} - Micro-anneaux individuels par Luxura.",
            "concept": [
                "Mèches individuelles pour précision maximale",
                "Micro-anneaux sans chaleur ni colle",
                "Placement stratégique personnalisé",
                "Réutilisables avec remplacement d'anneaux"
            ],
            "application": "Application professionnelle requise"
        }
    }
    
    desc = descriptions.get(product_type, descriptions["halo"])
    
    # Construction HTML structurée
    html = f"""<h3>{desc['intro']}</h3>

<h4>🎯 CONCEPT UNIQUE</h4>
<ul>
{"".join(f"<li>{item}</li>" for item in desc['concept'])}
</ul>

<h4>💎 QUALITÉ PREMIUM</h4>
<ul>
<li>100% cheveux humains vierges Remy</li>
<li>Cuticules intactes pour un mouvement naturel</li>
<li>Série {series_name} - Collection polyvalente Luxura</li>
<li>Teinte: {luxe_name} #{color_code}</li>
</ul>

<h4>✨ AVANTAGES UNIQUES</h4>
<ul>
<li>Zéro dommage aux cheveux naturels</li>
<li>Parfait pour usage quotidien ou occasionnel</li>
<li>Idéal pour cheveux fins ou fragiles</li>
<li>Durée de vie: 12 mois et plus avec bon entretien</li>
</ul>

<h4>📍 APPLICATION</h4>
<p>{desc['application']}</p>

<p><strong>Luxura Distribution</strong> - Extensions professionnelles haut de gamme.</p>"""

    return html


def generate_additional_info_sections(product_type: str, color_code: str, variants: List[Dict]) -> List[Dict[str, str]]:
    """
    Générer les sections d'informations supplémentaires pour Wix
    """
    color_info = get_color_info(color_code)
    type_info = PRODUCT_TYPE_MAP.get(product_type, PRODUCT_TYPE_MAP["halo"])
    
    # Format des variantes pour la section "Format"
    format_text = ""
    if variants:
        format_parts = []
        for v in variants:
            length = v.get("length", "")
            weight = v.get("weight", "")
            if length and weight:
                format_parts.append(f"Longueur de {length} pouces - {weight} grammes")
        format_text = " | ".join(format_parts) if format_parts else "Contactez-nous pour les options disponibles"
    
    sections = [
        {
            "title": "Description",
            "description": f"Installation facile et rapide des extensions {type_info['name']}. Cheveux 100% humains Remy de qualité salon. Teinte {color_info['luxe']} - une couleur exclusive de la collection Luxura."
        },
        {
            "title": "À propos de nos extensions",
            "description": "Les extensions Luxura sont fabriquées avec des cheveux 100% humains vierges Remy. Cuticules alignées dans le même sens pour éviter les nœuds et garantir un mouvement naturel. Qualité professionnelle approuvée par les salons du Québec."
        },
        {
            "title": "Recommandation d'achat",
            "description": "1 paquet pour un ajout subtil de volume | 2 paquets pour un résultat complet | Consultez notre guide de quantité sur luxuradistribution.com"
        },
        {
            "title": "Format",
            "description": format_text or "Plusieurs longueurs et poids disponibles - voir options"
        },
        {
            "title": "Entretien recommandé",
            "description": "Un shampooing doux et hydratant fera que vos extensions dureront longtemps. Évitez les produits contenant des sulfates. Brossez délicatement avec une brosse à poils souples. Rangez dans un étui de protection entre les utilisations."
        },
        {
            "title": "Précommande",
            "description": "Nous acceptons les précommandes pour les teintes en rupture de stock. Vous serez avisé dès la réception. Délai habituel: 2-3 semaines."
        }
    ]
    
    return sections


# ════════════════════════════════════════════════════════════════════════════════
# HELPERS WIX API
# ════════════════════════════════════════════════════════════════════════════════

def _get_instance_id() -> str:
    instance_id = (os.getenv("WIX_INSTANCE_ID") or "").strip()
    if not instance_id:
        raise HTTPException(500, "Missing env: WIX_INSTANCE_ID")
    return instance_id


def _get_public_base_url() -> str:
    return (os.getenv("PUBLIC_BASE_URL") or DEFAULT_PUBLIC_BASE).strip().rstrip("/")


def _fetch_access_token(instance_id: str) -> str:
    """Obtenir un token d'accès via l'endpoint /wix/token"""
    base = _get_public_base_url()
    try:
        token_res = requests.post(
            f"{base}/wix/token",
            params={"instance_id": instance_id},
            timeout=30,
        )
    except requests.RequestException as e:
        raise HTTPException(502, f"Token fetch network error: {e}")

    if not token_res.ok:
        raise HTTPException(502, f"Token fetch failed: {token_res.status_code} {token_res.text}")

    try:
        data = token_res.json()
    except ValueError:
        raise HTTPException(502, f"Token fetch invalid JSON: {token_res.text[:500]}")

    access_token = (data.get("access_token") or "").strip()
    if not access_token:
        raise HTTPException(502, "No access_token returned by /wix/token")

    return access_token


def _load_product_or_404(product_id: int, db: Session) -> Product:
    prod = db.exec(select(Product).where(Product.id == product_id)).first()
    if not prod:
        raise HTTPException(404, "Product not found in local database")
    return prod


def _wix_get_product(wix_id: str, access_token: str) -> Dict[str, Any]:
    """GET un produit depuis l'API Wix"""
    try:
        r = requests.get(
            f"{WIX_API_BASE}/stores/v1/products/{wix_id}",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            timeout=30,
        )
    except requests.RequestException as e:
        raise HTTPException(502, f"Wix GET network error: {e}")

    if not r.ok:
        raise HTTPException(502, f"Wix get failed: {r.status_code} {r.text}")

    try:
        return r.json()
    except ValueError:
        raise HTTPException(502, f"Wix get invalid JSON: {r.text[:500]}")


def _wix_update_product(wix_id: str, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """PATCH un produit sur l'API Wix"""
    try:
        r = requests.patch(
            f"{WIX_API_BASE}/stores/v1/products/{wix_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=30,
        )
    except requests.RequestException as e:
        raise HTTPException(502, f"Wix PATCH network error: {e}")

    if not r.ok:
        raise HTTPException(502, f"Wix update failed: {r.status_code} {r.text}")

    try:
        return r.json()
    except ValueError:
        return {"raw": r.text}


def _wix_update_variant(wix_id: str, variant_id: str, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Mettre à jour une variante spécifique sur Wix"""
    try:
        r = requests.patch(
            f"{WIX_API_BASE}/stores/v1/products/{wix_id}/variants/{variant_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={"variant": payload},
            timeout=30,
        )
    except requests.RequestException as e:
        raise HTTPException(502, f"Wix variant PATCH error: {e}")

    if not r.ok:
        # Log mais ne pas échouer pour les variantes
        return {"error": r.status_code, "message": r.text[:200]}

    try:
        return r.json()
    except ValueError:
        return {"raw": r.text}


# ════════════════════════════════════════════════════════════════════════════════
# ENDPOINTS API
# ════════════════════════════════════════════════════════════════════════════════

@router.get("/seo/preview/{product_id}")
def preview_seo_update(product_id: int, db: Session = Depends(get_session)):
    """
    Prévisualiser les changements SEO pour un produit SANS les appliquer
    Retourne: description HTML, SKUs des variantes, sections d'infos
    """
    prod = _load_product_or_404(product_id, db)
    
    # Extraire les infos du produit
    handle = prod.handle or ""
    name = prod.name or ""
    
    product_type = detect_product_type(handle, name)
    color_code = extract_color_code_from_handle(handle)
    type_info = PRODUCT_TYPE_MAP.get(product_type, PRODUCT_TYPE_MAP["halo"])
    color_info = get_color_info(color_code)
    
    # Récupérer les variantes depuis les options
    options = prod.options if isinstance(prod.options, dict) else {}
    variants_data = options.get("variants", [])
    
    # Générer les nouveaux SKUs pour chaque variante
    variant_skus = []
    for v in variants_data:
        choices = v.get("choices", {})
        longeur = choices.get("Longeur", "")
        
        # Parser longueur et poids depuis "20" 140 grammes"
        match = re.match(r'(\d+)["\'\′]?\s*(\d+)\s*gram', longeur.lower())
        length = match.group(1) if match else ""
        weight = match.group(2) if match else ""
        
        new_sku = generate_variant_sku(product_type, color_code, length, weight)
        variant_skus.append({
            "variant_id": v.get("id"),
            "current_sku": v.get("sku", ""),
            "new_sku": new_sku,
            "choice": longeur
        })
    
    # Générer la description SEO
    seo_description = generate_seo_description(product_type, color_code, type_info["series"])
    
    # Générer les sections d'infos supplémentaires
    additional_sections = generate_additional_info_sections(product_type, color_code, variants_data)
    
    return {
        "product_id": prod.id,
        "wix_id": prod.wix_id,
        "handle": handle,
        "detected_type": product_type,
        "detected_color": color_code,
        "luxe_name": color_info["luxe"],
        "preview": {
            "description_html": seo_description,
            "variant_skus": variant_skus,
            "additional_info_sections": additional_sections
        }
    }


@router.post("/seo/push/{product_id}")
def push_seo_update(
    product_id: int, 
    update_description: bool = Query(True, description="Mettre à jour la description"),
    update_skus: bool = Query(True, description="Mettre à jour les SKUs des variantes"),
    update_sections: bool = Query(True, description="Mettre à jour les sections d'info"),
    db: Session = Depends(get_session)
):
    """
    Appliquer les mises à jour SEO sur Wix pour un produit
    
    Paramètres:
    - update_description: Mettre à jour la description HTML (défaut: True)
    - update_skus: Mettre à jour les SKUs des variantes (défaut: True)
    - update_sections: Mettre à jour les sections d'info supplémentaires (défaut: True)
    """
    prod = _load_product_or_404(product_id, db)
    
    wix_id = (prod.wix_id or "").strip()
    if not wix_id:
        raise HTTPException(400, "Product has no wix_id")
    
    # Authentification Wix
    instance_id = _get_instance_id()
    access_token = _fetch_access_token(instance_id)
    
    # Extraire les infos
    handle = prod.handle or ""
    name = prod.name or ""
    product_type = detect_product_type(handle, name)
    color_code = extract_color_code_from_handle(handle)
    type_info = PRODUCT_TYPE_MAP.get(product_type, PRODUCT_TYPE_MAP["halo"])
    color_info = get_color_info(color_code)
    
    results = {
        "product_id": prod.id,
        "wix_id": wix_id,
        "updates": {}
    }
    
    # 1. Mettre à jour la description
    if update_description:
        seo_description = generate_seo_description(product_type, color_code, type_info["series"])
        desc_result = _wix_update_product(wix_id, access_token, {"description": seo_description})
        results["updates"]["description"] = {"success": True, "response": desc_result}
    
    # 2. Mettre à jour les sections d'informations supplémentaires
    if update_sections:
        options = prod.options if isinstance(prod.options, dict) else {}
        variants_data = options.get("variants", [])
        additional_sections = generate_additional_info_sections(product_type, color_code, variants_data)
        
        # Format Wix pour additionalInfoSections
        wix_sections = [
            {"title": s["title"], "description": s["description"]}
            for s in additional_sections
        ]
        
        sections_result = _wix_update_product(wix_id, access_token, {"additionalInfoSections": wix_sections})
        results["updates"]["sections"] = {"success": True, "response": sections_result}
    
    # 3. Mettre à jour les SKUs des variantes
    if update_skus:
        options = prod.options if isinstance(prod.options, dict) else {}
        variants_data = options.get("variants", [])
        
        sku_results = []
        for v in variants_data:
            variant_id = v.get("id")
            if not variant_id:
                continue
            
            choices = v.get("choices", {})
            longeur = choices.get("Longeur", "")
            
            match = re.match(r'(\d+)["\'\′]?\s*(\d+)\s*gram', longeur.lower())
            length = match.group(1) if match else ""
            weight = match.group(2) if match else ""
            
            new_sku = generate_variant_sku(product_type, color_code, length, weight)
            
            # Mettre à jour la variante sur Wix
            variant_result = _wix_update_variant(wix_id, variant_id, access_token, {"sku": new_sku})
            sku_results.append({
                "variant_id": variant_id,
                "new_sku": new_sku,
                "result": variant_result
            })
        
        results["updates"]["variant_skus"] = sku_results
    
    return results


@router.post("/seo/push_batch")
def push_seo_batch(
    category: Optional[str] = Query(None, description="Filtrer par catégorie (halo, genius, tape, i-tip)"),
    limit: int = Query(10, description="Nombre max de produits à traiter"),
    dry_run: bool = Query(True, description="Prévisualisation uniquement"),
    db: Session = Depends(get_session)
):
    """
    Traitement par lot des mises à jour SEO
    
    - dry_run=True: Prévisualise uniquement (défaut)
    - dry_run=False: Applique les changements
    - category: Filtrer par type de produit
    - limit: Nombre max de produits (défaut: 10)
    """
    # Récupérer tous les produits
    query = select(Product)
    products = db.exec(query).all()
    
    results = {
        "dry_run": dry_run,
        "processed": [],
        "skipped": [],
        "errors": []
    }
    
    count = 0
    for prod in products:
        if count >= limit:
            break
        
        handle = prod.handle or ""
        name = prod.name or ""
        product_type = detect_product_type(handle, name)
        
        # Filtrer par catégorie si spécifié
        if category and product_type != category:
            continue
        
        # Vérifier qu'on a un wix_id
        if not prod.wix_id:
            results["skipped"].append({
                "id": prod.id,
                "name": name[:40],
                "reason": "No wix_id"
            })
            continue
        
        try:
            if dry_run:
                # Mode preview
                preview = preview_seo_update(prod.id, db)
                results["processed"].append({
                    "id": prod.id,
                    "name": name[:40],
                    "type": product_type,
                    "preview": preview["preview"]
                })
            else:
                # Mode push réel
                push_result = push_seo_update(prod.id, True, True, True, db)
                results["processed"].append({
                    "id": prod.id,
                    "name": name[:40],
                    "result": push_result
                })
            
            count += 1
            
        except Exception as e:
            results["errors"].append({
                "id": prod.id,
                "name": name[:40],
                "error": str(e)
            })
    
    results["summary"] = {
        "total_processed": len(results["processed"]),
        "total_skipped": len(results["skipped"]),
        "total_errors": len(results["errors"])
    }
    
    return results


@router.get("/seo/status")
def get_seo_status(db: Session = Depends(get_session)):
    """
    Obtenir le statut SEO de tous les produits
    """
    products = db.exec(select(Product)).all()
    
    status = {
        "total": len(products),
        "by_type": {},
        "missing_wix_id": 0,
        "ready_for_update": 0
    }
    
    for prod in products:
        handle = prod.handle or ""
        name = prod.name or ""
        product_type = detect_product_type(handle, name)
        
        if product_type not in status["by_type"]:
            status["by_type"][product_type] = 0
        status["by_type"][product_type] += 1
        
        if not prod.wix_id:
            status["missing_wix_id"] += 1
        else:
            status["ready_for_update"] += 1
    
    return status
