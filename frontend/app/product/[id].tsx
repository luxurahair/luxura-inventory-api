import React, { useEffect, useState } from 'react';
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
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.headerButton}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <TouchableOpacity onPress={() => router.push('/cart')} style={styles.headerButton}>
          <Ionicons name="bag-outline" size={24} color="#fff" />
          {count > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{count > 9 ? '9+' : count}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
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
          
          <Text style={styles.productName}>{product.name}</Text>
          
          {product.color_code && (
            <Text style={styles.colorCode}>Code couleur: {product.color_code}</Text>
          )}
          
          <Text style={styles.price}>{product.price.toFixed(2)} C$</Text>
          
          <View style={styles.divider} />
          
          <Text style={styles.descriptionTitle}>Description</Text>
          <Text style={styles.description}>{product.description}</Text>
          
          {/* Variant Selector */}
          {product.variants && product.variants.length > 0 && (
            <View style={styles.variantSection}>
              <Text style={styles.variantTitle}>Sélectionner une variante</Text>
              <View style={styles.variantGrid}>
                {product.variants.map((variant, index) => {
                  const isSelected = selectedVariant?.id === variant.id;
                  const isAvailable = variant.is_in_stock || variant.quantity > 0;
                  
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
                        {variant.longeur_raw}
                      </Text>
                      {variant.sku && (
                        <Text style={[
                          styles.variantSku,
                          isSelected && styles.variantSkuSelected,
                        ]}>
                          {variant.sku}
                        </Text>
                      )}
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
                  <Text style={styles.selectedVariantValue}>{selectedVariant.longeur_raw}</Text>
                  {selectedVariant.sku && (
                    <Text style={styles.selectedVariantSku}>SKU: {selectedVariant.sku}</Text>
                  )}
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
    paddingHorizontal: 16,
    paddingBottom: 12,
    zIndex: 10,
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
    height: width * 1.2,
    backgroundColor: '#1a1a1a',
  },
  mainImage: {
    width: '100%',
    height: '100%',
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
