/**
 * Luxura Marketing Dashboard
 * Mini dashboard pour gérer les campagnes publicitaires automatisées
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
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || '';

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

export default function MarketingDashboard() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  
  const [jobs, setJobs] = useState<AdJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  
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

  useEffect(() => {
    loadJobs();
    // Auto-refresh toutes les 30 secondes
    const interval = setInterval(loadJobs, 30000);
    return () => clearInterval(interval);
  }, [loadJobs]);

  const onRefresh = () => {
    setRefreshing(true);
    loadJobs();
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

  // Status badge
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

  // Render job card
  const renderJobCard = (job: AdJob) => (
    <View key={job.job_id} style={styles.jobCard}>
      {/* Header */}
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

      {/* Copy preview */}
      {job.copy && (
        <View style={styles.copySection}>
          <Text style={styles.copyHeadline}>{job.copy.headline}</Text>
          <Text style={styles.copyText} numberOfLines={2}>{job.copy.primary_text}</Text>
        </View>
      )}

      {/* Videos status */}
      <View style={styles.videosRow}>
        <TouchableOpacity 
          style={[
            styles.videoStatus,
            job.story_video?.video_url && styles.videoReady
          ]}
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
          style={[
            styles.videoStatus,
            job.feed_video?.video_url && styles.videoReady
          ]}
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

      {/* Actions */}
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

      {/* Error */}
      {job.error && (
        <Text style={styles.errorText}>❌ {job.error}</Text>
      )}

      {/* Timestamp */}
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
        <Text style={styles.headerTitle}>Marketing Automation</Text>
        <TouchableOpacity 
          style={styles.addButton}
          onPress={() => setShowCreateModal(true)}
        >
          <Ionicons name="add-circle" size={28} color="#c9a050" />
        </TouchableOpacity>
      </View>

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

      {/* Jobs list */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#c9a050" />
          <Text style={styles.loadingText}>Chargement...</Text>
        </View>
      ) : (
        <ScrollView
          style={styles.jobsList}
          contentContainerStyle={styles.jobsContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor="#c9a050"
            />
          }
        >
          {jobs.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="megaphone-outline" size={64} color="#333" />
              <Text style={styles.emptyTitle}>Aucune campagne</Text>
              <Text style={styles.emptyText}>Créez votre première pub automatisée</Text>
              <TouchableOpacity 
                style={styles.createFirstButton}
                onPress={() => setShowCreateModal(true)}
              >
                <Text style={styles.createFirstText}>Créer une pub</Text>
              </TouchableOpacity>
            </View>
          ) : (
            jobs.map(renderJobCard)
          )}
        </ScrollView>
      )}

      {/* Create Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowCreateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Nouvelle Publicité</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.formScroll}>
              {/* Type d'offre */}
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

              {/* Produit */}
              <Text style={styles.label}>Nom du produit</Text>
              <TextInput
                style={styles.input}
                value={formData.product_name}
                onChangeText={(text) => setFormData({...formData, product_name: text})}
                placeholder="Ex: Rallonges premium Luxura"
                placeholderTextColor="#666"
              />

              {/* Hook */}
              <Text style={styles.label}>Accroche</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={formData.hook}
                onChangeText={(text) => setFormData({...formData, hook: text})}
                placeholder="L'accroche principale de la pub"
                placeholderTextColor="#666"
                multiline
              />

              {/* Preuve */}
              <Text style={styles.label}>Preuve / Bénéfice</Text>
              <TextInput
                style={styles.input}
                value={formData.proof}
                onChangeText={(text) => setFormData({...formData, proof: text})}
                placeholder="Qualité, avantages..."
                placeholderTextColor="#666"
              />

              {/* CTA */}
              <Text style={styles.label}>Call-to-Action</Text>
              <TextInput
                style={styles.input}
                value={formData.cta}
                onChangeText={(text) => setFormData({...formData, cta: text})}
                placeholder="Commander maintenant"
                placeholderTextColor="#666"
              />

              {/* URL */}
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

            {/* Submit */}
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
                  <Text style={styles.submitText}>Générer la pub</Text>
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
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingVertical: 16,
    gap: 8,
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#888',
    marginTop: 12,
  },
  jobsList: {
    flex: 1,
  },
  jobsContent: {
    padding: 16,
    gap: 16,
  },
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
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
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
