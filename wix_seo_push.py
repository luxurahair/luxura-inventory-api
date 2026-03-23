"""
WIX SEO PUSH - Script complet pour mettre à jour les produits Wix
À copier dans: luxura-inventory-api/app/routes/wix_seo_push.py
"""

import os
import re
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

router = APIRouter(prefix="/wix/seo", tags=["Wix SEO Push"])

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")
WIX_ACCOUNT_ID = os.getenv("WIX_ACCOUNT_ID")
ADMIN_SECRET = os.getenv("SEO_ADMIN_SECRET", "luxura-seo-2024")

WIX_BASE_URL = "https://www.wixapis.com/stores/v1"

# ═══════════════════════════════════════════════════════════════
# MAPPING COULEURS LUXURA
# ═══════════════════════════════════════════════════════════════

COLOR_MAPPING = {
    "1": {"luxe": "Onyx Noir", "sku": "ONYX-NOIR"},
    "1B": {"luxe": "Noir Soie", "sku": "NOIR-SOIE"},
    "2": {"luxe": "Espresso Intense", "sku": "ESPRESSO-INTENSE"},
    "3": {"luxe": "Châtaigne Douce", "sku": "CHATAIGNE-DOUCE"},
    "6": {"luxe": "Caramel Doré", "sku": "CARAMEL-DORE"},
    "6/24": {"luxe": "Golden Hour", "sku": "GOLDEN-HOUR"},
    "6/6T24": {"luxe": "Caramel Soleil", "sku": "CARAMEL-SOLEIL"},
    "18/22": {"luxe": "Champagne Doré", "sku": "CHAMPAGNE-DORE"},
    "60A": {"luxe": "Platine Pur", "sku": "PLATINE-PUR"},
    "HPS": {"luxe": "Cendré Étoilé", "sku": "CENDRE-ETOILE"},
    "CB": {"luxe": "Miel Sauvage Ombré", "sku": "MIEL-SAUVAGE-OMBRE"},
    "DB": {"luxe": "Nuit Mystère", "sku": "NUIT-MYSTERE"},
    "DC": {"luxe": "Chocolat Profond", "sku": "CHOCOLAT-PROFOND"},
    "PHA": {"luxe": "Cendré Céleste", "sku": "CENDRE-CELESTE"},
    "613/18A": {"luxe": "Diamant Glacé", "sku": "DIAMANT-GLACE"},
    "CACAO": {"luxe": "Cacao Velours", "sku": "CACAO-VELOURS"},
    "CHENGTU": {"luxe": "Soie d'Orient", "sku": "SOIE-ORIENT"},
    "FOOCHOW": {"luxe": "Cachemire Oriental", "sku": "CACHEMIRE-ORIENTAL"},
    "CINNAMON": {"luxe": "Cannelle Épicée", "sku": "CANNELLE-EPICEE"},
    "IVORY": {"luxe": "Ivoire Précieux", "sku": "IVOIRE-PRECIEUX"},
    "ICW": {"luxe": "Cristal Polaire", "sku": "CRISTAL-POLAIRE"},
    "5AT60": {"luxe": "Aurore Glaciale", "sku": "AURORE-GLACIALE"},
    "5ATP18B62": {"luxe": "Aurore Boréale", "sku": "AURORE-BOREALE"},
    "2BTP18/1006": {"luxe": "Espresso Lumière", "sku": "ESPRESSO-LUMIERE"},
    "T14/P14/24": {"luxe": "Venise Dorée", "sku": "VENISE-DOREE"},
}

# Catégories et séries
CATEGORY_SERIES = {
    "halo": {"type": "Halo", "serie": "Everly", "prefix": "H"},
    "genius": {"type": "Genius", "serie": "Vivian", "prefix": "G"},
    "tape": {"type": "Bande Adhésive", "serie": "Aurora", "prefix": "T"},
    "i-tip": {"type": "I-Tip", "serie": "Eleanor", "prefix": "I"},
}

# ═══════════════════════════════════════════════════════════════
# HELPERS - EXTRACTION CODE COULEUR
# ═══════════════════════════════════════════════════════════════

def extract_color_code(name: str) -> Optional[str]:
    """Extrait le code couleur d'un nom de produit (ex: #6/24, #HPS, #1B)"""
    # Pattern pour trouver #CODE
    match = re.search(r'#([A-Za-z0-9/]+)', name)
    if match:
        return match.group(1).upper()
    return None

def get_luxe_info(color_code: str) -> Dict[str, str]:
    """Retourne le nom luxe et SKU pour un code couleur"""
    # Chercher exact match
    if color_code in COLOR_MAPPING:
        return COLOR_MAPPING[color_code]
    
    # Chercher case-insensitive
    for code, info in COLOR_MAPPING.items():
        if code.upper() == color_code.upper():
            return info
    
    # Fallback
    return {"luxe": color_code, "sku": color_code.replace("/", "-")}

def detect_category(name: str, handle: str = "") -> str:
    """Détecte la catégorie d'un produit"""
    text = (name + " " + handle).lower()
    if "halo" in text:
        return "halo"
    elif "genius" in text or "trame" in text:
        return "genius"
    elif "tape" in text or "bande" in text or "adhésive" in text:
        return "tape"
    elif "i-tip" in text or "itip" in text or "kératine" in text:
        return "i-tip"
    return "halo"  # Default

# ═══════════════════════════════════════════════════════════════
# GÉNÉRATEURS DE CONTENU
# ═══════════════════════════════════════════════════════════════

def generate_product_name(current_name: str, category: str) -> str:
    """Génère le nouveau nom luxe pour un produit"""
    color_code = extract_color_code(current_name)
    if not color_code:
        return current_name
    
    luxe_info = get_luxe_info(color_code)
    cat_info = CATEGORY_SERIES.get(category, CATEGORY_SERIES["halo"])
    
    # Format: "{Type} {Série} {Nom Luxe} #{Code}"
    new_name = f"{cat_info['type']} {cat_info['serie']} {luxe_info['luxe']} #{color_code}"
    return new_name

def generate_variant_sku(current_sku: str, color_code: str, category: str) -> str:
    """Génère le nouveau SKU pour une variante"""
    # Extraire longueur et poids du SKU actuel (ex: H16120#1 -> 16, 120)
    # Pattern: TYPE + LONGUEUR + POIDS + #CODE
    match = re.match(r'[A-Z]+(\d{2})(\d{2,3}).*', current_sku)
    if match:
        length = match.group(1)  # 16 ou 20
        weight = match.group(2)  # 120 ou 140
    else:
        # Fallback: essayer d'extraire de la variante
        length = "20"
        weight = "140"
    
    luxe_info = get_luxe_info(color_code)
    cat_info = CATEGORY_SERIES.get(category, CATEGORY_SERIES["halo"])
    
    # Format: {PREFIX}-{LONGUEUR}-{POIDS}-{CODE}-{NOM_LUXE_SKU}
    # Ex: H-16-120-1-ONYX-NOIR
    code_clean = color_code.replace("/", "-")
    new_sku = f"{cat_info['prefix']}-{length}-{weight}-{code_clean}-{luxe_info['sku']}"
    return new_sku

def generate_description(category: str, color_code: str) -> str:
    """Génère la description SEO principale"""
    luxe_info = get_luxe_info(color_code)
    cat_info = CATEGORY_SERIES.get(category, CATEGORY_SERIES["halo"])
    
    descriptions = {
        "halo": f"""Extensions {cat_info['type']} Série {cat_info['serie']} - Volume instantané sans engagement

CONCEPT
• Fil invisible ajustable
• Aucune fixation permanente
• 100% réversible
• Application en moins de 2 minutes
• Retrait instantané sans aide professionnelle

QUALITÉ PREMIUM
• 100% cheveux humains vierges Remy
• Cuticules intactes
• Mouvement naturel
• Finition professionnelle salon Québec

DURÉE DE VIE
• Jusqu'à 12 mois et plus avec bon entretien

APPLICATION
• Auto-application simple
• Aucune aide requise
• Ajustement rapide et facile

COLLECTION
• Série {cat_info['serie']}
• Collection polyvalente Luxura
• Teinte: #{color_code} {luxe_info['luxe']}

Extensions capillaires Québec Montréal - Livraison rapide partout au Canada
Luxura Distribution - Extensions professionnelles haut de gamme""",

        "genius": f"""Extensions {cat_info['type']} Série {cat_info['serie']} - Trame invisible ultra-fine

TECHNOLOGIE
• Trame invisible ultra-fine
• Zéro tension sur le cuir chevelu
• Couture plate professionnelle
• Installation en moins de 45 minutes

QUALITÉ PREMIUM
• 100% cheveux humains vierges Remy
• Cuticules alignées naturellement
• Texture soyeuse premium
• Qualité salon haut de gamme Québec

DURÉE DE VIE
• 12 à 18 mois avec entretien professionnel

APPLICATION
• Installation par professionnel recommandée
• Couture ou micro-anneaux
• Réutilisable plusieurs fois

COLLECTION
• Série {cat_info['serie']}
• Collection polyvalente Luxura
• Teinte: #{color_code} {luxe_info['luxe']}

Extensions capillaires volume Montréal Québec
Luxura Distribution - Grossiste extensions Canada""",

        "tape": f"""Extensions {cat_info['type']} Série {cat_info['serie']} - Pose rapide invisible

CONCEPT
• Bande adhésive médicale
• Pose sandwich invisible
• Confort toute la journée
• Aucun dommage aux cheveux

QUALITÉ PREMIUM
• 100% cheveux humains Remy
• Cuticules intactes
• Adhésif hypoallergénique
• Approuvé salons professionnels Canada

DURÉE DE VIE
• 6 à 8 semaines par pose
• Réutilisable 3-4 fois

APPLICATION
• Pose rapide 30-45 minutes
• Retrait facile avec solvant
• Repositionnable

COLLECTION
• Série {cat_info['serie']}
• Collection polyvalente Luxura
• Teinte: #{color_code} {luxe_info['luxe']}

Extensions tape-in Montréal Québec
Luxura Distribution - Extensions professionnelles""",

        "i-tip": f"""Extensions {cat_info['type']} Série {cat_info['serie']} - Fusion naturelle durable

TECHNOLOGIE
• Pointe kératine italienne
• Fusion à chaud précise
• Mèche par mèche naturelle
• Invisible à l'œil nu

QUALITÉ PREMIUM
• 100% cheveux humains vierges Remy
• Kératine de grade médical
• Cuticules parfaitement alignées
• Standard salon luxe Montréal

DURÉE DE VIE
• 4 à 6 mois par application
• Cheveux réutilisables 2-3 fois

APPLICATION
• Installation professionnelle requise
• Pince à fusion ou ultrason
• Retrait avec pince spécialisée

COLLECTION
• Série {cat_info['serie']}
• Collection polyvalente Luxura
• Teinte: #{color_code} {luxe_info['luxe']}

Extensions kératine Québec Montréal
Luxura Distribution - Fournisseur extensions Canada"""
    }
    
    return descriptions.get(category, descriptions["halo"])

def generate_additional_info_sections(category: str) -> List[Dict[str, str]]:
    """Génère les sections d'informations supplémentaires pour Wix"""
    
    sections_by_category = {
        "halo": [
            {
                "title": "Description",
                "description": "Installation rapide et facile. Extensions confortables et discrètes fixées par fil invisible avec coutures renforcées pour durabilité accrue. Cheveux 100% naturels Remy à cuticules alignées pour éviter l'emmêlement. Pleine longueur et pointes épaisses."
            },
            {
                "title": "À propos de nos extensions",
                "description": "Les extensions Luxura sont fabriquées avec des cheveux 100% naturels Remy. Durée de vie de 9-12 mois avec soins appropriés. Se jumellent naturellement à vos cheveux et peuvent être lavées et coiffées normalement."
            },
            {
                "title": "Recommandation d'achat",
                "description": "1 paquet pour volume naturel. 2 paquets pour volume maximum ou cheveux très longs."
            },
            {
                "title": "Format",
                "description": "16 pouces (120 grammes) | 20 pouces (140 grammes)"
            },
            {
                "title": "Entretien recommandé",
                "description": "Shampooing doux sans sulfates ni parabènes. Lavage 1 fois par semaine. Masque hydratant 1 fois sur 2. Démêler avec peigne à grosses dents en commençant par les pointes. Séchage à l'air libre. Éviter les produits contenant de l'alcool."
            },
            {
                "title": "Précommande",
                "description": "Pré-commandes acceptées. Vous serez avisé directement à l'arrivée du stock."
            }
        ],
        "genius": [
            {
                "title": "Description",
                "description": "Trame invisible ultra-fine pour un volume spectaculaire. Technologie de pointe avec couture plate professionnelle. Zéro tension sur le cuir chevelu. Cheveux 100% naturels Remy de qualité salon."
            },
            {
                "title": "À propos de nos extensions",
                "description": "Extensions Genius Weft Luxura fabriquées avec cheveux 100% Remy. Durée de vie 12-18 mois avec entretien professionnel. Réutilisables plusieurs fois."
            },
            {
                "title": "Recommandation d'achat",
                "description": "1-2 trames pour volume naturel. 3-4 trames pour transformation complète."
            },
            {
                "title": "Format",
                "description": "18 pouces (50-60 grammes) | 20 pouces (50-60 grammes)"
            },
            {
                "title": "Entretien recommandé",
                "description": "Shampooing professionnel sans sulfates. Masque nourrissant hebdomadaire. Brossage délicat avec brosse spéciale extensions. Séchage naturel ou à basse température."
            },
            {
                "title": "Précommande",
                "description": "Pré-commandes acceptées. Notification automatique à la réception du stock."
            }
        ],
        "tape": [
            {
                "title": "Description",
                "description": "Extensions à bande adhésive professionnelle pour pose rapide et invisible. Adhésif médical hypoallergénique. Confort toute la journée sans dommage aux cheveux naturels."
            },
            {
                "title": "À propos de nos extensions",
                "description": "Extensions Tape-In Luxura avec adhésif de grade médical. Cheveux 100% Remy. Réutilisables 3-4 fois avec changement d'adhésif."
            },
            {
                "title": "Recommandation d'achat",
                "description": "20-40 bandes pour volume naturel. 40-60 bandes pour volume complet."
            },
            {
                "title": "Format",
                "description": "16 pouces (25 grammes/paquet) | 20 pouces (25 grammes/paquet) | 24 pouces (25 grammes/paquet)"
            },
            {
                "title": "Entretien recommandé",
                "description": "Éviter huiles et silicones près des racines. Shampooing doux. Brossage délicat. Repose recommandée toutes les 6-8 semaines."
            },
            {
                "title": "Précommande",
                "description": "Pré-commandes disponibles. Avis par courriel à l'arrivée."
            }
        ],
        "i-tip": [
            {
                "title": "Description",
                "description": "Extensions I-Tip à pointe kératine pour fusion naturelle et durable. Installation mèche par mèche pour résultat imperceptible. Kératine italienne de grade médical."
            },
            {
                "title": "À propos de nos extensions",
                "description": "Extensions I-Tip Luxura avec kératine premium. Cheveux 100% Remy vierges. Durée 4-6 mois par application. Cheveux réutilisables avec nouvelle kératine."
            },
            {
                "title": "Recommandation d'achat",
                "description": "100-150 mèches pour volume naturel. 150-200 mèches pour volume complet."
            },
            {
                "title": "Format",
                "description": "18 pouces (0.5g/mèche) | 20 pouces (0.5g/mèche) | 22 pouces (1g/mèche)"
            },
            {
                "title": "Entretien recommandé",
                "description": "Shampooing doux en évitant les racines. Pas de chaleur excessive sur les points de fusion. Brossage quotidien délicat. Retrait professionnel recommandé."
            },
            {
                "title": "Précommande",
                "description": "Pré-commandes acceptées pour toutes les teintes. Délai moyen 2-3 semaines."
            }
        ]
    }
    
    return sections_by_category.get(category, sections_by_category["halo"])

# ═══════════════════════════════════════════════════════════════
# WIX API HELPERS
# ═══════════════════════════════════════════════════════════════

def get_wix_headers() -> Dict[str, str]:
    """Retourne les headers pour l'API Wix"""
    return {
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json",
    }

def fetch_wix_product(product_id: str) -> Optional[Dict]:
    """Récupère un produit Wix par ID"""
    try:
        url = f"{WIX_BASE_URL}/products/{product_id}"
        response = requests.get(url, headers=get_wix_headers(), timeout=30)
        if response.status_code == 200:
            return response.json().get("product")
        return None
    except Exception as e:
        print(f"[ERROR] Fetch product {product_id}: {e}")
        return None

def update_wix_product(product_id: str, update_data: Dict) -> Dict:
    """Met à jour un produit Wix"""
    try:
        url = f"{WIX_BASE_URL}/products/{product_id}"
        response = requests.patch(url, headers=get_wix_headers(), json=update_data, timeout=30)
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_wix_variant(product_id: str, variant_id: str, update_data: Dict) -> Dict:
    """Met à jour une variante Wix"""
    try:
        url = f"{WIX_BASE_URL}/products/{product_id}/variants/{variant_id}"
        response = requests.patch(url, headers=get_wix_headers(), json=update_data, timeout=30)
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class SEOPushRequest(BaseModel):
    product_ids: Optional[List[str]] = None
    category: Optional[str] = None
    limit: Optional[int] = 10
    
class SEOApplyRequest(BaseModel):
    product_ids: Optional[List[str]] = None
    category: Optional[str] = None
    limit: Optional[int] = 10
    confirm: bool = False
    secret: str

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/push_preview")
async def seo_push_preview(request: SEOPushRequest):
    """
    Preview des modifications SEO sans les appliquer (DRY RUN)
    Retourne ce qui serait modifié pour chaque produit
    """
    from sqlmodel import Session, select
    from app.db.session import engine
    from app.models.product import Product
    
    results = []
    
    with Session(engine) as db:
        # Construire la requête
        stmt = select(Product)
        
        if request.product_ids:
            stmt = stmt.where(Product.id.in_([int(pid) for pid in request.product_ids]))
        
        if request.limit:
            stmt = stmt.limit(request.limit)
        
        products = db.exec(stmt).all()
        
        for product in products:
            current_name = product.name or ""
            color_code = extract_color_code(current_name)
            
            if not color_code:
                results.append({
                    "product_id": product.id,
                    "wix_id": product.wix_id,
                    "status": "skipped",
                    "reason": "No color code found in name",
                    "current_name": current_name
                })
                continue
            
            category = detect_category(current_name, product.handle or "")
            
            # Générer les nouvelles données
            new_name = generate_product_name(current_name, category)
            new_description = generate_description(category, color_code)
            new_sections = generate_additional_info_sections(category)
            
            # Préparer le preview pour les variantes
            variant_previews = []
            if product.options and isinstance(product.options, dict):
                current_sku = product.sku or ""
                new_sku = generate_variant_sku(current_sku, color_code, category)
                variant_previews.append({
                    "current_sku": current_sku,
                    "new_sku": new_sku,
                    "wix_variant_id": product.options.get("wix_variant_id")
                })
            
            results.append({
                "product_id": product.id,
                "wix_id": product.wix_id,
                "status": "preview",
                "color_code": color_code,
                "category": category,
                "changes": {
                    "name": {
                        "current": current_name,
                        "new": new_name
                    },
                    "description": {
                        "current_length": len(product.description or ""),
                        "new_length": len(new_description),
                        "preview": new_description[:200] + "..."
                    },
                    "additional_sections": [s["title"] for s in new_sections],
                    "variants": variant_previews
                }
            })
    
    return {
        "mode": "preview",
        "timestamp": datetime.utcnow().isoformat(),
        "total_products": len(results),
        "products": results
    }

@router.post("/push_apply")
async def seo_push_apply(request: SEOApplyRequest):
    """
    Applique les modifications SEO sur Wix
    REQUIERT: secret admin + confirm=true
    """
    # Vérifier le secret
    if request.secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Must set confirm=true to apply changes")
    
    from sqlmodel import Session, select
    from app.db.session import engine
    from app.models.product import Product
    
    results = {
        "success": [],
        "skipped": [],
        "errors": []
    }
    
    with Session(engine) as db:
        stmt = select(Product)
        
        if request.product_ids:
            stmt = stmt.where(Product.id.in_([int(pid) for pid in request.product_ids]))
        
        if request.limit:
            stmt = stmt.limit(request.limit)
        
        products = db.exec(stmt).all()
        
        for product in products:
            current_name = product.name or ""
            color_code = extract_color_code(current_name)
            wix_id = product.wix_id
            
            if not color_code or not wix_id:
                results["skipped"].append({
                    "product_id": product.id,
                    "reason": "No color code or wix_id"
                })
                continue
            
            category = detect_category(current_name, product.handle or "")
            
            try:
                # Générer les nouvelles données
                new_name = generate_product_name(current_name, category)
                new_description = generate_description(category, color_code)
                new_sections = generate_additional_info_sections(category)
                
                # Préparer le payload Wix
                update_payload = {
                    "product": {
                        "name": new_name,
                        "description": new_description,
                        "additionalInfoSections": new_sections
                    }
                }
                
                # Appeler l'API Wix
                result = update_wix_product(wix_id, update_payload)
                
                if result["success"]:
                    results["success"].append({
                        "product_id": product.id,
                        "wix_id": wix_id,
                        "old_name": current_name,
                        "new_name": new_name
                    })
                    
                    # Mettre à jour aussi dans notre base locale
                    product.name = new_name
                    product.description = new_description
                    db.add(product)
                    db.commit()
                else:
                    results["errors"].append({
                        "product_id": product.id,
                        "wix_id": wix_id,
                        "error": result.get("error") or result.get("response")
                    })
                    
            except Exception as e:
                results["errors"].append({
                    "product_id": product.id,
                    "wix_id": wix_id,
                    "error": str(e)
                })
    
    return {
        "mode": "apply",
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "success": len(results["success"]),
            "skipped": len(results["skipped"]),
            "errors": len(results["errors"])
        },
        "results": results
    }

@router.get("/test_connection")
async def test_wix_connection():
    """Teste la connexion à l'API Wix"""
    try:
        url = f"{WIX_BASE_URL}/products"
        params = {"query": {"paging": {"limit": 1}}}
        response = requests.post(
            f"{WIX_BASE_URL}/products/query",
            headers=get_wix_headers(),
            json=params,
            timeout=30
        )
        return {
            "status": "connected" if response.status_code == 200 else "error",
            "status_code": response.status_code,
            "has_api_key": bool(WIX_API_KEY),
            "has_site_id": bool(WIX_SITE_ID)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/color_mapping")
async def get_color_mapping():
    """Retourne le mapping complet des couleurs"""
    return {
        "mapping": COLOR_MAPPING,
        "categories": CATEGORY_SERIES
    }
