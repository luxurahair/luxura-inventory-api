import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Pressable,
  Image,
  TextInput,
  Alert,
  ActivityIndicator,
  Platform,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || '';

const SERIES = [
  { id: 'genius', name: 'Vivian', color: '#9333ea' },
  { id: 'halo', name: 'Everly', color: '#3b82f6' },
  { id: 'tape', name: 'Aurora', color: '#22c55e' },
  { id: 'i-tip', name: 'Eleanor', color: '#f59e0b' },
];

interface EliteColor {
  code: string;
  name: string;
  order: number;
  image_url: string;
  filename: string;
}

export default function AdminColorEngine() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'create' | 'library' | 'add'>('create');
  const [gabarit, setGabarit] = useState<string | null>(null);
  const [reference, setReference] = useState<string | null>(null);
  const [selectedEliteColor, setSelectedEliteColor] = useState<EliteColor | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedSeries, setSelectedSeries] = useState('genius');
  const [intensity, setIntensity] = useState(0.75);
  const [colorName, setColorName] = useState('');
  const [colorCode, setColorCode] = useState('');
  
  // Elite colors from API
  const [eliteColors, setEliteColors] = useState<EliteColor[]>([]);
  const [loadingColors, setLoadingColors] = useState(false);
  
  // Generated images history
  const [generatedImages, setGeneratedImages] = useState<any[]>([]);
  const [lastGeneratedUrl, setLastGeneratedUrl] = useState<string | null>(null);

  // Charger les couleurs Elite au démarrage
  useEffect(() => {
    fetchEliteColors();
    fetchGeneratedHistory();
  }, []);

  const fetchEliteColors = async () => {
    setLoadingColors(true);
    try {
      const url = `${API_URL}/api/color-engine/colors`;
      console.log('🔍 Fetching elite colors from:', url);
      const response = await fetch(url);
      console.log('📡 Response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('📦 Colors data:', data);
        setEliteColors(data.colors || []);
      } else {
        console.error('❌ Fetch failed:', response.status);
      }
    } catch (error) {
      console.error('❌ Error fetching elite colors:', error);
    }
    setLoadingColors(false);
  };

  const selectEliteColor = (color: EliteColor) => {
    setSelectedEliteColor(color);
    // Construire l'URL complète de l'image
    const imageUrl = `${API_URL}${color.image_url}`;
    setReference(imageUrl);
  };

  const fetchGeneratedHistory = async () => {
    try {
      const response = await fetch(`${API_URL}/api/color-engine/generated`);
      if (response.ok) {
        const data = await response.json();
        setGeneratedImages(data.images || []);
      }
    } catch (error) {
      console.error('Error fetching generated history:', error);
    }
  };

  const downloadImage = async (url: string, filename: string) => {
    try {
      const fullUrl = `${API_URL}${url}`;
      console.log('📥 Downloading:', fullUrl);
      
      if (Platform.OS === 'web') {
        // Sur web, ouvrir l'URL directement dans un nouvel onglet
        window.open(fullUrl, '_blank');
      } else {
        // Sur mobile, utiliser Linking
        const { Linking } = await import('react-native');
        Linking.openURL(fullUrl);
      }
    } catch (error) {
      console.error('Download error:', error);
      Alert.alert('Erreur', 'Impossible de télécharger l\'image');
    }
  };

  const deleteGeneratedImage = async (filename: string) => {
    try {
      const response = await fetch(`${API_URL}/api/color-engine/generated/${filename}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setGeneratedImages(prev => prev.filter(img => img.filename !== filename));
        Alert.alert('Succès', 'Image supprimée');
      }
    } catch (error) {
      Alert.alert('Erreur', 'Impossible de supprimer l\'image');
    }
  };

  const pickImage = async (setter: (uri: string) => void) => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (!permissionResult.granted) {
      Alert.alert('Permission requise', 'Accès à la galerie nécessaire');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
      base64: true,
    });

    if (!result.canceled && result.assets[0]) {
      const base64 = `data:image/jpeg;base64,${result.assets[0].base64}`;
      setter(base64);
    }
  };

  const handleGenerate = async () => {
    console.log('🎨 handleGenerate called', { selectedEliteColor, reference, gabarit });
    
    if (!selectedEliteColor && !reference) {
      Alert.alert('Erreur', 'Veuillez sélectionner une couleur Elite ou charger une référence');
      return;
    }

    setLoading(true);
    console.log('🚀 Starting generation...');

    try {
      const requestBody: any = {
        series: selectedSeries,
        intensity: intensity,
      };

      // Si on a une couleur Elite sélectionnée, utiliser son code
      if (selectedEliteColor) {
        requestBody.elite_color_code = selectedEliteColor.code;
      } else if (reference) {
        // Sinon utiliser l'image de référence en base64
        requestBody.reference = reference;
      }

      // Si on a un gabarit uploadé, l'envoyer
      if (gabarit) {
        requestBody.gabarit = gabarit;
      }

      const response = await fetch(`${API_URL}/api/color-engine/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.image) {
          setResult(data.image);
          setLastGeneratedUrl(data.download_url);
          // Rafraîchir l'historique
          fetchGeneratedHistory();
          // Success notification (moins intrusif que Alert sur web)
          console.log('✅ Image générée avec succès!', data.saved_filename);
        } else {
          Alert.alert('Erreur', data.detail || 'Échec de la génération');
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        Alert.alert('Erreur', errorData.detail || `Erreur ${response.status}`);
      }
    } catch (error) {
      console.error('Generate error:', error);
      Alert.alert('Erreur', 'Impossible de générer l\'image. Vérifiez votre connexion.');
    }

    setLoading(false);
  };

  const handleSaveColor = async () => {
    if (!reference || !colorName || !colorCode) {
      Alert.alert('Erreur', 'Remplissez tous les champs');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/color-library/${selectedSeries}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: reference,
          name: colorName,
          code: colorCode,
        }),
      });

      if (response.ok) {
        Alert.alert('Succès', `Couleur "${colorName}" enregistrée !`);
        setColorName('');
        setColorCode('');
        setReference(null);
      } else {
        Alert.alert('Info', 'Mode démo - sauvegarde simulée');
      }
    } catch (error) {
      Alert.alert('Info', 'Mode démo - API non connectée');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.title}>Color Engine PRO</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'create' && styles.tabActive]}
          onPress={() => setActiveTab('create')}
        >
          <Text style={[styles.tabText, activeTab === 'create' && styles.tabTextActive]}>
            🖼️ Créer
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'library' && styles.tabActive]}
          onPress={() => setActiveTab('library')}
        >
          <Text style={[styles.tabText, activeTab === 'library' && styles.tabTextActive]}>
            📚 Répertoire
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'add' && styles.tabActive]}
          onPress={() => setActiveTab('add')}
        >
          <Text style={[styles.tabText, activeTab === 'add' && styles.tabTextActive]}>
            ➕ Ajouter
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* CREATE TAB */}
        {activeTab === 'create' && (
          <View style={styles.createTab}>
            {/* Gabarit */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>📐 Gabarit Fixe</Text>
              <TouchableOpacity
                style={styles.uploadBox}
                onPress={() => pickImage(setGabarit)}
              >
                {gabarit ? (
                  <Image source={{ uri: gabarit }} style={styles.previewImage} />
                ) : (
                  <>
                    <Ionicons name="cloud-upload-outline" size={40} color="#666" />
                    <Text style={styles.uploadText}>Charger le gabarit</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>

            {/* Reference - Now with Elite Colors Grid */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>🎨 Couleur de Référence</Text>
              
              {/* Elite Colors Grid */}
              <Text style={styles.subsectionTitle}>Couleurs Elite ({eliteColors.length})</Text>
              {loadingColors ? (
                <ActivityIndicator size="small" color="#c9a050" style={{ marginVertical: 20 }} />
              ) : (
                <ScrollView 
                  horizontal 
                  showsHorizontalScrollIndicator={false}
                  style={styles.eliteColorsScroll}
                  contentContainerStyle={styles.eliteColorsContainer}
                >
                  {eliteColors.map((color) => (
                    <TouchableOpacity
                      key={color.code}
                      style={[
                        styles.eliteColorItem,
                        selectedEliteColor?.code === color.code && styles.eliteColorSelected
                      ]}
                      onPress={() => selectEliteColor(color)}
                    >
                      <Image
                        source={{ uri: `${API_URL}${color.image_url}` }}
                        style={styles.eliteColorImage}
                      />
                      <Text style={styles.eliteColorCode}>#{color.code}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              )}
              
              {/* Selected Color Preview or Manual Upload */}
              <View style={styles.referencePreviewContainer}>
                {selectedEliteColor ? (
                  <View style={styles.selectedColorInfo}>
                    <Image 
                      source={{ uri: reference || '' }} 
                      style={styles.selectedColorPreview} 
                    />
                    <View style={styles.selectedColorDetails}>
                      <Text style={styles.selectedColorName}>{selectedEliteColor.name}</Text>
                      <Text style={styles.selectedColorCodeLarge}>#{selectedEliteColor.code}</Text>
                      <TouchableOpacity 
                        style={styles.clearButton}
                        onPress={() => { setSelectedEliteColor(null); setReference(null); }}
                      >
                        <Text style={styles.clearButtonText}>Changer</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ) : (
                  <TouchableOpacity
                    style={styles.uploadBoxSmall}
                    onPress={() => pickImage(setReference)}
                  >
                    {reference ? (
                      <Image source={{ uri: reference }} style={styles.previewImage} />
                    ) : (
                      <>
                        <Ionicons name="color-palette-outline" size={32} color="#666" />
                        <Text style={styles.uploadText}>Ou charger manuellement</Text>
                      </>
                    )}
                  </TouchableOpacity>
                )}
              </View>
            </View>

            {/* Series Selection */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Série & Watermark</Text>
              <View style={styles.seriesGrid}>
                {SERIES.map((serie) => (
                  <TouchableOpacity
                    key={serie.id}
                    style={[
                      styles.seriesButton,
                      selectedSeries === serie.id && { borderColor: '#c9a050', backgroundColor: 'rgba(201, 160, 80, 0.1)' }
                    ]}
                    onPress={() => setSelectedSeries(serie.id)}
                  >
                    <View style={[styles.seriesDot, { backgroundColor: serie.color }]} />
                    <Text style={[
                      styles.seriesText,
                      selectedSeries === serie.id && { color: '#c9a050' }
                    ]}>
                      {serie.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Intensity Slider */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Intensité: {intensity.toFixed(2)}</Text>
              <View style={styles.sliderContainer}>
                <TouchableOpacity
                  style={styles.sliderButton}
                  onPress={() => setIntensity(Math.max(0, intensity - 0.1))}
                >
                  <Text style={styles.sliderButtonText}>-</Text>
                </TouchableOpacity>
                <View style={styles.sliderTrack}>
                  <View style={[styles.sliderFill, { width: `${intensity * 100}%` }]} />
                </View>
                <TouchableOpacity
                  style={styles.sliderButton}
                  onPress={() => setIntensity(Math.min(1, intensity + 0.1))}
                >
                  <Text style={styles.sliderButtonText}>+</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Generate Button */}
            <Pressable
              style={[styles.generateButton, (!selectedEliteColor && !reference) && styles.buttonDisabled]}
              onPress={handleGenerate}
              disabled={(!selectedEliteColor && !reference) || loading}
              testID="generate-button"
            >
              {loading ? (
                <ActivityIndicator color="#000" />
              ) : (
                <>
                  <Ionicons name="sparkles" size={20} color="#000" />
                  <Text style={styles.generateButtonText}>Générer l'Image</Text>
                </>
              )}
            </Pressable>

            {/* Result */}
            {result && (
              <View style={styles.resultSection}>
                <Text style={styles.sectionTitle}>✨ Résultat</Text>
                <Image source={{ uri: result }} style={styles.resultImage} />
                
                {/* Download Button */}
                {lastGeneratedUrl && (
                  <TouchableOpacity
                    style={styles.downloadButton}
                    onPress={() => {
                      const filename = lastGeneratedUrl.split('/').pop() || 'image.png';
                      downloadImage(lastGeneratedUrl, filename);
                    }}
                  >
                    <Ionicons name="download-outline" size={20} color="#fff" />
                    <Text style={styles.downloadButtonText}>Télécharger l'image</Text>
                  </TouchableOpacity>
                )}
              </View>
            )}
          </View>
        )}

        {/* LIBRARY TAB */}
        {activeTab === 'library' && (
          <View style={styles.libraryTab}>
            {/* Section: Images Générées */}
            <Text style={styles.sectionTitle}>📁 Images Générées</Text>
            {generatedImages.length > 0 ? (
              <>
                <Text style={styles.totalColors}>{generatedImages.length} images sauvegardées</Text>
                <View style={styles.generatedGrid}>
                  {generatedImages.map((img) => (
                    <View key={img.filename} style={styles.generatedItem}>
                      <Image
                        source={{ uri: `${API_URL}${img.preview_url}` }}
                        style={styles.generatedImage}
                      />
                      <Text style={styles.generatedSeries}>{img.series}</Text>
                      <Text style={styles.generatedColor}>#{img.color_code}</Text>
                      <Text style={styles.generatedSize}>{img.size_kb} KB</Text>
                      <View style={styles.generatedActions}>
                        <TouchableOpacity
                          style={styles.actionButton}
                          onPress={() => downloadImage(img.download_url, img.filename)}
                        >
                          <Ionicons name="download-outline" size={16} color="#c9a050" />
                        </TouchableOpacity>
                        <TouchableOpacity
                          style={styles.actionButtonDelete}
                          onPress={() => {
                            Alert.alert(
                              'Supprimer',
                              `Voulez-vous supprimer ${img.filename}?`,
                              [
                                { text: 'Annuler', style: 'cancel' },
                                { text: 'Supprimer', style: 'destructive', onPress: () => deleteGeneratedImage(img.filename) }
                              ]
                            );
                          }}
                        >
                          <Ionicons name="trash-outline" size={16} color="#ef4444" />
                        </TouchableOpacity>
                      </View>
                    </View>
                  ))}
                </View>
              </>
            ) : (
              <Text style={styles.emptyText}>Aucune image générée. Utilisez l'onglet "Créer" pour commencer.</Text>
            )}
            
            {/* Section: Couleurs Elite */}
            <Text style={[styles.sectionTitle, { marginTop: 24 }]}>🎨 Couleurs Elite</Text>
            
            {loadingColors ? (
              <ActivityIndicator size="large" color="#c9a050" style={{ marginVertical: 40 }} />
            ) : (
              <>
                <Text style={styles.totalColors}>{eliteColors.length} couleurs disponibles</Text>
                
                {/* Grid of all Elite Colors */}
                <View style={styles.libraryColorGrid}>
                  {eliteColors.map((color) => (
                    <TouchableOpacity
                      key={color.code}
                      style={styles.libraryColorItem}
                      onPress={() => {
                        selectEliteColor(color);
                        setActiveTab('create');
                      }}
                    >
                      <Image
                        source={{ uri: `${API_URL}${color.image_url}` }}
                        style={styles.libraryColorImage}
                      />
                      <Text style={styles.libraryColorName}>{color.name}</Text>
                      <Text style={styles.libraryColorCode}>#{color.code}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </>
            )}
            
            <TouchableOpacity 
              style={styles.refreshButton}
              onPress={() => { fetchEliteColors(); fetchGeneratedHistory(); }}
            >
              <Ionicons name="refresh" size={20} color="#c9a050" />
              <Text style={styles.refreshButtonText}>Actualiser</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ADD TAB */}
        {activeTab === 'add' && (
          <View style={styles.addTab}>
            <Text style={styles.sectionTitle}>➕ Nouvelle Couleur</Text>

            {/* Series Selection */}
            <Text style={styles.label}>Catégorie</Text>
            <View style={styles.seriesGrid}>
              {SERIES.map((serie) => (
                <TouchableOpacity
                  key={serie.id}
                  style={[
                    styles.seriesButton,
                    selectedSeries === serie.id && { borderColor: '#c9a050', backgroundColor: 'rgba(201, 160, 80, 0.1)' }
                  ]}
                  onPress={() => setSelectedSeries(serie.id)}
                >
                  <Text style={[
                    styles.seriesText,
                    selectedSeries === serie.id && { color: '#c9a050' }
                  ]}>
                    {serie.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.label}>Code couleur</Text>
            <TextInput
              style={styles.input}
              placeholder="Ex: 6, DC, HPS"
              placeholderTextColor="#666"
              value={colorCode}
              onChangeText={setColorCode}
            />

            <Text style={styles.label}>Nom de la couleur</Text>
            <TextInput
              style={styles.input}
              placeholder="Ex: Caramel Doré"
              placeholderTextColor="#666"
              value={colorName}
              onChangeText={setColorName}
            />

            <Text style={styles.label}>Image de référence</Text>
            <TouchableOpacity
              style={styles.uploadBox}
              onPress={() => pickImage(setReference)}
            >
              {reference ? (
                <Image source={{ uri: reference }} style={styles.previewImage} />
              ) : (
                <>
                  <Ionicons name="image-outline" size={40} color="#666" />
                  <Text style={styles.uploadText}>Charger l'image</Text>
                </>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.saveButton, (!reference || !colorName || !colorCode) && styles.buttonDisabled]}
              onPress={handleSaveColor}
              disabled={!reference || !colorName || !colorCode}
            >
              <Ionicons name="save" size={20} color="#000" />
              <Text style={styles.saveButtonText}>Enregistrer</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
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
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#c9a050',
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 12,
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
  },
  tabActive: {
    backgroundColor: '#c9a050',
  },
  tabText: {
    color: '#888',
    fontSize: 13,
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#000',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  createTab: {},
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  uploadBox: {
    height: 180,
    borderRadius: 12,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: '#333',
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  uploadText: {
    color: '#666',
    marginTop: 8,
  },
  previewImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  // Elite Colors Styles
  subsectionTitle: {
    color: '#888',
    fontSize: 13,
    marginBottom: 10,
  },
  eliteColorsScroll: {
    marginBottom: 16,
  },
  eliteColorsContainer: {
    paddingRight: 16,
    gap: 10,
  },
  eliteColorItem: {
    width: 70,
    alignItems: 'center',
    borderRadius: 8,
    borderWidth: 2,
    borderColor: 'transparent',
    padding: 4,
    backgroundColor: '#1a1a1a',
  },
  eliteColorSelected: {
    borderColor: '#c9a050',
    backgroundColor: 'rgba(201, 160, 80, 0.15)',
  },
  eliteColorImage: {
    width: 56,
    height: 56,
    borderRadius: 6,
    backgroundColor: '#333',
  },
  eliteColorCode: {
    color: '#aaa',
    fontSize: 10,
    marginTop: 4,
    fontWeight: '600',
  },
  referencePreviewContainer: {
    marginTop: 8,
  },
  selectedColorInfo: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#c9a050',
  },
  selectedColorPreview: {
    width: 80,
    height: 80,
    borderRadius: 8,
    backgroundColor: '#333',
  },
  selectedColorDetails: {
    marginLeft: 16,
    flex: 1,
    justifyContent: 'center',
  },
  selectedColorName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  selectedColorCodeLarge: {
    color: '#c9a050',
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 4,
  },
  clearButton: {
    marginTop: 8,
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: '#333',
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  clearButtonText: {
    color: '#888',
    fontSize: 12,
  },
  uploadBoxSmall: {
    height: 100,
    borderRadius: 12,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: '#333',
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  seriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  seriesButton: {
    flex: 1,
    minWidth: '45%',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333',
    backgroundColor: '#1a1a1a',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  seriesDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  seriesText: {
    color: '#888',
    fontWeight: '500',
  },
  sliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  sliderButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#333',
  },
  sliderButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  sliderTrack: {
    flex: 1,
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
    overflow: 'hidden',
  },
  sliderFill: {
    height: '100%',
    backgroundColor: '#c9a050',
    borderRadius: 4,
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#c9a050',
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 8,
  },
  generateButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: 'bold',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  resultSection: {
    marginTop: 24,
  },
  resultImage: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 12,
    backgroundColor: '#1a1a1a',
  },
  libraryTab: {},
  totalColors: {
    color: '#c9a050',
    fontSize: 14,
    marginBottom: 16,
  },
  libraryColorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  libraryColorItem: {
    width: '30%',
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
    padding: 8,
    alignItems: 'center',
  },
  libraryColorImage: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 8,
    backgroundColor: '#333',
  },
  libraryColorName: {
    color: '#fff',
    fontSize: 11,
    marginTop: 6,
    textAlign: 'center',
  },
  libraryColorCode: {
    color: '#c9a050',
    fontSize: 12,
    fontWeight: 'bold',
    marginTop: 2,
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#c9a050',
    borderRadius: 8,
    marginTop: 10,
  },
  refreshButtonText: {
    color: '#c9a050',
    fontWeight: '600',
  },
  downloadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#c9a050',
    paddingVertical: 14,
    borderRadius: 10,
    marginTop: 16,
  },
  downloadButtonText: {
    color: '#000',
    fontWeight: '600',
    fontSize: 16,
  },
  generatedGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  generatedItem: {
    width: '30%',
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
    padding: 8,
    alignItems: 'center',
  },
  generatedImage: {
    width: '100%',
    aspectRatio: 0.75,
    borderRadius: 8,
    backgroundColor: '#333',
  },
  generatedSeries: {
    color: '#c9a050',
    fontSize: 11,
    fontWeight: '600',
    marginTop: 6,
    textTransform: 'uppercase',
  },
  generatedColor: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    marginTop: 2,
  },
  generatedSize: {
    color: '#888',
    fontSize: 10,
    marginTop: 2,
  },
  generatedActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  actionButton: {
    padding: 8,
    backgroundColor: '#333',
    borderRadius: 6,
  },
  actionButtonDelete: {
    padding: 8,
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    borderRadius: 6,
  },
  emptyText: {
    color: '#888',
    textAlign: 'center',
    paddingVertical: 20,
    fontStyle: 'italic',
  },
  infoText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 20,
  },
  librarySection: {
    marginBottom: 24,
  },
  librarySectionTitle: {
    color: '#c9a050',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
  },
  colorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  emptyColorBox: {
    width: 60,
    height: 60,
    borderRadius: 8,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: '#333',
    alignItems: 'center',
    justifyContent: 'center',
  },
  hintText: {
    color: '#666',
    textAlign: 'center',
    marginTop: 20,
  },
  addTab: {},
  label: {
    color: '#888',
    fontSize: 14,
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#fff',
    fontSize: 16,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#22c55e',
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 24,
  },
  saveButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
