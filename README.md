# Luxura Distribution - Application Mobile

Application mobile e-commerce pour Luxura Distribution (extensions de cheveux professionnels).

## Architecture

```
├── /app/frontend/          # Application Expo (React Native)
├── /app/backend/           # API FastAPI (proxy local)
├── API Render externe      # luxura-inventory-api.onrender.com
└── Supabase               # Base de données PostgreSQL
```

## Variables d'Environnement

### Backend Local (`/app/backend/.env`)

```env
# MongoDB (local - auth, panier)
MONGO_URL=mongodb://localhost:27017
DB_NAME=luxura

# Wix API
WIX_API_KEY=IST.eyJraWQiOi...  # Clé API Wix Stores
WIX_SITE_ID=f1b961d0-c64e-4614-afd1-e9a1dc5ac057

# Luxura Salon (inventaire principal)
LUXURA_SALON_ID=4
```

### API Render (`luxura-inventory-api.onrender.com`)

Variables à configurer sur Render Dashboard > Environment :

```env
# Supabase PostgreSQL
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# Wix OAuth (pour synchronisation)
WIX_CLIENT_ID=votre_client_id
WIX_CLIENT_SECRET=votre_client_secret
WIX_REFRESH_TOKEN=votre_refresh_token

# Optionnel
ENVIRONMENT=production
```

### Frontend Expo (`/app/frontend/.env`)

```env
EXPO_PUBLIC_BACKEND_URL=https://votre-domaine.com/api
```

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
| Genius | Vivian | Trame invisible ultra-fine |
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
    "1": "...",      # Noir Foncé
    "1b": "...",     # Noir Doux
    "6": "...",      # Caramel Doré
    "6/6t24": "...", # Caramel Soleil
    "18/22": "...",  # Champagne Doré
    "60a": "...",    # Platine Pur
    "hps": "...",    # Cendré Étoilé
    # ... etc
}
```

## Templates SEO par Catégorie

Chaque catégorie a un template SEO optimisé avec 5 sections :

1. **CONCEPT/TECHNOLOGIE** - Points différenciateurs
2. **QUALITÉ PREMIUM** - Caractéristiques cheveux
3. **DURÉE DE VIE** - Longévité produit
4. **APPLICATION** - Mode d'emploi
5. **COLLECTION** - Série + Teinte (dynamique)

## Endpoints API Locaux

| Endpoint | Description |
|----------|-------------|
| `GET /api/products` | Liste tous les produits |
| `GET /api/products?category=halo` | Filtre par catégorie |
| `GET /api/products/{id}` | Détails d'un produit |
| `GET /api/categories` | Liste des catégories |
| `GET /api/ping` | Health check |

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

## Notes Importantes

- **NE PAS MODIFIER** les SKUs ou la base Wix/Supabase (nettoyage complet effectué)
- **115 produits** synchronisés avec **229 variantes**
- Toutes les variantes ont un SKU valide
- L'inventaire du **Salon ID 4** est la source de vérité

## Contact

Luxura Distribution - Extensions de cheveux professionnels
Québec, Canada
