import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
  RefreshControl,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import axios from 'axios';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';
const RENDER_API = 'https://luxura-inventory-api.onrender.com';

interface ApiStatus {
  local: boolean;
  render: boolean;
  productCount: number;
  categoryCount: number;
}

interface ProductStats {
  total: number;
  byCategory: { [key: string]: number };
  inStock: number;
  outOfStock: number;
  withVariants: number;
}

export default function AdminScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [apiStatus, setApiStatus] = useState<ApiStatus>({
    local: false,
    render: false,
    productCount: 0,
    categoryCount: 0,
  });
  const [productStats, setProductStats] = useState<ProductStats>({
    total: 0,
    byCategory: {},
    inStock: 0,
    outOfStock: 0,
    withVariants: 0,
  });

  const fetchStatus = async () => {
    // Set loading false immediately with empty data to show UI
    let localOk = false;
    let productCount = 0;
    let categoryCount = 0;
    let stats: ProductStats = {
      total: 0,
      byCategory: {},
      inStock: 0,
      outOfStock: 0,
      withVariants: 0,
    };

    try {
      // First get categories (fast)
      const categoriesRes = await axios.get(`${API_URL}/api/categories`, { timeout: 5000 });
      localOk = true;
      categoryCount = (categoriesRes.data || []).length;
      
      // Update UI immediately with categories
      setApiStatus({
        local: true,
        render: false,
        productCount: 0,
        categoryCount,
      });
      setLoading(false);
      
      // Then try products (can be slow due to Render)
      try {
        const productsRes = await axios.get(`${API_URL}/api/products`, { timeout: 30000 });
        const products = productsRes.data || [];
        productCount = products.length;
        stats.total = products.length;
        
        products.forEach((p: any) => {
          const cat = p.category || 'autre';
          stats.byCategory[cat] = (stats.byCategory[cat] || 0) + 1;
          if (p.in_stock) stats.inStock++;
          else stats.outOfStock++;
          if (p.variant_count > 0) stats.withVariants++;
        });
        
        setProductStats(stats);
        setApiStatus(prev => ({ ...prev, productCount }));
      } catch (e) {
        console.log('Products API slow or failed:', e);
      }
    } catch (e) {
      console.log('Local API error:', e);
      setLoading(false);
    }
    
    // Check Render API separately
    try {
      const res = await axios.get(`${RENDER_API}/products`, { timeout: 15000 });
      setApiStatus(prev => ({ ...prev, render: res.status === 200 }));
    } catch (e) {
      console.log('Render API unavailable');
    }
    
    setRefreshing(false);
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchStatus();
  };

  const openSwagger = () => {
    // Swagger is on port 8001 directly, not through Expo proxy
    const swaggerUrl = Platform.OS === 'web' 
      ? `${window.location.protocol}//${window.location.hostname}:8001/api/docs`
      : 'http://localhost:8001/api/docs';
    if (Platform.OS === 'web') {
      window.open(swaggerUrl, '_blank');
    } else {
      Linking.openURL(swaggerUrl);
    }
  };

  const openRenderSwagger = () => {
    const swaggerUrl = `${RENDER_API}/docs`;
    if (Platform.OS === 'web') {
      window.open(swaggerUrl, '_blank');
    } else {
      Linking.openURL(swaggerUrl);
    }
  };

  const openWixDashboard = () => {
    const wixUrl = 'https://manage.wix.com/dashboard/6e62c946-d068-45c1-8f5f-7af998f0d7b3/store/products';
    if (Platform.OS === 'web') {
      window.open(wixUrl, '_blank');
    } else {
      Linking.openURL(wixUrl);
    }
  };

  const StatusBadge = ({ status, label }: { status: boolean; label: string }) => (
    <View style={[styles.statusBadge, status ? styles.statusOnline : styles.statusOffline]}>
      <View style={[styles.statusDot, status ? styles.dotOnline : styles.dotOffline]} />
      <Text style={styles.statusText}>{label}</Text>
      <Text style={[styles.statusValue, status ? styles.valueOnline : styles.valueOffline]}>
        {status ? 'En ligne' : 'Hors ligne'}
      </Text>
    </View>
  );

  const StatCard = ({ icon, label, value, color }: { icon: string; label: string; value: number | string; color: string }) => (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <Ionicons name={icon as any} size={24} color={color} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );

  const ActionButton = ({ icon, label, onPress, color = '#c9a050' }: { icon: string; label: string; onPress: () => void; color?: string }) => (
    <TouchableOpacity style={[styles.actionButton, { borderColor: color }]} onPress={onPress} activeOpacity={0.7}>
      <Ionicons name={icon as any} size={22} color={color} />
      <Text style={[styles.actionLabel, { color }]}>{label}</Text>
      <Ionicons name="chevron-forward" size={18} color="#666" />
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.title}>Admin Dashboard</Text>
        <TouchableOpacity onPress={onRefresh} style={styles.refreshButton}>
          <Ionicons name="refresh" size={22} color="#c9a050" />
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#c9a050" />
          <Text style={styles.loadingText}>Chargement des données...</Text>
        </View>
      ) : (
        <ScrollView
          style={styles.content}
          contentContainerStyle={styles.contentContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c9a050" />
          }
          showsVerticalScrollIndicator={false}
        >
          {/* API Status Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              <Ionicons name="pulse" size={18} color="#c9a050" /> État des Services
            </Text>
            <View style={styles.statusGrid}>
              <StatusBadge status={apiStatus.local} label="API Locale (Emergent)" />
              <StatusBadge status={apiStatus.render} label="API Render (Production)" />
            </View>
          </View>

          {/* Stats Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              <Ionicons name="stats-chart" size={18} color="#c9a050" /> Statistiques
            </Text>
            <View style={styles.statsGrid}>
              <StatCard icon="cube-outline" label="Produits" value={productStats.total} color="#c9a050" />
              <StatCard icon="checkmark-circle-outline" label="En stock" value={productStats.inStock} color="#4CAF50" />
              <StatCard icon="close-circle-outline" label="Épuisés" value={productStats.outOfStock} color="#f44336" />
              <StatCard icon="layers-outline" label="Avec variantes" value={productStats.withVariants} color="#2196F3" />
            </View>
          </View>

          {/* Categories Breakdown */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              <Ionicons name="folder-outline" size={18} color="#c9a050" /> Par Catégorie
            </Text>
            <View style={styles.categoryList}>
              {Object.entries(productStats.byCategory).map(([cat, count]) => (
                <View key={cat} style={styles.categoryRow}>
                  <Text style={styles.categoryName}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</Text>
                  <View style={styles.categoryBar}>
                    <View 
                      style={[
                        styles.categoryBarFill, 
                        { width: `${(count / productStats.total) * 100}%` }
                      ]} 
                    />
                  </View>
                  <Text style={styles.categoryCount}>{count}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Quick Actions */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              <Ionicons name="flash-outline" size={18} color="#c9a050" /> Actions Rapides
            </Text>
            
            <ActionButton 
              icon="code-slash-outline" 
              label="Swagger API Locale" 
              onPress={openSwagger}
            />
            
            <ActionButton 
              icon="cloud-outline" 
              label="Swagger API Render" 
              onPress={openRenderSwagger}
            />
            
            <ActionButton 
              icon="storefront-outline" 
              label="Dashboard Wix" 
              onPress={openWixDashboard}
              color="#0070f3"
            />
            
            <ActionButton 
              icon="grid-outline" 
              label="Voir le Catalogue" 
              onPress={() => router.push('/(tabs)/catalogue')}
              color="#4CAF50"
            />
          </View>

          {/* API Endpoints Info */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              <Ionicons name="link-outline" size={18} color="#c9a050" /> Endpoints API
            </Text>
            <View style={styles.endpointList}>
              <View style={styles.endpoint}>
                <Text style={styles.endpointMethod}>GET</Text>
                <Text style={styles.endpointPath}>/api/products</Text>
              </View>
              <View style={styles.endpoint}>
                <Text style={styles.endpointMethod}>GET</Text>
                <Text style={styles.endpointPath}>/api/products/{'{id}'}</Text>
              </View>
              <View style={styles.endpoint}>
                <Text style={styles.endpointMethod}>GET</Text>
                <Text style={styles.endpointPath}>/api/categories</Text>
              </View>
              <View style={styles.endpoint}>
                <Text style={styles.endpointMethod}>GET</Text>
                <Text style={styles.endpointPath}>/api/colors</Text>
              </View>
              <View style={styles.endpoint}>
                <Text style={styles.endpointMethod}>POST</Text>
                <Text style={styles.endpointPath}>/api/cart</Text>
              </View>
              <View style={styles.endpoint}>
                <Text style={[styles.endpointMethod, styles.methodPost]}>POST</Text>
                <Text style={styles.endpointPath}>/wix/seo/push_preview</Text>
              </View>
              <View style={styles.endpoint}>
                <Text style={[styles.endpointMethod, styles.methodPost]}>POST</Text>
                <Text style={styles.endpointPath}>/wix/seo/push_apply</Text>
              </View>
            </View>
          </View>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>Luxura Distribution</Text>
            <Text style={styles.footerSubtext}>Panel d'Administration v1.0</Text>
          </View>
        </ScrollView>
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
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a1a',
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  title: {
    flex: 1,
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
  },
  refreshButton: {
    padding: 8,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#666',
    marginTop: 12,
    fontSize: 14,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  statusGrid: {
    gap: 10,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
  },
  statusOnline: {
    borderColor: '#4CAF50',
  },
  statusOffline: {
    borderColor: '#f44336',
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 10,
  },
  dotOnline: {
    backgroundColor: '#4CAF50',
  },
  dotOffline: {
    backgroundColor: '#f44336',
  },
  statusText: {
    flex: 1,
    color: '#fff',
    fontSize: 14,
  },
  statusValue: {
    fontSize: 12,
    fontWeight: '600',
  },
  valueOnline: {
    color: '#4CAF50',
  },
  valueOffline: {
    color: '#f44336',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderLeftWidth: 3,
  },
  statValue: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '700',
    marginTop: 8,
  },
  statLabel: {
    color: '#888',
    fontSize: 12,
    marginTop: 4,
  },
  categoryList: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 14,
  },
  categoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  categoryName: {
    color: '#fff',
    fontSize: 13,
    width: 80,
  },
  categoryBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#2a2a2a',
    borderRadius: 4,
    marginHorizontal: 10,
    overflow: 'hidden',
  },
  categoryBarFill: {
    height: '100%',
    backgroundColor: '#c9a050',
    borderRadius: 4,
  },
  categoryCount: {
    color: '#c9a050',
    fontSize: 13,
    fontWeight: '600',
    width: 30,
    textAlign: 'right',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  actionLabel: {
    flex: 1,
    fontSize: 15,
    fontWeight: '500',
    marginLeft: 12,
  },
  endpointList: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 12,
  },
  endpoint: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  endpointMethod: {
    backgroundColor: '#4CAF50',
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    overflow: 'hidden',
    marginRight: 10,
  },
  methodPost: {
    backgroundColor: '#FF9800',
  },
  endpointPath: {
    color: '#aaa',
    fontSize: 13,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 20,
    borderTopWidth: 1,
    borderTopColor: '#1a1a1a',
    marginTop: 10,
  },
  footerText: {
    color: '#c9a050',
    fontSize: 16,
    fontWeight: '600',
  },
  footerSubtext: {
    color: '#666',
    fontSize: 12,
    marginTop: 4,
  },
});
