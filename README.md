# Luxura Distribution - Application Mobile

Application mobile e-commerce pour Luxura Distribution (extensions de cheveux professionnels).

## Architecture

```
├── /app/frontend/          # Application Expo (React Native)
├── /app/backend/           # API FastAPI (proxy local)
├── Render: luxura_inventory_api       # API principale
├── Render: luxura_inventory_sync_cron # Cron synchronisation
└── Supabase               # Base de données PostgreSQL
```

---

## ⚠️ VARIABLES D'ENVIRONNEMENT COMPLÈTES

### 1. Backend Local (`/app/backend/.env`)

```env
# MongoDB Local
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"

# Emergent LLM Key
EMERGENT_LLM_KEY=sk-emergent-c23DdEcC8C04049755

# ==================== WIX API ====================
WIX_API_KEY=IST.eyJraWQiOiJQb3pIX2FDMiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjoie1wiaWRcIjpcIjYzNzc3NDkyLWMxYWUtNDdkZS1iYWJlLTQ1MDYzYTg4Y2Y5MFwiLFwiaWRlbnRpdHlcIjp7XCJ0eXBlXCI6XCJhcHBsaWNhdGlvblwiLFwiaWRcIjpcImRlOTc0ZTRjLTg0YTUtNDhmNy1hMzEwLWU5OGRlOWM4ZTFkNVwifSxcInRlbmFudFwiOntcInR5cGVcIjpcImFjY291bnRcIixcImlkXCI6XCJmMWI5NjFlZC04MmQ2LTRiMzgtOTY3Yi01NTdhMGMzNDUxNjVcIn19IiwiaWF0IjoxNzY0MzU4MjU1fQ.A0WDKrxYuUcCKdOkA9mT550__khyEbUxObTS3Mq87ZKW6UGPiwVuw-V3mylYq-W95-0yFkQueUirX1-yCDJDTQcnGB6AEnHDgF2Z3OnxZLg6dpKbCc3qOCCNTKYPXRpowdfEenrIDc0knGccjtc-iRBXjlMuFbMeu92mVv0gIk236ING73TP8nHcsc8z6aBK-YNyUs1qzg8N3EbVy3e3XNGgK1889X6-5Lj0t_dw2v68S2YZz412XZGhC4kOnoZWvh5WRytgZIkxsjsnY2r8y5BCZbPKuQoRYRQtlEJU4THceXhQZhmrsCiP9Nb8_xuv7_q3xzfXazFJ0g7RSe3ddw
WIX_SITE_ID=6e62c946-d068-45c1-8f5f-7af998f0d7b3

# ==================== WIX OAUTH ====================
WIX_INSTANCE_ID=ab8a5a88-69a5-4348-ad2e-06017de46f57
WIX_CLIENT_ID=1969322e-ef8d-4aa4-90e1-d6fd3eb994ff
WIX_CLIENT_SECRET=58e2d7b7-5a8d-44dc-bd74-b9e0c37c58fc
WIX_ACCOUNT_ID=f1b961ed-82d6-4b38-967b-557a0c345165
WIX_OAUTH_SCOPES=SCOPE.DC-STORES-MEGA.MANAGE-STORES
WIX_REDIRECT_URL=https://luxura-inventory-api.onrender.com/wix/oauth/callback

# ==================== SECRETS ====================
WIX_PUSH_SECRET=9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f
SEO_SECRET=9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f

# ==================== SUPABASE ====================
DATABASE_URL=postgresql+psycopg://postgres.cpnwntahrkfpenjsqzsy:Lianagir20180921@aws-1-ca-central-1.pooler.supabase.com:5432/postgres?sslmode=require

# ==================== EMAIL ====================
LUXURA_EMAIL=info@luxuradistribution.com
LUXURA_APP_PASSWORD=zgvsfiajermjqpgh

# ==================== INVENTAIRE ====================
LUXURA_SALON_ID=4
```

---

### 2. Render: `luxura_inventory_api` (API principale)

URL: `https://luxura-inventory-api.onrender.com`

```env
# ==================== SUPABASE ====================
DATABASE_URL=postgresql+psycopg://postgres.cpnwntahrkfpenjsqzsy:Lianagir20180921@aws-1-ca-central-1.pooler.supabase.com:5432/postgres?sslmode=require

# ==================== CORS ====================
CORS_ORIGINS=https://editor.wix.com,https://www.wix.com,https://static.parastorage.com,https://*.wixsite.com,https://*.wixstudio.io,https://*.wix.com

# ==================== WIX API ====================
WIX_API_KEY=IST.eyJraWQiOiJQb3pIX2FDMiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjoie1wiaWRcIjpcIjYzNzc3NDkyLWMxYWUtNDdkZS1iYWJlLTQ1MDYzYTg4Y2Y5MFwiLFwiaWRlbnRpdHlcIjp7XCJ0eXBlXCI6XCJhcHBsaWNhdGlvblwiLFwiaWRcIjpcImRlOTc0ZTRjLTg0YTUtNDhmNy1hMzEwLWU5OGRlOWM4ZTFkNVwifSxcInRlbmFudFwiOntcInR5cGVcIjpcImFjY291bnRcIixcImlkXCI6XCJmMWI5NjFlZC04MmQ2LTRiMzgtOTY3Yi01NTdhMGMzNDUxNjVcIn19IiwiaWF0IjoxNzY0MzU4MjU1fQ.A0WDKrxYuUcCKdOkA9mT550__khyEbUxObTS3Mq87ZKW6UGPiwVuw-V3mylYq-W95-0yFkQueUirX1-yCDJDTQcnGB6AEnHDgF2Z3OnxZLg6dpKbCc3qOCCNTKYPXRpowdfEenrIDc0knGccjtc-iRBXjlMuFbMeu92mVv0gIk236ING73TP8nHcsc8z6aBK-YNyUs1qzg8N3EbVy3e3XNGgK1889X6-5Lj0t_dw2v68S2YZz412XZGhC4kOnoZWvh5WRytgZIkxsjsnY2r8y5BCZbPKuQoRYRQtlEJU4THceXhQZhmrsCiP9Nb8_xuv7_q3xzfXazFJ0g7RSe3ddw
WIX_SITE_ID=6e62c946-d068-45c1-8f5f-7af998f0d7b3
WIX_ACCOUNT_ID=f1b961ed-82d6-4b38-967b-557a0c345165

# ==================== WIX OAUTH ====================
WIX_CLIENT_ID=1969322e-ef8d-4aa4-90e1-d6fd3eb994ff
WIX_CLIENT_SECRET=58e2d7b7-5a8d-44dc-bd74-b9e0c37c58fc
WIX_INSTANCE_ID=ab8a5a88-69a5-4348-ad2e-06017de46f57
WIX_OAUTH_SCOPES=SCOPE.DC-STORES-MEGA.MANAGE-STORES
WIX_REDIRECT_URL=https://luxura-inventory-api.onrender.com/wix/oauth/callback

# ==================== SECRETS ====================
WIX_PUSH_SECRET=9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f
SEO_SECRET=9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f

# ==================== INVENTAIRE ====================
LUXURA_SALON_ID=4
```

---

### 3. Render: `luxura_inventory_sync_cron` (Cron Job)

```env
# ==================== SUPABASE ====================
DATABASE_URL=postgresql+psycopg://postgres.cpnwntahrkfpenjsqzsy:Lianagir20180921@aws-1-ca-central-1.pooler.supabase.com:5432/postgres?sslmode=require

# ==================== PYTHON ====================
PYTHON_VERSION=3.12.7
PYTHONUNBUFFERED=1

# ==================== WIX API (différent de l'API principale) ====================
WIX_API_KEY=IST.eyJraWQiOiJQb3pIX2FDMiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjoie1wiaWRcIjpcIjJjYjMzMjgzLTNlNTYtNDExOS04OGQ5LWU0YTQ0NjE4MDBkOFwiLFwiaWRlbnRpdHlcIjp7XCJ0eXBlXCI6XCJhcHBsaWNhdGlvblwiLFwiaWRcIjpcIjdkNjc2ZWM5LWZjMDAtNGI5NC1hMDUyLTEwNDNmODc4ZDQ4NlwifSxcInRlbmFudFwiOntcInR5cGVcIjpcImFjY291bnRcIixcImlkXCI6XCJmMWI5NjFlZC04MmQ2LTRiMzgtOTY3Yi01NTdhMGMzNDUxNjVcIn19IiwiaWF0IjoxNzY0MDIyMzEwfQ.OVzQv7PhALsLDcjHgTp9MCIeXMDrFfgPHKhRc2iNyRFUyJAbA3soVT_oT9WKlnvJJ8PdiYQ83MMR4pdxOpfMcBNMMSPRBfSfP4aBHhhKAuZe6JiFz_jKY2bGdku3WJszbtd4_Laj8Ij-0xpk5_udcP_JXxiUyckK2N3A625fbjOQjQ29-v0huXvabfGeSZTw1IHMS1qRt-bVST3N1pu7lQgwjm0-fbkEajkst5wrhwY4QtUFi7iVkPKCLJZPCYDi5qXBcmeMBH9pE745whHpdexDYVpe3glMGin1FHTziTJwP_Nyc7MBZERWFk-Vct3EXAvy3lNh-KTN0dFqiJ89GA
WIX_SITE_ID=6e62c946-d068-45c1-8f5f-7af998f0d7b3

# ==================== WIX OAUTH ====================
WIX_CLIENT_ID=1969322e-ef8d-4aa4-90e1-d6fd3eb994ff
WIX_CLIENT_SECRET=58e2d7b7-5a8d-44dc-bd74-b9e0c37c58fc
WIX_INSTANCE_ID=ab8a5a88-69a5-4348-ad2e-06017de46f57

# ==================== SECRETS ====================
WIX_PUSH_SECRET=9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f
```

---

### 4. Frontend Expo (`/app/frontend/.env`)

```env
EXPO_PUBLIC_BACKEND_URL=/api
```

---

## Structure Base de Données (Supabase)

**Connection:** `postgres.cpnwntahrkfpenjsqzsy` @ `aws-1-ca-central-1.pooler.supabase.com`

### Tables principales

| Table | Description |
|-------|-------------|
| `product` | Catalogue produits (wix_id, sku, name, price, options) |
| `salon` | Points de stockage (id, name, code, is_active) |
| `inventory_item` | Pivot salon×produit (salon_id, product_id, quantity) |
| `sync_runs` | État des synchronisations Wix |

### Logique Multi-Salons

- **Salon ID 4** = Inventaire principal Wix (source de vérité)
- Autres salons = Inventaire déduit/transféré

---

## Catégories de Produits

| Catégorie | Série | Type |
|-----------|-------|------|
| Genius | Vivian | Trame invisible ultra-fine 0.78mm |
| Halo | Everly | Fil invisible ajustable |
| Tape | Aurora | Bande adhésive médicale |
| I-Tip | Eleanor | Fusion kératine mèche par mèche |
| Ponytail | Victoria | Queue de cheval wrap-around |
| Clip-In | Sophia | Extensions à clips amovibles |
| Essentiels | Luxura | Outils et entretien |

---

## Endpoints API

### API Locale (Backend Emergent)

| Endpoint | Description |
|----------|-------------|
| `GET /api/products` | Liste tous les produits |
| `GET /api/products?category=halo` | Filtre par catégorie |
| `GET /api/products/{id}` | Détails d'un produit + variantes |
| `GET /api/categories` | Liste des catégories |
| `GET /api/ping` | Health check |

### API Render (luxura-inventory-api.onrender.com)

| Endpoint | Description |
|----------|-------------|
| `GET /products` | Liste produits Supabase |
| `GET /products/{id}` | Détails produit |
| `GET /inventory/view` | Vue jointe produit + quantités |
| `GET /inventory/export.xlsx` | Export Excel |
| `GET /salons` | Liste des salons |
| `POST /wix/sync` | Déclencher synchronisation |

---

## Commandes

```bash
# Démarrer le backend
sudo supervisorctl restart backend

# Démarrer le frontend
sudo supervisorctl restart expo

# Voir les logs
sudo supervisorctl tail -f backend
sudo supervisorctl tail -f expo
```

---

## ⚠️ Notes Importantes

- **NE PAS MODIFIER** les SKUs ou la base Wix/Supabase (nettoyage complet effectué)
- **115 produits** synchronisés avec **229 variantes**
- Toutes les variantes ont un SKU valide
- L'inventaire du **Salon ID 4** est la source de vérité
- **2 services Render** : API + Cron (clés WIX_API_KEY différentes!)

---

## Contact

Luxura Distribution - Extensions de cheveux professionnels
Québec, Canada
- Site: www.luxuradistribution.com
- Email: info@luxuradistribution.com

---

## Fonctionnalités Automatisées

### 1. Système de Backlinks Automatiques

**Endpoint**: `POST /api/backlinks/run`

Lance l'automatisation Playwright pour soumettre Luxura aux annuaires d'entreprises :
- Soumission automatique aux directories
- Capture d'écran de confirmation
- Vérification des emails de confirmation

**Variables requises**:
```env
LUXURA_EMAIL=info@luxuradistribution.com
LUXURA_APP_PASSWORD=zgvsfiajermjqpgh  # Mot de passe d'application Gmail
```

**Status**: `GET /api/backlinks/status`

### 2. Génération de Blog SEO avec IA

**Endpoint**: `POST /api/blog/generate`

Génère automatiquement un article de blog optimisé SEO en utilisant l'IA (Emergent LLM).

**Variables requises**:
```env
EMERGENT_LLM_KEY=sk-emergent-c23DdEcC8C04049755
```

**Endpoints blog**:
- `GET /api/blog` - Liste tous les articles
- `GET /api/blog/{id}` - Article spécifique
- `POST /api/blog/generate` - Générer nouvel article
- `DELETE /api/blog/{id}` - Supprimer un article

### 3. Publication automatique sur Wix (À CONFIGURER)

Pour publier automatiquement les blogs sur Wix :

1. **API Wix Blog** : Utiliser l'endpoint `/wix/seo/push_apply` sur l'API Render
2. **Cron Job** : Configurer sur Render pour exécuter quotidiennement

**Commande cron suggérée**:
```bash
# Tous les jours à 9h00
0 9 * * * curl -X POST https://luxura-inventory-api.onrender.com/blog/generate
```

### 4. Vérification automatique des emails (Backlinks)

**Endpoint**: `POST /api/backlinks/auto-verify`

Vérifie automatiquement les emails de confirmation reçus pour les backlinks soumis.

---

## Cron Jobs Recommandés

| Tâche | Fréquence | Endpoint |
|-------|-----------|----------|
| Sync Wix → Supabase | Toutes les 6h | `/wix/sync` |
| Génération Blog | Quotidien 9h | `/api/blog/generate` |
| Vérification Backlinks | Quotidien 10h | `/api/backlinks/auto-verify` |
