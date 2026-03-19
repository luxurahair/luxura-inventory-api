import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface User {
  user_id: string;
  email: string;
  name: string;
  picture?: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  sessionToken: string | null;
  setUser: (user: User | null) => void;
  setSessionToken: (token: string | null) => void;
  setLoading: (loading: boolean) => void;
  login: () => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
  exchangeSession: (sessionId: string) => Promise<User | null>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  sessionToken: null,

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setSessionToken: (token) => set({ sessionToken: token }),
  setLoading: (loading) => set({ isLoading: loading }),

  login: () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = `${API_URL}/auth-callback`;
    const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    // This will be handled by the WebBrowser in the component
    return authUrl;
  },

  logout: async () => {
    try {
      const token = get().sessionToken;
      await axios.post(`${API_URL}/api/auth/logout`, {}, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        withCredentials: true,
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      await AsyncStorage.removeItem('session_token');
      set({ user: null, isAuthenticated: false, sessionToken: null });
    }
  },

  checkAuth: async () => {
    try {
      set({ isLoading: true });
      
      // Try to get stored session token
      const storedToken = await AsyncStorage.getItem('session_token');
      
      if (!storedToken) {
        set({ isLoading: false, isAuthenticated: false });
        return false;
      }

      const response = await axios.get(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${storedToken}` },
        withCredentials: true,
      });

      if (response.data) {
        set({ 
          user: response.data, 
          isAuthenticated: true, 
          sessionToken: storedToken,
          isLoading: false 
        });
        return true;
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      await AsyncStorage.removeItem('session_token');
    }
    
    set({ isLoading: false, isAuthenticated: false, user: null, sessionToken: null });
    return false;
  },

  exchangeSession: async (sessionId: string) => {
    try {
      const response = await axios.post(`${API_URL}/api/auth/session`, {
        session_id: sessionId,
      }, {
        withCredentials: true,
      });

      if (response.data) {
        // Extract session token from response or cookie
        const sessionToken = response.data.session_token || sessionId;
        await AsyncStorage.setItem('session_token', sessionToken);
        
        set({ 
          user: response.data, 
          isAuthenticated: true, 
          sessionToken,
          isLoading: false 
        });
        
        return response.data;
      }
    } catch (error) {
      console.error('Session exchange failed:', error);
    }
    return null;
  },
}));
