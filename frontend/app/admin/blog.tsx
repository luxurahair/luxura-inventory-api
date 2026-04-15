import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  RefreshControl,
  Modal,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface BlogPost {
  id: string | number;
  title: string;
  content: string;
  excerpt: string;
  image?: string;
  author: string;
  created_at: string;
  wix_post_id?: string;
  published_to_wix?: boolean;
  auto_generated?: boolean;
}

interface Topic {
  topic: string;
  keywords: string[];
  focus_product: string | null;
}

interface TopicsData {
  total_topics: number;
  categories: {
    [key: string]: Topic[];
  };
}

export default function AdminBlogScreen() {
  const router = useRouter();
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [topics, setTopics] = useState<TopicsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [showTopicsModal, setShowTopicsModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'posts' | 'generate'>('posts');

  const fetchPosts = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/blog`);
      setPosts(response.data);
    } catch (error) {
      console.error('Error fetching posts:', error);
    }
  };

  const fetchTopics = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/blog/topics`);
      setTopics(response.data);
    } catch (error) {
      console.error('Error fetching topics:', error);
    }
  };

  const loadData = async () => {
    setLoading(true);
    await Promise.all([fetchPosts(), fetchTopics()]);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchPosts(), fetchTopics()]);
    setRefreshing(false);
  };

  const generateArticle = async (topic: Topic) => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API_URL}/api/blog/generate`, {
        topic: topic.topic,
        keywords: topic.keywords,
        focus_product: topic.focus_product,
      });
      
      Alert.alert(
        'Article généré !',
        `L'article "${response.data.title}" a été créé avec succès.`,
        [{ text: 'OK', onPress: () => fetchPosts() }]
      );
      setShowTopicsModal(false);
    } catch (error: any) {
      console.error('Error generating article:', error);
      Alert.alert(
        'Erreur',
        error.response?.data?.detail || 'Impossible de générer l\'article.'
      );
    } finally {
      setGenerating(false);
    }
  };

  const deletePost = async (postId: string | number) => {
    Alert.alert(
      'Supprimer l\'article',
      'Êtes-vous sûr de vouloir supprimer cet article ?',
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(`${API_URL}/api/blog/${postId}`);
              fetchPosts();
            } catch (error) {
              Alert.alert('Erreur', 'Impossible de supprimer l\'article.');
            }
          },
        },
      ]
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-CA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const renderPostCard = (post: BlogPost) => (
    <View key={post.id} style={styles.postCard}>
      <View style={styles.postHeader}>
        <View style={styles.postBadges}>
          {post.auto_generated && (
            <View style={[styles.badge, styles.aiBadge]}>
              <Ionicons name="sparkles" size={12} color="#fff" />
              <Text style={styles.badgeText}>IA</Text>
            </View>
          )}
          {post.published_to_wix && (
            <View style={[styles.badge, styles.wixBadge]}>
              <Ionicons name="globe" size={12} color="#fff" />
              <Text style={styles.badgeText}>Wix</Text>
            </View>
          )}
        </View>
        <TouchableOpacity onPress={() => deletePost(post.id)} style={styles.deleteButton}>
          <Ionicons name="trash-outline" size={20} color="#ef4444" />
        </TouchableOpacity>
      </View>
      
      <Text style={styles.postTitle} numberOfLines={2}>{post.title}</Text>
      <Text style={styles.postExcerpt} numberOfLines={2}>{post.excerpt}</Text>
      
      <View style={styles.postFooter}>
        <Text style={styles.postDate}>{formatDate(post.created_at)}</Text>
        <TouchableOpacity 
          style={styles.viewButton}
          onPress={() => router.push(`/blog/${post.id}`)}
        >
          <Text style={styles.viewButtonText}>Voir</Text>
          <Ionicons name="arrow-forward" size={14} color="#c9a050" />
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderTopicCard = (topic: Topic, category: string) => (
    <TouchableOpacity
      key={topic.topic}
      style={styles.topicCard}
      onPress={() => {
        setSelectedTopic(topic);
        Alert.alert(
          'Générer un article',
          `Voulez-vous générer un article sur "${topic.topic}" ?`,
          [
            { text: 'Annuler', style: 'cancel' },
            { text: 'Générer', onPress: () => generateArticle(topic) },
          ]
        );
      }}
      disabled={generating}
    >
      <View style={styles.topicContent}>
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryText}>{category.replace('_', ' ')}</Text>
        </View>
        <Text style={styles.topicTitle}>{topic.topic}</Text>
        {topic.focus_product && (
          <Text style={styles.topicProduct}>Produit: {topic.focus_product}</Text>
        )}
        <View style={styles.keywordsContainer}>
          {topic.keywords.slice(0, 3).map((keyword, idx) => (
            <View key={idx} style={styles.keywordBadge}>
              <Text style={styles.keywordText}>{keyword}</Text>
            </View>
          ))}
        </View>
      </View>
      <Ionicons name="add-circle" size={24} color="#c9a050" />
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#c9a050" />
          <Text style={styles.loadingText}>Chargement...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Gestion Blog</Text>
        <TouchableOpacity onPress={onRefresh} style={styles.refreshButton}>
          <Ionicons name="refresh" size={24} color="#c9a050" />
        </TouchableOpacity>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'posts' && styles.activeTab]}
          onPress={() => setActiveTab('posts')}
        >
          <Ionicons 
            name="document-text" 
            size={18} 
            color={activeTab === 'posts' ? '#c9a050' : '#666'} 
          />
          <Text style={[styles.tabText, activeTab === 'posts' && styles.activeTabText]}>
            Articles ({posts.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'generate' && styles.activeTab]}
          onPress={() => setActiveTab('generate')}
        >
          <Ionicons 
            name="sparkles" 
            size={18} 
            color={activeTab === 'generate' ? '#c9a050' : '#666'} 
          />
          <Text style={[styles.tabText, activeTab === 'generate' && styles.activeTabText]}>
            Générer IA
          </Text>
        </TouchableOpacity>
      </View>

      {generating && (
        <View style={styles.generatingBanner}>
          <ActivityIndicator size="small" color="#000" />
          <Text style={styles.generatingText}>Génération de l'article en cours...</Text>
        </View>
      )}

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c9a050" />
        }
      >
        {activeTab === 'posts' ? (
          <>
            {posts.length === 0 ? (
              <View style={styles.emptyContainer}>
                <Ionicons name="newspaper-outline" size={48} color="#666" />
                <Text style={styles.emptyText}>Aucun article</Text>
                <Text style={styles.emptySubtext}>Utilisez l'onglet "Générer IA" pour créer des articles</Text>
              </View>
            ) : (
              posts.map(renderPostCard)
            )}
          </>
        ) : (
          <>
            <View style={styles.generateHeader}>
              <Text style={styles.generateTitle}>Sujets suggérés</Text>
              <Text style={styles.generateSubtitle}>
                {topics?.total_topics || 0} sujets disponibles
              </Text>
            </View>
            
            {topics && Object.entries(topics.categories).map(([category, categoryTopics]) => (
              <View key={category}>
                <Text style={styles.categoryHeader}>
                  {category.replace('_', ' ').toUpperCase()}
                </Text>
                {categoryTopics.map((topic) => renderTopicCard(topic, category))}
              </View>
            ))}
          </>
        )}
        
        <View style={{ height: 100 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#888',
    marginTop: 12,
    fontSize: 14,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#c9a050',
  },
  refreshButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333',
  },
  activeTab: {
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
    borderColor: '#c9a050',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#666',
  },
  activeTabText: {
    color: '#c9a050',
  },
  generatingBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#c9a050',
    paddingVertical: 10,
    marginHorizontal: 16,
    borderRadius: 8,
    marginBottom: 12,
  },
  generatingText: {
    color: '#000',
    fontWeight: '600',
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    color: '#666',
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
  },
  emptySubtext: {
    color: '#555',
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
  },
  postCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  postHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  postBadges: {
    flexDirection: 'row',
    gap: 8,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  aiBadge: {
    backgroundColor: '#9333ea',
  },
  wixBadge: {
    backgroundColor: '#3b82f6',
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
  deleteButton: {
    padding: 8,
  },
  postTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  postExcerpt: {
    color: '#888',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 12,
  },
  postFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  postDate: {
    color: '#666',
    fontSize: 12,
  },
  viewButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  viewButtonText: {
    color: '#c9a050',
    fontSize: 13,
    fontWeight: '500',
  },
  generateHeader: {
    marginBottom: 16,
  },
  generateTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
  generateSubtitle: {
    color: '#888',
    fontSize: 14,
    marginTop: 4,
  },
  categoryHeader: {
    color: '#c9a050',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    marginTop: 16,
    marginBottom: 8,
  },
  topicCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#333',
  },
  topicContent: {
    flex: 1,
  },
  categoryBadge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginBottom: 8,
  },
  categoryText: {
    color: '#c9a050',
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  topicTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 6,
  },
  topicProduct: {
    color: '#22c55e',
    fontSize: 12,
    marginBottom: 8,
  },
  keywordsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  keywordBadge: {
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  keywordText: {
    color: '#888',
    fontSize: 10,
  },
});
