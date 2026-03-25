import React, { useEffect, useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Alert,
  Linking,
} from 'react-native';
import { Image } from 'expo-image';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuthStore } from '../../src/store/authStore';
import { useCartStore } from '../../src/store/cartStore';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';
const { width } = Dimensions.get('window');
const LUXURA_LOGO = 'https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/i7uo40l8_Luxura%20Distribution%20-%20OR%20-%20PNG.png';

// ═══════════════════════════════════════════════════════════════
// COLOR SYSTEM - Noms de luxe Luxura (copie locale pour affichage)
// ═══════════════════════════════════════════════════════════════
const COLOR_LUXE_NAMES: { [key: string]: string } = {
  "1": "Onyx Noir",
  "1B": "Noir Soie",
  "2": "Espresso Intense",
  "DB": "Nuit Mystère",
  "DC": "Chocolat Profond",
  "CACAO": "Cacao Velours",
  "CHENGTU": "Soie d'Orient",
  "FOOCHOW": "Cachemire Oriental",
  "3": "Châtaigne Douce",
  "CINNAMON": "Cannelle Épicée",
  "3/3T24": "Châtaigne Lumière Dorée",
  "6": "Caramel Doré",
  "BM": "Miel Sauvage",
  "6/24": "Golden Hour",
  "6/6T24": "Caramel Soleil",
  "18/22": "Champagne Doré",
  "60A": "Platine Pur",
  "PHA": "Cendré Céleste",
  "613/18A": "Diamant Glacé",
  "IVORY": "Ivoire Précieux",
  "ICW": "Cristal Polaire",
  "CB": "Miel Sauvage Ombré",
  "HPS": "Cendré Étoilé",
  "5AT60": "Aurore Glaciale",
  "5ATP18B62": "Aurore Boréale",
  "2BTP18/1006": "Espresso Lumière",
  "T14/P14/24": "Venise Dorée",
};

/**
 * Extraire le code couleur d'un nom de produit et retourner le nom de luxe
 * Exemple: "Halo Série Everly Balayage Blond Foncé #6/24" → "Golden Hour"
 */
function getLuxeName(productName: string): { luxeName: string; colorCode: string } {
  if (!productName) return { luxeName: '', colorCode: '' };
  
  // Chercher le pattern #CODE dans le nom
  const match = productName.match(/#([A-Za-z0-9/]+)/);
  if (!match) return { luxeName: '', colorCode: '' };
  
  const colorCode = match[1].toUpperCase();
  const luxeName = COLOR_LUXE_NAMES[colorCode] || '';
  
  return { luxeName, colorCode };
}

// ═══════════════════════════════════════════════════════════════
// SYSTÈME DE DESCRIPTION SEO LUXURA
// Mots-clés ciblés: St-Georges → Québec → Montréal
// ═══════════════════════════════════════════════════════════════

interface SEOSection {
  title: string;
  items: string[];
}

interface SEOContent {
  intro: string;
  sections: SEOSection[];
}

// Descriptions SEO optimisées par catégorie de produit
// Mots-clés ciblés : extensions cheveux Québec, Montréal, Canada, cheveux naturels, Remy hair
const SEO_TEMPLATES: { [category: string]: SEOContent } = {
  halo: {
    intro: "Extensions Halo Everly – Volume instantané zéro dommage. Fil invisible breveté qui repose confortablement sans tirer. La méthode la plus sécuritaire pour cheveux fins ou fragilisés. Livraison rapide partout au Québec.",
    sections: [
      {
        title: "CONCEPT UNIQUE",
        items: [
          "Fil invisible ajustable breveté",
          "Poids réparti uniformément sur la tête",
          "Zéro traction – protège contre l'alopécie",
          "Application en moins de 2 minutes",
          "Retrait instantané sans aide"
        ]
      },
      {
        title: "QUALITÉ PREMIUM",
        items: [
          "100% cheveux humains vierges Remy",
          "Cuticules intactes alignées",
          "Mouvement fluide et naturel",
          "Provenance éthique certifiée"
        ]
      },
      {
        title: "DURÉE DE VIE",
        items: [
          "12 à 18 mois avec entretien approprié",
          "Achat unique – économique à long terme"
        ]
      },
      {
        title: "APPLICATION",
        items: [
          "Auto-installation en 2 minutes",
          "Aucune colle, clip ou couture",
          "Ajustement rapide et discret"
        ]
      }
    ]
  },
  genius: {
    intro: "Extensions Genius Weft Vivian – Trame ultra-fine révolutionnaire de 0.78mm. La technologie la plus avancée pour volume maximal avec minimum de matériel. Choix #1 des stylistes professionnels de Montréal à Québec.",
    sections: [
      {
        title: "TECHNOLOGIE AVANCÉE",
        items: [
          "Trame ultra-fine 0.78mm invisible",
          "Découpable n'importe où sans effilochage",
          "Moins de rangées = moins de tension",
          "Plat contre le cuir chevelu"
        ]
      },
      {
        title: "QUALITÉ PREMIUM",
        items: [
          "100% cheveux humains vierges Remy",
          "Densité supérieure par trame",
          "Cuticules parfaitement alignées",
          "Qualité salon luxe Canada"
        ]
      },
      {
        title: "DURÉE DE VIE",
        items: [
          "12 à 18 mois avec entretien professionnel",
          "Réutilisable 2-3 fois minimum"
        ]
      },
      {
        title: "APPLICATION",
        items: [
          "Installation professionnelle recommandée",
          "Couture plate ou micro-anneaux",
          "Temps réduit vs autres méthodes"
        ]
      }
    ]
  },
  tape: {
    intro: "Extensions Bande Adhésive Aurora – Pose sandwich invisible et confortable. Adhésif médical hypoallergénique pour une tenue sécuritaire. Solution populaire dans les salons professionnels de St-Georges à Montréal.",
    sections: [
      {
        title: "CONCEPT SANDWICH",
        items: [
          "Bande adhésive médicale premium",
          "Pose invisible entre deux mèches",
          "Confort optimal toute la journée",
          "Aucun dommage aux cheveux naturels"
        ]
      },
      {
        title: "QUALITÉ PREMIUM",
        items: [
          "100% cheveux humains vierges Remy",
          "Adhésif hypoallergénique testé",
          "Cuticules intactes et alignées",
          "Approuvé salons Canada"
        ]
      },
      {
        title: "DURÉE DE VIE",
        items: [
          "6 à 8 semaines par pose",
          "Cheveux réutilisables 3-4 fois",
          "Économique sur 12-18 mois"
        ]
      },
      {
        title: "APPLICATION",
        items: [
          "Pose professionnelle 30-45 min",
          "Retrait facile avec solvant doux",
          "Repositionnable facilement"
        ]
      }
    ]
  },
  "i-tip": {
    intro: "Extensions I-Tip Eleanor – Fusion kératine froide mèche par mèche. Technique premium pour un résultat ultra-naturel imperceptible. Méthode préférée des stylistes haut de gamme au Québec.",
    sections: [
      {
        title: "TECHNOLOGIE KÉRATINE",
        items: [
          "Pointe kératine italienne premium",
          "Fusion froide sans chaleur excessive",
          "Installation mèche par mèche",
          "Invisible même à l'inspection proche"
        ]
      },
      {
        title: "QUALITÉ PREMIUM",
        items: [
          "100% cheveux humains vierges Remy",
          "Kératine de grade médical",
          "Cuticules parfaitement alignées",
          "Standard salon luxe Montréal"
        ]
      },
      {
        title: "DURÉE DE VIE",
        items: [
          "3 à 4 mois par application",
          "Cheveux réutilisables 2-3 fois",
          "Rentable sur le long terme"
        ]
      },
      {
        title: "APPLICATION",
        items: [
          "Installation professionnelle requise",
          "Micro-anneaux silicone ou fusion",
          "Retrait doux avec pince spécialisée"
        ]
      }
    ]
  },
  essentiels: {
    intro: "Outils et produits d'entretien professionnels Luxura. Essentiels pour maximiser la beauté et prolonger la durée de vie de vos extensions capillaires premium.",
    sections: [
      {
        title: "QUALITÉ PROFESSIONNELLE",
        items: [
          "Formules salon haut de gamme",
          "Sans sulfate ni parabène",
          "Testés par coiffeurs experts",
          "Compatibles toutes extensions"
        ]
      },
      {
        title: "UTILISATION FACILE",
        items: [
          "Instructions détaillées incluses",
          "Résultats visibles immédiatement",
          "Support client Québec disponible"
        ]
      }
    ]
  },
  ponytail: {
    intro: "Queue de Cheval Victoria – Volume XXL spectaculaire en 30 secondes. Fixation wrap-around ultra-sécurisée ou clip robuste. Transformation instantanée pour événements ou quotidien au Québec.",
    sections: [
      {
        title: "APPLICATION ÉCLAIR",
        items: [
          "Installation en 30 secondes",
          "Fixation wrap-around sécurisée",
          "Clip robuste option alternative",
          "Retrait instantané"
        ]
      },
      {
        title: "QUALITÉ PREMIUM",
        items: [
          "100% cheveux humains vierges Remy",
          "Volume XXL naturel garanti",
          "Cuticules intactes et alignées",
          "Qualité salon professionnel"
        ]
      },
      {
        title: "DURÉE DE VIE",
        items: [
          "12 mois et plus avec bon entretien",
          "Réutilisation illimitée",
          "Investissement économique"
        ]
      },
      {
        title: "POLYVALENCE",
        items: [
          "Compatible tous types de cheveux",
          "Styles multiples possibles",
          "Parfait événements spéciaux"
        ]
      }
    ]
  },
  "clip-in": {
    intro: "Extensions à Clips Sophia – Volume et longueur sans engagement permanent. Clips silicone antidérapants ultra-discrets. Solution parfaite pour femmes actives du Québec cherchant flexibilité totale.",
    sections: [
      {
        title: "LIBERTÉ TOTALE",
        items: [
          "Application en moins de 5 minutes",
          "Retrait en quelques secondes",
          "100% réversible sans dommage",
          "Portez quand vous voulez"
        ]
      },
      {
        title: "QUALITÉ PREMIUM",
        items: [
          "100% cheveux humains vierges Remy",
          "Clips silicone antidérapants",
          "Trame invisible ultra-fine",
          "Mouvement fluide et naturel"
        ]
      },
      {
        title: "DURÉE DE VIE",
        items: [
          "12 à 18 mois avec entretien",
          "Réutilisation quotidienne possible",
          "Meilleur rapport qualité-prix"
        ]
      },
      {
        title: "IDÉAL POUR",
        items: [
          "Débutantes en extensions",
          "Événements spéciaux",
          "Usage occasionnel ou quotidien"
        ]
      }
    ]
  }
};

// Générer la description SEO complète
function generateSEODescription(category: string, colorCode: string, luxeName: string, seriesName: string): SEOContent {
  const template = SEO_TEMPLATES[category] || SEO_TEMPLATES.halo;
  
  // Clone le template
  const content: SEOContent = {
    intro: template.intro,
    sections: template.sections.map(s => ({ ...s, items: [...s.items] }))
  };
  
  // Ajouter la section COLLECTION avec les infos du produit
  const collectionSection: SEOSection = {
    title: "COLLECTION",
    items: [
      `Série ${seriesName || 'Everly'}`,
      "Collection polyvalente Luxura",
      `Teinte: ${colorCode ? `#${colorCode}` : ''} ${luxeName || ''}`.trim()
    ].filter(item => item.length > 0)
  };
  
  content.sections.push(collectionSection);
  
  return content;
}

// Component to format description into sections
const FormattedDescription = ({ 
  description, 
  category = 'halo', 
  colorCode = '', 
  luxeName = '',
  seriesName = 'Everly'
}: { 
  description: string; 
  category?: string;
  colorCode?: string;
  luxeName?: string;
  seriesName?: string;
}) => {
  // Utiliser le contenu SEO généré
  const seoContent = generateSEODescription(category, colorCode, luxeName, seriesName);
  
  // Toujours utiliser le template SEO pour garantir un affichage complet et cohérent
  // Les templates contiennent toutes les sections: CONCEPT, QUALITÉ PREMIUM, DURÉE DE VIE, APPLICATION, COLLECTION
  const { intro, sections } = seoContent;
  
  return (
    <View style={descStyles.container}>
      {intro ? (
        <Text style={descStyles.intro}>{intro}</Text>
      ) : null}
      
      <View style={descStyles.sectionsGrid}>
        {sections.map((section, index) => (
          <View key={index} style={descStyles.section}>
            <Text style={descStyles.sectionTitle}>{section.title}</Text>
            {section.items.map((item, itemIndex) => (
              <View key={itemIndex} style={descStyles.bulletItem}>
                <Text style={descStyles.bullet}>•</Text>
                <Text style={descStyles.bulletText}>{item}</Text>
              </View>
            ))}
          </View>
        ))}
      </View>
    </View>
  );
};

// Fallback simple description (deprecated)
const SimpleDescription = ({ description }: { description: string }) => (
  <View style={descStyles.container}>
    <Text style={descStyles.sectionTitle}>Description</Text>
    <Text style={descStyles.intro}>{description}</Text>
    </View>
);

const descStyles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  intro: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 16,
  },
  sectionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
  },
  section: {
    width: '48%',
    marginBottom: 12,
    minHeight: 80,
  },
  sectionTitle: {
    color: '#c9a050',
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  bulletItem: {
    flexDirection: 'row',
    marginBottom: 4,
    paddingRight: 4,
  },
  bullet: {
    color: '#888',
    fontSize: 12,
    marginRight: 6,
    marginTop: 1,
  },
  bulletText: {
    color: '#aaa',
    fontSize: 12,
    lineHeight: 18,
    flex: 1,
  },
});

interface Variant {
  id: number;
  sku: string | null;
  wix_variant_id: string;
  longeur_raw: string;
  length: string;
  weight: string;
  price: number;
  quantity: number;
  is_in_stock: boolean;
}

interface Product {
  id: string;
  name: string;
  price: number;
  original_price?: number;
  description: string;
  category: string;
  images: string[];
  in_stock: boolean;
  total_quantity?: number;
  color_code?: string;
  series?: string;
  wix_url?: string;
  handle?: string;
  variants?: Variant[];
  variant_count?: number;
}

export default function ProductScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { isAuthenticated, sessionToken } = useAuthStore();
  const { addToCart, count } = useCartStore();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [addingToCart, setAddingToCart] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [selectedVariant, setSelectedVariant] = useState<Variant | null>(null);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/products/${id}`);
        setProduct(response.data);
        
        // Auto-select first in-stock variant if available
        if (response.data.variants && response.data.variants.length > 0) {
          const inStockVariant = response.data.variants.find((v: Variant) => v.is_in_stock || v.quantity > 0);
          setSelectedVariant(inStockVariant || response.data.variants[0]);
        }
      } catch (error) {
        console.error('Error fetching product:', error);
        Alert.alert('Erreur', 'Impossible de charger le produit');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchProduct();
    }
  }, [id]);

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (!product) return;

    setAddingToCart(true);
    const success = await addToCart(product.id, quantity, sessionToken);
    setAddingToCart(false);

    if (success) {
      Alert.alert(
        'Ajouté au panier',
        `${product.name} a été ajouté à votre panier.`,
        [
          { text: 'Continuer', style: 'cancel' },
          { text: 'Voir le panier', onPress: () => router.push('/cart') },
        ]
      );
    }
  };

  const handleBuyNow = () => {
    // Redirect to Wix product page for length/weight selection
    const wixUrl = product?.wix_url || 'https://www.luxuradistribution.com/category/all-products';
    Linking.openURL(wixUrl);
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#c9a050" />
      </View>
    );
  }

  if (!product) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color="#666" />
        <Text style={styles.errorText}>Produit non trouvé</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Retour</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header - Navigation fixe avec logo */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <TouchableOpacity 
          onPress={() => {
            if (router.canGoBack()) {
              router.back();
            } else {
              router.replace('/(tabs)/catalogue');
            }
          }} 
          style={styles.headerButton}
          activeOpacity={0.6}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Image 
          source={{ uri: LUXURA_LOGO }}
          style={styles.logoImage}
          contentFit="contain"
        />
        <TouchableOpacity 
          onPress={() => router.push('/cart')} 
          style={styles.headerButton} 
          activeOpacity={0.6}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          <Ionicons name="bag-outline" size={24} color="#fff" />
          {count > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{count > 9 ? '9+' : count}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.scrollView} 
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 20 }}
        bounces={true}
      >
        {/* Product Images */}
        <View style={styles.imageSection}>
          <Image
            source={{ uri: product.images[selectedImageIndex] || product.images[0] }}
            style={styles.mainImage}
            contentFit="cover"
          />
          {!product.in_stock && (
            <View style={styles.outOfStockOverlay}>
              <Text style={styles.outOfStockText}>Rupture de stock</Text>
            </View>
          )}
        </View>

        {/* Image Thumbnails */}
        {product.images.length > 1 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.thumbnailsContainer}>
            {product.images.map((image, index) => (
              <TouchableOpacity
                key={index}
                onPress={() => setSelectedImageIndex(index)}
                style={[
                  styles.thumbnail,
                  selectedImageIndex === index && styles.thumbnailActive,
                ]}
              >
                <Image source={{ uri: image }} style={styles.thumbnailImage} contentFit="cover" />
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}

        {/* Product Info */}
        <View style={styles.infoSection}>
          <View style={styles.categoryBadge}>
            <Text style={styles.categoryText}>{product.series || 'Luxura'}</Text>
          </View>
          
          {/* Afficher le nom de luxe si disponible, sinon le nom brut */}
          {(() => {
            const { luxeName, colorCode } = getLuxeName(product.name);
            return (
              <>
                <Text style={styles.productName}>
                  {luxeName || product.name}
                </Text>
                {colorCode && (
                  <Text style={styles.colorCode}>Code couleur: #{colorCode}</Text>
                )}
                {!colorCode && product.color_code && (
                  <Text style={styles.colorCode}>Code couleur: {product.color_code}</Text>
                )}
              </>
            );
          })()}
          
          <Text style={styles.price}>{product.price.toFixed(2)} C$</Text>
          
          {/* Affichage simplifié du stock */}
          <View style={styles.stockBadge}>
            <Ionicons 
              name={product.in_stock ? "checkmark-circle" : "close-circle"} 
              size={16} 
              color={product.in_stock ? "#4a4" : "#f44"} 
            />
            <Text style={[
              styles.stockText,
              product.in_stock ? styles.stockInStock : styles.stockOutOfStock
            ]}>
              {product.in_stock ? 'En stock' : 'Rupture de stock'}
            </Text>
          </View>
          
          <View style={styles.divider} />
          
          {/* Formatted Description Sections - avec SEO dynamique */}
          {(() => {
            const { colorCode } = getLuxeName(product.name);
            const luxeNameForDesc = COLOR_LUXE_NAMES[colorCode] || '';
            return (
              <FormattedDescription 
                description={product.description}
                category={product.category || 'halo'}
                colorCode={colorCode}
                luxeName={luxeNameForDesc}
                seriesName={product.series || 'Everly'}
              />
            );
          })()}
          
          {/* Variant Selector */}
          {product.variants && product.variants.length > 0 && (
            <View style={styles.variantSection}>
              <Text style={styles.variantTitle}>Sélectionner une variante</Text>
              <View style={styles.variantGrid}>
                {product.variants.map((variant, index) => {
                  const isSelected = selectedVariant?.id === variant.id;
                  const isAvailable = variant.is_in_stock || variant.quantity > 0;
                  
                  // Format propre pour l'affichage de la variante
                  const variantLabel = variant.length && variant.weight 
                    ? `${variant.length} - ${variant.weight}`
                    : variant.longeur_raw || `Variante ${index + 1}`;
                  
                  return (
                    <TouchableOpacity
                      key={variant.id || index}
                      style={[
                        styles.variantButton,
                        isSelected && styles.variantButtonSelected,
                        !isAvailable && styles.variantButtonDisabled,
                      ]}
                      onPress={() => setSelectedVariant(variant)}
                      activeOpacity={0.7}
                    >
                      <Text style={[
                        styles.variantText,
                        isSelected && styles.variantTextSelected,
                        !isAvailable && styles.variantTextDisabled,
                      ]}>
                        {variantLabel}
                      </Text>
                      {!isAvailable && (
                        <Text style={styles.variantOutOfStock}>Épuisé</Text>
                      )}
                      {isAvailable && variant.quantity > 0 && (
                        <Text style={[
                          styles.variantStock,
                          isSelected && styles.variantStockSelected,
                        ]}>
                          {variant.quantity} en stock
                        </Text>
                      )}
                    </TouchableOpacity>
                  );
                })}
              </View>
              
              {selectedVariant && (
                <View style={styles.selectedVariantInfo}>
                  <Text style={styles.selectedVariantLabel}>Variante sélectionnée:</Text>
                  <Text style={styles.selectedVariantValue}>
                    {selectedVariant.length && selectedVariant.weight 
                      ? `${selectedVariant.length} - ${selectedVariant.weight}`
                      : selectedVariant.longeur_raw}
                  </Text>
                </View>
              )}
            </View>
          )}
          
          <View style={styles.featuresSection}>
            <View style={styles.feature}>
              <Ionicons name="checkmark-circle" size={20} color="#c9a050" />
              <Text style={styles.featureText}>Cheveux 100% naturels Remy Hair</Text>
            </View>
            <View style={styles.feature}>
              <Ionicons name="checkmark-circle" size={20} color="#c9a050" />
              <Text style={styles.featureText}>Qualité professionnelle</Text>
            </View>
            <View style={styles.feature}>
              <Ionicons name="checkmark-circle" size={20} color="#c9a050" />
              <Text style={styles.featureText}>Livraison rapide au Québec</Text>
            </View>
          </View>
        </View>

        <View style={{ height: 150 }} />
      </ScrollView>

      {/* Bottom Action Bar */}
      <View style={[styles.bottomBar, { paddingBottom: insets.bottom + 16 }]}>
        {product.in_stock && (
          <View style={styles.quantitySelector}>
            <TouchableOpacity
              style={styles.quantityButton}
              onPress={() => setQuantity(Math.max(1, quantity - 1))}
            >
              <Ionicons name="remove" size={20} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.quantityText}>{quantity}</Text>
            <TouchableOpacity
              style={styles.quantityButton}
              onPress={() => setQuantity(quantity + 1)}
            >
              <Ionicons name="add" size={20} color="#fff" />
            </TouchableOpacity>
          </View>
        )}
        
        <View style={styles.actionButtons}>
          {product.in_stock ? (
            <>
              <TouchableOpacity
                style={styles.addToCartButton}
                onPress={handleAddToCart}
                disabled={addingToCart}
              >
                {addingToCart ? (
                  <ActivityIndicator size="small" color="#c9a050" />
                ) : (
                  <>
                    <Ionicons name="bag-add-outline" size={20} color="#c9a050" />
                    <Text style={styles.addToCartText}>Panier</Text>
                  </>
                )}
              </TouchableOpacity>
              <TouchableOpacity style={styles.buyNowButton} onPress={handleBuyNow}>
                <Text style={styles.buyNowText}>Acheter sur Wix</Text>
              </TouchableOpacity>
            </>
          ) : (
            <View style={styles.outOfStockButton}>
              <Ionicons name="alert-circle-outline" size={20} color="#666" />
              <Text style={styles.outOfStockButtonText}>Rupture de stock</Text>
            </View>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0c0c0c',
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    backgroundColor: '#0c0c0c',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    color: '#666',
    fontSize: 18,
    marginTop: 16,
    marginBottom: 24,
  },
  backButton: {
    backgroundColor: '#c9a050',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  backButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 12,
    zIndex: 10,
  },
  logoImage: {
    width: 100,
    height: 28,
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  badge: {
    position: 'absolute',
    top: 0,
    right: 0,
    backgroundColor: '#c9a050',
    width: 18,
    height: 18,
    borderRadius: 9,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeText: {
    color: '#000',
    fontSize: 10,
    fontWeight: '700',
  },
  scrollView: {
    flex: 1,
  },
  imageSection: {
    width: width,
    height: 300,  // Hauteur fixe pour éviter les problèmes de layout
    backgroundColor: '#1a1a1a',
    overflow: 'hidden',
  },
  mainImage: {
    width: '100%',
    height: 300,
    resizeMode: 'contain',
  },
  outOfStockOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  outOfStockText: {
    color: '#ff4444',
    fontSize: 24,
    fontWeight: '700',
  },
  thumbnailsContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  thumbnail: {
    width: 60,
    height: 60,
    borderRadius: 8,
    marginRight: 8,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  thumbnailActive: {
    borderColor: '#c9a050',
  },
  thumbnailImage: {
    width: '100%',
    height: '100%',
  },
  infoSection: {
    padding: 20,
  },
  categoryBadge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginBottom: 12,
  },
  categoryText: {
    color: '#c9a050',
    fontSize: 12,
    fontWeight: '600',
  },
  productName: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 8,
  },
  colorCode: {
    color: '#aaa',
    fontSize: 14,
    marginBottom: 12,
  },
  price: {
    color: '#c9a050',
    fontSize: 28,
    fontWeight: '800',
  },
  stockBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    backgroundColor: 'rgba(255,255,255,0.05)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  stockText: {
    fontSize: 13,
    fontWeight: '600',
  },
  stockInStock: {
    color: '#4a4',
  },
  stockOutOfStock: {
    color: '#f44',
  },
  divider: {
    height: 1,
    backgroundColor: '#2a2a2a',
    marginVertical: 20,
  },
  descriptionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  description: {
    color: '#aaa',
    fontSize: 15,
    lineHeight: 24,
    marginBottom: 20,
  },
  featuresSection: {
    gap: 12,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  featureText: {
    color: '#fff',
    fontSize: 14,
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#0c0c0c',
    borderTopWidth: 1,
    borderTopColor: '#1a1a1a',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  quantitySelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    gap: 20,
  },
  quantityButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantityText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '600',
    minWidth: 40,
    textAlign: 'center',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  addToCartButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#c9a050',
    gap: 8,
  },
  addToCartText: {
    color: '#c9a050',
    fontSize: 16,
    fontWeight: '600',
  },
  buyNowButton: {
    flex: 2,
    backgroundColor: '#c9a050',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  buyNowText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '700',
  },
  outOfStockButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#2a2a2a',
    gap: 8,
  },
  outOfStockButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  // Variant Selector Styles
  variantSection: {
    marginTop: 20,
    marginBottom: 16,
  },
  variantTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  variantGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  variantButton: {
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#333',
    minWidth: 100,
  },
  variantButtonSelected: {
    borderColor: '#c9a050',
    backgroundColor: '#2a2a1a',
  },
  variantButtonDisabled: {
    opacity: 0.5,
    backgroundColor: '#111',
  },
  variantText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '500',
  },
  variantTextSelected: {
    color: '#c9a050',
  },
  variantTextDisabled: {
    color: '#666',
    textDecorationLine: 'line-through',
  },
  variantSku: {
    color: '#888',
    fontSize: 10,
    marginTop: 2,
  },
  variantSkuSelected: {
    color: '#c9a050',
  },
  variantStock: {
    color: '#4a4',
    fontSize: 10,
    marginTop: 2,
  },
  variantStockSelected: {
    color: '#6c6',
  },
  variantOutOfStock: {
    color: '#f44',
    fontSize: 10,
    marginTop: 2,
    fontWeight: '600',
  },
  selectedVariantInfo: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#c9a050',
  },
  selectedVariantLabel: {
    color: '#888',
    fontSize: 12,
  },
  selectedVariantValue: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
    marginTop: 4,
  },
  selectedVariantSku: {
    color: '#c9a050',
    fontSize: 12,
    marginTop: 4,
  },
});
