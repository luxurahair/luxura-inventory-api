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
  Image,
  Platform,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';
const SCREEN_WIDTH = Dimensions.get('window').width;
const CARD_WIDTH = Math.floor((SCREEN_WIDTH - 48) / 2);
const IMAGE_SIZE = CARD_WIDTH;

interface Product {
  id: number | string;
  name: string;
  price: number;
  images: string[];
  quantity?: number;
  sku?: string;
  in_stock?: boolean;
  category?: string;
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

  const renderProductCard = ({ item: product }: { item: Product }) => (
    <TouchableOpacity
      onPress={() => router.push(`/product/${product.id}`)}
      activeOpacity={0.8}
      style={styles.card}
    >
      <View style={styles.imageContainer}>
        <Image
          source={{ uri: product.images?.[0] }}
          style={styles.productImage}
          resizeMode="cover"
        />
        {!product.in_stock && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>Épuisé</Text>
          </View>
        )}
      </View>
      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={2}>{product.name}</Text>
        {product.sku && <Text style={styles.sku}>{product.sku}</Text>}
        <Text style={styles.price}>{product.price?.toFixed(2)} $</Text>
      </View>
    </TouchableOpacity>
  );

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
    width: CARD_WIDTH,
    maxWidth: CARD_WIDTH,
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
    overflow: 'hidden',
  },
  imageContainer: {
    width: CARD_WIDTH,
    height: CARD_WIDTH,
    maxWidth: CARD_WIDTH,
    maxHeight: CARD_WIDTH,
    backgroundColor: '#222',
    overflow: 'hidden',
  },
  productImage: {
    width: CARD_WIDTH,
    height: CARD_WIDTH,
    maxWidth: CARD_WIDTH,
    maxHeight: CARD_WIDTH,
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
});
