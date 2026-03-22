import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
  FlatList,
  Platform,
} from 'react-native';
import { Image } from 'expo-image';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';

// Use fixed width for consistent layout on web and mobile
const getCardWidth = () => {
  const screenWidth = Dimensions.get('window').width;
  // Cap the card width for larger screens
  const maxContainerWidth = Math.min(screenWidth, 500);
  return Math.floor((maxContainerWidth - 48) / 2);
};

interface Product {
  id: number | string;
  name: string;
  price: number;
  images: string[];
  quantity?: number;
  total_quantity?: number;
  sku?: string;
  in_stock?: boolean;
  category?: string;
  variant_count?: number;
}

interface Category {
  id: string;
  name: string;
}

export default function CatalogueScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const insets = useSafeAreaInsets();

  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(
    params.category as string || null
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [productsRes, categoriesRes] = await Promise.all([
        axios.get(`${API_URL}/api/products`, {
          params: {
            category: selectedCategory || undefined,
            search: searchQuery || undefined,
          },
        }),
        axios.get(`${API_URL}/api/categories`),
      ]);
      setProducts((productsRes.data || []).slice(0, 50));
      setCategories(categoriesRes.data || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchData();
  }, [selectedCategory, searchQuery]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const CARD_WIDTH = getCardWidth();
  
  const renderProductCard = ({ item: product }: { item: Product }) => {
    const stockQty = product.total_quantity || product.quantity || 0;
    const isLowStock = stockQty > 0 && stockQty <= 5;
    
    return (
      <TouchableOpacity
        onPress={() => router.push(`/product/${product.id}`)}
        activeOpacity={0.8}
        style={[styles.card, { width: CARD_WIDTH }]}
      >
        <View style={[styles.imageContainer, { width: CARD_WIDTH, height: CARD_WIDTH }]}>
          <Image
            source={{ uri: product.images?.[0] }}
            style={{ width: CARD_WIDTH, height: CARD_WIDTH }}
            contentFit="cover"
          />
          {!product.in_stock && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>Épuisé</Text>
            </View>
          )}
          {product.in_stock && isLowStock && (
            <View style={styles.lowStockBadge}>
              <Text style={styles.lowStockBadgeText}>Stock limité</Text>
            </View>
          )}
          {product.variant_count && product.variant_count > 0 && (
            <View style={styles.variantBadge}>
              <Text style={styles.variantBadgeText}>{product.variant_count} options</Text>
            </View>
          )}
        </View>
        <View style={styles.info}>
          <Text style={styles.name} numberOfLines={2}>{product.name}</Text>
          <View style={styles.stockRow}>
            {product.in_stock ? (
              <View style={styles.stockIndicator}>
                <View style={[styles.stockDot, isLowStock ? styles.stockDotLow : styles.stockDotOk]} />
                <Text style={[styles.stockText, isLowStock ? styles.stockTextLow : styles.stockTextOk]}>
                  {stockQty > 0 ? `${stockQty} en stock` : 'En stock'}
                </Text>
              </View>
            ) : (
              <View style={styles.stockIndicator}>
                <View style={[styles.stockDot, styles.stockDotOut]} />
                <Text style={[styles.stockText, styles.stockTextOut]}>Épuisé</Text>
              </View>
            )}
          </View>
          <Text style={styles.price}>{product.price?.toFixed(2)} $</Text>
        </View>
      </TouchableOpacity>
    );
  };

  const renderHeader = () => (
    <>
      <View style={styles.searchBox}>
        <Ionicons name="search" size={18} color="#666" />
        <TextInput
          style={styles.searchInput}
          placeholder="Rechercher..."
          placeholderTextColor="#666"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false} 
        style={styles.cats}
        contentContainerStyle={{ paddingHorizontal: 16 }}
      >
        <TouchableOpacity
          style={[styles.cat, !selectedCategory && styles.catActive]}
          onPress={() => setSelectedCategory(null)}
        >
          <Text style={[styles.catText, !selectedCategory && styles.catTextActive]}>Tous</Text>
        </TouchableOpacity>
        {categories.map((c) => (
          <TouchableOpacity
            key={c.id}
            style={[styles.cat, selectedCategory === c.id && styles.catActive]}
            onPress={() => setSelectedCategory(c.id)}
          >
            <Text style={[styles.catText, selectedCategory === c.id && styles.catTextActive]}>{c.name}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <Text style={styles.count}>{products.length} produits</Text>
    </>
  );

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <Text style={styles.title}>Catalogue</Text>
        <TouchableOpacity onPress={() => router.push('/cart')}>
          <Ionicons name="bag-outline" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {loading ? (
        <>
          {renderHeader()}
          <View style={styles.loading}>
            <ActivityIndicator size="large" color="#c9a050" />
          </View>
        </>
      ) : (
        <FlatList
          data={products}
          renderItem={renderProductCard}
          keyExtractor={(item) => String(item.id)}
          numColumns={2}
          columnWrapperStyle={styles.row}
          contentContainerStyle={styles.listContent}
          ListHeaderComponent={renderHeader}
          refreshControl={
            <RefreshControl 
              refreshing={refreshing} 
              onRefresh={onRefresh} 
              tintColor="#c9a050" 
            />
          }
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#0c0c0c' 
  },
  header: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    paddingHorizontal: 16, 
    paddingBottom: 12,
    zIndex: 10,
  },
  title: { 
    color: '#fff', 
    fontSize: 26, 
    fontWeight: '800' 
  },
  searchBox: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    backgroundColor: '#1a1a1a', 
    borderRadius: 10, 
    marginHorizontal: 16, 
    paddingHorizontal: 12, 
    paddingVertical: 10, 
    marginBottom: 10 
  },
  searchInput: { 
    flex: 1, 
    color: '#fff', 
    fontSize: 15, 
    marginLeft: 8 
  },
  cats: { 
    maxHeight: 40, 
    marginBottom: 8,
  },
  cat: { 
    paddingHorizontal: 14, 
    paddingVertical: 8, 
    borderRadius: 16, 
    backgroundColor: '#1a1a1a', 
    marginRight: 8 
  },
  catActive: { 
    backgroundColor: '#c9a050' 
  },
  catText: { 
    color: '#fff', 
    fontSize: 13 
  },
  catTextActive: { 
    color: '#000' 
  },
  count: { 
    color: '#666', 
    fontSize: 11, 
    paddingHorizontal: 16, 
    marginBottom: 8 
  },
  loading: { 
    flex: 1, 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 100,
  },
  row: {
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  card: {
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
    overflow: 'hidden',
  },
  imageContainer: {
    backgroundColor: '#222',
    overflow: 'hidden',
  },
  productImage: {
    // Dynamic sizing applied inline
  },
  badge: { 
    position: 'absolute', 
    top: 6, 
    right: 6, 
    backgroundColor: '#f44', 
    paddingHorizontal: 6, 
    paddingVertical: 2, 
    borderRadius: 4 
  },
  badgeText: { 
    color: '#fff', 
    fontSize: 9, 
    fontWeight: '600' 
  },
  info: { 
    padding: 8 
  },
  name: { 
    color: '#fff', 
    fontSize: 11, 
    fontWeight: '500', 
    marginBottom: 2, 
    lineHeight: 14 
  },
  sku: { 
    color: '#c9a050', 
    fontSize: 9, 
    marginBottom: 4 
  },
  price: { 
    color: '#c9a050', 
    fontSize: 13, 
    fontWeight: '700' 
  },
  variantBadge: {
    position: 'absolute',
    bottom: 6,
    left: 6,
    backgroundColor: 'rgba(201, 160, 80, 0.9)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  variantBadgeText: {
    color: '#000',
    fontSize: 9,
    fontWeight: '600',
  },
  lowStockBadge: {
    position: 'absolute',
    top: 6,
    right: 6,
    backgroundColor: '#f5a623',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  lowStockBadgeText: {
    color: '#000',
    fontSize: 9,
    fontWeight: '600',
  },
  stockRow: {
    marginTop: 2,
    marginBottom: 4,
  },
  stockIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stockDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 4,
  },
  stockDotOk: {
    backgroundColor: '#4CAF50',
  },
  stockDotLow: {
    backgroundColor: '#f5a623',
  },
  stockDotOut: {
    backgroundColor: '#f44336',
  },
  stockText: {
    fontSize: 9,
    fontWeight: '500',
  },
  stockTextOk: {
    color: '#4CAF50',
  },
  stockTextLow: {
    color: '#f5a623',
  },
  stockTextOut: {
    color: '#f44336',
  },
});
