/**
 * Luxura Marketing Dashboard - Version Améliorée
 * Dashboard complet avec templates prêts à l'emploi et plan hebdomadaire
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Linking,
  Modal,
  Share,
  Clipboard,
  Platform,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';

// Types
interface AdJob {
  job_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  input: {
    offer_type: string;
    product_name: string;
    hook: string;
    cta: string;
    landing_url: string;
  };
  copy?: {
    primary_text: string;
    headline: string;
  };
  story_video?: {
    status: string;
    video_url?: string;
  };
  feed_video?: {
    status: string;
    video_url?: string;
  };
  error?: string;
}

interface CaptionTemplate {
  id: string;
  category: string;
  title: string;
  caption: string;
  photo_suggestion: string;
  hashtags: string[];
}

interface WeeklyPost {
  date: string;
  day_name: string;
  category: string;
  title: string;
  photo_suggestion: string;
  caption: string;
  hashtags: string[];
}

// Tab type
type TabType = 'jobs' | 'templates' | 'weekly';

export default function MarketingDashboard() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  
  // Active tab
  const [activeTab, setActiveTab] = useState<TabType>('templates');
  
  // Jobs state
  const [jobs, setJobs] = useState<AdJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  
  // Templates state
  const [templates, setTemplates] = useState<CaptionTemplate[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<CaptionTemplate | null>(null);
  
  // Weekly plan state
  const [weeklyPlan, setWeeklyPlan] = useState<WeeklyPost[]>([]);
  const [loadingWeekly, setLoadingWeekly] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    offer_type: 'direct_sale',
    product_name: 'Rallonges premium Luxura',
    hook: 'Importateur direct de rallonges capillaires premium',
    proof: 'Qualité salon, rendu naturel, texture riche',
    cta: 'Commander maintenant',
    landing_url: 'https://www.luxuradistribution.com/',
  });

  // Charger les jobs
  const loadJobs = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/marketing/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error('Erreur chargement jobs:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Charger les templates
  const loadTemplates = useCallback(async () => {
    setLoadingTemplates(true);
    try {
      const response = await axios.get(`${API_URL}/api/marketing/templates/ready-captions`);
      if (response.data.success) {
        setTemplates(response.data.captions);
      }
    } catch (error) {
      console.error('Erreur chargement templates:', error);
    } finally {
      setLoadingTemplates(false);
    }
  }, []);

  // Charger le plan hebdomadaire
  const loadWeeklyPlan = useCallback(async () => {
    setLoadingWeekly(true);
    try {
      const response = await axios.get(`${API_URL}/api/marketing/templates/weekly-plan`);
      if (response.data.success) {
        setWeeklyPlan(response.data.plan);
      }
    } catch (error) {
      console.error('Erreur chargement plan:', error);
    } finally {
      setLoadingWeekly(false);
    }
  }, []);

  useEffect(() => {
    loadJobs();
    loadTemplates();
    loadWeeklyPlan();
    // Auto-refresh toutes les 60 secondes
    const interval = setInterval(loadJobs, 60000);
    return () => clearInterval(interval);
  }, [loadJobs, loadTemplates, loadWeeklyPlan]);

  const onRefresh = () => {
    setRefreshing(true);
    loadJobs();
    loadTemplates();
    loadWeeklyPlan();
  };

  // Copier le texte
  const copyToClipboard = async (text: string, label: string = 'Texte') => {
    try {
      if (Platform.OS === 'web') {
        await navigator.clipboard.writeText(text);
      } else {
        Clipboard.setString(text);
      }
      Alert.alert('Copié!', `${label} copié dans le presse-papier`);
    } catch (error) {
      Alert.alert('Erreur', 'Impossible de copier');
    }
  };

  // Partager
  const shareContent = async (title: string, message: string) => {
    try {
      await Share.share({
        title,
        message,
      });
    } catch (error) {
      console.error('Erreur partage:', error);
    }
  };

  // Créer un nouveau job
  const createJob = async () => {
    setCreating(true);
    try {
      const response = await axios.post(`${API_URL}/api/marketing/jobs`, formData);
      if (response.data.success) {
        Alert.alert('Succès', `Job créé: ${response.data.job_id}`);
        setShowCreateModal(false);
        loadJobs();
      }
    } catch (error: any) {
      Alert.alert('Erreur', error.response?.data?.detail || 'Erreur création');
    } finally {
      setCreating(false);
    }
  };

  // Rafraîchir le status d'un job
  const refreshJobStatus = async (jobId: string) => {
    try {
      await axios.post(`${API_URL}/api/marketing/jobs/${jobId}/refresh-status`);
      loadJobs();
    } catch (error) {
      console.error('Erreur refresh:', error);
    }
  };

  // Approuver un job
  const approveJob = async (jobId: string) => {
    try {
      const response = await axios.post(`${API_URL}/api/marketing/jobs/${jobId}/approve`);
      if (response.data.success) {
        Alert.alert('Succès', 'Job approuvé!');
        loadJobs();
      }
    } catch (error: any) {
      Alert.alert('Erreur', error.response?.data?.detail || 'Erreur approbation');
    }
  };

  // Ouvrir une vidéo
  const openVideo = (url: string) => {
    Linking.openURL(url);
  };

  // Status badge colors
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return '#4CAF50';
      case 'generating': return '#FF9800';
      case 'published': return '#2196F3';
      case 'active': return '#8BC34A';
      case 'failed': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ready': return 'Prêt';
      case 'generating': return 'En cours...';
      case 'published': return 'Publié';
      case 'active': return 'Actif';
      case 'failed': return 'Échec';
      case 'draft': return 'Brouillon';
      default: return status;
    }
  };

  // Category colors
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'product': return '#c9a050';
      case 'educational': return '#4CAF50';
      case 'b2b_salon': return '#2196F3';
      case 'promo': return '#F44336';
      case 'local_trust': return '#9C27B0';
      default: return '#888';
    }
  };

  const getCategoryEmoji = (category: string) => {
    switch (category) {
      case 'product': return '✨';
      case 'educational': return '📚';
      case 'b2b_salon': return '💼';
      case 'promo': return '🔥';
      case 'local_trust': return '🍁';
      default: return '📝';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'product': return 'Produit';
      case 'educational': return 'Éducatif';
      case 'b2b_salon': return 'B2B Salon';
      case 'promo': return 'Promo';
      case 'local_trust': return 'Local';
      default: return category;
    }
  };

  // Render template card
  const renderTemplateCard = (template: CaptionTemplate) => (
    <TouchableOpacity 
      key={template.id} 
      style={styles.templateCard}
      onPress={() => setSelectedTemplate(template)}
    >
      <View style={styles.templateHeader}>
        <View style={[styles.categoryBadge, { backgroundColor: getCategoryColor(template.category) }]}>
          <Text style={styles.categoryText}>
            {getCategoryEmoji(template.category)} {getCategoryLabel(template.category)}
          </Text>
        </View>
      </View>
      <Text style={styles.templateTitle}>{template.title}</Text>
      <Text style={styles.templatePreview} numberOfLines={3}>
        {template.caption.substring(0, 150)}...
      </Text>
      <View style={styles.templateActions}>
        <TouchableOpacity 
          style={styles.quickAction}
          onPress={() => copyToClipboard(template.caption, 'Légende')}
        >
          <Ionicons name="copy-outline" size={18} color="#c9a050" />
          <Text style={styles.quickActionText}>Copier</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.quickAction}
          onPress={() => shareContent(template.title, template.caption)}
        >
          <Ionicons name="share-outline" size={18} color="#c9a050" />
          <Text style={styles.quickActionText}>Partager</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  // Render weekly post card
  const renderWeeklyCard = (post: WeeklyPost, index: number) => (
    <View key={`${post.date}-${index}`} style={styles.weeklyCard}>
      <View style={styles.weeklyHeader}>
        <View style={styles.weeklyDate}>
          <Text style={styles.weeklyDay}>{post.day_name}</Text>
          <Text style={styles.weeklyDateText}>{post.date}</Text>
        </View>
        <View style={[styles.categoryBadge, { backgroundColor: getCategoryColor(post.category) }]}>
          <Text style={styles.categoryText}>
            {getCategoryEmoji(post.category)} {getCategoryLabel(post.category)}
          </Text>
        </View>
      </View>
      <Text style={styles.weeklyTitle}>{post.title}</Text>
      <View style={styles.photoSuggestion}>
        <Ionicons name="camera-outline" size={14} color="#888" />
        <Text style={styles.photoText}>{post.photo_suggestion}</Text>
      </View>
      <Text style={styles.weeklyCaption} numberOfLines={4}>
        {post.caption.substring(0, 200)}...
      </Text>
      <View style={styles.hashtagsRow}>
        {post.hashtags.slice(0, 3).map((tag, i) => (
          <Text key={i} style={styles.hashtag}>#{tag}</Text>
        ))}
      </View>
      <View style={styles.weeklyActions}>
        <TouchableOpacity 
          style={styles.actionBtn}
          onPress={() => copyToClipboard(post.caption, 'Légende')}
        >
          <Ionicons name="copy" size={16} color="#000" />
          <Text style={styles.actionBtnText}>Copier</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.actionBtn, styles.actionBtnOutline]}
          onPress={() => shareContent(post.title, post.caption)}
        >
          <Ionicons name="share-social" size={16} color="#c9a050" />
          <Text style={[styles.actionBtnText, { color: '#c9a050' }]}>Partager</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  // Render job card
  const renderJobCard = (job: AdJob) => (
    <View key={job.job_id} style={styles.jobCard}>
      <View style={styles.jobHeader}>
        <View style={styles.jobTitleRow}>
          <Text style={styles.jobTitle}>{job.input.product_name}</Text>
          <View style={[styles.statusBadge, { backgroundColor: getStatusColor(job.status) }]}>
            <Text style={styles.statusText}>{getStatusLabel(job.status)}</Text>
          </View>
        </View>
        <Text style={styles.jobType}>
          {job.input.offer_type === 'direct_sale' ? '🛒 Vente directe' : '💼 Salon affilié'}
        </Text>
      </View>

      {job.copy && (
        <View style={styles.copySection}>
          <Text style={styles.copyHeadline}>{job.copy.headline}</Text>
          <Text style={styles.copyText} numberOfLines={2}>{job.copy.primary_text}</Text>
        </View>
      )}

      <View style={styles.videosRow}>
        <TouchableOpacity 
          style={[styles.videoStatus, job.story_video?.video_url && styles.videoReady]}
          onPress={() => job.story_video?.video_url && openVideo(job.story_video.video_url)}
          disabled={!job.story_video?.video_url}
        >
          <Ionicons 
            name="phone-portrait-outline" 
            size={16} 
            color={job.story_video?.video_url ? '#4CAF50' : '#9E9E9E'} 
          />
          <Text style={styles.videoLabel}>Story 9:16</Text>
          {job.story_video?.video_url ? (
            <View style={styles.playButton}>
              <Ionicons name="play" size={14} color="#000" />
            </View>
          ) : job.story_video?.status === 'IN_PROGRESS' || job.story_video?.status === 'IN_QUEUE' ? (
            <ActivityIndicator size="small" color="#c9a050" />
          ) : null}
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.videoStatus, job.feed_video?.video_url && styles.videoReady]}
          onPress={() => job.feed_video?.video_url && openVideo(job.feed_video.video_url)}
          disabled={!job.feed_video?.video_url}
        >
          <Ionicons 
            name="tablet-portrait-outline" 
            size={16} 
            color={job.feed_video?.video_url ? '#4CAF50' : '#9E9E9E'} 
          />
          <Text style={styles.videoLabel}>Feed 4:5</Text>
          {job.feed_video?.video_url ? (
            <View style={styles.playButton}>
              <Ionicons name="play" size={14} color="#000" />
            </View>
          ) : job.feed_video?.status === 'IN_PROGRESS' || job.feed_video?.status === 'IN_QUEUE' ? (
            <ActivityIndicator size="small" color="#c9a050" />
          ) : null}
        </TouchableOpacity>
      </View>

      <View style={styles.actionsRow}>
        <TouchableOpacity 
          style={styles.actionButton}
          onPress={() => refreshJobStatus(job.job_id)}
        >
          <Ionicons name="refresh" size={18} color="#c9a050" />
          <Text style={styles.actionText}>Rafraîchir</Text>
        </TouchableOpacity>
        
        {job.status === 'ready' && (
          <TouchableOpacity 
            style={[styles.actionButton, styles.approveButton]}
            onPress={() => approveJob(job.job_id)}
          >
            <Ionicons name="checkmark-circle" size={18} color="#fff" />
            <Text style={[styles.actionText, { color: '#fff' }]}>Approuver</Text>
          </TouchableOpacity>
        )}
      </View>

      {job.error && (
        <Text style={styles.errorText}>❌ {job.error}</Text>
      )}

      <Text style={styles.timestamp}>
        Créé: {new Date(job.created_at).toLocaleString('fr-CA')}
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Marketing</Text>
        <TouchableOpacity 
          style={styles.addButton}
          onPress={() => setShowCreateModal(true)}
        >
          <Ionicons name="add-circle" size={28} color="#c9a050" />
        </TouchableOpacity>
      </View>

      {/* Tab Bar */}
      <View style={styles.tabBar}>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'templates' && styles.tabActive]}
          onPress={() => setActiveTab('templates')}
        >
          <Ionicons name="document-text" size={18} color={activeTab === 'templates' ? '#c9a050' : '#888'} />
          <Text style={[styles.tabText, activeTab === 'templates' && styles.tabTextActive]}>
            Templates
          </Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'weekly' && styles.tabActive]}
          onPress={() => setActiveTab('weekly')}
        >
          <Ionicons name="calendar" size={18} color={activeTab === 'weekly' ? '#c9a050' : '#888'} />
          <Text style={[styles.tabText, activeTab === 'weekly' && styles.tabTextActive]}>
            7 Jours
          </Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'jobs' && styles.tabActive]}
          onPress={() => setActiveTab('jobs')}
        >
          <Ionicons name="videocam" size={18} color={activeTab === 'jobs' ? '#c9a050' : '#888'} />
          <Text style={[styles.tabText, activeTab === 'jobs' && styles.tabTextActive]}>
            Vidéos IA
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#c9a050"
          />
        }
      >
        {/* Templates Tab */}
        {activeTab === 'templates' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>📋 8 Posts Prêts à l'Emploi</Text>
              <Text style={styles.sectionSubtitle}>Copiez et publiez directement sur Facebook/Instagram</Text>
            </View>
            
            {loadingTemplates ? (
              <ActivityIndicator size="large" color="#c9a050" style={{ marginTop: 40 }} />
            ) : (
              templates.map(renderTemplateCard)
            )}
          </>
        )}

        {/* Weekly Plan Tab */}
        {activeTab === 'weekly' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>📅 Plan des 7 Prochains Jours</Text>
              <Text style={styles.sectionSubtitle}>10 posts optimisés pour votre calendrier</Text>
            </View>
            
            {loadingWeekly ? (
              <ActivityIndicator size="large" color="#c9a050" style={{ marginTop: 40 }} />
            ) : (
              weeklyPlan.map((post, index) => renderWeeklyCard(post, index))
            )}
          </>
        )}

        {/* Jobs Tab */}
        {activeTab === 'jobs' && (
          <>
            {/* Stats */}
            <View style={styles.statsRow}>
              <View style={styles.statBox}>
                <Text style={styles.statNumber}>{jobs.length}</Text>
                <Text style={styles.statLabel}>Total</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={[styles.statNumber, { color: '#FF9800' }]}>
                  {jobs.filter(j => j.status === 'generating').length}
                </Text>
                <Text style={styles.statLabel}>En cours</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={[styles.statNumber, { color: '#4CAF50' }]}>
                  {jobs.filter(j => j.status === 'ready').length}
                </Text>
                <Text style={styles.statLabel}>Prêts</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={[styles.statNumber, { color: '#2196F3' }]}>
                  {jobs.filter(j => j.status === 'published' || j.status === 'active').length}
                </Text>
                <Text style={styles.statLabel}>Publiés</Text>
              </View>
            </View>

            {loading ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#c9a050" />
                <Text style={styles.loadingText}>Chargement...</Text>
              </View>
            ) : jobs.length === 0 ? (
              <View style={styles.emptyState}>
                <Ionicons name="megaphone-outline" size={64} color="#333" />
                <Text style={styles.emptyTitle}>Aucune campagne vidéo</Text>
                <Text style={styles.emptyText}>Créez votre première pub vidéo IA</Text>
                <TouchableOpacity 
                  style={styles.createFirstButton}
                  onPress={() => setShowCreateModal(true)}
                >
                  <Text style={styles.createFirstText}>Créer une vidéo</Text>
                </TouchableOpacity>
              </View>
            ) : (
              jobs.map(renderJobCard)
            )}
          </>
        )}
      </ScrollView>

      {/* Template Detail Modal */}
      <Modal
        visible={!!selectedTemplate}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setSelectedTemplate(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.templateModalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{selectedTemplate?.title}</Text>
              <TouchableOpacity onPress={() => setSelectedTemplate(null)}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.templateModalBody}>
              {selectedTemplate && (
                <>
                  <View style={[styles.categoryBadge, { backgroundColor: getCategoryColor(selectedTemplate.category), alignSelf: 'flex-start', marginBottom: 16 }]}>
                    <Text style={styles.categoryText}>
                      {getCategoryEmoji(selectedTemplate.category)} {getCategoryLabel(selectedTemplate.category)}
                    </Text>
                  </View>
                  
                  <Text style={styles.modalLabel}>📸 Suggestion de photo</Text>
                  <Text style={styles.modalPhotoSuggestion}>{selectedTemplate.photo_suggestion}</Text>
                  
                  <Text style={styles.modalLabel}>📝 Légende complète</Text>
                  <View style={styles.captionBox}>
                    <Text style={styles.captionText}>{selectedTemplate.caption}</Text>
                  </View>
                  
                  <Text style={styles.modalLabel}>#️⃣ Hashtags</Text>
                  <View style={styles.hashtagsBox}>
                    {selectedTemplate.hashtags.map((tag, i) => (
                      <TouchableOpacity 
                        key={i} 
                        style={styles.hashtagChip}
                        onPress={() => copyToClipboard(`#${tag}`, 'Hashtag')}
                      >
                        <Text style={styles.hashtagChipText}>#{tag}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </>
              )}
            </ScrollView>
            
            <View style={styles.modalActions}>
              <TouchableOpacity 
                style={styles.modalActionBtn}
                onPress={() => selectedTemplate && copyToClipboard(selectedTemplate.caption, 'Légende')}
              >
                <Ionicons name="copy" size={20} color="#000" />
                <Text style={styles.modalActionText}>Copier Légende</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalActionBtn, styles.modalActionSecondary]}
                onPress={() => selectedTemplate && copyToClipboard(selectedTemplate.hashtags.map(t => `#${t}`).join(' '), 'Hashtags')}
              >
                <Ionicons name="pricetag" size={20} color="#c9a050" />
                <Text style={[styles.modalActionText, { color: '#c9a050' }]}>Copier Hashtags</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Create Job Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowCreateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Nouvelle Vidéo IA</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.formScroll}>
              <Text style={styles.label}>Type d'offre</Text>
              <View style={styles.typeSelector}>
                <TouchableOpacity
                  style={[
                    styles.typeOption,
                    formData.offer_type === 'direct_sale' && styles.typeSelected
                  ]}
                  onPress={() => setFormData({...formData, offer_type: 'direct_sale'})}
                >
                  <Text style={styles.typeText}>🛒 Vente directe</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.typeOption,
                    formData.offer_type === 'salon_affilie' && styles.typeSelected
                  ]}
                  onPress={() => setFormData({...formData, offer_type: 'salon_affilie'})}
                >
                  <Text style={styles.typeText}>💼 Salon affilié</Text>
                </TouchableOpacity>
              </View>

              <Text style={styles.label}>Nom du produit</Text>
              <TextInput
                style={styles.input}
                value={formData.product_name}
                onChangeText={(text) => setFormData({...formData, product_name: text})}
                placeholder="Ex: Rallonges premium Luxura"
                placeholderTextColor="#666"
              />

              <Text style={styles.label}>Accroche</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={formData.hook}
                onChangeText={(text) => setFormData({...formData, hook: text})}
                placeholder="L'accroche principale de la pub"
                placeholderTextColor="#666"
                multiline
              />

              <Text style={styles.label}>Preuve / Bénéfice</Text>
              <TextInput
                style={styles.input}
                value={formData.proof}
                onChangeText={(text) => setFormData({...formData, proof: text})}
                placeholder="Qualité, avantages..."
                placeholderTextColor="#666"
              />

              <Text style={styles.label}>Call-to-Action</Text>
              <TextInput
                style={styles.input}
                value={formData.cta}
                onChangeText={(text) => setFormData({...formData, cta: text})}
                placeholder="Commander maintenant"
                placeholderTextColor="#666"
              />

              <Text style={styles.label}>URL de destination</Text>
              <TextInput
                style={styles.input}
                value={formData.landing_url}
                onChangeText={(text) => setFormData({...formData, landing_url: text})}
                placeholder="https://..."
                placeholderTextColor="#666"
                keyboardType="url"
              />
            </ScrollView>

            <TouchableOpacity
              style={[styles.submitButton, creating && styles.buttonDisabled]}
              onPress={createJob}
              disabled={creating}
            >
              {creating ? (
                <ActivityIndicator color="#000" />
              ) : (
                <>
                  <Ionicons name="rocket" size={20} color="#000" />
                  <Text style={styles.submitText}>Générer la vidéo IA</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a1a',
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
  addButton: {
    padding: 4,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 8,
    paddingVertical: 8,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 8,
    gap: 6,
  },
  tabActive: {
    backgroundColor: 'rgba(201, 160, 80, 0.15)',
  },
  tabText: {
    fontSize: 13,
    color: '#888',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#c9a050',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  sectionHeader: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  // Template card styles
  templateCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  templateHeader: {
    marginBottom: 10,
  },
  categoryBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  templateTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
  },
  templatePreview: {
    fontSize: 13,
    color: '#aaa',
    lineHeight: 20,
  },
  templateActions: {
    flexDirection: 'row',
    marginTop: 12,
    gap: 16,
  },
  quickAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  quickActionText: {
    fontSize: 13,
    color: '#c9a050',
    fontWeight: '500',
  },
  // Weekly card styles
  weeklyCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  weeklyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  weeklyDate: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 8,
  },
  weeklyDay: {
    fontSize: 16,
    fontWeight: '700',
    color: '#c9a050',
  },
  weeklyDateText: {
    fontSize: 12,
    color: '#666',
  },
  weeklyTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
  },
  photoSuggestion: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
    backgroundColor: '#252525',
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
  },
  photoText: {
    fontSize: 12,
    color: '#888',
    flex: 1,
  },
  weeklyCaption: {
    fontSize: 13,
    color: '#aaa',
    lineHeight: 20,
  },
  hashtagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 10,
  },
  hashtag: {
    fontSize: 11,
    color: '#c9a050',
    backgroundColor: 'rgba(201, 160, 80, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  weeklyActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 14,
  },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#c9a050',
    paddingVertical: 10,
    borderRadius: 8,
  },
  actionBtnOutline: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#c9a050',
  },
  actionBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#000',
  },
  // Stats styles
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  statBox: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: '#c9a050',
  },
  statLabel: {
    fontSize: 11,
    color: '#888',
    marginTop: 4,
  },
  // Job card styles
  jobCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  jobHeader: {
    marginBottom: 12,
  },
  jobTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  jobTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  jobType: {
    fontSize: 13,
    color: '#888',
    marginTop: 4,
  },
  copySection: {
    backgroundColor: '#252525',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  copyHeadline: {
    fontSize: 14,
    fontWeight: '600',
    color: '#c9a050',
    marginBottom: 4,
  },
  copyText: {
    fontSize: 13,
    color: '#ccc',
  },
  videosRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  videoStatus: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#252525',
    borderRadius: 8,
    padding: 10,
  },
  videoLabel: {
    fontSize: 12,
    color: '#888',
    flex: 1,
  },
  videoReady: {
    borderColor: '#4CAF50',
    borderWidth: 1,
  },
  playButton: {
    backgroundColor: '#c9a050',
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#c9a050',
  },
  approveButton: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  actionText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#c9a050',
  },
  errorText: {
    color: '#F44336',
    fontSize: 12,
    marginTop: 8,
  },
  timestamp: {
    fontSize: 11,
    color: '#555',
    marginTop: 12,
  },
  // Loading & Empty states
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  loadingText: {
    color: '#888',
    marginTop: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: '#888',
    marginTop: 8,
  },
  createFirstButton: {
    marginTop: 24,
    backgroundColor: '#c9a050',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  createFirstText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
  },
  templateModalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '95%',
    flex: 1,
  },
  templateModalBody: {
    padding: 16,
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
    flex: 1,
  },
  modalLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#c9a050',
    marginBottom: 8,
    marginTop: 16,
  },
  modalPhotoSuggestion: {
    fontSize: 14,
    color: '#aaa',
    backgroundColor: '#252525',
    padding: 12,
    borderRadius: 8,
  },
  captionBox: {
    backgroundColor: '#252525',
    padding: 16,
    borderRadius: 12,
  },
  captionText: {
    fontSize: 14,
    color: '#fff',
    lineHeight: 22,
  },
  hashtagsBox: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  hashtagChip: {
    backgroundColor: 'rgba(201, 160, 80, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  hashtagChipText: {
    fontSize: 13,
    color: '#c9a050',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  modalActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#c9a050',
    paddingVertical: 14,
    borderRadius: 12,
  },
  modalActionSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#c9a050',
  },
  modalActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
  },
  formScroll: {
    padding: 16,
    maxHeight: 400,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#c9a050',
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    backgroundColor: '#252525',
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#333',
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  typeSelector: {
    flexDirection: 'row',
    gap: 12,
  },
  typeOption: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333',
    alignItems: 'center',
  },
  typeSelected: {
    borderColor: '#c9a050',
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
  },
  typeText: {
    fontSize: 14,
    color: '#fff',
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#c9a050',
    margin: 16,
    padding: 16,
    borderRadius: 12,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  submitText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#000',
  },
});
