import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  ActivityIndicator,
  TouchableOpacity,
  Pressable,
  useWindowDimensions,
  Share,
  Alert,
  Platform,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import RenderHtml from 'react-native-render-html';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';
const LUXURA_LOGO = 'https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/i7uo40l8_Luxura%20Distribution%20-%20OR%20-%20PNG.png';

interface BlogPost {
  id: string;
  title: string;
  content: string;
  excerpt: string;
  image?: string;
  author: string;
  created_at: string;
}

export default function BlogPostScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();

  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPost = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/blog/${id}`);
        setPost(response.data);
      } catch (error) {
        console.error('Error fetching blog post:', error);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchPost();
    }
  }, [id]);

  const handleGoBack = () => {
    try {
      if (router.canGoBack()) {
        router.back();
      } else {
        router.replace('/(tabs)/blog');
      }
    } catch (error) {
      // Fallback si erreur
      router.replace('/(tabs)/blog');
    }
  };

  const handleShare = async () => {
    if (!post) return;
    
    try {
      const shareUrl = `https://www.luxuradistribution.com/blog/${id}`;
      const result = await Share.share({
        title: post.title,
        message: Platform.select({
          ios: post.title,
          default: `${post.title}\n\n${post.excerpt}\n\nLire l'article: ${shareUrl}`,
        }),
        url: Platform.OS === 'ios' ? shareUrl : undefined,
      });
      
      if (result.action === Share.sharedAction) {
        // Article partagé avec succès
      }
    } catch (error: any) {
      Alert.alert('Erreur', 'Impossible de partager cet article.');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-CA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Styles pour le HTML rendu
  const tagsStyles = {
    body: {
      color: '#ccc',
      fontSize: 16,
      lineHeight: 26,
    },
    h1: {
      color: '#fff',
      fontSize: 28,
      fontWeight: '800',
      marginTop: 24,
      marginBottom: 16,
    },
    h2: {
      color: '#fff',
      fontSize: 22,
      fontWeight: '700',
      marginTop: 20,
      marginBottom: 12,
    },
    h3: {
      color: '#fff',
      fontSize: 18,
      fontWeight: '600',
      marginTop: 16,
      marginBottom: 10,
    },
    p: {
      color: '#ccc',
      fontSize: 16,
      lineHeight: 26,
      marginBottom: 16,
    },
    strong: {
      color: '#c9a050',
      fontWeight: '700',
    },
    em: {
      color: '#e0e0e0',
      fontStyle: 'italic',
    },
    a: {
      color: '#c9a050',
      textDecorationLine: 'underline',
    },
    ul: {
      color: '#ccc',
      marginBottom: 16,
      paddingLeft: 20,
    },
    ol: {
      color: '#ccc',
      marginBottom: 16,
      paddingLeft: 20,
    },
    li: {
      color: '#ccc',
      fontSize: 16,
      lineHeight: 26,
      marginBottom: 8,
    },
    blockquote: {
      borderLeftWidth: 4,
      borderLeftColor: '#c9a050',
      paddingLeft: 16,
      marginLeft: 0,
      marginVertical: 16,
      fontStyle: 'italic',
      color: '#aaa',
    },
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#c9a050" />
      </View>
    );
  }

  if (!post) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color="#666" />
        <Text style={styles.errorText}>Article non trouvé</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Retour</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Préparer le contenu HTML
  const htmlContent = post.content.includes('<') 
    ? post.content 
    : `<p>${post.content.split('\n\n').join('</p><p>')}</p>`;

  return (
    <View style={styles.container}>
      {/* Header avec logo */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <Pressable 
          onPress={() => {
            console.log('Back button pressed');
            if (router.canGoBack()) {
              router.back();
            } else {
              router.push('/(tabs)/blog');
            }
          }} 
          style={({ pressed }) => [
            styles.headerButton,
            pressed && styles.headerButtonPressed
          ]}
        >
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </Pressable>
        <Image source={{ uri: LUXURA_LOGO }} style={styles.logoImage} resizeMode="contain" />
        <Pressable 
          style={({ pressed }) => [
            styles.headerButton,
            pressed && styles.headerButtonPressed
          ]}
          onPress={async () => {
            console.log('Share button pressed');
            if (!post) return;
            try {
              const shareUrl = `https://www.luxuradistribution.com/blog/${id}`;
              await Share.share({
                title: post.title,
                message: `${post.title}\n\n${post.excerpt}\n\nLire: ${shareUrl}`,
                url: Platform.OS === 'ios' ? shareUrl : undefined,
              });
            } catch (error) {
              Alert.alert('Partage', 'Article copié !');
            }
          }}
        >
          <Ionicons name="share-outline" size={24} color="#fff" />
        </Pressable>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Hero Image */}
        {post.image && (
          <Image source={{ uri: post.image }} style={styles.heroImage} resizeMode="cover" />
        )}

        {/* Content */}
        <View style={styles.content}>
          <Text style={styles.title}>{post.title}</Text>
          
          <View style={styles.meta}>
            <View style={styles.authorSection}>
              <View style={styles.authorAvatar}>
                <Ionicons name="person" size={16} color="#c9a050" />
              </View>
              <Text style={styles.authorName}>{post.author}</Text>
            </View>
            <Text style={styles.date}>{formatDate(post.created_at)}</Text>
          </View>

          <View style={styles.divider} />

          {/* Render HTML content */}
          <RenderHtml
            contentWidth={width - 40}
            source={{ html: htmlContent }}
            tagsStyles={tagsStyles}
            enableExperimentalBRCollapsing={true}
            enableExperimentalMarginCollapsing={true}
          />
        </View>

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
    cursor: 'pointer',
  },
  headerButtonPressed: {
    backgroundColor: 'rgba(201,160,80,0.3)',
    transform: [{ scale: 0.95 }],
  },
  scrollView: {
    flex: 1,
  },
  heroImage: {
    width: '100%',
    height: 300,
  },
  content: {
    padding: 20,
  },
  title: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '800',
    lineHeight: 36,
    marginBottom: 16,
  },
  meta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  authorSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  authorAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  authorName: {
    color: '#c9a050',
    fontSize: 14,
    fontWeight: '500',
  },
  date: {
    color: '#666',
    fontSize: 14,
  },
  divider: {
    height: 1,
    backgroundColor: '#2a2a2a',
    marginBottom: 20,
  },
});
