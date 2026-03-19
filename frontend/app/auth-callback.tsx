import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';

export default function AuthCallbackScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const hasProcessed = useRef(false);
  const { exchangeSession, checkAuth } = useAuthStore();

  useEffect(() => {
    // Use useRef to prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      try {
        // Get session_id from params or URL hash
        let sessionId = params.session_id as string;
        
        if (!sessionId && typeof window !== 'undefined') {
          const hash = window.location.hash;
          if (hash && hash.includes('session_id=')) {
            sessionId = hash.split('session_id=')[1]?.split('&')[0];
          }
        }

        if (sessionId) {
          const user = await exchangeSession(sessionId);
          if (user) {
            // Successfully authenticated, go to home
            router.replace('/(tabs)');
            return;
          }
        }

        // If no session_id or exchange failed, check existing auth
        const isAuth = await checkAuth();
        if (isAuth) {
          router.replace('/(tabs)');
        } else {
          router.replace('/login');
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        router.replace('/login');
      }
    };

    processAuth();
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#c9a050" />
      <Text style={styles.text}>Connexion en cours...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    color: '#aaa',
    fontSize: 16,
    marginTop: 16,
  },
});
