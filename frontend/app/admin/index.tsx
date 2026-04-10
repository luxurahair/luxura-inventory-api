import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

const ADMIN_TOOLS = [
  {
    id: 'color-engine',
    title: 'Color Engine PRO',
    description: 'Créer des images produits avec watermarks',
    icon: 'color-palette',
    color: '#9333ea',
    route: '/admin/color-engine',
  },
  {
    id: 'images',
    title: 'Répertoire Images',
    description: 'Gérer les images par catégorie',
    icon: 'images',
    color: '#3b82f6',
    route: '/admin/images',
  },
  {
    id: 'blog',
    title: 'Gestion Blog',
    description: 'Créer et gérer les articles',
    icon: 'document-text',
    color: '#22c55e',
    route: '/admin/blog',
  },
  {
    id: 'inventory',
    title: 'Inventaire',
    description: 'Voir les stocks et produits',
    icon: 'cube',
    color: '#f59e0b',
    route: '/admin/inventory',
  },
];

export default function AdminIndex() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.title}>Administration</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Welcome */}
        <View style={styles.welcomeSection}>
          <Text style={styles.welcomeTitle}>Dashboard Admin</Text>
          <Text style={styles.welcomeSubtitle}>
            Gérez votre boutique Luxura Distribution
          </Text>
        </View>

        {/* Tools Grid */}
        <View style={styles.toolsGrid}>
          {ADMIN_TOOLS.map((tool) => (
            <TouchableOpacity
              key={tool.id}
              style={styles.toolCard}
              onPress={() => router.push(tool.route as any)}
              activeOpacity={0.8}
            >
              <View style={[styles.toolIcon, { backgroundColor: tool.color }]}>
                <Ionicons name={tool.icon as any} size={28} color="#fff" />
              </View>
              <Text style={styles.toolTitle}>{tool.title}</Text>
              <Text style={styles.toolDescription}>{tool.description}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Quick Stats */}
        <View style={styles.statsSection}>
          <Text style={styles.sectionTitle}>Statistiques</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>67</Text>
              <Text style={styles.statLabel}>Produits</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>4</Text>
              <Text style={styles.statLabel}>Catégories</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>25</Text>
              <Text style={styles.statLabel}>Couleurs</Text>
            </View>
          </View>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
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
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#c9a050',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  welcomeSection: {
    marginBottom: 24,
  },
  welcomeTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  welcomeSubtitle: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  toolsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  toolCard: {
    width: '48%',
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  toolIcon: {
    width: 50,
    height: 50,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  toolTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  toolDescription: {
    fontSize: 12,
    color: '#888',
  },
  statsSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#c9a050',
  },
  statLabel: {
    fontSize: 12,
    color: '#888',
    marginTop: 4,
  },
});
