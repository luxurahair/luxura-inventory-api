# 🏗️ Architecture Technique - Luxura Distribution

> Documentation complète de l'architecture du système d'automatisation Wix, Facebook & Marketing AI.

---

## 📁 Structure des dossiers

```
/app/
├── README.md                    # Documentation principale
├── ARCHITECTURE.md              # Ce fichier
├── test_result.md               # Résultats des tests
│
├── backend/                     # API FastAPI principale
│   ├── .env                     # Variables d'environnement
│   ├── server.py                # Point d'entrée API (~4000 lignes)
│   ├── requirements.txt         # Dépendances Python
│   │
│   ├── # === MODULES FACEBOOK ===
│   ├── (intégré dans server.py) # Endpoints /facebook/*
│   │
│   ├── # === MODULES SEO IMAGE ===
│   ├── seo_image_optimizer.py   # Génération noms SEO géolocalisés
│   │
│   ├── # === MODULES BLOG ===
│   ├── blog_automation.py       # Génération & publication blogs
│   ├── editorial_calendar.py    # Calendrier 2 semaines
│   ├── editorial_guard.py       # Anti-doublon intelligent
│   ├── image_generation.py      # DALL-E 3 + upload Wix
│   ├── internal_linking.py      # Maillage interne SEO
│   ├── logo_overlay.py          # Overlay logo sur images
│   │
│   ├── # === MODULES SEO PRODUITS ===
│   ├── color_system.py          # 40+ couleurs avec noms luxueux
│   ├── seo_description_template.py  # Templates descriptions
│   │
│   ├── # === COLOR ENGINE PRO ===
│   ├── color_engine/            # Micro-service Streamlit
│   │   ├── app.py               # UI Streamlit + OpenCV
│   │   ├── requirements.txt
│   │   ├── render.yaml
│   │   └── README.md
│   │
│   ├── # === VIDÉO AI ===
│   ├── services/
│   │   ├── video_generator.py   # Génération vidéos Fal.ai
│   │   └── wix_media.py
│   │
│   └── exports/                 # Fichiers générés
│       ├── facebook.py          # Code pour Render API
│       └── luxura-facebook-update.zip
│
├── scripts/                     # Scripts standalone
│   ├── wix_seo_push_corrected.py    # Push SEO complet
│   ├── rename_handtied_products.py  # Renommage Hand-Tied
│   └── fix_genius_skus_wix.py       # Fix SKUs Genius
│
├── frontend/                    # Application Expo React Native
│   ├── app/                     # Routes (expo-router)
│   │   ├── index.tsx            # Page d'accueil
│   │   ├── _layout.tsx          # Layout principal
│   │   ├── admin.tsx            # Dashboard admin
│   │   └── (tabs)/              # Navigation par onglets
│   ├── components/              # Composants réutilisables
│   ├── contexts/                # React Context (Auth, Cart)
│   └── .env
│
└── luxura-inventory-api/        # API Render (GitHub)
    ├── app/
    │   ├── main.py              # Point d'entrée
    │   └── routes/
    │       ├── products.py
    │       ├── facebook.py      # 🆕 Endpoints Facebook
    │       ├── wix_seo_push.py
    │       ├── wix_oauth.py
    │       ├── wix_token.py
    │       └── wix_webhooks.py
    └── requirements.txt
```

---

## 🔄 Flux de données

### 1. Publication Facebook

```
┌─────────────────┐     POST /facebook/post     ┌──────────────────┐
│   App Locale    │ ──────────────────────────> │   Render API     │
│   ou Client     │                             │   (Centralisé)   │
└─────────────────┘                             └────────┬─────────┘
                                                         │
                                                         │ Graph API v25.0
                                                         ▼
                                                ┌──────────────────┐
                                                │   Facebook       │
                                                │   Page Luxura    │
                                                │   ID: 183841...  │
                                                └──────────────────┘
```

### 2. Génération Noms SEO Images

```
┌─────────────────┐
│   Requête       │  product_type=genius
│   /api/seo/     │  color_codes=60a
│   filename-gen  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     Rotation          ┌─────────────────┐
│   Type Produit  │ ──────────────────>   │   Régions       │
│   Genius/Tape/  │                       │   Québec/Beauce │
│   Halo/I-Tip    │                       │   Lévis/...     │
└────────┬────────┘                       └────────┬────────┘
         │                                         │
         ▼                                         ▼
┌──────────────────────────────────────────────────────────┐
│   Génération Nom Fichier SEO                             │
│   luxura-rallonge-genius-blond-platine-quebec-20po.jpg   │
│   luxura-extension-genius-blond-platine-beauce-20po.jpg  │
│   luxura-rallonge-genius-blond-platine-levis-20po.jpg    │
└──────────────────────────────────────────────────────────┘
```

### 3. Synchronisation Produits

```
┌─────────────┐     Sync      ┌──────────────────┐     Query     ┌─────────────┐
│   Wix API   │ ────────────> │  Render API      │ <──────────── │  Frontend   │
│  (Source)   │               │  (PostgreSQL)    │               │   (Expo)    │
└─────────────┘               └──────────────────┘               └─────────────┘
       │                              │
       │ Update                       │ Cache
       ▼                              ▼
┌─────────────┐               ┌──────────────────┐
│  Scripts    │               │  MongoDB Local   │
│  SEO Push   │               │  (Auth, Cart)    │
└─────────────┘               └──────────────────┘
```

### 4. Génération Blog + Publication Facebook

```
┌─────────────┐     Generate    ┌──────────────┐     Image      ┌─────────────┐
│   Cron Job  │ ──────────────> │   GPT-4o     │ ─────────────> │   DALL-E 3  │
│  (Schedule) │                 │  (Content)   │                │   (Cover)   │
└─────────────┘                 └──────────────┘                └─────────────┘
                                       │                               │
                                       │ HTML                          │ PNG
                                       ▼                               ▼
                               ┌──────────────┐                ┌─────────────┐
                               │   Wix Blog   │                │ Logo Overlay│
                               │   API        │                └─────────────┘
                               └──────┬───────┘
                                      │
                                      │ Published
                                      ▼
                               ┌──────────────┐
                               │   Facebook   │  POST /facebook/post-blog
                               │   Auto-Post  │
                               └──────────────┘
```

---

## 🔌 APIs Externes

### Facebook Graph API

| Service | URL | Auth |
|---------|-----|------|
| Pages API | `https://graph.facebook.com/v25.0/{page_id}/feed` | Page Access Token |
| Photos API | `https://graph.facebook.com/v25.0/{page_id}/photos` | Page Access Token |

### Wix REST API

| Service | URL | Auth |
|---------|-----|------|
| Stores API | `https://www.wixapis.com/stores/v1` | `Authorization: IST.xxx` |
| Blog API | `https://www.wixapis.com/blog/v3` | Idem |
| Media API | `https://www.wixapis.com/site-media/v1` | Idem |

### OpenAI API (via Emergent)

| Service | Modèle | Usage |
|---------|--------|-------|
| Chat Completions | GPT-4o | Génération contenu blog |
| Images | DALL-E 3 | Génération images blog |
| Images | gpt-image-1 | Génération marketing |

### Fal.ai API

| Service | Usage |
|---------|-------|
| Image-to-Video | Génération vidéos marketing produits |

---

## 📊 Endpoints Complets

### API Locale (http://localhost:8001/api)

```
# === FACEBOOK ===
GET  /facebook/status           # Statut connexion (local + Render)
POST /facebook/post             # Publier message/lien/image
POST /facebook/post-blog        # Publier article blog formaté
POST /facebook/update-token     # Mettre à jour token local

# === SEO IMAGES ===
GET  /seo/filename-generator    # Générer noms fichiers SEO
GET  /seo/config                # Configuration SEO disponible
POST /seo/image/generate        # Données SEO complètes pour 1 produit
GET  /seo/image/preview         # Prévisualiser variations géo

# === BLOG ===
POST /blog/generate             # Générer brouillon
POST /blog/publish/{id}         # Publier brouillon
GET  /blog/drafts               # Liste brouillons
GET  /blog/posts                # Liste publiés
GET  /blog/calendar             # Statut calendrier

# === PRODUITS ===
GET  /products                  # Liste produits
GET  /products/{id}             # Détails produit
GET  /categories                # Liste catégories
GET  /colors                    # Liste couleurs

# === WIX ===
GET  /wix/capabilities          # Capacités API Wix
POST /wix/token/refresh         # Refresh OAuth token
```

### API Render (https://luxura-inventory-api.onrender.com)

```
# === FACEBOOK ===
GET  /facebook/status           # Statut connexion
GET  /facebook/test             # Test rapide
POST /facebook/post             # Publier
POST /facebook/post-blog        # Publier blog formaté

# === WIX SEO ===
POST /wix/seo/push_preview      # Prévisualiser changements SEO
POST /wix/seo/push_apply        # Appliquer changements

# === WIX TOKEN ===
POST /wix/token                 # Générer/refresh OAuth token

# === PRODUITS ===
GET  /products                  # Liste produits synchronisés
GET  /inventory/view            # Vue inventaire
```

---

## 📊 Bases de données

### MongoDB Local

```javascript
// Collection: blog_posts
{
  _id: ObjectId,
  title: String,
  slug: String,
  content_html: String,
  category: "entretien" | "guide" | "comparatif" | "b2b_salon",
  status: "draft" | "published",
  wix_post_id: String,
  facebook_post_id: String,  // 🆕
  created_at: Date,
  published_at: Date,
  topic_hash: String
}

// Collection: users
{
  _id: ObjectId,
  email: String,
  password_hash: String,
  role: "client" | "salon" | "admin"
}
```

### PostgreSQL (Render)

```sql
-- Table: products
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  wix_id VARCHAR(100) UNIQUE,
  name VARCHAR(255),
  sku VARCHAR(50),
  price DECIMAL(10,2),
  collection_ids TEXT[],
  synced_at TIMESTAMP
);

-- Table: salons
CREATE TABLE salons (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  email VARCHAR(255),
  status VARCHAR(20) DEFAULT 'active'
);
```

---

## 🔐 Variables d'environnement

### /app/backend/.env (Local)

```env
# === WIX ===
WIX_API_KEY=IST.eyJ...
WIX_SITE_ID=6e62c946-d068-45c1-8f5f-7af998f0d7b3

# === FACEBOOK ===
FB_PAGE_ID=1838415193042352
FB_PAGE_ACCESS_TOKEN=EAAU4dnLcR8IB...

# === AI ===
EMERGENT_LLM_KEY=...
FAL_KEY=...

# === DATABASE ===
MONGO_URL=mongodb://...

# === RENDER API ===
LUXURA_API_URL=https://luxura-inventory-api.onrender.com
```

### Render Environment Variables

```env
# === WIX ===
WIX_CLIENT_ID=...
WIX_CLIENT_SECRET=...
WIX_REFRESH_TOKEN=...

# === FACEBOOK ===
FB_PAGE_ID=1838415193042352
FB_PAGE_ACCESS_TOKEN=EAAU4dnLcR8IB...

# === DATABASE ===
DATABASE_URL=postgresql://...
```

---

## 🚀 Déploiement

### Services Locaux

| Service | Port | Commande |
|---------|------|----------|
| Backend FastAPI | 8001 | `sudo supervisorctl restart backend` |
| Frontend Expo | 3000 | `sudo supervisorctl restart expo` |
| MongoDB | 27017 | Auto |

### Services Render

| Service | URL | Auto-deploy |
|---------|-----|-------------|
| luxura-inventory-api | https://luxura-inventory-api.onrender.com | GitHub push |

### URLs de production

| Service | URL |
|---------|-----|
| Site Wix | https://www.luxuradistribution.com |
| API Render | https://luxura-inventory-api.onrender.com |
| Page Facebook | https://www.facebook.com/1838415193042352 |

---

## 📈 Monitoring

### Logs

```bash
# Backend
tail -f /var/log/supervisor/backend.err.log

# Expo
tail -f /var/log/supervisor/expo.err.log
```

### Health Checks

```bash
# Local
curl http://localhost:8001/api/ping

# Render
curl https://luxura-inventory-api.onrender.com/health

# Facebook
curl https://luxura-inventory-api.onrender.com/facebook/test
```

---

## 🔧 Maintenance

### Tâches Cron

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| Blog generation | Selon calendrier | Génère brouillons |
| Render ping | 5 min | Garde API éveillée |
| Wix token refresh | 3h | Renouvelle OAuth |

### Tokens à surveiller

| Token | Expiration | Renouvellement |
|-------|------------|----------------|
| Wix OAuth | 14 jours | Auto via cron |
| Facebook Page | ~60 jours | Manuel via Graph Explorer |

---

## 📞 Contacts

- **Email:** info@luxuradistribution.com
- **Téléphone:** 418-774-4315
- **Adresse:** 8905 Boulevard Lacroix, Saint-Georges, QC G5Y 1T4

---

*Dernière mise à jour: Avril 2025*
