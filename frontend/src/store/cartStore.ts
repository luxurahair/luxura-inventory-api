import { create } from 'zustand';
import axios from 'axios';
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface Product {
  id: string;
  name: string;
  price: number;
  description: string;
  category: string;
  images: string[];
  in_stock: boolean;
  color_code?: string;
  series?: string;
}

interface CartItem {
  id: string;
  product: Product;
  quantity: number;
  item_total: number;
}

interface CartState {
  items: CartItem[];
  total: number;
  count: number;
  isLoading: boolean;
  fetchCart: (token: string | null) => Promise<void>;
  addToCart: (productId: string, quantity: number, token: string | null) => Promise<boolean>;
  updateQuantity: (itemId: string, quantity: number, token: string | null) => Promise<void>;
  removeItem: (itemId: string, token: string | null) => Promise<void>;
  clearCart: (token: string | null) => Promise<void>;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  total: 0,
  count: 0,
  isLoading: false,

  fetchCart: async (token) => {
    if (!token) return;
    
    try {
      set({ isLoading: true });
      const response = await axios.get(`${API_URL}/api/cart`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      set({ 
        items: response.data.items, 
        total: response.data.total,
        count: response.data.count,
        isLoading: false 
      });
    } catch (error) {
      console.error('Fetch cart error:', error);
      set({ isLoading: false });
    }
  },

  addToCart: async (productId, quantity, token) => {
    if (!token) return false;
    
    try {
      await axios.post(`${API_URL}/api/cart`, 
        { product_id: productId, quantity },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Refresh cart
      await get().fetchCart(token);
      return true;
    } catch (error) {
      console.error('Add to cart error:', error);
      return false;
    }
  },

  updateQuantity: async (itemId, quantity, token) => {
    if (!token) return;
    
    try {
      await axios.put(`${API_URL}/api/cart/${itemId}`, 
        { quantity },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      await get().fetchCart(token);
    } catch (error) {
      console.error('Update quantity error:', error);
    }
  },

  removeItem: async (itemId, token) => {
    if (!token) return;
    
    try {
      await axios.delete(`${API_URL}/api/cart/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      await get().fetchCart(token);
    } catch (error) {
      console.error('Remove item error:', error);
    }
  },

  clearCart: async (token) => {
    if (!token) return;
    
    try {
      await axios.delete(`${API_URL}/api/cart`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      set({ items: [], total: 0, count: 0 });
    } catch (error) {
      console.error('Clear cart error:', error);
    }
  },
}));
