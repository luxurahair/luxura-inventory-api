import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';
const LUXURA_LOGO = 'https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/i7uo40l8_Luxura%20Distribution%20-%20OR%20-%20PNG.png';

interface BlogPost {
  id: string;
  title: string;
  excerpt: string;
  image?: string;
  author: string;
  created_at: string;
}

export default function BlogScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchPosts = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/blog`);
      setPosts(response.data);
    } catch (error) {
      console.error('Error fetching blog posts:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchPosts();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-CA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Helper pour obtenir l'URL complète de l'image
  const getImageUrl = (imageUrl: string | undefined): string | undefined => {
    if (!imageUrl) return undefined;
    // Si l'URL commence par /api/, c'est une URL relative - ajouter le backend URL
    if (imageUrl.startsWith('/api/')) {
      return `${API_URL}${imageUrl}`;
    }
    // Sinon retourner l'URL telle quelle (Unsplash, etc.)
    return imageUrl;
  };

  const renderPost = ({ item }: { item: BlogPost }) => (
    <TouchableOpacity
      style={styles.postCard}
      onPress={() => router.push(`/blog/${item.id}`)}
      activeOpacity={0.8}
    >
      {item.image && (
        <Image source={{ uri: getImageUrl(item.image) }} style={styles.postImage} resizeMode="cover" />
      )}
      <View style={styles.postContent}>
        <Text style={styles.postTitle}>{item.title}</Text>
        <Text style={styles.postExcerpt} numberOfLines={2}>{item.excerpt}</Text>
        <View style={styles.postMeta}>
          <Text style={styles.postAuthor}>{item.author}</Text>
          <Text style={styles.postDate}>{formatDate(item.created_at)}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <View style={styles.headerPlaceholder} />
        <Image source={{ uri: LUXURA_LOGO }} style={styles.logoImage} resizeMode="contain" />
        <View style={styles.headerPlaceholder} />
      </View>

      {/* Blog Posts */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#c9a050" />
        </View>
      ) : (
        <FlatList
          data={posts}
          renderItem={renderPost}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.postsList}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c9a050" />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="newspaper-outline" size={48} color="#666" />
              <Text style={styles.emptyText}>Aucun article disponible</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  headerPlaceholder: {
    width: 44,
  },
  logoImage: {
    width: 120,
    height: 32,
  },
  title: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '800',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  postsList: {
    paddingHorizontal: 16,
    paddingBottom: 100,
  },
  postCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    marginBottom: 16,
    overflow: 'hidden',
  },
  postImage: {
    width: '100%',
    height: 180,
  },
  postContent: {
    padding: 16,
  },
  postTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
  },
  postExcerpt: {
    color: '#aaa',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  postMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  postAuthor: {
    color: '#c9a050',
    fontSize: 13,
    fontWeight: '500',
  },
  postDate: {
    color: '#666',
    fontSize: 13,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    color: '#666',
    fontSize: 16,
    marginTop: 12,
  },
});
