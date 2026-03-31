# 🏗️ Architecture Technique - Luxura Distribution

> Documentation complète de l'architecture du système d'automatisation Wix & SEO.

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
│   ├── server.py                # Point d'entrée API (3681 lignes)
│   ├── requirements.txt         # Dépendances Python
│   │
│   ├── # === MODULES BLOG ===
│   ├── blog_automation.py       # Génération & publication blogs (2686 lignes)
│   ├── editorial_calendar.py    # Calendrier 2 semaines
│   ├── editorial_guard.py       # Anti-doublon intelligent
│   ├── image_generation.py      # DALL-E 3 + upload Wix
│   ├── internal_linking.py      # Maillage interne SEO
│   ├── logo_overlay.py          # Overlay logo sur images
│   ├── image_brief_generator.py # Génération briefs pour images
│   │
│   ├── # === MODULES SEO PRODUITS ===
│   ├── color_system.py          # 40+ couleurs avec noms luxueux
│   ├── seo_description_template.py  # Templates descriptions
│   ├── wix_seo_cleanup.py       # Nettoyage SEO
│   ├── wix_seo_fix.py           # Corrections SEO
│   ├── wix_description_fix.py   # Fix descriptions
│   │
│   ├── # === MODULES BACKLINKS (PAUSÉ) ===
│   ├── backlinks/               # Architecture V2 backlinks
│   │   ├── backlink_orchestrator.py
│   │   ├── backlink_routes.py
│   │   ├── directory_registry.py
│   │   └── models.py
│   ├── backlink_automation.py   # Automation Playwright (pausé)
│   ├── gmail_checker.py         # Vérification emails (pausé)
│   │
│   ├── # === DONNÉES GÉNÉRÉES ===
│   ├── data/
│   │   ├── page_devenir_revendeur_optimisee.md  # Contenu SEO page
│   │   └── schema_faq_revendeur.html            # Schema JSON-LD
│   │
│   └── services/                # Services utilitaires
│       └── wix_media.py
│
├── scripts/                     # Scripts standalone
│   ├── wix_seo_push_corrected.py    # Push SEO complet (1460 lignes)
│   ├── rename_handtied_products.py  # Renommage Hand-Tied
│   ├── fix_genius_skus_wix.py       # Fix SKUs Genius
│   └── wix_velo_fix_genius_skus.js  # Script Velo Wix
│
├── frontend/                    # Application Expo React Native
│   ├── app/                     # Routes (expo-router)
│   │   ├── index.tsx
│   │   ├── _layout.tsx
│   │   └── (tabs)/
│   ├── components/              # Composants réutilisables
│   ├── contexts/                # React Context (Auth, Cart)
│   ├── package.json
│   └── .env
│
├── luxura-inventory-api/        # API Render (synchronisation)
│   ├── app/
│   │   ├── main.py
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routes/              # API endpoints
│   │   │   ├── products.py
│   │   │   ├── wix_seo_push.py
│   │   │   ├── wix_webhooks.py
│   │   │   └── seo.py
│   │   └── services/
│   │       ├── wix_client.py    # Client API Wix
│   │       ├── wix_sync.py      # Synchronisation
│   │       └── catalog_normalizer.py
│   └── scripts/
│       ├── sync_wix_to_luxura.py
│       └── import_inventory_from_csv.py
│
└── tests/                       # Tests automatisés
```

---

## 🔄 Flux de données

### 1. Synchronisation Produits

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

### 2. Génération Blog

```
┌─────────────┐     Generate    ┌──────────────────┐     Upload     ┌─────────────┐
│   Cron Job  │ ──────────────> │   GPT-4o         │ ─────────────> │   DALL-E 3  │
│  (08:00 EST)│                 │  (Contenu SEO)   │                │   (Images)  │
└─────────────┘                 └──────────────────┘                └─────────────┘
                                        │                                  │
                                        │ HTML                             │ PNG
                                        ▼                                  ▼
                                ┌──────────────────┐               ┌─────────────┐
                                │   Editorial      │               │ Logo Overlay│
                                │   Guard          │               │ (Luxura)    │
                                │  (Anti-doublon)  │               └─────────────┘
                                └──────────────────┘                       │
                                        │                                  │
                                        │ Validated                        │
                                        ▼                                  ▼
                                ┌──────────────────────────────────────────────┐
                                │              Wix Blog API                    │
                                │         (Draft ou Publication)               │
                                └──────────────────────────────────────────────┘
```

### 3. Push SEO Produits

```
┌─────────────────┐
│ Script Python   │
│ ou API Endpoint │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     Query Products     ┌─────────────────┐
│ Wix API         │ ◄────────────────────── │ Filter by       │
│ (Products)      │                         │ Collection ID   │
└────────┬────────┘                         └─────────────────┘
         │
         │ For each product
         ▼
┌─────────────────┐
│ Detect Type     │  Genius? Tape? Halo? Hand-Tied? I-Tip?
│ (from name/SKU) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Color   │  #18/22 → "Champagne Doré"
│ (from name)     │  #1B → "Noir Soie"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate        │  HTML description with:
│ Description     │  - Type-specific features
│ (SEO Template)  │  - Color name
│                 │  - Quebec SEO keywords
│                 │  - Luxura branding
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PATCH Wix API   │  Update:
│ (Update Product)│  - name
│                 │  - description
│                 │  - sku
└─────────────────┘
```

---

## 🔌 APIs Externes

### Wix REST API

| Service | URL | Authentification |
|---------|-----|------------------|
| Stores API | `https://www.wixapis.com/stores/v1` | `Authorization: IST.xxx` + `wix-site-id` |
| Blog API | `https://www.wixapis.com/blog/v3` | Idem |
| Media API | `https://www.wixapis.com/site-media/v1` | Idem |

### Endpoints Wix utilisés

```
POST /stores/v1/products/query          # Lister produits
PATCH /stores/v1/products/{id}          # Modifier produit
POST /stores/v1/collections/query       # Lister collections
POST /blog/v3/draft-posts               # Créer brouillon
POST /blog/v3/posts/publish             # Publier article
POST /site-media/v1/files/upload-url    # Upload média
```

### OpenAI API

| Service | Modèle | Usage |
|---------|--------|-------|
| Chat Completions | GPT-4o | Génération contenu blog |
| Images | DALL-E 3 | Génération images blog |

### Luxura Inventory API (Render)

| Endpoint | Description |
|----------|-------------|
| `GET /products` | Liste produits synchronisés |
| `POST /seo/push-all` | Push SEO global |
| `GET /seo/status` | Statut dernier push |
| `POST /sync/wix` | Sync depuis Wix |

---

## 📊 Base de données

### MongoDB Local (Auth, Cart, Blog Cache)

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
  created_at: Date,
  published_at: Date,
  topic_hash: String,  // Anti-doublon
  keywords: [String]
}

// Collection: users
{
  _id: ObjectId,
  email: String,
  password_hash: String,
  role: "client" | "salon" | "admin",
  created_at: Date
}

// Collection: carts
{
  _id: ObjectId,
  user_id: ObjectId,
  items: [{ product_id, quantity, variant }],
  updated_at: Date
}
```

### PostgreSQL (Render - Inventaire)

```sql
-- Table: products
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  wix_id VARCHAR(100) UNIQUE,
  name VARCHAR(255),
  sku VARCHAR(50),
  price DECIMAL(10,2),
  description TEXT,
  collection_ids TEXT[],
  synced_at TIMESTAMP
);

-- Table: salons
CREATE TABLE salons (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(20),
  address TEXT,
  status VARCHAR(20) DEFAULT 'active'
);

-- Table: inventory_movements
CREATE TABLE inventory_movements (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES products(id),
  salon_id INTEGER REFERENCES salons(id),
  quantity INTEGER,
  type VARCHAR(20),  -- 'deposit' | 'sale' | 'return'
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔐 Sécurité

### Variables sensibles

| Variable | Localisation | Usage |
|----------|--------------|-------|
| `WIX_API_KEY` | `/app/backend/.env` | Authentification Wix API |
| `WIX_SITE_ID` | `/app/backend/.env` | Identification site Wix |
| `EMERGENT_LLM_KEY` | `/app/backend/.env` | OpenAI via Emergent |
| `LUXURA_APP_PASSWORD` | `/app/backend/.env` | Email SMTP |
| `MONGO_URL` | `/app/backend/.env` | MongoDB connection |

### Bonnes pratiques

- ✅ Toutes les clés dans `.env` (jamais en dur)
- ✅ `.env` dans `.gitignore`
- ✅ Validation des entrées utilisateur
- ✅ Rate limiting sur les endpoints sensibles

---

## 🚀 Déploiement

### Services

| Service | Port | Commande |
|---------|------|----------|
| Backend FastAPI | 8001 | `sudo supervisorctl restart backend` |
| Frontend Expo | 3000 | `sudo supervisorctl restart expo` |
| MongoDB | 27017 | Automatique |

### URLs

| Environnement | URL |
|---------------|-----|
| API Backend | `http://localhost:8001/api` |
| Frontend Web | `http://localhost:3000` |
| API Render | `https://luxura-inventory-api.onrender.com` |
| Site Wix | `https://www.luxuradistribution.com` |

---

## 📈 Monitoring

### Logs

```bash
# Backend
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/backend.out.log

# Frontend
tail -f /var/log/supervisor/expo.err.log
tail -f /var/log/supervisor/expo.out.log
```

### Health checks

```bash
# Backend health
curl http://localhost:8001/api/ping

# Luxura API health
curl https://luxura-inventory-api.onrender.com/products?limit=1
```

---

## 🔧 Maintenance

### Tâches planifiées (Cron)

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| Blog generation | Lun/Mer/Ven 08:00 EST | Génère brouillons selon calendrier |
| Luxura API ping | Toutes les 5 min | Garde l'API Render éveillée |

### Nettoyage

```bash
# Supprimer les logs anciens
find /var/log/supervisor -name "*.log" -mtime +30 -delete

# Vider le cache MongoDB
mongosh luxura_db --eval "db.cache.drop()"
```

---

## 📞 Contacts

- **Email technique:** info@luxuradistribution.com
- **Téléphone:** 418-774-4315
- **Adresse:** 8905 Boulevard Lacroix, Saint-Georges, QC G5Y 1T4

---

*Dernière mise à jour: Mars 2025*
