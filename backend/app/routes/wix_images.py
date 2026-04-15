"""
Luxura Wix Image ALT Text Updater - SEO OPTIMISÉ QUÉBEC
Génère des textes ALT ultra-ciblés pour le référencement local
"""

import os
import re
import logging
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wix/images", tags=["Wix Images SEO"])

WIX_API_BASE = "https://www.wixapis.com"

# ============ SEO KEYWORDS DATABASE ============

# Mots-clés SEO ciblés par type de produit
SEO_KEYWORDS = {
    "ponytail": {
        "type_fr": "Queue de cheval extensions",
        "keywords": ["ponytail naturel", "queue de cheval clip", "rallonge ponytail"],
        "intent": "acheter"
    },
    "tape": {
        "type_fr": "Extensions bandes adhésives Tape-In",
        "keywords": ["tape in extensions", "bandes adhésives cheveux", "extensions tape"],
        "intent": "achat"
    },
    "genius": {
        "type_fr": "Genius Weft trame invisible",
        "keywords": ["genius weft", "trame invisible", "weft extensions"],
        "intent": "commander"
    },
    "itip": {
        "type_fr": "Extensions I-Tip kératine",
        "keywords": ["i-tip extensions", "extensions kératine", "tip extensions"],
        "intent": "acheter"
    },
    "halo": {
        "type_fr": "Halo fil invisible",
        "keywords": ["halo extensions", "fil invisible", "extensions sans clip"],
        "intent": "achat"
    },
    "clip": {
        "type_fr": "Extensions à clips",
        "keywords": ["clip in extensions", "extensions clips", "rajouts clips"],
        "intent": "acheter"
    },
    "micro": {
        "type_fr": "Extensions micro-anneaux",
        "keywords": ["micro ring", "micro billes", "extensions anneaux"],
        "intent": "achat"
    },
    "weft": {
        "type_fr": "Trame cousue extensions",
        "keywords": ["weft extensions", "trame cheveux", "extensions cousues"],
        "intent": "commander"
    },
    "default": {
        "type_fr": "Extensions cheveux naturels",
        "keywords": ["extensions cheveux", "rallonges capillaires", "cheveux naturels"],
        "intent": "acheter"
    }
}

# Couleurs SEO mapping
COLOR_SEO = {
    "noir": "noir naturel",
    "brun": "brun chocolat",
    "châtain": "châtain naturel",
    "blond": "blond naturel",
    "caramel": "caramel doré",
    "miel": "miel ambré",
    "platine": "blond platine",
    "cendré": "blond cendré",
    "ombré": "ombré naturel",
    "balayage": "balayage californien",
    "roux": "roux cuivré",
    "auburn": "auburn naturel",
    "doré": "reflets dorés",
}

# Localisations SEO Québec
LOCATIONS_SEO = [
    "Québec",
    "Montréal", 
    "Laval",
    "Gatineau",
    "Sherbrooke",
    "Trois-Rivières",
    "St-Georges",
]

# ============ MODELS ============

class ImageAltUpdate(BaseModel):
    product_id: str
    image_url: str
    current_alt: Optional[str] = None
    new_alt: str

# ============ HELPER FUNCTIONS ============

def get_wix_access_token() -> str:
    """Get Wix access token using the centralized token manager"""
    from app.routes.wix_token import get_wix_access_token as get_token
    return get_token()


def detect_product_type(name: str) -> Dict:
    """Détecte le type de produit et retourne les infos SEO"""
    name_lower = name.lower()
    
    if "ponytail" in name_lower or "queue" in name_lower:
        return SEO_KEYWORDS["ponytail"]
    elif "tape" in name_lower or "bande" in name_lower or "aurora" in name_lower:
        return SEO_KEYWORDS["tape"]
    elif "genius" in name_lower:
        return SEO_KEYWORDS["genius"]
    elif "i-tip" in name_lower or "itip" in name_lower or "tip" in name_lower:
        return SEO_KEYWORDS["itip"]
    elif "halo" in name_lower:
        return SEO_KEYWORDS["halo"]
    elif "clip" in name_lower:
        return SEO_KEYWORDS["clip"]
    elif "micro" in name_lower or "bille" in name_lower or "anneau" in name_lower:
        return SEO_KEYWORDS["micro"]
    elif "weft" in name_lower or "trame" in name_lower:
        return SEO_KEYWORDS["weft"]
    else:
        return SEO_KEYWORDS["default"]


def extract_color_from_name(name: str) -> str:
    """Extrait et optimise la couleur pour le SEO"""
    name_lower = name.lower()
    
    for color_key, color_seo in COLOR_SEO.items():
        if color_key in name_lower:
            return color_seo
    
    # Chercher le code couleur (#xx ou #xxx)
    color_match = re.search(r'#([A-Za-z0-9/]+)', name)
    if color_match:
        return f"couleur {color_match.group(1)}"
    
    return ""


def extract_length_from_name(name: str) -> str:
    """Extrait la longueur du nom du produit"""
    # Chercher des patterns comme "18 pouces", "22po", "24""
    length_match = re.search(r'(\d{2})\s*(pouces?|po|"|inches?)?', name.lower())
    if length_match:
        return f"{length_match.group(1)} pouces"
    return ""


def generate_seo_alt_v2(product_name: str, image_index: int = 0) -> str:
    """
    Génère un ALT text ultra-optimisé pour le SEO Québec
    
    Format: [Intent] [Type produit] [Nom] [Couleur] - [Keyword] [Localisation]
    
    Exemples:
    - "Acheter Queue de cheval extensions Victoria Châtaigne - ponytail naturel Québec"
    - "Extensions bandes adhésives Tape-In Aurora blonde - tape in extensions Montréal"
    """
    
    # Détecter le type de produit
    product_info = detect_product_type(product_name)
    
    # Extraire la couleur
    color = extract_color_from_name(product_name)
    
    # Extraire la longueur
    length = extract_length_from_name(product_name)
    
    # Nettoyer le nom du produit
    clean_name = product_name
    clean_name = re.sub(r'#[A-Za-z0-9/]+', '', clean_name)  # Retirer code couleur
    clean_name = re.sub(r'\d{2}\s*(pouces?|po|")?', '', clean_name)  # Retirer longueur
    clean_name = clean_name.replace("Luxura", "").strip()
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()  # Normaliser espaces
    
    # Choisir une localisation (alterner pour diversifier)
    location = LOCATIONS_SEO[hash(product_name) % len(LOCATIONS_SEO)]
    
    # Choisir un keyword secondaire
    keyword = product_info["keywords"][hash(product_name) % len(product_info["keywords"])]
    
    # Construire l'ALT
    parts = []
    
    # Intent (pour images principales)
    if image_index == 0:
        parts.append(product_info["intent"].capitalize())
    
    # Type de produit
    parts.append(product_info["type_fr"])
    
    # Nom nettoyé
    if clean_name and len(clean_name) > 3:
        parts.append(clean_name)
    
    # Couleur
    if color:
        parts.append(color)
    
    # Longueur
    if length:
        parts.append(length)
    
    # Assembler la première partie
    alt_text = " ".join(parts)
    
    # Ajouter keyword et localisation
    alt_text += f" - {keyword} {location}"
    
    # Limiter à 125 caractères pour SEO optimal
    if len(alt_text) > 125:
        # Raccourcir en gardant les éléments essentiels
        alt_text = f"{product_info['intent'].capitalize()} {product_info['type_fr']} {color} - {keyword} {location}"
    
    return alt_text[:125]


def get_all_wix_products(access_token: str) -> List[Dict]:
    """Fetch all products from Wix store"""
    products = []
    offset = 0
    limit = 100
    
    while True:
        try:
            response = requests.post(
                f"{WIX_API_BASE}/stores/v1/products/query",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": {
                        "paging": {"limit": limit, "offset": offset}
                    }
                },
                timeout=30
            )
            
            if not response.ok:
                logger.error(f"Wix API error: {response.status_code} {response.text}")
                break
            
            data = response.json()
            batch = data.get("products", [])
            products.extend(batch)
            
            if len(batch) < limit:
                break
            
            offset += limit
            
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            break
    
    return products


# ============ ENDPOINTS ============

@router.get("/status")
async def images_status():
    """Check Wix images service status"""
    try:
        token = get_wix_access_token()
        return {
            "status": "ok",
            "wix_connected": bool(token),
            "service": "Luxura Wix Images SEO v2"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/list")
async def list_all_images():
    """Liste toutes les images de tous les produits avec leurs ALT actuels"""
    token = get_wix_access_token()
    products = get_all_wix_products(token)
    
    images_data = []
    
    for product in products:
        product_id = product.get("id", "")
        product_name = product.get("name", "")
        media = product.get("media", {})
        main_media = media.get("mainMedia", {})
        items = media.get("items", [])
        
        # Image principale
        if main_media:
            image_info = main_media.get("image", {})
            images_data.append({
                "product_id": product_id,
                "product_name": product_name,
                "image_url": image_info.get("url", ""),
                "current_alt": image_info.get("altText", ""),
                "is_main": True
            })
        
        # Autres images
        for idx, item in enumerate(items):
            if item.get("mediaType") == "IMAGE":
                image_info = item.get("image", {})
                images_data.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "image_url": image_info.get("url", ""),
                    "current_alt": image_info.get("altText", ""),
                    "is_main": False
                })
    
    total_images = len(images_data)
    images_without_alt = len([img for img in images_data if not img.get("current_alt")])
    
    return {
        "success": True,
        "total_products": len(products),
        "total_images": total_images,
        "images_without_alt": images_without_alt,
        "images_with_alt": total_images - images_without_alt,
        "seo_score": f"{((total_images - images_without_alt) / total_images * 100) if total_images > 0 else 0:.1f}%",
        "images": images_data
    }


@router.get("/seo-keywords")
async def get_seo_keywords():
    """Retourne les mots-clés SEO utilisés pour la génération d'ALT"""
    return {
        "product_types": SEO_KEYWORDS,
        "colors": COLOR_SEO,
        "locations": LOCATIONS_SEO
    }


@router.post("/generate-alts")
async def generate_alt_texts():
    """Génère des textes ALT ultra-optimisés pour SEO"""
    token = get_wix_access_token()
    products = get_all_wix_products(token)
    
    generated_alts = []
    
    for product in products:
        product_id = product.get("id", "")
        product_name = product.get("name", "")
        media = product.get("media", {})
        main_media = media.get("mainMedia", {})
        items = media.get("items", [])
        
        # Image principale
        if main_media:
            image_info = main_media.get("image", {})
            current_alt = image_info.get("altText", "")
            new_alt = generate_seo_alt_v2(product_name, image_index=0)
            
            generated_alts.append({
                "product_id": product_id,
                "product_name": product_name,
                "image_url": image_info.get("url", ""),
                "current_alt": current_alt,
                "new_alt": new_alt,
                "needs_update": current_alt != new_alt,
                "seo_analysis": {
                    "product_type": detect_product_type(product_name)["type_fr"],
                    "color_detected": extract_color_from_name(product_name),
                    "length_detected": extract_length_from_name(product_name)
                }
            })
        
        # Images secondaires
        for idx, item in enumerate(items):
            if item.get("mediaType") == "IMAGE":
                image_info = item.get("image", {})
                current_alt = image_info.get("altText", "")
                new_alt = generate_seo_alt_v2(product_name, image_index=idx+1) + f" vue {idx+2}"
                
                generated_alts.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "image_url": image_info.get("url", ""),
                    "current_alt": current_alt,
                    "new_alt": new_alt,
                    "needs_update": current_alt != new_alt
                })
    
    needs_update = [alt for alt in generated_alts if alt.get("needs_update")]
    
    return {
        "success": True,
        "total_images": len(generated_alts),
        "needs_update": len(needs_update),
        "already_optimized": len(generated_alts) - len(needs_update),
        "seo_strategy": {
            "format": "[Intent] [Type produit] [Nom] [Couleur] [Longueur] - [Keyword SEO] [Localisation Québec]",
            "example": "Acheter Queue de cheval extensions Victoria châtain naturel - ponytail naturel Québec",
            "locations_used": LOCATIONS_SEO,
            "max_length": "125 caractères"
        },
        "preview": needs_update[:10],
        "all_updates": needs_update
    }


@router.post("/update-alts")
async def update_all_alt_texts(dry_run: bool = True):
    """
    Met à jour les textes ALT de toutes les images sur Wix
    
    Parameters:
    - dry_run: Si True, ne fait que prévisualiser (défaut: True)
    """
    token = get_wix_access_token()
    products = get_all_wix_products(token)
    
    results = {
        "success": True,
        "dry_run": dry_run,
        "updated": [],
        "failed": [],
        "skipped": []
    }
    
    for product in products:
        product_id = product.get("id", "")
        product_name = product.get("name", "")
        
        # Générer le nouvel ALT
        new_alt = generate_seo_alt_v2(product_name, image_index=0)
        
        media = product.get("media", {})
        current_alt = media.get("mainMedia", {}).get("image", {}).get("altText", "")
        
        if current_alt == new_alt:
            results["skipped"].append({
                "product_id": product_id,
                "name": product_name,
                "reason": "ALT already optimized"
            })
            continue
        
        if dry_run:
            results["updated"].append({
                "product_id": product_id,
                "name": product_name,
                "old_alt": current_alt,
                "new_alt": new_alt,
                "status": "would_update"
            })
        else:
            # Mettre à jour via l'API Wix
            try:
                update_response = requests.patch(
                    f"{WIX_API_BASE}/stores/v1/products/{product_id}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "product": {
                            "media": {
                                "mainMedia": {
                                    "image": {
                                        "altText": new_alt
                                    }
                                }
                            }
                        }
                    },
                    timeout=30
                )
                
                if update_response.ok:
                    results["updated"].append({
                        "product_id": product_id,
                        "name": product_name,
                        "old_alt": current_alt,
                        "new_alt": new_alt,
                        "status": "updated"
                    })
                else:
                    results["failed"].append({
                        "product_id": product_id,
                        "name": product_name,
                        "error": update_response.text[:200]
                    })
                    
            except Exception as e:
                results["failed"].append({
                    "product_id": product_id,
                    "name": product_name,
                    "error": str(e)
                })
    
    results["summary"] = {
        "total_products": len(products),
        "updated": len(results["updated"]),
        "failed": len(results["failed"]),
        "skipped": len(results["skipped"])
    }
    
    return results


@router.post("/update-single")
async def update_single_image_alt(product_id: str, new_alt: str):
    """Met à jour l'ALT d'une image spécifique"""
    token = get_wix_access_token()
    
    try:
        response = requests.patch(
            f"{WIX_API_BASE}/stores/v1/products/{product_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "product": {
                    "media": {
                        "mainMedia": {
                            "image": {
                                "altText": new_alt
                            }
                        }
                    }
                }
            },
            timeout=30
        )
        
        if response.ok:
            return {
                "success": True,
                "product_id": product_id,
                "new_alt": new_alt,
                "message": "ALT text updated successfully"
            }
        else:
            raise HTTPException(500, f"Wix API error: {response.text[:200]}")
            
    except Exception as e:
        raise HTTPException(500, f"Update failed: {str(e)}")


@router.get("/preview/{product_id}")
async def preview_single_alt(product_id: str):
    """Prévisualise l'ALT qui serait généré pour un produit spécifique"""
    token = get_wix_access_token()
    
    try:
        response = requests.get(
            f"{WIX_API_BASE}/stores/v1/products/{product_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if not response.ok:
            raise HTTPException(404, "Product not found")
        
        product = response.json().get("product", {})
        product_name = product.get("name", "")
        
        new_alt = generate_seo_alt_v2(product_name)
        
        return {
            "product_id": product_id,
            "product_name": product_name,
            "generated_alt": new_alt,
            "analysis": {
                "product_type": detect_product_type(product_name)["type_fr"],
                "color": extract_color_from_name(product_name),
                "length": extract_length_from_name(product_name),
                "keywords": detect_product_type(product_name)["keywords"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
