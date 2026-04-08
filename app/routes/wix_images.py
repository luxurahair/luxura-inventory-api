"""
Luxura Wix Image ALT Text Updater
Met à jour automatiquement les textes ALT de toutes les images produits sur Wix
pour améliorer le SEO.

Endpoints:
- GET /wix/images/list - Liste toutes les images avec leurs ALT actuels
- POST /wix/images/generate-alts - Génère les ALT optimisés pour SEO
- POST /wix/images/update-alts - Met à jour les ALT sur Wix
"""

import os
import logging
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wix/images", tags=["Wix Images SEO"])

WIX_API_BASE = "https://www.wixapis.com"

# ============ MODELS ============

class ImageAltUpdate(BaseModel):
    product_id: str
    image_url: str
    current_alt: Optional[str] = None
    new_alt: str

class BulkAltUpdateRequest(BaseModel):
    updates: List[ImageAltUpdate]

# ============ HELPERS ============

def get_wix_access_token() -> str:
    """Get Wix access token using the centralized token manager"""
    from app.routes.wix_token import get_wix_access_token as get_token
    return get_token()


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


def generate_seo_alt(product_name: str, product_type: str = "", color: str = "", length: str = "") -> str:
    """
    Génère un texte ALT optimisé pour le SEO
    
    Format: [Type] [Nom] [Couleur] [Longueur] - Luxura Distribution Québec
    """
    parts = []
    
    # Type de produit
    if product_type:
        parts.append(product_type)
    
    # Nom du produit
    if product_name:
        # Nettoyer le nom
        clean_name = product_name.replace("Luxura", "").strip()
        parts.append(clean_name)
    
    # Couleur
    if color:
        parts.append(f"couleur {color}")
    
    # Longueur
    if length:
        parts.append(f"{length} pouces")
    
    # Assembler
    alt_text = " ".join(parts)
    
    # Ajouter le branding
    alt_text += " - Extensions capillaires Luxura Distribution Québec"
    
    return alt_text[:125]  # Max 125 caractères pour SEO optimal


def extract_product_details(product: Dict) -> Dict:
    """Extrait les détails d'un produit Wix pour générer l'ALT"""
    name = product.get("name", "")
    product_type = ""
    color = ""
    length = ""
    
    # Détecter le type de produit
    name_lower = name.lower()
    if "genius weft" in name_lower:
        product_type = "Genius Weft"
    elif "tape" in name_lower or "bande" in name_lower:
        product_type = "Extensions Bandes Adhésives"
    elif "i-tip" in name_lower or "itip" in name_lower:
        product_type = "Extensions I-Tips Kératine"
    elif "halo" in name_lower:
        product_type = "Halo Extensions"
    elif "micro" in name_lower:
        product_type = "Extensions Micro Billes"
    elif "clip" in name_lower:
        product_type = "Extensions à Clips"
    else:
        product_type = "Extensions Capillaires"
    
    # Extraire les options (couleur, longueur)
    options = product.get("productOptions", [])
    for opt in options:
        opt_name = opt.get("name", "").lower()
        choices = opt.get("choices", [])
        if choices:
            first_choice = choices[0].get("description", "")
            if "couleur" in opt_name or "color" in opt_name:
                color = first_choice
            elif "longueur" in opt_name or "length" in opt_name or "pouce" in opt_name:
                length = first_choice
    
    return {
        "name": name,
        "type": product_type,
        "color": color,
        "length": length
    }


# ============ ENDPOINTS ============

@router.get("/status")
async def images_status():
    """Check Wix images service status"""
    try:
        token = get_wix_access_token()
        return {
            "status": "ok",
            "wix_connected": bool(token),
            "service": "Luxura Wix Images SEO"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/list")
async def list_all_images():
    """
    Liste toutes les images de tous les produits avec leurs ALT actuels
    """
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
        for item in items:
            if item.get("mediaType") == "IMAGE":
                image_info = item.get("image", {})
                images_data.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "image_url": image_info.get("url", ""),
                    "current_alt": image_info.get("altText", ""),
                    "is_main": False
                })
    
    # Stats
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


@router.post("/generate-alts")
async def generate_alt_texts():
    """
    Génère des textes ALT optimisés pour SEO pour tous les produits
    """
    token = get_wix_access_token()
    products = get_all_wix_products(token)
    
    generated_alts = []
    
    for product in products:
        product_id = product.get("id", "")
        details = extract_product_details(product)
        
        # Générer l'ALT
        new_alt = generate_seo_alt(
            product_name=details["name"],
            product_type=details["type"],
            color=details["color"],
            length=details["length"]
        )
        
        media = product.get("media", {})
        main_media = media.get("mainMedia", {})
        items = media.get("items", [])
        
        # Pour l'image principale
        if main_media:
            image_info = main_media.get("image", {})
            current_alt = image_info.get("altText", "")
            
            generated_alts.append({
                "product_id": product_id,
                "product_name": details["name"],
                "image_url": image_info.get("url", ""),
                "current_alt": current_alt,
                "new_alt": new_alt,
                "needs_update": current_alt != new_alt
            })
        
        # Pour les autres images (ajouter un index)
        for idx, item in enumerate(items):
            if item.get("mediaType") == "IMAGE":
                image_info = item.get("image", {})
                current_alt = image_info.get("altText", "")
                
                # Ajouter un index pour différencier
                indexed_alt = f"{new_alt} - Vue {idx + 2}"
                
                generated_alts.append({
                    "product_id": product_id,
                    "product_name": details["name"],
                    "image_url": image_info.get("url", ""),
                    "current_alt": current_alt,
                    "new_alt": indexed_alt,
                    "needs_update": current_alt != indexed_alt
                })
    
    needs_update = [alt for alt in generated_alts if alt.get("needs_update")]
    
    return {
        "success": True,
        "total_images": len(generated_alts),
        "needs_update": len(needs_update),
        "already_optimized": len(generated_alts) - len(needs_update),
        "preview": needs_update[:10],  # Preview first 10
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
        details = extract_product_details(product)
        
        # Générer l'ALT
        new_alt = generate_seo_alt(
            product_name=details["name"],
            product_type=details["type"],
            color=details["color"],
            length=details["length"]
        )
        
        media = product.get("media", {})
        current_alt = media.get("mainMedia", {}).get("image", {}).get("altText", "")
        
        if current_alt == new_alt:
            results["skipped"].append({
                "product_id": product_id,
                "name": details["name"],
                "reason": "ALT already optimized"
            })
            continue
        
        if dry_run:
            results["updated"].append({
                "product_id": product_id,
                "name": details["name"],
                "old_alt": current_alt,
                "new_alt": new_alt,
                "status": "would_update"
            })
        else:
            # Mettre à jour via l'API Wix
            try:
                # Note: Wix API pour mettre à jour les images nécessite
                # une structure spécifique. Voici un exemple:
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
                        "name": details["name"],
                        "old_alt": current_alt,
                        "new_alt": new_alt,
                        "status": "updated"
                    })
                else:
                    results["failed"].append({
                        "product_id": product_id,
                        "name": details["name"],
                        "error": update_response.text[:200]
                    })
                    
            except Exception as e:
                results["failed"].append({
                    "product_id": product_id,
                    "name": details["name"],
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
async def update_single_image_alt(
    product_id: str,
    new_alt: str
):
    """
    Met à jour l'ALT d'une image spécifique
    """
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
