# ============================================================
# CODE CORRIGÉ POUR wix_seo_push.py (Backend Render)
# ============================================================
# 
# PROBLÈME: L'API Wix V1 applique le MÊME SKU à toutes les variantes
#           quand on utilise {"id": "...", "sku": "..."} dans le payload
#
# SOLUTION: Utiliser {"choices": {"Longeur": "16\" 120 grammes"}, "sku": "..."} 
#           au lieu de {"id": "...", "sku": "..."}
#
# ============================================================

# ANCIENNE FONCTION (BUGGUÉE) - NE PAS UTILISER
# ------------------------------------------------
async def _wix_v1_patch_variants_OLD_BUGGY(wix_product_id: str, variants_data: list, access_token: str):
    """
    ❌ CETTE VERSION EST BUGGUÉE - Elle écrase tous les SKUs avec la même valeur
    """
    url = f"https://www.wixapis.com/stores/v1/products/{wix_product_id}/variants"
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json"
    }
    
    # ❌ BUG: Utiliser "id" fait que Wix applique le dernier SKU à TOUTES les variantes
    payload = {
        "variants": [
            {"id": v["variant_id"], "variant": {"sku": v["target_sku"]}}
            for v in variants_data
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(url, headers=headers, json=payload)
        return response.json()


# NOUVELLE FONCTION (CORRIGÉE) - UTILISER CELLE-CI
# ------------------------------------------------
async def _wix_v1_patch_variants(wix_product_id: str, variants_data: list, access_token: str):
    """
    ✅ VERSION CORRIGÉE - Utilise 'choices' pour différencier chaque variante
    
    Args:
        wix_product_id: L'ID Wix du produit (ex: "c2e7afd1-810f-4003-9693-839d1912a818")
        variants_data: Liste de dicts avec 'choice' et 'target_sku'
                      Ex: [{"choice": "16\" 120 grammes", "target_sku": "H-16-120-3-3T24"}]
        access_token: Token Wix OAuth
    """
    url = f"https://www.wixapis.com/stores/v1/products/{wix_product_id}/variants"
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json"
    }
    
    # ✅ SOLUTION: Utiliser "choices" avec le nom de l'option ("Longeur") et sa valeur
    # Cela permet à Wix d'identifier PRÉCISÉMENT quelle variante mettre à jour
    payload = {
        "variants": [
            {
                "choices": {"Longeur": v["choice"]},  # Ex: {"Longeur": "16\" 120 grammes"}
                "variant": {"sku": v["target_sku"]}   # Ex: {"sku": "H-16-120-3-3T24"}
            }
            for v in variants_data
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(url, headers=headers, json=payload)
        return response.json()


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

# Pour le produit "Halo Everly Brun Châtaigne #3/3T24"
# wix_product_id = "c2e7afd1-810f-4003-9693-839d1912a818"

variants_to_update = [
    {
        "choice": "16\" 120 grammes",
        "target_sku": "H-16-120-3-3T24"
    },
    {
        "choice": "20\" 140 grammes", 
        "target_sku": "H-20-140-3-3T24"
    }
]

# Appel de la fonction corrigée:
# result = await _wix_v1_patch_variants(
#     wix_product_id="c2e7afd1-810f-4003-9693-839d1912a818",
#     variants_data=variants_to_update,
#     access_token="Bearer YOUR_WIX_TOKEN"
# )


# ============================================================
# PAYLOAD JSON ENVOYÉ À WIX (pour référence)
# ============================================================
"""
{
    "variants": [
        {
            "choices": {"Longeur": "16\" 120 grammes"},
            "variant": {"sku": "H-16-120-3-3T24"}
        },
        {
            "choices": {"Longeur": "20\" 140 grammes"},
            "variant": {"sku": "H-20-140-3-3T24"}
        }
    ]
}
"""

# ============================================================
# NOTES IMPORTANTES
# ============================================================
# 
# 1. Le nom de l'option est "Longeur" (pas "Longueur") - c'est comme ça 
#    qu'il est défini dans votre boutique Wix
#
# 2. Les valeurs de choices doivent correspondre EXACTEMENT à celles 
#    affichées dans Wix (ex: "16\" 120 grammes" avec les guillemets échappés)
#
# 3. L'API Wix V1 accepte plusieurs variantes dans un seul appel PATCH
#
# 4. Si vous migrez vers Wix API V3 à l'avenir, la syntaxe sera différente
#
