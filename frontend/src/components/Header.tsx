import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useCartStore } from '../store/cartStore';

const LUXURA_LOGO = 'https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/i7uo40l8_Luxura%20Distribution%20-%20OR%20-%20PNG.png';

interface HeaderProps {
  title?: string;
  showBack?: boolean;
  showCart?: boolean;
  showLogo?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ 
  title, 
  showBack = false, 
  showCart = true,
  showLogo = true  // Default to true - show logo everywhere
}) => {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { count } = useCartStore();

  return (
    <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
      <View style={styles.left}>
        {showBack ? (
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
        ) : (
          <View style={styles.placeholder} />
        )}
      </View>
      
      <View style={styles.center}>
        {showLogo ? (
          <Image 
            source={{ uri: LUXURA_LOGO }}
            style={styles.logoImage}
            resizeMode="contain"
          />
        ) : (
          <Text style={styles.title}>{title}</Text>
        )}
      </View>
      
      <View style={styles.right}>
        {showCart && (
          <TouchableOpacity onPress={() => router.push('/cart')} style={styles.cartButton}>
            <Ionicons name="bag-outline" size={24} color="#fff" />
            {count > 0 && (
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{count > 9 ? '9+' : count}</Text>
              </View>
            )}
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: '#0c0c0c',
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a1a',
  },
  left: {
    width: 44,
  },
  center: {
    flex: 1,
    alignItems: 'center',
  },
  right: {
    width: 44,
    alignItems: 'flex-end',
  },
  backButton: {
    padding: 4,
  },
  placeholder: {
    width: 32,
  },
  logoImage: {
    width: 120,
    height: 32,
  },
  logo: {
    color: '#c9a050',
    fontSize: 24,
    fontWeight: '800',
    letterSpacing: 4,
  },
  title: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  cartButton: {
    padding: 4,
    position: 'relative',
  },
  badge: {
    position: 'absolute',
    top: 0,
    right: 0,
    backgroundColor: '#c9a050',
    width: 18,
    height: 18,
    borderRadius: 9,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeText: {
    color: '#000',
    fontSize: 10,
    fontWeight: '700',
  },
});
