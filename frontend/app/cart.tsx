import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
  Linking,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuthStore } from '../src/store/authStore';
import { useCartStore } from '../src/store/cartStore';

export default function CartScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { isAuthenticated, sessionToken } = useAuthStore();
  const { items, total, count, fetchCart, updateQuantity, removeItem, isLoading } = useCartStore();
  const [updatingItem, setUpdatingItem] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated && sessionToken) {
      fetchCart(sessionToken);
    }
  }, [isAuthenticated, sessionToken]);

  const handleUpdateQuantity = async (itemId: string, newQuantity: number) => {
    setUpdatingItem(itemId);
    await updateQuantity(itemId, newQuantity, sessionToken);
    setUpdatingItem(null);
  };

  const handleRemoveItem = async (itemId: string, productName: string) => {
    Alert.alert(
      'Supprimer',
      `Voulez-vous supprimer ${productName} du panier?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: async () => {
            setUpdatingItem(itemId);
            await removeItem(itemId, sessionToken);
            setUpdatingItem(null);
          },
        },
      ]
    );
  };

  const handleCheckout = () => {
    // Redirect to Wix checkout
    const wixUrl = 'https://www.luxuradistribution.com/category/all-products';
    Linking.openURL(wixUrl);
  };

  if (!isAuthenticated) {
    return (
      <View style={styles.container}>
        <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Mon Panier</Text>
          <View style={styles.placeholder} />
        </View>

        <View style={styles.emptyContainer}>
          <View style={styles.emptyIcon}>
            <Ionicons name="person-outline" size={48} color="#c9a050" />
          </View>
          <Text style={styles.emptyTitle}>Connectez-vous</Text>
          <Text style={styles.emptySubtitle}>
            Connectez-vous pour voir votre panier et passer commande.
          </Text>
          <TouchableOpacity style={styles.loginButton} onPress={() => router.push('/login')}>
            <Text style={styles.loginButtonText}>Se connecter</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Mon Panier ({count})</Text>
        <View style={styles.placeholder} />
      </View>

      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#c9a050" />
        </View>
      ) : items.length === 0 ? (
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIcon}>
            <Ionicons name="bag-outline" size={48} color="#c9a050" />
          </View>
          <Text style={styles.emptyTitle}>Panier vide</Text>
          <Text style={styles.emptySubtitle}>
            Vous n'avez pas encore ajouté de produits à votre panier.
          </Text>
          <TouchableOpacity style={styles.shopButton} onPress={() => router.push('/catalogue')}>
            <Text style={styles.shopButtonText}>Découvrir nos produits</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
            {items.map((item) => (
              <View key={item.id} style={styles.cartItem}>
                <Image
                  source={{ uri: item.product.images[0] }}
                  style={styles.itemImage}
                  resizeMode="cover"
                />
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName} numberOfLines={2}>{item.product.name}</Text>
                  {item.product.color_code && (
                    <Text style={styles.itemColor}>{item.product.color_code}</Text>
                  )}
                  <Text style={styles.itemPrice}>{item.product.price.toFixed(2)} C$</Text>
                  
                  <View style={styles.itemActions}>
                    <View style={styles.quantityControl}>
                      <TouchableOpacity
                        style={styles.quantityButton}
                        onPress={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                        disabled={updatingItem === item.id}
                      >
                        <Ionicons name="remove" size={16} color="#fff" />
                      </TouchableOpacity>
                      
                      {updatingItem === item.id ? (
                        <ActivityIndicator size="small" color="#c9a050" style={styles.quantityLoader} />
                      ) : (
                        <Text style={styles.quantityText}>{item.quantity}</Text>
                      )}
                      
                      <TouchableOpacity
                        style={styles.quantityButton}
                        onPress={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                        disabled={updatingItem === item.id}
                      >
                        <Ionicons name="add" size={16} color="#fff" />
                      </TouchableOpacity>
                    </View>
                    
                    <TouchableOpacity
                      onPress={() => handleRemoveItem(item.id, item.product.name)}
                      disabled={updatingItem === item.id}
                    >
                      <Ionicons name="trash-outline" size={20} color="#ff4444" />
                    </TouchableOpacity>
                  </View>
                </View>
                
                <Text style={styles.itemTotal}>{item.item_total.toFixed(2)} C$</Text>
              </View>
            ))}
            
            <View style={{ height: 200 }} />
          </ScrollView>

          {/* Checkout Bar */}
          <View style={[styles.checkoutBar, { paddingBottom: insets.bottom + 16 }]}>
            <View style={styles.totalSection}>
              <Text style={styles.totalLabel}>Total</Text>
              <Text style={styles.totalAmount}>{total.toFixed(2)} C$</Text>
            </View>
            <TouchableOpacity style={styles.checkoutButton} onPress={handleCheckout}>
              <Text style={styles.checkoutButtonText}>Commander sur Wix</Text>
              <Ionicons name="arrow-forward" size={20} color="#000" />
            </TouchableOpacity>
          </View>
        </>
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
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a1a',
  },
  backButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'flex-start',
  },
  headerTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  placeholder: {
    width: 44,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(201, 160, 80, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  emptyTitle: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 12,
  },
  emptySubtitle: {
    color: '#aaa',
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  loginButton: {
    backgroundColor: '#c9a050',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  loginButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '600',
  },
  shopButton: {
    backgroundColor: '#c9a050',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  shopButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  cartItem: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  itemImage: {
    width: 80,
    height: 100,
    borderRadius: 8,
    backgroundColor: '#2a2a2a',
  },
  itemInfo: {
    flex: 1,
    marginLeft: 12,
  },
  itemName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  itemColor: {
    color: '#c9a050',
    fontSize: 12,
    marginBottom: 4,
  },
  itemPrice: {
    color: '#aaa',
    fontSize: 14,
    marginBottom: 12,
  },
  itemActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  quantityControl: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  quantityButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantityText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    minWidth: 24,
    textAlign: 'center',
  },
  quantityLoader: {
    minWidth: 24,
  },
  itemTotal: {
    color: '#c9a050',
    fontSize: 16,
    fontWeight: '700',
    position: 'absolute',
    top: 12,
    right: 12,
  },
  checkoutBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#0c0c0c',
    borderTopWidth: 1,
    borderTopColor: '#1a1a1a',
    padding: 16,
  },
  totalSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  totalLabel: {
    color: '#aaa',
    fontSize: 16,
  },
  totalAmount: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '800',
  },
  checkoutButton: {
    backgroundColor: '#c9a050',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  checkoutButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '700',
  },
});
