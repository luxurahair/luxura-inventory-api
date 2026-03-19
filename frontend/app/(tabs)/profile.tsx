import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  Alert,
  Linking,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as WebBrowser from 'expo-web-browser';
import { useAuthStore } from '../../src/store/authStore';
import { useCartStore } from '../../src/store/cartStore';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';

export default function ProfileScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { user, isAuthenticated, logout } = useAuthStore();
  const { count } = useCartStore();

  const handleLogin = async () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = `${API_URL}/auth-callback`;
    const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    await WebBrowser.openBrowserAsync(authUrl);
  };

  const handleLogout = () => {
    Alert.alert(
      'Déconnexion',
      'Êtes-vous sûr de vouloir vous déconnecter?',
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Déconnecter',
          style: 'destructive',
          onPress: logout,
        },
      ]
    );
  };

  const handleContact = () => {
    Linking.openURL('mailto:contact@luxuradistribution.com');
  };

  const handleWebsite = () => {
    Linking.openURL('https://www.luxuradistribution.com');
  };

  const handleInstagram = () => {
    Linking.openURL('https://www.instagram.com/luxura_distribution/');
  };

  const MenuItem = ({ icon, title, onPress, showBadge = false, badgeCount = 0 }: any) => (
    <TouchableOpacity style={styles.menuItem} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.menuIcon}>
        <Ionicons name={icon} size={22} color="#c9a050" />
      </View>
      <Text style={styles.menuTitle}>{title}</Text>
      <View style={styles.menuRight}>
        {showBadge && badgeCount > 0 && (
          <View style={styles.menuBadge}>
            <Text style={styles.menuBadgeText}>{badgeCount}</Text>
          </View>
        )}
        <Ionicons name="chevron-forward" size={20} color="#666" />
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <Text style={styles.title}>Profil</Text>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Profile Section */}
        {isAuthenticated && user ? (
          <View style={styles.profileSection}>
            {user.picture ? (
              <Image source={{ uri: user.picture }} style={styles.profileImage} />
            ) : (
              <View style={styles.profilePlaceholder}>
                <Ionicons name="person" size={40} color="#c9a050" />
              </View>
            )}
            <Text style={styles.profileName}>{user.name}</Text>
            <Text style={styles.profileEmail}>{user.email}</Text>
          </View>
        ) : (
          <View style={styles.loginSection}>
            <View style={styles.loginIcon}>
              <Ionicons name="person-outline" size={48} color="#c9a050" />
            </View>
            <Text style={styles.loginTitle}>Bienvenue chez Luxura</Text>
            <Text style={styles.loginSubtitle}>
              Connectez-vous pour accéder à votre panier et vos commandes
            </Text>
            <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
              <Ionicons name="logo-google" size={20} color="#000" />
              <Text style={styles.loginButtonText}>Continuer avec Google</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Menu Items */}
        <View style={styles.menuSection}>
          <MenuItem
            icon="bag-outline"
            title="Mon panier"
            onPress={() => router.push('/cart')}
            showBadge
            badgeCount={count}
          />
          <MenuItem
            icon="heart-outline"
            title="Mes favoris"
            onPress={() => Alert.alert('Bientôt disponible', 'Cette fonctionnalité arrive bientôt!')}
          />
          <MenuItem
            icon="receipt-outline"
            title="Mes commandes"
            onPress={() => Alert.alert('Bientôt disponible', 'Cette fonctionnalité arrive bientôt!')}
          />
        </View>

        <View style={styles.menuSection}>
          <MenuItem
            icon="globe-outline"
            title="Site web Luxura"
            onPress={handleWebsite}
          />
          <MenuItem
            icon="logo-instagram"
            title="Instagram"
            onPress={handleInstagram}
          />
          <MenuItem
            icon="mail-outline"
            title="Nous contacter"
            onPress={handleContact}
          />
        </View>

        {isAuthenticated && (
          <View style={styles.menuSection}>
            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
              <Ionicons name="log-out-outline" size={22} color="#ff4444" />
              <Text style={styles.logoutText}>Déconnexion</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* App Info */}
        <View style={styles.appInfo}>
          <Text style={styles.appName}>LUXURA</Text>
          <Text style={styles.appVersion}>Version 1.0.0</Text>
          <Text style={styles.appCopyright}>© 2025 Luxura Distribution</Text>
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
  header: {
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  title: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '800',
  },
  scrollView: {
    flex: 1,
  },
  profileSection: {
    alignItems: 'center',
    padding: 24,
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    marginBottom: 16,
  },
  profilePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  profileName: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 4,
  },
  profileEmail: {
    color: '#aaa',
    fontSize: 14,
  },
  loginSection: {
    alignItems: 'center',
    padding: 24,
    margin: 16,
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
  },
  loginIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  loginTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
  },
  loginSubtitle: {
    color: '#aaa',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  loginButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#c9a050',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    gap: 10,
  },
  loginButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '600',
  },
  menuSection: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    overflow: 'hidden',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  menuIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  menuTitle: {
    flex: 1,
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
  menuRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  menuBadge: {
    backgroundColor: '#c9a050',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  menuBadgeText: {
    color: '#000',
    fontSize: 12,
    fontWeight: '700',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  logoutText: {
    color: '#ff4444',
    fontSize: 16,
    fontWeight: '500',
  },
  appInfo: {
    alignItems: 'center',
    padding: 24,
  },
  appName: {
    color: '#c9a050',
    fontSize: 18,
    fontWeight: '800',
    letterSpacing: 4,
    marginBottom: 4,
  },
  appVersion: {
    color: '#666',
    fontSize: 12,
    marginBottom: 4,
  },
  appCopyright: {
    color: '#444',
    fontSize: 12,
  },
});
