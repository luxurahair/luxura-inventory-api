#!/usr/bin/env python3
"""
Script pour renommer les produits Hand-Tied Weft dans Wix
et mettre à jour leurs descriptions SEO
"""

import os
import requests
import re
import json

# Read from .env file
def load_env():
    env = {}
    with open("/app/backend/.env") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                env[key] = value
    return env

ENV = load_env()
WIX_API_KEY = ENV.get("WIX_API_KEY", "")
WIX_SITE_ID = ENV.get("WIX_SITE_ID", "")

HEADERS = {
    "Authorization": WIX_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
    "wix-site-id": WIX_SITE_ID,
}

# HandTied Weft collection ID
HANDTIED_COLLECTION_ID = "ffa67c64-ec16-1770-6aef-03dfc39a166c"

# Color mapping for luxe names
COLOR_MAP = {
    "18/22": {"luxe": "Champagne Doré", "sku": "CHAMPAGNE-DORE"},
    "613/18A": {"luxe": "Diamant Glacé", "sku": "DIAMANT-GLACE"},
    "CB": {"luxe": "Miel Sauvage Ombré", "sku": "MIEL-SAUVAGE-OMBRE"},
    "6/6T24": {"luxe": "Caramel Soleil", "sku": "CARAMEL-SOLEIL"},
    "60A": {"luxe": "Platine Pur", "sku": "PLATINE-PUR"},
    "DB": {"luxe": "Nuit Mystère", "sku": "NUIT-MYSTERE"},
    "3/3T24": {"luxe": "Châtaigne Lumière", "sku": "CHATAIGNE-LUMIERE"},
    "HPS": {"luxe": "Cendré Étoilé", "sku": "CENDRE-ETOILE"},
}


def build_handtied_description(color_code: str) -> str:
    """Build SEO-optimized description for Hand-Tied Weft"""
    color_info = COLOR_MAP.get(color_code.upper(), {"luxe": color_code, "sku": color_code})
    luxe_name = color_info["luxe"]
    
    luxura = '<span style="color:#D4AF37;font-weight:bold;">Luxura</span>'
    
    seo_local = f"""<p><strong>Disponible au Québec:</strong><br>
<strong>Rajouts cheveux</strong> Québec | <strong>Rallonges capillaires</strong> Montréal | <strong>Volume capillaire</strong> Laval<br>
<strong>Cheveux naturels Remy</strong> Lévis | <strong>Extensions professionnelles</strong> Trois-Rivières | <strong>Pose extensions</strong> Beauce</p>
<br>
<p>{luxura} Distribution – Leader des <strong>extensions capillaires professionnelles</strong> au Québec et au Canada.</p>"""
    
    return f"""<p><strong>Extensions Hand-Tied Weft Aurora</strong> – Trame cousue main artisanale par {luxura}.</p>
<br>
<p><strong>Qualité Russe exceptionnelle</strong> – Les cheveux les plus fins et soyeux au monde.</p>
<br>
<p><strong>Fabrication artisanale:</strong><br>
• Chaque mèche cousue individuellement à la main<br>
• Trame ultra-fine, plate et flexible<br>
• Épouse parfaitement le cuir chevelu<br>
• Résultat naturel et invisible<br>
• <strong>Ne peut pas être coupée</strong> – trame intacte pour durabilité maximale</p>
<br>
<p><strong>Qualité Premium:</strong><br>
• 100% <strong>cheveux humains vierges Remy</strong><br>
• Cuticules intactes alignées dans le même sens<br>
• Série Aurora – Collection professionnelle {luxura}<br>
• Teinte: <strong>{luxe_name} #{color_code}</strong></p>
<br>
<p><strong>Avantages uniques:</strong><br>
• Idéal pour cheveux fins ou clairsemés<br>
• Installation sans chaleur ni colle – cousue sur tresse<br>
• Légère et confortable toute la journée<br>
• Durée de vie: 9-12 mois avec bon entretien</p>
<br>
<p><strong>Application:</strong> Pose professionnelle en salon (méthode couture sur tresse)</p>
<br>
{seo_local}"""


def extract_color_code(name: str) -> str:
    """Extract color code from product name"""
    match = re.search(r'#([A-Za-z0-9/]+)$', name.strip())
    if match:
        return match.group(1).upper()
    return ""


def build_new_name(color_code: str) -> str:
    """Build new product name for Hand-Tied"""
    color_info = COLOR_MAP.get(color_code.upper(), {"luxe": color_code})
    luxe_name = color_info["luxe"]
    return f"Hand-Tied Aurora {luxe_name} #{color_code}"


def get_all_products():
    """Fetch all products from Wix"""
    url = "https://www.wixapis.com/stores/v1/products/query"
    all_products = []
    cursor = None
    
    for page in range(10):
        body = {"query": {"paging": {"limit": 100}}}
        if cursor:
            body["query"]["cursorPaging"] = {"cursor": cursor}
        
        response = requests.post(url, headers=HEADERS, json=body, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            all_products.extend(products)
            
            cursor = data.get("nextCursor")
            if not cursor or not products:
                break
        else:
            print(f"Error fetching products: {response.status_code}")
            break
    
    return all_products


def update_product(product_id: str, new_name: str, new_description: str, new_sku: str) -> dict:
    """Update product name, description and SKU in Wix"""
    url = f"https://www.wixapis.com/stores/v1/products/{product_id}"
    
    payload = {
        "product": {
            "name": new_name,
            "description": new_description,
        }
    }
    
    # Add SKU if provided
    if new_sku:
        payload["product"]["sku"] = new_sku
    
    response = requests.patch(url, headers=HEADERS, json=payload, timeout=30)
    
    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    else:
        return {"success": False, "error": response.text, "status_code": response.status_code}


def main(dry_run: bool = True):
    """Main function to rename Hand-Tied products"""
    print("=" * 60)
    print("RENOMMAGE DES PRODUITS HAND-TIED WEFT")
    print("=" * 60)
    print(f"Mode: {'SIMULATION (dry_run)' if dry_run else '⚠️  PRODUCTION - MODIFICATIONS RÉELLES'}")
    print()
    
    # Get all products
    products = get_all_products()
    print(f"Total products fetched: {len(products)}")
    
    # Filter Hand-Tied products
    handtied_products = [
        p for p in products 
        if HANDTIED_COLLECTION_ID in p.get("collectionIds", [])
        and "Genius" in p.get("name", "")  # Only rename those with wrong "Genius" name
    ]
    
    print(f"Hand-Tied products to rename: {len(handtied_products)}")
    print()
    
    results = []
    
    for p in handtied_products:
        product_id = p.get("id")
        current_name = p.get("name", "")
        current_sku = p.get("sku", "")
        
        # Extract color code
        color_code = extract_color_code(current_name)
        
        if not color_code:
            print(f"⚠️  Skipping {current_name} - no color code found")
            continue
        
        # Build new name and description
        new_name = build_new_name(color_code)
        new_description = build_handtied_description(color_code)
        
        # Build new SKU
        color_info = COLOR_MAP.get(color_code.upper(), {"sku": color_code.replace("/", "-")})
        new_sku = f"HW-{color_info['sku']}"
        
        print(f"📦 Product: {current_name}")
        print(f"   ➜ New name: {new_name}")
        print(f"   ➜ New SKU: {new_sku}")
        print(f"   ➜ ID: {product_id}")
        
        if not dry_run:
            result = update_product(product_id, new_name, new_description, new_sku)
            if result["success"]:
                print(f"   ✅ Updated successfully!")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            results.append(result)
        else:
            print(f"   🔄 Would update (dry_run)")
        
        print()
    
    print("=" * 60)
    if dry_run:
        print(f"SIMULATION TERMINÉE - {len(handtied_products)} produits seraient modifiés")
        print("Pour exécuter réellement, lancez avec: python3 rename_handtied_products.py --apply")
    else:
        success = sum(1 for r in results if r.get("success"))
        print(f"TERMINÉ - {success}/{len(results)} produits mis à jour avec succès")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    dry_run = "--apply" not in sys.argv
    main(dry_run=dry_run)
