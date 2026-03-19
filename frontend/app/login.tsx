import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as WebBrowser from 'expo-web-browser';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';

export default function LoginScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const handleGoogleLogin = async () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = `${API_URL}/auth-callback`;
    const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    
    const result = await WebBrowser.openAuthSessionAsync(authUrl, redirectUrl);
    
    if (result.type === 'success' && result.url) {
      // Extract session_id from URL
      const url = new URL(result.url);
      const sessionId = url.hash?.split('session_id=')[1];
      
      if (sessionId) {
        // Navigate to auth callback to process the session
        router.replace({
          pathname: '/auth-callback',
          params: { session_id: sessionId },
        });
      }
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeButton}>
          <Ionicons name="close" size={28} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Content */}
      <View style={styles.content}>
        <Text style={styles.logo}>LUXURA</Text>
        <Text style={styles.title}>Bienvenue</Text>
        <Text style={styles.subtitle}>
          Connectez-vous pour accéder à votre panier, suivre vos commandes et profiter d'une expérience personnalisée.
        </Text>

        <View style={styles.features}>
          <View style={styles.feature}>
            <Ionicons name="bag-outline" size={20} color="#c9a050" />
            <Text style={styles.featureText}>Gérer votre panier</Text>
          </View>
          <View style={styles.feature}>
            <Ionicons name="heart-outline" size={20} color="#c9a050" />
            <Text style={styles.featureText}>Sauvegarder vos favoris</Text>
          </View>
          <View style={styles.feature}>
            <Ionicons name="receipt-outline" size={20} color="#c9a050" />
            <Text style={styles.featureText}>Suivre vos commandes</Text>
          </View>
        </View>

        <TouchableOpacity style={styles.googleButton} onPress={handleGoogleLogin}>
          <Ionicons name="logo-google" size={22} color="#000" />
          <Text style={styles.googleButtonText}>Continuer avec Google</Text>
        </TouchableOpacity>

        <Text style={styles.terms}>
          En continuant, vous acceptez nos conditions d'utilisation et notre politique de confidentialité.
        </Text>
      </View>
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
    justifyContent: 'flex-end',
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  closeButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    paddingHorizontal: 32,
    paddingTop: 40,
    alignItems: 'center',
  },
  logo: {
    color: '#c9a050',
    fontSize: 32,
    fontWeight: '800',
    letterSpacing: 6,
    marginBottom: 40,
  },
  title: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '800',
    marginBottom: 12,
  },
  subtitle: {
    color: '#aaa',
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },
  features: {
    alignSelf: 'stretch',
    gap: 16,
    marginBottom: 40,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
  },
  featureText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '500',
  },
  googleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#c9a050',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    gap: 12,
    alignSelf: 'stretch',
  },
  googleButtonText: {
    color: '#000',
    fontSize: 17,
    fontWeight: '700',
  },
  terms: {
    color: '#666',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 24,
    lineHeight: 18,
  },
});
