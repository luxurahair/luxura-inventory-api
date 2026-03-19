import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

interface Category {
  id: string;
  name: string;
  description: string;
  image?: string;
}

interface CategoryCardProps {
  category: Category;
  onPress: () => void;
}

export const CategoryCard: React.FC<CategoryCardProps> = ({ category, onPress }) => {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.8}>
      <Image 
        source={{ uri: category.image || 'https://via.placeholder.com/300' }} 
        style={styles.image}
        resizeMode="cover"
      />
      <View style={styles.overlay} />
      <View style={styles.content}>
        <Text style={styles.name}>{category.name}</Text>
        <Ionicons name="arrow-forward" size={20} color="#c9a050" />
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    width: width - 32,
    height: 120,
    borderRadius: 12,
    marginBottom: 12,
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
    position: 'absolute',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  content: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
  },
  name: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
});
