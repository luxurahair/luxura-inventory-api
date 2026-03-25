/**
 * =====================================================================
 * SCRIPT VELO: Correction des SKUs Genius - Luxura Distribution
 * =====================================================================
 * 
 * À EXÉCUTER DEPUIS: Wix Editor > Dev Mode > Velo Backend
 * 
 * INSTRUCTIONS:
 * 1. Allez sur votre éditeur Wix
 * 2. Activez le "Dev Mode" (menu en haut)
 * 3. Créez un fichier backend: backend/fixGeniusSKUs.jsw
 * 4. Copiez ce code dans le fichier
 * 5. Créez une page de test avec un bouton qui appelle fixAllGeniusSKUs()
 * =====================================================================
 */

import wixStoresBackend from 'wix-stores-backend';

// Mapping des codes couleur vers noms Luxe
const COLOR_LUXE_MAP = {
    "1": "ONYX-NOIR",
    "1b": "NOIR-SOIE",
    "2": "ESPRESSO-INTENSE",
    "db": "NUIT-MYSTERE",
    "dc": "CHOCOLAT-PROFOND",
    "cacao": "CACAO-VELOURS",
    "chengtu": "SOIE-ORIENT",
    "foochow": "CACHEMIRE-ORIENTAL",
    "3": "CHATAIGNE-DOUCE",
    "cinnamon": "CANNELLE-EPICEE",
    "3/3t24": "CHATAIGNE-LUMIERE",
    "6": "CARAMEL-DORE",
    "bm": "MIEL-SAUVAGE",
    "6/24": "GOLDEN-HOUR",
    "6/6t24": "CARAMEL-SOLEIL",
    "18/22": "CHAMPAGNE-DORE",
    "60a": "PLATINE-PUR",
    "pha": "CENDRE-CELESTE",
    "613/18a": "DIAMANT-GLACE",
    "ivory": "IVOIRE-PRECIEUX",
    "icw": "CRISTAL-POLAIRE",
    "cb": "MIEL-SAUVAGE-OMBRE",
    "hps": "CENDRE-ETOILE",
    "5at60": "AURORE-GLACIALE",
    "5atp18b62": "AURORE-BOREALE",
    "2btp18/1006": "ESPRESSO-LUMIERE",
    "t14/p14/24": "VENISE-DOREE",
};

// ID de la collection Genius (trouvé précédemment)
const GENIUS_COLLECTION_ID = "df309160-f8c2-4bfb-8b96-4c7167d6ca80";

/**
 * Extrait le code couleur du nom du produit
 */
function extractColorCode(productName) {
    const match = productName.match(/#([A-Za-z0-9/]+)$/);
    if (match) {
        return match[1].toLowerCase();
    }
    return null;
}

/**
 * Génère un SKU Genius au format: G-LONGUEUR-POIDS-NOM-LUXE
 */
function generateGeniusSKU(length, weight, colorCode) {
    const luxeName = COLOR_LUXE_MAP[colorCode.toLowerCase()] || colorCode.toUpperCase().replace(/\//g, '-');
    return `G-${length}-${weight}-${luxeName}`;
}

/**
 * Parse les options de variante pour extraire longueur et poids
 */
function parseVariantOptions(variantChoices) {
    let length = "18";
    let weight = "50";
    
    // Chercher dans les choix de variante
    for (let key in variantChoices) {
        const value = variantChoices[key].toString().toLowerCase();
        
        // Longueur: 18', 20", 24", 26"
        const lengthMatch = value.match(/(\d{2})['"]/);
        if (lengthMatch) {
            length = lengthMatch[1];
        }
        
        // Poids: 50 grammes, 60g
        const weightMatch = value.match(/(\d{2,3})\s*(?:grammes?|g)/);
        if (weightMatch) {
            weight = weightMatch[1];
        }
    }
    
    return { length, weight };
}

/**
 * Corrige tous les SKUs des produits Genius
 * @returns {Object} Résumé des modifications
 */
export async function fixAllGeniusSKUs() {
    console.log("========================================");
    console.log("CORRECTION DES SKUs GENIUS");
    console.log("========================================");
    
    let success = 0;
    let failed = 0;
    let skipped = 0;
    const results = [];
    
    try {
        // Récupérer tous les produits de la collection Genius
        const queryResult = await wixStoresBackend.queryProducts()
            .hasSome("collections", [GENIUS_COLLECTION_ID])
            .limit(100)
            .find();
        
        const products = queryResult.items;
        console.log(`${products.length} produits Genius trouvés`);
        
        for (const product of products) {
            console.log(`\nProduit: ${product.name}`);
            
            // Extraire le code couleur
            const colorCode = extractColorCode(product.name);
            if (!colorCode) {
                console.log("  ⚠️ Code couleur non détecté");
                skipped++;
                continue;
            }
            
            console.log(`  Couleur: ${colorCode} -> ${COLOR_LUXE_MAP[colorCode] || colorCode}`);
            
            // Récupérer les variantes du produit
            const variants = product.productOptions || [];
            
            if (!product.manageVariants || !product.variants || product.variants.length === 0) {
                console.log("  ⚠️ Pas de variantes à mettre à jour");
                skipped++;
                continue;
            }
            
            // Préparer les variantes à mettre à jour
            const variantsToUpdate = [];
            
            for (const variant of product.variants) {
                const { length, weight } = parseVariantOptions(variant.choices || {});
                const newSKU = generateGeniusSKU(length, weight, colorCode);
                
                if (variant.sku === newSKU) {
                    console.log(`  ✓ ${length}" ${weight}g: SKU OK`);
                    continue;
                }
                
                console.log(`  🔄 ${length}" ${weight}g: ${variant.sku || '(vide)'} -> ${newSKU}`);
                
                variantsToUpdate.push({
                    variantId: variant._id,
                    variant: {
                        sku: newSKU
                    }
                });
            }
            
            // Mettre à jour les variantes
            if (variantsToUpdate.length > 0) {
                try {
                    await wixStoresBackend.updateProductVariants(product._id, variantsToUpdate);
                    success += variantsToUpdate.length;
                    console.log(`  ✅ ${variantsToUpdate.length} variantes mises à jour`);
                    
                    results.push({
                        product: product.name,
                        updated: variantsToUpdate.length,
                        status: "success"
                    });
                } catch (updateError) {
                    failed += variantsToUpdate.length;
                    console.log(`  ❌ Erreur: ${updateError.message}`);
                    
                    results.push({
                        product: product.name,
                        error: updateError.message,
                        status: "failed"
                    });
                }
            }
        }
        
    } catch (error) {
        console.log(`Erreur globale: ${error.message}`);
        return {
            success: false,
            error: error.message
        };
    }
    
    // Résumé
    console.log("\n========================================");
    console.log("RÉSUMÉ");
    console.log("========================================");
    console.log(`✅ Succès: ${success}`);
    console.log(`❌ Échecs: ${failed}`);
    console.log(`⏭️ Ignorés: ${skipped}`);
    
    return {
        success: true,
        summary: {
            updated: success,
            failed: failed,
            skipped: skipped
        },
        details: results
    };
}

/**
 * Preview des modifications sans les appliquer
 */
export async function previewGeniusSKUChanges() {
    console.log("========================================");
    console.log("PREVIEW DES MODIFICATIONS SKU GENIUS");
    console.log("========================================");
    
    const changes = [];
    
    try {
        const queryResult = await wixStoresBackend.queryProducts()
            .hasSome("collections", [GENIUS_COLLECTION_ID])
            .limit(100)
            .find();
        
        for (const product of queryResult.items) {
            const colorCode = extractColorCode(product.name);
            if (!colorCode) continue;
            
            if (!product.variants || product.variants.length === 0) continue;
            
            for (const variant of product.variants) {
                const { length, weight } = parseVariantOptions(variant.choices || {});
                const newSKU = generateGeniusSKU(length, weight, colorCode);
                
                if (variant.sku !== newSKU) {
                    changes.push({
                        product: product.name,
                        variant: `${length}" ${weight}g`,
                        currentSKU: variant.sku || "(vide)",
                        newSKU: newSKU
                    });
                }
            }
        }
        
        console.log(`${changes.length} modifications à effectuer`);
        return {
            success: true,
            count: changes.length,
            changes: changes
        };
        
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
}
