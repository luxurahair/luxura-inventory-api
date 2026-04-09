# 🌟 Luxura Distribution - Application Mobile & Système d'Automatisation

> **Plateforme complète** de gestion automatisée pour extensions capillaires professionnelles au Québec.

---

## 📋 Table des matières

1. [Architecture Globale](#architecture-globale)
2. [Stack Technique](#stack-technique)
3. [Variables d'Environnement](#variables-denvironnement)
4. [Configuration Supabase](#configuration-supabase)
5. [Configuration Render](#configuration-render)
6. [API Endpoints](#api-endpoints)
7. [Application Mobile](#application-mobile)
8. [Commandes Utiles](#commandes-utiles)

---

## 🏗️ Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LUXURA DISTRIBUTION                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐      ┌──────────────────┐      ┌────────────────┐ │
│  │   EXPO MOBILE    │      │  FASTAPI PROXY   │      │   RENDER API   │ │
│  │   /app/frontend  │ ──▶  │  /app/backend    │ ──▶  │   (External)   │ │
│  │                  │      │                  │      │                │ │
│  │  • React Native  │      │  • Port 8001     │      │  luxura-       │ │
│  │  • Expo Router   │      │  • MongoDB local │      │  inventory-api │ │
│  │  • Zustand       │      │  • Auth/Cart     │      │                │ │
│  │  • Port 3000     │      │  • Blog CRON     │      │  • Wix Sync    │ │
│  └──────────────────┘      └──────────────────┘      │  • Supabase DB │ │
│           │                         │                │  • Facebook    │ │
│           │                         │                └────────────────┘ │
│           │                         │                        │          │
│           ▼                         ▼                        ▼          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                         BASES DE DONNÉES                          │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  MongoDB (Local)           │    Supabase (Cloud - PostgreSQL)    │   │
│  │  • Users                   │    • Products (Wix sync)            │   │
│  │  • Sessions                │    • Inventory_items                │   │
│  │  • Cart items              │    • Salons                         │   │
│  │  • Blog drafts             │    • Categories                     │   │
│  │  • Marketing jobs          │    • Blog posts                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    INTÉGRATIONS EXTERNES                          │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  Wix Store API  │  Facebook Graph  │  OpenAI GPT  │  Fal.ai     │   │
│  │  • Products     │  • Page posts    │  • Blog gen  │  • Videos   │   │
│  │  • Inventory    │  • Scheduling    │  • SEO       │  • Images   │   │
│  │  • Blog posts   │                  │              │             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Technique

### Frontend (Application Mobile)
| Composant | Technologie | Version |
|-----------|-------------|---------|
| Framework | Expo (React Native) | SDK 52 |
| Routing | expo-router | 4.x |
| State | Zustand | 5.x |
| UI | React Native + Custom |
| Images | expo-image | 2.x |
| Auth | Google OAuth (Emergent) |

### Backend Local (Proxy)
| Composant | Technologie | Version |
|-----------|-------------|---------|
| Framework | FastAPI | 0.115+ |
| Database | MongoDB | 7.x |
| Auth | JWT Sessions |
| Scheduler | APScheduler | 3.x |

### Backend Render (API Principale)
| Composant | Technologie |
|-----------|-------------|
| Framework | FastAPI |
| Database | Supabase (PostgreSQL) |
| ORM | SQLModel |
| Hosting | Render.com |

---

## 🔐 Variables d'Environnement

### Frontend (`/app/frontend/.env`)
```env
EXPO_TUNNEL_SUBDOMAIN=hair-extensions-shop
EXPO_PACKAGER_HOSTNAME=https://hair-extensions-shop.preview.emergentagent.com
EXPO_PUBLIC_BACKEND_URL=https://hair-extensions-shop.preview.emergentagent.com
EXPO_USE_FAST_RESOLVER="1"
METRO_CACHE_ROOT=/app/frontend/.metro-cache
```

### Backend Local (`/app/backend/.env`)
```env
# === MONGODB (Local) ===
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"

# === AI / LLM ===
EMERGENT_LLM_KEY=sk-emergent-xxxxx
OPENAI_API_KEY=sk-proj-xxxxx

# === WIX API ===
WIX_API_KEY=IST.eyJ...
WIX_SITE_ID=6e62c946-d068-45c1-8f5f-7af998f0d7b3
WIX_INSTANCE_ID=ab8a5a88-69a5-4348-ad2e-06017de46f57
WIX_CLIENT_ID=1969322e-ef8d-4aa4-90e1-d6fd3eb994ff
WIX_CLIENT_SECRET=58e2d7b7-5a8d-44dc-bd74-b9e0c37c58fc
WIX_ACCOUNT_ID=f1b961ed-82d6-4b38-967b-557a0c345165
WIX_OAUTH_SCOPES=SCOPE.DC-STORES-MEGA.MANAGE-STORES
WIX_REDIRECT_URL=https://luxura-inventory-api.onrender.com/wix/oauth/callback

# === SUPABASE ===
DATABASE_URL=postgresql+psycopg://postgres.xxxxx:password@aws-1-ca-central-1.pooler.supabase.com:5432/postgres?sslmode=require

# === FACEBOOK ===
FB_PAGE_ID=1838415193042352
FB_PAGE_ACCESS_TOKEN=EAAU4dnLcR8IB...

# === FAL.AI (Video Generation) ===
FAL_KEY=xxxxx:xxxxx

# === EMAIL (IMAP/SMTP) ===
LUXURA_EMAIL=info@luxuradistribution.com
LUXURA_APP_PASSWORD=xxxxx
EMAIL_USERNAME=info@luxuradistribution.com
EMAIL_PASSWORD=xxxxx
IMAP_HOST=imap.gmail.com
IMAP_PORT=993

# === GOOGLE DRIVE ===
GOOGLE_DRIVE_FOLDER_ID=0AP66guFE3lalUk9PVA
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# === SECRETS ===
WIX_PUSH_SECRET=xxxxx
SEO_SECRET=xxxxx

# === INVENTAIRE ===
LUXURA_SALON_ID=4
```

---

## 🗄️ Configuration Supabase

### Accès Dashboard
- **URL:** https://supabase.com/dashboard/project/cpnwntahrkfpenjsqzsy
- **Projet:** `cpnwntahrkfpenjsqzsy`
- **Région:** `aws-1-ca-central-1` (Montréal)

### Connection String
```
postgresql://postgres.cpnwntahrkfpenjsqzsy:[PASSWORD]@aws-1-ca-central-1.pooler.supabase.com:5432/postgres
```

### Tables Principales
| Table | Description | Colonnes clés |
|-------|-------------|---------------|
| `product` | Produits synchronisés depuis Wix | `id`, `wix_id`, `sku`, `name`, `category`, `quantity`, `price` |
| `inventory_item` | Stock par salon | `product_id`, `salon_id`, `quantity` |
| `salon` | Liste des salons partenaires | `id`, `name`, `email`, `is_active` |
| `blog` | Articles de blog | `id`, `title`, `content`, `wix_post_id` |

### Schéma Product
```sql
CREATE TABLE product (
    id SERIAL PRIMARY KEY,
    wix_id VARCHAR(255) UNIQUE,
    wix_variant_id VARCHAR(255),
    sku VARCHAR(100),
    name VARCHAR(500),
    handle VARCHAR(500),
    description TEXT,
    price DECIMAL(10,2),
    quantity INTEGER DEFAULT 0,
    category VARCHAR(100),  -- genius, halo, tape, i-tip, etc.
    is_in_stock BOOLEAN DEFAULT true,
    options JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 Configuration Render

### Service Principal
- **URL:** https://luxura-inventory-api.onrender.com
- **Repo GitHub:** luxura-inventory-api
- **Type:** Web Service (Python)
- **Region:** Oregon (US West)

### Variables Render (Environment)
```env
# Base de données
DATABASE_URL=postgresql+psycopg://...

# Wix
WIX_API_KEY=IST.eyJ...
WIX_SITE_ID=...
WIX_CLIENT_ID=...
WIX_CLIENT_SECRET=...
WIX_ACCOUNT_ID=...

# Facebook
FB_PAGE_ID=...
FB_PAGE_ACCESS_TOKEN=...

# Secrets
SEO_SECRET=...
WIX_PUSH_SECRET=...

# Email
LUXURA_EMAIL=...
LUXURA_APP_PASSWORD=...
```

### CRON Jobs (Render)
| Job | Fréquence | Endpoint | Description |
|-----|-----------|----------|-------------|
| Wix Sync | Toutes les 15 min | `POST /wix/sync` | Synchronise produits Wix → Supabase |
| Keep Alive | Toutes les 10 min | `GET /health` | Garde le service actif |

### Fichier cron.yaml (Render)
```yaml
jobs:
  - name: wix-sync
    schedule: "*/15 * * * *"
    command: "python scripts/sync_wix_to_luxura.py"
    env:
      X-SEO-SECRET: ${SEO_SECRET}
```

---

## 🔌 API Endpoints

### Backend Local (http://localhost:8001/api)

#### Authentification
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/auth/session` | POST | Échange session_id pour token |
| `/auth/me` | GET | Utilisateur courant |
| `/auth/logout` | POST | Déconnexion |

#### Produits (Proxy vers Luxura API)
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/products` | GET | Liste tous les produits |
| `/products?category=halo` | GET | Filtre par catégorie |
| `/products/{handle}` | GET | Détail produit par handle |
| `/categories` | GET | Liste des catégories |

#### Panier
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/cart` | GET | Contenu du panier |
| `/cart` | POST | Ajouter au panier |
| `/cart/{id}` | PUT | Modifier quantité |
| `/cart/{id}` | DELETE | Supprimer item |

#### Blog
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/blog/posts` | GET | Liste des articles |
| `/blog/posts/{id}` | GET | Détail article |
| `/blog/generate` | POST | Générer brouillon AI |
| `/blog/drafts` | GET | Brouillons en attente |

#### Marketing
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/marketing/jobs` | GET | Jobs marketing actifs |
| `/marketing/generate-legend` | POST | Générer légende social |
| `/facebook/post` | POST | Publier sur Facebook |

### Render API (https://luxura-inventory-api.onrender.com)

#### Synchronisation Wix
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/wix/sync` | POST | Déclenche sync manuelle |
| `/wix/token` | POST | Refresh OAuth token |
| `/wix/capabilities` | GET | Capacités API Wix |

#### Inventaire
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/products` | GET | Tous les produits |
| `/inventory/view` | GET | Vue inventaire complète |
| `/inventory/export.xlsx` | GET | Export Excel |

#### Facebook
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/facebook/status` | GET | Statut connexion |
| `/facebook/post` | POST | Publier message |
| `/facebook/post-blog` | POST | Publier article |

---

## 📱 Application Mobile

### Navigation (Expo Router)
```
/app/frontend/app/
├── (tabs)/
│   ├── _layout.tsx      # Tab navigator
│   ├── index.tsx        # Accueil
│   ├── catalogue.tsx    # Catalogue produits
│   ├── salons.tsx       # Carte des salons
│   ├── blog.tsx         # Articles de blog
│   └── profile.tsx      # Profil utilisateur
├── product/
│   └── [id].tsx         # Page détail produit
├── blog/
│   └── [id].tsx         # Page détail article
├── cart.tsx             # Panier
├── login.tsx            # Connexion
├── marketing.tsx        # Dashboard marketing (admin)
└── admin.tsx            # Admin panel
```

### Stores Zustand
| Store | Fichier | Usage |
|-------|---------|-------|
| authStore | `/src/store/authStore.ts` | Auth, session, user |
| cartStore | `/src/store/cartStore.ts` | Panier, count |

### Catégories Produits
| ID | Nom | Série |
|----|-----|-------|
| `genius` | Genius Weft | Vivian |
| `halo` | Halo | Everly |
| `tape` | Bande Adhésive | Aurora |
| `i-tip` | I-Tip Kératine | Eleanor |
| `ponytail` | Queue de Cheval | Victoria |
| `clip-in` | Extensions Clips | Sophia |
| `essentiels` | Accessoires | - |

---

## 🚀 Commandes Utiles

### Services
```bash
# Redémarrer backend
sudo supervisorctl restart backend

# Redémarrer frontend Expo
sudo supervisorctl restart expo

# Voir statut tous les services
sudo supervisorctl status
```

### Logs
```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log

# Expo logs
tail -f /var/log/supervisor/expo.out.log

# Backend API requests
tail -f /var/log/supervisor/backend.out.log
```

### Tests API
```bash
# Tester produits
curl http://localhost:8001/api/products?limit=5

# Tester catégorie Halo
curl "http://localhost:8001/api/products?category=halo"

# Tester Facebook
curl https://luxura-inventory-api.onrender.com/facebook/status

# Tester sync Wix (avec secret)
curl -X POST https://luxura-inventory-api.onrender.com/wix/sync \
  -H "X-SEO-SECRET: votre_secret"
```

### Base de données
```bash
# MongoDB local
mongosh luxura_db

# Supabase (via psql)
psql "postgresql://postgres.cpnwntahrkfpenjsqzsy:PASSWORD@aws-1-ca-central-1.pooler.supabase.com:5432/postgres"
```

---

## 📞 Support

- **Email:** info@luxuradistribution.com
- **Téléphone:** 418-774-4315
- **Adresse:** 8905 Boulevard Lacroix, Saint-Georges, QC G5Y 1T4
- **Site Web:** https://www.luxuradistribution.com

---

*Dernière mise à jour: Avril 2025*
