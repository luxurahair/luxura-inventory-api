# 🌟 Luxura Distribution - Système d'Automatisation Wix & Marketing

> **Plateforme complète** de gestion automatisée pour extensions capillaires professionnelles au Québec.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [🆕 Nouvelles fonctionnalités](#-nouvelles-fonctionnalités)
3. [Facebook Marketing](#-facebook-marketing)
4. [SEO Image Optimizer](#-seo-image-optimizer)
5. [Vidéos Marketing AI](#-vidéos-marketing-ai)
6. [Capacités SEO Wix](#capacités-seo-wix)
7. [Blog Automation](#blog-automation)
8. [API Endpoints](#api-endpoints)
9. [Configuration](#configuration)
10. [Commandes utiles](#commandes-utiles)

---

## 🎯 Vue d'ensemble

Ce système permet de :
- ✅ **Publier automatiquement sur Facebook** via API Graph
- ✅ **Générer des noms d'images SEO-friendly** géolocalisés (Québec, Beauce, Lévis...)
- ✅ **Créer des vidéos marketing AI** avec Fal.ai
- ✅ **Modifier automatiquement les produits Wix** (noms, descriptions, SKUs)
- ✅ **Générer et publier des articles de blog** SEO-optimisés
- ✅ **Synchroniser l'inventaire** entre Wix et la base locale
- ✅ **Recolorer des images produits** avec le Color Engine PRO

---

## 🆕 Nouvelles fonctionnalités

### Avril 2025

| Fonctionnalité | Description | Statut |
|----------------|-------------|--------|
| **Facebook Auto-Post** | Publication automatique sur la page FB Luxura | ✅ Live |
| **SEO Image Optimizer** | Génération de noms de fichiers SEO géolocalisés | ✅ Live |
| **Vidéos AI Marketing** | Génération de vidéos promotionnelles avec Fal.ai | ✅ Live |
| **Color Engine PRO** | Recoloration d'images produits (OpenCV/Streamlit) | ✅ Prêt |

---

## 📘 Facebook Marketing

### Endpoints disponibles

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/facebook/status` | GET | Vérifier la connexion Facebook |
| `/facebook/test` | GET | Test rapide de la connexion |
| `/facebook/post` | POST | Publier un message/lien/image |
| `/facebook/post-blog` | POST | Publier un article de blog formaté |

### Utilisation

```bash
# Vérifier le statut (Local ou Render)
curl https://luxura-inventory-api.onrender.com/facebook/status

# Publier un message
curl -X POST "https://luxura-inventory-api.onrender.com/facebook/post" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "✨ Nouvelles extensions Genius disponibles!\n\n#LuxuraDistribution #Quebec",
    "link": "https://www.luxuradistribution.com/genius"
  }'

# Publier un article de blog
curl -X POST "https://luxura-inventory-api.onrender.com/facebook/post-blog" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Guide entretien extensions",
    "excerpt": "Découvrez nos conseils pour...",
    "url": "https://www.luxuradistribution.com/blog/guide-entretien"
  }'
```

### Configuration Facebook

Variables d'environnement requises sur **Render** :
```env
FB_PAGE_ID=1838415193042352
FB_PAGE_ACCESS_TOKEN=EAAU4dnLcR8IB...
```

---

## 🔍 SEO Image Optimizer

### Génération de noms de fichiers SEO

L'outil génère automatiquement des noms de fichiers optimisés avec :
- Rotation "rallonge" / "extension"
- Régions géolocalisées (Québec, Beauce, Lévis, Chaudière-Appalaches...)
- Noms de couleurs en français

### Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/seo/filename-generator` | GET | Génère des noms SEO pour plusieurs couleurs |
| `/api/seo/config` | GET | Configuration SEO disponible |
| `/api/seo/image/generate` | POST | Génère les données SEO complètes |
| `/api/seo/image/preview` | GET | Prévisualise toutes les variations |

### Utilisation

```bash
# Générer des noms pour les produits Genius
curl "http://localhost:8001/api/seo/filename-generator?product_type=genius&color_codes=1,6,60a,hps"

# Résultat:
# luxura-rallonge-genius-noir-fonce-quebec-20po.jpg
# luxura-extension-genius-noir-fonce-beauce-20po.jpg
# luxura-rallonge-genius-noir-fonce-levis-20po.jpg
```

### Régions supportées

```python
GEO_REGIONS = [
    "Québec", "Beauce", "Lévis", "Chaudière-Appalaches", 
    "Rive-Sud", "St-Georges", "Thetford", "Montmagny",
    "Trois-Rivières", "Montréal", "Sherbrooke", "Gatineau", "Saguenay"
]
```

---

## 🎬 Vidéos Marketing AI

### Génération avec Fal.ai

Le système peut générer des vidéos promotionnelles à partir d'images produits.

```bash
# Générer une vidéo pour un produit
curl -X POST "http://localhost:8001/api/video/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://static.wixstatic.com/media/...",
    "prompt": "Elegant hair flowing in slow motion, luxury salon ambiance"
  }'
```

### Vidéos générées

| Collection | Couleur | Durée | Statut |
|------------|---------|-------|--------|
| Genius | Onyx Noir (#1) | 5s | ✅ Généré |
| Genius | Espresso (#2) | 5s | ✅ Généré |
| Genius | Blond Platine (#60a) | 5s | ✅ Généré |
| ... | ... | ... | ... |

---

## 🔧 Capacités SEO Wix

### Push SEO Global

```bash
# Via l'API Render (recommandé)
curl -X POST "https://luxura-inventory-api.onrender.com/wix/seo/push_preview" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'

# Appliquer les changements
curl -X POST "https://luxura-inventory-api.onrender.com/wix/seo/push_apply" \
  -H "Content-Type: application/json" \
  -d '{"confirm": true, "limit": 10}'
```

### Types de produits supportés

```python
TYPE_META = {
    "halo": {"label": "Halo", "series": "Everly"},
    "genius": {"label": "Genius", "series": "Vivian"},
    "tape": {"label": "Tape", "series": "Aurora"},
    "i-tip": {"label": "I-Tip", "series": "Eleanor"},
    "ponytail": {"label": "Ponytail", "series": "Victoria"},
    "clip-in": {"label": "Clip-In", "series": "Sophia"},
    "hand-tied": {"label": "Hand-Tied", "series": "Aurora"},
}
```

---

## 📝 Blog Automation

### Calendrier éditorial

| Jour | Heure | Type | Audience |
|------|-------|------|----------|
| Lundi | 07:00 | Transformation | Femmes |
| Mardi | 12:00 | Cheveux fins | Femmes |
| Mercredi | 19:00 | Comparatif | Femmes |
| Jeudi | 07:00 | B2B Salon | Salons |
| Vendredi | 12:00 | Tendances | Femmes |
| Samedi | 10:00 | Inspiration | Femmes |
| Dimanche | 20:00 | Témoignages | Femmes |

### Génération manuelle

```bash
# Générer un brouillon
curl -X POST "http://localhost:8001/api/blog/generate" \
  -H "Content-Type: application/json" \
  -d '{"category": "entretien", "auto_publish": false}'

# Publier un brouillon
curl -X POST "http://localhost:8001/api/blog/publish/{draft_id}"
```

---

## 🔌 API Endpoints

### Local (http://localhost:8001/api)

| Catégorie | Endpoint | Méthode | Description |
|-----------|----------|---------|-------------|
| **Facebook** | `/facebook/status` | GET | Statut connexion FB |
| **Facebook** | `/facebook/post` | POST | Publier sur FB |
| **SEO** | `/seo/filename-generator` | GET | Noms fichiers SEO |
| **SEO** | `/seo/config` | GET | Config SEO |
| **Blog** | `/blog/generate` | POST | Générer brouillon |
| **Blog** | `/blog/publish/{id}` | POST | Publier brouillon |
| **Produits** | `/products` | GET | Liste produits |
| **Wix** | `/wix/capabilities` | GET | Capacités API Wix |

### Render (https://luxura-inventory-api.onrender.com)

| Catégorie | Endpoint | Méthode | Description |
|-----------|----------|---------|-------------|
| **Facebook** | `/facebook/status` | GET | Statut connexion FB |
| **Facebook** | `/facebook/post` | POST | Publier sur FB |
| **Facebook** | `/facebook/post-blog` | POST | Publier blog sur FB |
| **Wix SEO** | `/wix/seo/push_preview` | POST | Prévisualiser SEO |
| **Wix SEO** | `/wix/seo/push_apply` | POST | Appliquer SEO |
| **Wix Token** | `/wix/token` | POST | Refresh OAuth token |
| **Produits** | `/products` | GET | Liste produits sync |

---

## ⚙️ Configuration

### Variables d'environnement (/app/backend/.env)

```env
# === WIX API ===
WIX_API_KEY=IST.eyJ...
WIX_SITE_ID=6e62c946-d068-45c1-8f5f-7af998f0d7b3

# === FACEBOOK ===
FB_PAGE_ID=1838415193042352
FB_PAGE_ACCESS_TOKEN=EAAU4dnLcR8IB...

# === OPENAI (via Emergent) ===
EMERGENT_LLM_KEY=...

# === FAL.AI (Vidéos) ===
FAL_KEY=...

# === MONGODB ===
MONGO_URL=mongodb://...
DB_NAME=luxura_db

# === RENDER API ===
LUXURA_API_URL=https://luxura-inventory-api.onrender.com

# === EMAIL ===
LUXURA_EMAIL=info@luxuradistribution.com
LUXURA_APP_PASSWORD=...
```

---

## 🚀 Commandes utiles

### Redémarrer les services

```bash
# Backend
sudo supervisorctl restart backend

# Frontend Expo
sudo supervisorctl restart expo
```

### Vérifier les logs

```bash
# Backend
tail -f /var/log/supervisor/backend.err.log

# Expo
tail -f /var/log/supervisor/expo.err.log
```

### Tests rapides

```bash
# Facebook status
curl https://luxura-inventory-api.onrender.com/facebook/status

# SEO filenames
curl "http://localhost:8001/api/seo/filename-generator?product_type=genius&color_codes=60a"

# Wix capabilities
curl http://localhost:8001/api/wix/capabilities
```

---

## 📞 Support

- **Email:** info@luxuradistribution.com
- **Téléphone:** 418-774-4315
- **Adresse:** 8905 Boulevard Lacroix, Saint-Georges, QC G5Y 1T4

---

*Dernière mise à jour: Avril 2025*
