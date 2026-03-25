#!/usr/bin/env python3
"""
==============================================================================
SCRIPT: Correction des SKUs Genius sur Wix
==============================================================================
Ce script met à jour les SKUs de TOUTES les variantes des produits Genius
dans votre boutique Wix avec le format correct utilisant les noms de couleurs Luxe.

FORMAT SKU: G-[LONGUEUR]-[POIDS]-[NOM-COULEUR-LUXE]
Exemples:
  - G-18-50-CHOCOLAT-PROFOND
  - G-20-60-CHAMPAGNE-DORE
  - G-18-60-PLATINE-PUR

À EXÉCUTER SUR: Console Render (luxura-inventory-api)
==============================================================================
"""

import os
import httpx
import asyncio
import re
from typing import Dict, List, Optional, Tuple

# ==================== CONFIGURATION ====================

# Wix OAuth credentials (utiliser vos credentials existants)
WIX_CLIENT_ID = os.getenv("WIX_CLIENT_ID", "")
WIX_CLIENT_SECRET = os.getenv("WIX_CLIENT_SECRET", "")
WIX_ACCOUNT_ID = os.getenv("WIX_ACCOUNT_ID", "")
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "")

# ==================== MAPPING COULEURS LUXE ====================

# Mapping: code_couleur_brut → nom_luxe_pour_sku
COLOR_LUXE_MAP = {
    # Noirs
    "1": "ONYX-NOIR",
    "1b": "NOIR-SOIE",
    # Bruns
    "2": "ESPRESSO-INTENSE",
    "db": "NUIT-MYSTERE",
    "dc": "CHOCOLAT-PROFOND",
    "cacao": "CACAO-VELOURS",
    "chengtu": "SOIE-ORIENT",
    "foochow": "CACHEMIRE-ORIENTAL",
    # Châtaignes
    "3": "CHATAIGNE-DOUCE",
    "cinnamon": "CANNELLE-EPICEE",
    "3-3t24": "CHATAIGNE-LUMIERE",
    # Caramels
    "6": "CARAMEL-DORE",
    "bm": "MIEL-SAUVAGE",
    "6-24": "GOLDEN-HOUR",
    "6-6t24": "CARAMEL-SOLEIL",
    # Blonds
    "18-22": "CHAMPAGNE-DORE",
    "60a": "PLATINE-PUR",
    "pha": "CENDRE-CELESTE",
    "613-18a": "DIAMANT-GLACE",
    # Blancs
    "ivory": "IVOIRE-PRECIEUX",
    "icw": "CRISTAL-POLAIRE",
    # Ombrés
    "cb": "MIEL-SAUVAGE-OMBRE",
    "hps": "CENDRE-ETOILE",
    "5at60": "AURORE-GLACIALE",
    "5atp18b62": "AURORE-BOREALE",
    "2btp18-1006": "ESPRESSO-LUMIERE",
    "t14-p14-24": "VENISE-DOREE",
}

# ==================== FONCTIONS UTILITAIRES ====================

def extract_color_code_from_name(product_name: str) -> Optional[str]:
    """
    Extrait le code couleur du nom du produit Genius.
    Ex: "Genius Vivian Chocolat Profond #DC" → "dc"
    Ex: "Genius Série Vivian Blond Platine 60A" → "60a"
    """
    name_lower = product_name.lower()
    
    # Chercher le code couleur dans le nom (du plus long au plus court)
    for code in sorted(COLOR_LUXE_MAP.keys(), key=len, reverse=True):
        code_lower = code.lower()
        # Chercher le code à la fin ou précédé d'un espace/#/-
        patterns = [
            f"#{code_lower}",
            f" {code_lower}$",
            f"-{code_lower}$",
            f" {code_lower} ",
        ]
        for pattern in patterns:
            if pattern in name_lower or name_lower.endswith(f" {code_lower}"):
                return code_lower
    
    # Chercher dans le handle si présent
    return None

def extract_color_from_handle(handle: str) -> Optional[str]:
    """
    Extrait le code couleur depuis le handle Wix.
    Ex: "genius-trame-invisible-série-vivian-dark-chocolate-dc" → "dc"
    """
    if not handle:
        return None
    
    handle_lower = handle.lower()
    
    # Chercher le code couleur à la fin du handle
    for code in sorted(COLOR_LUXE_MAP.keys(), key=len, reverse=True):
        if handle_lower.endswith(f"-{code}"):
            return code
    
    return None

def generate_genius_sku(length: str, weight: str, color_code: str) -> str:
    """
    Génère un SKU Genius au format correct.
    
    Args:
        length: Longueur en pouces (ex: "18", "20")
        weight: Poids en grammes (ex: "50", "60")
        color_code: Code couleur brut (ex: "dc", "60a")
    
    Returns:
        SKU formaté (ex: "G-18-50-CHOCOLAT-PROFOND")
    """
    luxe_name = COLOR_LUXE_MAP.get(color_code.lower(), color_code.upper())
    return f"G-{length}-{weight}-{luxe_name}"

def parse_variant_options(variant: dict) -> Tuple[str, str]:
    """
    Parse les options de variante pour extraire longueur et poids.
    
    Returns:
        (length, weight) - ex: ("18", "50")
    """
    length = ""
    weight = ""
    
    choices = variant.get("choices", {})
    
    # Chercher dans les choix de variante
    for key, value in choices.items():
        value_str = str(value).lower()
        
        # Extraire la longueur (ex: "18'" ou "20"")
        length_match = re.search(r"(\d{2})[\'\"]", value_str)
        if length_match:
            length = length_match.group(1)
        
        # Extraire le poids (ex: "50 grammes" ou "60g")
        weight_match = re.search(r"(\d{2,3})\s*(?:grammes?|g)", value_str)
        if weight_match:
            weight = weight_match.group(1)
    
    # Si pas trouvé dans choices, chercher dans le nom de la variante
    if not length or not weight:
        variant_name = str(variant.get("variant", {}).get("name", "")).lower()
        if not length:
            length_match = re.search(r"(\d{2})[\'\"]", variant_name)
            if length_match:
                length = length_match.group(1)
        if not weight:
            weight_match = re.search(r"(\d{2,3})\s*(?:grammes?|g)", variant_name)
            if weight_match:
                weight = weight_match.group(1)
    
    return length, weight

# ==================== WIX API ====================

async def get_wix_access_token() -> str:
    """Obtient un token d'accès Wix via OAuth2 client_credentials."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.wixapis.com/oauth2/token",
            json={
                "grant_type": "client_credentials",
                "client_id": WIX_CLIENT_ID,
                "client_secret": WIX_CLIENT_SECRET,
            }
        )
        response.raise_for_status()
        return response.json()["access_token"]

async def get_genius_products(access_token: str) -> List[dict]:
    """Récupère tous les produits de la catégorie Genius."""
    products = []
    
    headers = {
        "Authorization": access_token,
        "wix-account-id": WIX_ACCOUNT_ID,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        # D'abord, récupérer l'ID de la catégorie Genius
        cat_response = await client.post(
            "https://www.wixapis.com/stores/v1/collections/query",
            headers=headers,
            json={"query": {}}
        )
        cat_response.raise_for_status()
        
        genius_collection_id = None
        for collection in cat_response.json().get("collections", []):
            if "genius" in collection.get("name", "").lower():
                genius_collection_id = collection.get("id")
                break
        
        if not genius_collection_id:
            print("❌ Collection 'Genius' non trouvée!")
            return []
        
        print(f"✅ Collection Genius trouvée: {genius_collection_id}")
        
        # Récupérer les produits de la catégorie Genius
        offset = 0
        limit = 100
        
        while True:
            response = await client.post(
                "https://www.wixapis.com/stores/v1/products/query",
                headers=headers,
                json={
                    "query": {
                        "filter": json.dumps({"collectionIds": genius_collection_id}),
                        "paging": {"limit": limit, "offset": offset}
                    },
                    "includeVariants": True
                }
            )
            response.raise_for_status()
            data = response.json()
            
            batch = data.get("products", [])
            if not batch:
                break
                
            products.extend(batch)
            print(f"📦 Récupéré {len(batch)} produits (total: {len(products)})")
            
            if len(batch) < limit:
                break
            offset += limit
    
    return products

async def update_variant_sku(access_token: str, product_id: str, variant_id: str, new_sku: str) -> bool:
    """Met à jour le SKU d'une variante spécifique."""
    headers = {
        "Authorization": access_token,
        "wix-account-id": WIX_ACCOUNT_ID,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.patch(
                f"https://www.wixapis.com/stores/v1/products/{product_id}/variants/{variant_id}",
                headers=headers,
                json={
                    "variant": {
                        "sku": new_sku
                    }
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Erreur mise à jour variante {variant_id}: {e}")
            return False

# ==================== IMPORT MANQUANT ====================
import json

# ==================== SCRIPT PRINCIPAL ====================

async def fix_genius_skus():
    """Script principal pour corriger les SKUs Genius."""
    print("=" * 60)
    print("🔧 CORRECTION DES SKUs GENIUS - Luxura Distribution")
    print("=" * 60)
    
    # Vérifier les credentials
    if not all([WIX_CLIENT_ID, WIX_CLIENT_SECRET, WIX_ACCOUNT_ID, WIX_SITE_ID]):
        print("❌ Variables d'environnement Wix manquantes!")
        print("   Requis: WIX_CLIENT_ID, WIX_CLIENT_SECRET, WIX_ACCOUNT_ID, WIX_SITE_ID")
        return
    
    # Obtenir le token d'accès
    print("\n🔑 Authentification Wix...")
    try:
        access_token = await get_wix_access_token()
        print("✅ Authentification réussie!")
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
        return
    
    # Récupérer les produits Genius
    print("\n📥 Récupération des produits Genius...")
    products = await get_genius_products(access_token)
    
    if not products:
        print("❌ Aucun produit Genius trouvé!")
        return
    
    print(f"\n✅ {len(products)} produits Genius trouvés")
    
    # Traiter chaque produit
    updates_success = 0
    updates_failed = 0
    skipped = 0
    
    for product in products:
        product_id = product.get("id")
        product_name = product.get("name", "")
        handle = product.get("slug", "") or product.get("handle", "")
        
        print(f"\n📦 Produit: {product_name}")
        
        # Extraire le code couleur
        color_code = extract_color_from_handle(handle)
        if not color_code:
            color_code = extract_color_code_from_name(product_name)
        
        if not color_code:
            print(f"   ⚠️ Code couleur non trouvé - SKU ignoré")
            skipped += 1
            continue
        
        print(f"   🎨 Couleur détectée: {color_code} → {COLOR_LUXE_MAP.get(color_code.lower(), 'INCONNU')}")
        
        # Traiter les variantes
        variants = product.get("variants", [])
        
        for variant in variants:
            variant_id = variant.get("id")
            current_sku = variant.get("sku", "")
            
            # Extraire longueur et poids
            length, weight = parse_variant_options(variant)
            
            if not length:
                length = "18"  # Défaut
            if not weight:
                weight = "50"  # Défaut
            
            # Générer le nouveau SKU
            new_sku = generate_genius_sku(length, weight, color_code)
            
            # Vérifier si mise à jour nécessaire
            if current_sku == new_sku:
                print(f"   ✓ Variante {length}\" {weight}g: SKU déjà correct")
                continue
            
            print(f"   🔄 Variante {length}\" {weight}g: {current_sku or '(vide)'} → {new_sku}")
            
            # Mettre à jour
            success = await update_variant_sku(access_token, product_id, variant_id, new_sku)
            
            if success:
                updates_success += 1
                print(f"      ✅ Mis à jour!")
            else:
                updates_failed += 1
            
            # Pause pour éviter le rate limiting
            await asyncio.sleep(0.3)
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"✅ Mises à jour réussies: {updates_success}")
    print(f"❌ Mises à jour échouées: {updates_failed}")
    print(f"⚠️ Produits ignorés (couleur non détectée): {skipped}")
    print("=" * 60)

# ==================== EXÉCUTION ====================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 DÉMARRAGE DU SCRIPT DE CORRECTION DES SKUs GENIUS")
    print("=" * 60)
    asyncio.run(fix_genius_skus())
