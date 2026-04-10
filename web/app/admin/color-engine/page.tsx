'use client'

import { useState, useRef, useEffect } from 'react'
import Image from 'next/image'
import { 
  ArrowUpTrayIcon, 
  ArrowDownTrayIcon,
  SwatchIcon,
  AdjustmentsHorizontalIcon,
  SparklesIcon,
  FolderPlusIcon
} from '@heroicons/react/24/outline'

const SERIES = [
  { id: 'genius', name: 'Vivian', watermark: 'VIVIAN', description: 'Extensions à Trame Invisible' },
  { id: 'halo', name: 'Everly', watermark: 'EVERLY', description: 'Extensions Halo' },
  { id: 'tape', name: 'Aurora', watermark: 'AURORA', description: 'Extensions à Bandes Adhésives' },
  { id: 'i-tip', name: 'Eleanor', watermark: 'ELEANOR', description: 'Extensions à Kératine' },
]

// API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function ColorEnginePage() {
  const [gabarit, setGabarit] = useState<string | null>(null)
  const [reference, setReference] = useState<string | null>(null)
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedSeries, setSelectedSeries] = useState('genius')
  const [settings, setSettings] = useState({
    intensity: 0.75,
    brightness: 1.0,
    contrast: 1.0,
    saturation: 1.0,
    preserveHighlights: true,
    addLogo: true,
    addWatermark: true,
  })
  const [savedColors, setSavedColors] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState<'create' | 'library' | 'add'>('create')
  
  const gabaritInputRef = useRef<HTMLInputElement>(null)
  const referenceInputRef = useRef<HTMLInputElement>(null)

  // Load saved colors from API
  useEffect(() => {
    fetchSavedColors()
  }, [selectedSeries])

  const fetchSavedColors = async () => {
    try {
      const res = await fetch(`${API_URL}/api/color-library/${selectedSeries}`)
      if (res.ok) {
        const data = await res.json()
        setSavedColors(data.colors || [])
      }
    } catch (error) {
      console.log('No saved colors yet')
    }
  }

  const handleFileUpload = (
    e: React.ChangeEvent<HTMLInputElement>,
    setter: (value: string | null) => void
  ) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        setter(event.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleGenerate = async () => {
    if (!gabarit || !reference) return
    
    setLoading(true)
    
    try {
      const response = await fetch(`${API_URL}/api/color-engine/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gabarit,
          reference,
          series: selectedSeries,
          settings,
        }),
      })
      
      if (response.ok) {
        const data = await response.json()
        setResult(data.image)
      } else {
        // Fallback: just show the reference as result for demo
        setResult(reference)
      }
    } catch (error) {
      console.error('Generation error:', error)
      // Fallback for demo
      setResult(reference)
    }
    
    setLoading(false)
  }

  const handleDownload = () => {
    if (!result) return
    
    const link = document.createElement('a')
    link.href = result
    link.download = `LUXURA_${selectedSeries.toUpperCase()}_nouvelle_couleur.jpg`
    link.click()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <SwatchIcon className="w-8 h-8 text-luxura-gold" />
            Color Engine PRO
          </h1>
          <p className="text-gray-400 mt-1">Créez des images produits avec watermarks automatiques</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-800 pb-2">
        <button
          onClick={() => setActiveTab('create')}
          className={`px-4 py-2 rounded-t-lg transition ${
            activeTab === 'create' 
              ? 'bg-luxura-gold text-black' 
              : 'text-gray-400 hover:text-white'
          }`}
        >
          🖼️ Créer une Image
        </button>
        <button
          onClick={() => setActiveTab('library')}
          className={`px-4 py-2 rounded-t-lg transition ${
            activeTab === 'library' 
              ? 'bg-luxura-gold text-black' 
              : 'text-gray-400 hover:text-white'
          }`}
        >
          📚 Répertoire
        </button>
        <button
          onClick={() => setActiveTab('add')}
          className={`px-4 py-2 rounded-t-lg transition ${
            activeTab === 'add' 
              ? 'bg-luxura-gold text-black' 
              : 'text-gray-400 hover:text-white'
          }`}
        >
          ➕ Ajouter Couleur
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'create' && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left Column - Inputs */}
          <div className="space-y-6">
            {/* Gabarit Upload */}
            <div className="bg-luxura-gray rounded-xl p-6 border border-gray-800">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                📐 Gabarit Fixe
              </h3>
              <input
                ref={gabaritInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => handleFileUpload(e, setGabarit)}
                className="hidden"
              />
              {gabarit ? (
                <div className="relative">
                  <img 
                    src={gabarit} 
                    alt="Gabarit" 
                    className="w-full rounded-lg"
                  />
                  <button
                    onClick={() => gabaritInputRef.current?.click()}
                    className="absolute bottom-2 right-2 px-3 py-1 bg-black/70 text-white text-sm rounded-lg hover:bg-black"
                  >
                    Changer
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => gabaritInputRef.current?.click()}
                  className="w-full h-48 border-2 border-dashed border-gray-700 rounded-lg flex flex-col items-center justify-center gap-2 hover:border-luxura-gold transition"
                >
                  <ArrowUpTrayIcon className="w-8 h-8 text-gray-500" />
                  <span className="text-gray-400">Charger le gabarit</span>
                </button>
              )}
            </div>

            {/* Reference Upload */}
            <div className="bg-luxura-gray rounded-xl p-6 border border-gray-800">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                🎨 Couleur de Référence
              </h3>
              <input
                ref={referenceInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => handleFileUpload(e, setReference)}
                className="hidden"
              />
              
              {/* Saved colors quick select */}
              {savedColors.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm text-gray-400 mb-2">Couleurs enregistrées :</p>
                  <div className="flex flex-wrap gap-2">
                    {savedColors.slice(0, 6).map((color, idx) => (
                      <button
                        key={idx}
                        onClick={() => setReference(color.image)}
                        className="w-12 h-12 rounded-lg overflow-hidden border-2 border-gray-700 hover:border-luxura-gold transition"
                        title={color.name}
                      >
                        <img src={color.image} alt={color.name} className="w-full h-full object-cover" />
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              {reference ? (
                <div className="relative">
                  <img 
                    src={reference} 
                    alt="Reference" 
                    className="w-full rounded-lg"
                  />
                  <button
                    onClick={() => referenceInputRef.current?.click()}
                    className="absolute bottom-2 right-2 px-3 py-1 bg-black/70 text-white text-sm rounded-lg hover:bg-black"
                  >
                    Changer
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => referenceInputRef.current?.click()}
                  className="w-full h-48 border-2 border-dashed border-gray-700 rounded-lg flex flex-col items-center justify-center gap-2 hover:border-luxura-gold transition"
                >
                  <ArrowUpTrayIcon className="w-8 h-8 text-gray-500" />
                  <span className="text-gray-400">Charger la référence couleur</span>
                </button>
              )}
            </div>

            {/* Series Selection */}
            <div className="bg-luxura-gray rounded-xl p-6 border border-gray-800">
              <h3 className="text-lg font-semibold text-white mb-4">Série & Watermark</h3>
              <div className="grid grid-cols-2 gap-2">
                {SERIES.map((serie) => (
                  <button
                    key={serie.id}
                    onClick={() => setSelectedSeries(serie.id)}
                    className={`p-3 rounded-lg border transition ${
                      selectedSeries === serie.id
                        ? 'border-luxura-gold bg-luxura-gold/10 text-luxura-gold'
                        : 'border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    <p className="font-semibold">{serie.name}</p>
                    <p className="text-xs opacity-70">{serie.id.toUpperCase()}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Settings */}
            <div className="bg-luxura-gray rounded-xl p-6 border border-gray-800">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <AdjustmentsHorizontalIcon className="w-5 h-5" />
                Paramètres
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="flex justify-between text-sm text-gray-400 mb-1">
                    <span>Intensité</span>
                    <span>{settings.intensity}</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={settings.intensity}
                    onChange={(e) => setSettings({...settings, intensity: parseFloat(e.target.value)})}
                    className="w-full accent-luxura-gold"
                  />
                </div>
                <div>
                  <label className="flex justify-between text-sm text-gray-400 mb-1">
                    <span>Luminosité</span>
                    <span>{settings.brightness}</span>
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="1.5"
                    step="0.05"
                    value={settings.brightness}
                    onChange={(e) => setSettings({...settings, brightness: parseFloat(e.target.value)})}
                    className="w-full accent-luxura-gold"
                  />
                </div>
                <div>
                  <label className="flex justify-between text-sm text-gray-400 mb-1">
                    <span>Saturation</span>
                    <span>{settings.saturation}</span>
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="1.5"
                    step="0.05"
                    value={settings.saturation}
                    onChange={(e) => setSettings({...settings, saturation: parseFloat(e.target.value)})}
                    className="w-full accent-luxura-gold"
                  />
                </div>
                <div className="flex items-center gap-4 pt-2">
                  <label className="flex items-center gap-2 text-sm text-gray-400">
                    <input
                      type="checkbox"
                      checked={settings.addLogo}
                      onChange={(e) => setSettings({...settings, addLogo: e.target.checked})}
                      className="accent-luxura-gold"
                    />
                    Logo Luxura
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-400">
                    <input
                      type="checkbox"
                      checked={settings.addWatermark}
                      onChange={(e) => setSettings({...settings, addWatermark: e.target.checked})}
                      className="accent-luxura-gold"
                    />
                    Watermark Série
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Result */}
          <div className="space-y-6">
            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={!gabarit || !reference || loading}
              className="w-full py-4 bg-luxura-gold text-black font-bold rounded-xl hover:bg-yellow-500 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Génération en cours...
                </>
              ) : (
                <>
                  <SparklesIcon className="w-5 h-5" />
                  Générer l'Image
                </>
              )}
            </button>

            {/* Result Preview */}
            <div className="bg-luxura-gray rounded-xl p-6 border border-gray-800 min-h-[400px] flex items-center justify-center">
              {result ? (
                <div className="w-full">
                  <img 
                    src={result} 
                    alt="Result" 
                    className="w-full rounded-lg"
                  />
                  <button
                    onClick={handleDownload}
                    className="mt-4 w-full py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-500 transition flex items-center justify-center gap-2"
                  >
                    <ArrowDownTrayIcon className="w-5 h-5" />
                    Télécharger
                  </button>
                </div>
              ) : (
                <div className="text-center text-gray-500">
                  <SwatchIcon className="w-16 h-16 mx-auto mb-4 opacity-30" />
                  <p>Le résultat apparaîtra ici</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'library' && (
        <div className="bg-luxura-gray rounded-xl p-6 border border-gray-800">
          <h3 className="text-xl font-semibold text-white mb-6">📚 Répertoire de Couleurs</h3>
          
          {SERIES.map((serie) => (
            <div key={serie.id} className="mb-8">
              <h4 className="text-lg font-semibold text-luxura-gold mb-4">
                Série {serie.name} ({serie.id.toUpperCase()})
              </h4>
              <p className="text-gray-500 text-sm mb-4">{serie.description}</p>
              
              <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-4">
                {/* Placeholder for saved colors */}
                <div className="aspect-square bg-gray-800 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-700">
                  <FolderPlusIcon className="w-8 h-8 text-gray-600" />
                </div>
              </div>
            </div>
          ))}
          
          <p className="text-gray-500 text-center mt-8">
            Ajoutez des couleurs dans l'onglet "➕ Ajouter Couleur"
          </p>
        </div>
      )}

      {activeTab === 'add' && (
        <div className="max-w-2xl mx-auto">
          <div className="bg-luxura-gray rounded-xl p-6 border border-gray-800">
            <h3 className="text-xl font-semibold text-white mb-6">➕ Ajouter une Nouvelle Couleur</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Catégorie</label>
                <select
                  value={selectedSeries}
                  onChange={(e) => setSelectedSeries(e.target.value)}
                  className="w-full px-4 py-3 bg-luxura-dark border border-gray-700 rounded-lg text-white focus:border-luxura-gold focus:outline-none"
                >
                  {SERIES.map((serie) => (
                    <option key={serie.id} value={serie.id}>
                      Série {serie.name} ({serie.id.toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Code couleur (ex: 6, DC, HPS)</label>
                <input
                  type="text"
                  placeholder="6"
                  className="w-full px-4 py-3 bg-luxura-dark border border-gray-700 rounded-lg text-white focus:border-luxura-gold focus:outline-none"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Nom de la couleur</label>
                <input
                  type="text"
                  placeholder="Caramel Doré"
                  className="w-full px-4 py-3 bg-luxura-dark border border-gray-700 rounded-lg text-white focus:border-luxura-gold focus:outline-none"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Image de référence</label>
                <input
                  type="file"
                  accept="image/*"
                  className="w-full px-4 py-3 bg-luxura-dark border border-gray-700 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-luxura-gold file:text-black file:font-semibold hover:file:bg-yellow-500"
                />
              </div>
              
              <button className="w-full py-3 bg-luxura-gold text-black font-semibold rounded-lg hover:bg-yellow-500 transition mt-4">
                💾 Enregistrer dans le Répertoire
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
