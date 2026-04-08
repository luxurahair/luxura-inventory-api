"""
Luxura Marketing - Routes API pour les templates de contenu
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

import sys
sys.path.insert(0, '/app/backend')

from services.content_templates import (
    get_all_templates,
    get_template_by_category,
    get_template_by_id,
    get_featured_products,
    get_extension_methods,
    generate_weekly_content_plan,
    generate_wix_methods_page,
    BRAND_POSITIONING,
    CONTENT_CATEGORIES,
    READY_TO_USE_POSTS
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketing/templates", tags=["Marketing Templates"])


@router.get("/")
async def list_all_templates():
    """
    Liste tous les templates de posts disponibles
    """
    templates = get_all_templates()
    return {
        "success": True,
        "count": len(templates),
        "categories": list(CONTENT_CATEGORIES.keys()),
        "templates": templates
    }


@router.get("/brand")
async def get_brand_info():
    """
    Retourne les informations de marque Luxura
    """
    return {
        "success": True,
        "brand": BRAND_POSITIONING,
        "categories": CONTENT_CATEGORIES
    }


@router.get("/category/{category}")
async def get_templates_by_category(category: str):
    """
    Retourne les templates d'une catégorie spécifique
    
    Categories:
    - product: Posts produits
    - educational: Contenu éducatif
    - b2b_salon: Recrutement salons
    - promo: Promotions
    - local_trust: Confiance locale
    """
    if category not in CONTENT_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Catégorie invalide. Valides: {list(CONTENT_CATEGORIES.keys())}"
        )
    
    templates = get_template_by_category(category)
    return {
        "success": True,
        "category": category,
        "info": CONTENT_CATEGORIES[category],
        "count": len(templates),
        "templates": templates
    }


@router.get("/template/{template_id}")
async def get_single_template(template_id: str):
    """
    Retourne un template spécifique par son ID
    """
    template = get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    return {
        "success": True,
        "template": template
    }


@router.get("/weekly-plan")
async def get_weekly_content_plan(
    start_date: Optional[str] = Query(None, description="Date de début YYYY-MM-DD")
):
    """
    Génère un plan de contenu pour les 7 prochains jours avec 10 posts
    
    Mix optimal:
    - 3 posts produits
    - 3 posts éducatifs  
    - 2 posts B2B/local
    - 2 posts promos
    """
    try:
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start = datetime.now()
        
        plan = generate_weekly_content_plan(start)
        
        return {
            "success": True,
            "start_date": start.strftime("%Y-%m-%d"),
            "post_count": len(plan),
            "plan": plan
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Format de date invalide: {e}")


@router.get("/products")
async def list_featured_products():
    """
    Retourne la liste des produits vedettes Luxura
    """
    products = get_featured_products()
    return {
        "success": True,
        "count": len(products),
        "products": products
    }


@router.get("/methods")
async def list_extension_methods():
    """
    Retourne les 6 méthodes d'extensions avec leurs détails
    (Pour affichage dans l'app ou sur le site)
    """
    methods = get_extension_methods()
    return {
        "success": True,
        "count": len(methods),
        "methods": methods
    }


@router.get("/wix-page")
async def get_wix_methods_page():
    """
    Génère le contenu Markdown pour la page 'Nos méthodes d'extensions' sur Wix
    Copier-coller directement dans l'éditeur Wix
    """
    content = generate_wix_methods_page()
    return {
        "success": True,
        "format": "markdown",
        "instructions": "Copiez ce contenu dans l'éditeur Wix (ajoutez un bloc Texte Riche)",
        "content": content
    }


@router.get("/ready-captions")
async def get_ready_captions(limit: int = 10):
    """
    Retourne les légendes prêtes à copier-coller
    Idéal pour l'app mobile
    """
    captions = []
    for template in READY_TO_USE_POSTS[:limit]:
        # Remplacer les variables dynamiques
        caption = template["caption"]
        if "{end_date}" in caption:
            from datetime import timedelta
            end_date = datetime.now() + timedelta(days=7)
            caption = caption.replace("{end_date}", end_date.strftime("%d %B"))
        
        captions.append({
            "id": template["id"],
            "category": template["category"],
            "title": template["title"],
            "caption": caption,
            "photo_suggestion": template["photo_suggestion"],
            "hashtags": template["hashtags"]
        })
    
    return {
        "success": True,
        "count": len(captions),
        "captions": captions
    }
