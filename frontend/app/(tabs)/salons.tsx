import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface Salon {
  id: string;
  name: string;
  address: string;
  city: string;
  phone?: string;
  website?: string;
}

export default function SalonsScreen() {
  const insets = useSafeAreaInsets();
  const [salons, setSalons] = useState<Salon[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchSalons = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/salons`);
      setSalons(response.data);
    } catch (error) {
      console.error('Error fetching salons:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSalons();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchSalons();
  };

  const handleCall = (phone: string) => {
    Linking.openURL(`tel:${phone}`);
  };

  const handleWebsite = (website: string) => {
    Linking.openURL(website);
  };

  const renderSalon = ({ item }: { item: Salon }) => (
    <View style={styles.salonCard}>
      <View style={styles.salonIcon}>
        <Ionicons name="cut" size={24} color="#c9a050" />
      </View>
      <View style={styles.salonInfo}>
        <Text style={styles.salonName}>{item.name}</Text>
        <Text style={styles.salonAddress}>{item.address}</Text>
        <Text style={styles.salonCity}>{item.city}</Text>
        
        <View style={styles.salonActions}>
          {item.phone && (
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => handleCall(item.phone!)}
            >
              <Ionicons name="call" size={16} color="#c9a050" />
              <Text style={styles.actionText}>Appeler</Text>
            </TouchableOpacity>
          )}
          {item.website && (
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => handleWebsite(item.website!)}
            >
              <Ionicons name="globe" size={16} color="#c9a050" />
              <Text style={styles.actionText}>Site web</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <Text style={styles.title}>Salons Partenaires</Text>
      </View>

      {/* Info Banner */}
      <View style={styles.infoBanner}>
        <Ionicons name="information-circle" size={24} color="#c9a050" />
        <Text style={styles.infoText}>
          Plus de 30 salons partenaires au Québec avec inventaire réel et approvisionnement direct.
        </Text>
      </View>

      {/* Salons List */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#c9a050" />
        </View>
      ) : (
        <FlatList
          data={salons}
          renderItem={renderSalon}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.salonsList}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c9a050" />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="location-outline" size={48} color="#666" />
              <Text style={styles.emptyText}>Aucun salon trouvé</Text>
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
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  title: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '800',
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    gap: 12,
  },
  infoText: {
    flex: 1,
    color: '#aaa',
    fontSize: 14,
    lineHeight: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  salonsList: {
    paddingHorizontal: 16,
    paddingBottom: 100,
  },
  salonCard: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  salonIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  salonInfo: {
    flex: 1,
  },
  salonName: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  salonAddress: {
    color: '#aaa',
    fontSize: 14,
    marginBottom: 2,
  },
  salonCity: {
    color: '#c9a050',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 12,
  },
  salonActions: {
    flexDirection: 'row',
    gap: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  actionText: {
    color: '#c9a050',
    fontSize: 14,
    fontWeight: '500',
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
