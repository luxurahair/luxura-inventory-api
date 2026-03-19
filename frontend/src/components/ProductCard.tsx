import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');
const CARD_WIDTH = (width - 48) / 2;

interface Product {
  id: string;
  name: string;
  price: number;
  images: string[];
  in_stock: boolean;
  color_code?: string;
}

interface ProductCardProps {
  product: Product;
  onPress: () => void;
  onAddToCart?: () => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onPress, onAddToCart }) => {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.8}>
      <View style={styles.imageContainer}>
        <Image 
          source={{ uri: product.images[0] }} 
          style={styles.image}
          resizeMode="cover"
        />
        {!product.in_stock && (
          <View style={styles.outOfStockBadge}>
            <Text style={styles.outOfStockText}>Rupture</Text>
          </View>
        )}
      </View>
      
      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={2}>{product.name}</Text>
        {product.color_code && (
          <Text style={styles.colorCode}>{product.color_code}</Text>
        )}
        <View style={styles.priceRow}>
          <Text style={styles.price}>{product.price.toFixed(2)} C$</Text>
          {product.in_stock && onAddToCart && (
            <TouchableOpacity style={styles.addButton} onPress={onAddToCart}>
              <Ionicons name="add" size={18} color="#000" />
            </TouchableOpacity>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    width: CARD_WIDTH,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    marginBottom: 16,
    overflow: 'hidden',
  },
  imageContainer: {
    width: '100%',
    height: CARD_WIDTH * 1.2,
    backgroundColor: '#2a2a2a',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  outOfStockBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#ff4444',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  outOfStockText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '600',
  },
  info: {
    padding: 12,
  },
  name: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 4,
    lineHeight: 18,
  },
  colorCode: {
    color: '#c9a050',
    fontSize: 11,
    marginBottom: 8,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    color: '#c9a050',
    fontSize: 15,
    fontWeight: '700',
  },
  addButton: {
    backgroundColor: '#c9a050',
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
