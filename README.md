# Luxura Distribution - Application Mobile

Application mobile e-commerce pour Luxura Distribution (extensions de cheveux professionnels).

## Architecture

```
├── /app/frontend/          # Application Expo (React Native)
├── /app/backend/           # API FastAPI (proxy local)
├── API Render externe      # luxura-inventory-api.onrender.com
└── Supabase               # Base de données PostgreSQL
```

---

## ⚠️ VARIABLES D'ENVIRONNEMENT COMPLÈTES

### Backend Local (`/app/backend/.env`)

```env
# MongoDB Local
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"

# Emergent LLM Key
EMERGENT_LLM_KEY=sk-emergent-c23DdEcC8C04049755

# ==================== WIX API ====================
WIX_API_KEY=IST.eyJraWQiOiJQb3pIX2FDMiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjoie1wiaWRcIjpcImM5MmRkY2UzLTYyYjItNGRkOS04MjMzLWUyODc0OGU3NDJlMlwiLFwiaWRlbnRpdHlcIjp7XCJ0eXBlXCI6XCJhcHBsaWNhdGlvblwiLFwiaWRcIjpcImIyOWFmMDE1LWEzZjEtNDFjMi1iYzI2LTQzMzUwODEyOTY1YlwifSxcInRlbmFudFwiOntcInR5cGVcIjpcImFjY291bnRcIixcImlkXCI6XCJlMjI1YzI1Yi02Y2IwLTQ1MTItOGFiMS1hZDIyZGM2ZTQyYTdcIn19IiwiaWF0IjoxNzQyNTk1NDk2fQ.qPQu9kJTkWn8ZZEb2_XDVB4iZMd_SvqIxUFX-gLp5rAEWGkUdXu26qUALQAPHjYA5P1vE9Lc-mW0Ioy-NMn8NUaU6oNaAe3f5MvKxWrRdLGtIHXaY8LFaHlFCcP1rexfQ6mZMg3p0u7nKPZ4hqGo2cIdmjZ7dK93M_R5VKEkYx9tAG9CRfywJdGFoX9fBmCQl8sJWQ2k9SzAw8wdxPm_A7YxhJgz5M8wRuQSp8iOmV7m2D9Y8cNnQ4h0Sx7qA2TXKpLEWtNvB9mFjC3bPwYpZ6dN7RaXvQ8TfUc4gPnL2GYKJE5wRmN3aXcTuV8bpWkH1yD9J6o0Mf2qAs4C3TdNQ
WIX_SITE_ID=f1b961d0-c64e-4614-afd1-e9a1dc5ac057

# ==================== WIX OAUTH (pour Render) ====================
WIX_INSTANCE_ID=ab8a5a88-69a5-4348-ad2e-06017de46f57
WIX_CLIENT_ID=1969322e-ef8d-4aa4-90e1-d6fd3eb994ff
WIX_CLIENT_SECRET=58e2d7b7-5a8d-44dc-bd74-b9e0c37c58fc
WIX_ACCOUNT_ID=f1b961ed-82d6-4b38-967b-557a0c345165
WIX_OAUTH_SCOPES=SCOPE.DC-STORES-MEGA.MANAGE-STORES
WIX_REDIRECT_URL=https://luxura-inventory-api.onrender.com/wix/oauth/callback

# ==================== SECRETS ====================
WIX_PUSH_SECRET=9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f
SEO_SECRET=9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f

# ==================== EMAIL ====================
LUXURA_EMAIL=info@luxuradistribution.com
LUXURA_APP_PASSWORD=zgvsfiajermjqpgh

# ==================== INVENTAIRE ====================
LUXURA_SALON_ID=4
```

### API Render (`luxura-inventory-api.onrender.com`)

⚠️ **Variables à configurer sur Render Dashboard > Environment** :

```env
# ==================== SUPABASE (PostgreSQL) ====================
# ⚠️ MANQUANT - Obtenir depuis Supabase Dashboard > Settings > Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# ==================== WIX OAUTH ====================
WIX_CLIENT_ID=1969322e-ef8d-4aa4-90e1-d6fd3eb994ff
WIX_CLIENT_SECRET=58e2d7b7-5a8d-44dc-bd74-b9e0c37c58fc
WIX_INSTANCE_ID=ab8a5a88-69a5-4348-ad2e-06017de46f57
WIX_ACCOUNT_ID=f1b961ed-82d6-4b38-967b-557a0c345165
WIX_OAUTH_SCOPES=SCOPE.DC-STORES-MEGA.MANAGE-STORES
WIX_REDIRECT_URL=https://luxura-inventory-api.onrender.com/wix/oauth/callback

# ==================== SECRETS ====================
WIX_PUSH_SECRET=9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f
SEO_SECRET=9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f

# ==================== OPTIONNEL ====================
ENVIRONMENT=production
```

### Frontend Expo (`/app/frontend/.env`)

```env
EXPO_PUBLIC_BACKEND_URL=/api
```

---

## Structure Base de Données (Supabase)

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

## Système de Mapping Images

Les images sont mappées par **code couleur** extrait du handle :

```python
COLOR_CODE_IMAGES = {
    "1": "...",       # Noir Foncé
    "1b": "...",      # Noir Doux  
    "6": "...",       # Caramel Doré
    "6/6t24": "...",  # Caramel Soleil
    "18/22": "...",   # Champagne Doré
    "60a": "...",     # Platine Pur
    "hps": "...",     # Cendré Étoilé
    "613/18a": "...", # Diamant Glacé
    # ... etc
}
```

## Templates SEO par Catégorie

Chaque catégorie a un template SEO optimisé avec 5 sections :

1. **CONCEPT/TECHNOLOGIE** - Points différenciateurs
2. **QUALITÉ PREMIUM** - Caractéristiques cheveux Remy
3. **DURÉE DE VIE** - Longévité produit
4. **APPLICATION** - Mode d'emploi
5. **COLLECTION** - Série + Teinte (dynamique)

## Endpoints API Locaux

| Endpoint | Description |
|----------|-------------|
| `GET /api/products` | Liste tous les produits |
| `GET /api/products?category=halo` | Filtre par catégorie |
| `GET /api/products/{id}` | Détails d'un produit + variantes |
| `GET /api/categories` | Liste des catégories |
| `GET /api/ping` | Health check |

## Endpoints API Render

| Endpoint | Description |
|----------|-------------|
| `GET /products` | Liste produits Supabase |
| `GET /products/{id}` | Détails produit |
| `GET /inventory/view` | Vue jointe produit + quantités |
| `GET /inventory/export.xlsx` | Export Excel |
| `GET /salons` | Liste des salons |
| `POST /wix/sync` | Déclencher synchronisation |

## Commandes

```bash
# Démarrer le backend
cd /app/backend && uvicorn server:app --host 0.0.0.0 --port 8001

# Démarrer le frontend
cd /app/frontend && npx expo start --tunnel --port 3000

# Ou via supervisor
sudo supervisorctl restart backend
sudo supervisorctl restart expo
```

## Synchronisation Wix ↔ Supabase

La synchronisation est gérée par l'API Render avec :

1. **Cron Job** : Synchronise périodiquement les produits Wix vers Supabase
2. **Webhook** : Réception des mises à jour Wix en temps réel
3. **API `/inventory/view`** : Vue jointe produit + quantités par salon

## ⚠️ Notes Importantes

- **NE PAS MODIFIER** les SKUs ou la base Wix/Supabase (nettoyage complet effectué)
- **115 produits** synchronisés avec **229 variantes**
- Toutes les variantes ont un SKU valide
- L'inventaire du **Salon ID 4** est la source de vérité
- API Render : `https://luxura-inventory-api.onrender.com`

## Contact

Luxura Distribution - Extensions de cheveux professionnels
Québec, Canada
Site: www.luxuradistribution.com
Email: info@luxuradistribution.com
