import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Dimensions,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';
const { width } = Dimensions.get('window');
const CARD_WIDTH = (width - 48) / 2;

interface Product {
  id: string;
  name: string;
  price: number;
  description: string;
  category: string;
  images: string[];
  in_stock: boolean;
  color_code?: string;
}

interface Category {
  id: string;
  name: string;
  description: string;
  image?: string;
}

export default function HomeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [cartCount, setCartCount] = useState(0);

  const fetchData = async () => {
    try {
      const [productsRes, categoriesRes] = await Promise.all([
        axios.get(`${API_URL}/api/products`),
        axios.get(`${API_URL}/api/categories`),
      ]);
      setProducts(productsRes.data || []);
      setCategories(categoriesRes.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    const seedAndFetch = async () => {
      try {
        await axios.post(`${API_URL}/api/seed`);
      } catch (e) {
        // Ignore seed errors
      }
      fetchData();
    };
    seedAndFetch();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const featuredProducts = products.slice(0, 4);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#c9a050" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <Image 
          source={{ uri: 'https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/i7uo40l8_Luxura%20Distribution%20-%20OR%20-%20PNG.png' }}
          style={styles.logoImage}
          resizeMode="contain"
        />
        <TouchableOpacity onPress={() => router.push('/cart')} style={styles.cartButton}>
          <Ionicons name="bag-outline" size={24} color="#fff" />
          {cartCount > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{cartCount > 9 ? '9+' : cartCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c9a050" />
        }
      >
        {/* Hero Banner */}
        <View style={styles.heroBanner}>
          <Image
            source={{ uri: 'https://static.wixstatic.com/media/de6cdb_df3cf3adbce44d49b39546b5178c459d~mv2.jpg' }}
            style={styles.heroImage}
          />
          <View style={styles.heroOverlay} />
          <View style={styles.heroContent}>
            <Text style={styles.heroTitle}>Extensions Capillaires</Text>
            <Text style={styles.heroSubtitle}>Professionnelles au Québec</Text>
            <View style={styles.heroFeatures}>
              <Text style={styles.heroFeature}>✔ Approvisionnement direct</Text>
              <Text style={styles.heroFeature}>✔ Stock réel disponible</Text>
              <Text style={styles.heroFeature}>✔ Livraison rapide</Text>
            </View>
            <TouchableOpacity 
              style={styles.heroButton}
              onPress={() => router.push('/catalogue')}
            >
              <Text style={styles.heroButtonText}>Découvrir</Text>
              <Ionicons name="arrow-forward" size={18} color="#000" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Categories */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Catégories</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoriesScroll}>
            {categories.map((category) => (
              <TouchableOpacity
                key={category.id}
                style={styles.categoryCard}
                onPress={() => router.push(`/catalogue?category=${category.id}`)}
              >
                <Image
                  source={{ uri: category.image || 'https://via.placeholder.com/160x100' }}
                  style={styles.categoryImage}
                />
                <View style={styles.categoryOverlay} />
                <Text style={styles.categoryName}>{category.name}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Featured Products */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Meilleurs Vendeurs</Text>
            <TouchableOpacity onPress={() => router.push('/catalogue')}>
              <Text style={styles.seeAll}>Voir tout</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.productsGrid}>
            {featuredProducts.map((product) => (
              <TouchableOpacity
                key={product.id}
                style={styles.productCard}
                onPress={() => router.push(`/product/${product.id}`)}
              >
                <View style={styles.productImageContainer}>
                  <Image 
                    source={{ uri: product.images[0] }} 
                    style={styles.productImage}
                  />
                  {!product.in_stock && (
                    <View style={styles.outOfStockBadge}>
                      <Text style={styles.outOfStockText}>Rupture</Text>
                    </View>
                  )}
                </View>
                <View style={styles.productInfo}>
                  <Text style={styles.productName} numberOfLines={2}>{product.name}</Text>
                  {product.color_code && (
                    <Text style={styles.productColorCode}>{product.color_code}</Text>
                  )}
                  <Text style={styles.productPrice}>{product.price.toFixed(2)} C$</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* About Section */}
        <View style={styles.aboutSection}>
          <Text style={styles.aboutTitle}>Pourquoi Luxura</Text>
          <Text style={styles.aboutText}>
            Chez Luxura Distribution, nous sommes un importateur et distributeur direct d'extensions 
            capillaires professionnelles au Québec. Notre mission est d'offrir aux salons un 
            approvisionnement fiable, constant et transparent.
          </Text>
          <View style={styles.aboutFeatures}>
            <View style={styles.aboutFeature}>
              <Ionicons name="checkmark-circle" size={24} color="#c9a050" />
              <Text style={styles.aboutFeatureText}>100% Remy Hair</Text>
            </View>
            <View style={styles.aboutFeature}>
              <Ionicons name="checkmark-circle" size={24} color="#c9a050" />
              <Text style={styles.aboutFeatureText}>Qualité garantie</Text>
            </View>
            <View style={styles.aboutFeature}>
              <Ionicons name="checkmark-circle" size={24} color="#c9a050" />
              <Text style={styles.aboutFeatureText}>+30 salons partenaires</Text>
            </View>
          </View>
        </View>

        {/* Footer spacing */}
        <View style={{ height: 100 }} />
      </ScrollView>
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: '#0c0c0c',
  },
  logo: {
    color: '#c9a050',
    fontSize: 26,
    fontWeight: '800',
    letterSpacing: 4,
  },
  logoImage: {
    width: 140,
    height: 50,
  },
  cartButton: {
    padding: 4,
    position: 'relative',
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
  heroBanner: {
    height: 400,
    position: 'relative',
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  heroOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  heroContent: {
    position: 'absolute',
    bottom: 40,
    left: 20,
    right: 20,
  },
  heroTitle: {
    color: '#fff',
    fontSize: 32,
    fontWeight: '800',
    marginBottom: 4,
  },
  heroSubtitle: {
    color: '#c9a050',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  heroFeatures: {
    marginBottom: 20,
  },
  heroFeature: {
    color: '#fff',
    fontSize: 14,
    marginBottom: 4,
  },
  heroButton: {
    backgroundColor: '#c9a050',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignSelf: 'flex-start',
    gap: 8,
  },
  heroButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '700',
  },
  section: {
    paddingHorizontal: 16,
    paddingTop: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 16,
  },
  seeAll: {
    color: '#c9a050',
    fontSize: 14,
    fontWeight: '600',
  },
  categoriesScroll: {
    marginBottom: 8,
  },
  categoryCard: {
    width: 160,
    height: 100,
    borderRadius: 12,
    marginRight: 12,
    overflow: 'hidden',
    position: 'relative',
  },
  categoryImage: {
    width: '100%',
    height: '100%',
  },
  categoryOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  categoryName: {
    position: 'absolute',
    bottom: 12,
    left: 12,
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
  },
  productsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  productCard: {
    width: CARD_WIDTH,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    marginBottom: 16,
    overflow: 'hidden',
  },
  productImageContainer: {
    width: '100%',
    height: CARD_WIDTH * 1.2,
    backgroundColor: '#2a2a2a',
  },
  productImage: {
    width: '100%',
    height: '100%',
  },
  outOfStockBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#ff4444',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  outOfStockText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '600',
  },
  productInfo: {
    padding: 12,
  },
  productName: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 4,
    lineHeight: 18,
  },
  productColorCode: {
    color: '#c9a050',
    fontSize: 11,
    marginBottom: 8,
  },
  productPrice: {
    color: '#c9a050',
    fontSize: 15,
    fontWeight: '700',
  },
  aboutSection: {
    margin: 16,
    padding: 20,
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
  },
  aboutTitle: {
    color: '#c9a050',
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 12,
  },
  aboutText: {
    color: '#aaa',
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 16,
  },
  aboutFeatures: {
    gap: 12,
  },
  aboutFeature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  aboutFeatureText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
});
