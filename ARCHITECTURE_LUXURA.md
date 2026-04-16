# 🏗️ Architecture Luxura Distribution - Services Render

## Vue d'ensemble des 9 Services

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           RENDER SERVICES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────┐     ┌─────────────────────┐                    │
│  │ luxura-inventory-   │────▶│  luxura-inventory-  │◀──── Wix Catalog   │
│  │ sync-cron           │     │  api                │◀──── Supabase DB   │
│  │ (Cron: Sync Wix)    │     │  (API Principale)   │                    │
│  └─────────────────────┘     └─────────────────────┘                    │
│                                       │                                  │
│  ┌─────────────────────┐              │                                  │
│  │ luxura-blog-cron    │──────────────┘                                  │
│  │ (Cron: Blogs IA)    │              │                                  │
│  └─────────────────────┘              ▼                                  │
│                              ┌─────────────────────┐                    │
│  ┌─────────────────────┐     │    Supabase DB      │                    │
│  │ Facebook Weekend    │     │  - products         │                    │
│  │ Post (Cron)         │────▶│  - blog_posts       │                    │
│  └─────────────────────┘     │  - inventory        │                    │
│                              │  - salons           │                    │
│  ┌─────────────────────┐     └─────────────────────┘                    │
│  │ Facebook Educational│              │                                  │
│  │ Posts (Cron)        │──────────────┘                                  │
│  └─────────────────────┘                                                │
│                                                                          │
│  ┌─────────────────────┐                                                │
│  │ Facebook Product    │                                                │
│  │ Posts (Cron)        │                                                │
│  └─────────────────────┘                                                │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    KENBOT SERVICES (Séparé)                      │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │    │
│  │  │ kenbot-api      │  │ kenbot-runner   │  │kenbot-dashboard │  │    │
│  │  │                 │  │                 │  │-api             │  │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Détail des Services LUXURA

### 1. luxura-inventory-api (Web Service - Principal)
**URL**: `https://luxura-inventory-api.onrender.com`
**Rôle**: API Backend principale
**Endpoints critiques**:
- `/api/health` - Health check
- `/products` - Liste produits
- `/inventory/view` - Vue inventaire
- `/salons` - Liste salons
- `/api/blog` - Articles de blog
- `/api/blog/{id}` - Article individuel
- `/api/blog/auto-generate` - Génération IA
- `/api/blog-images/{filename}` - Images DALL-E

**Connexions**:
- ← Supabase PostgreSQL (DATABASE_URL)
- ← Wix API (WIX_API_KEY, WIX_SITE_ID)
- ← OpenAI/DALL-E (EMERGENT_LLM_KEY)
- ← Emergent (Expo App)

### 2. luxura-inventory-sync-cron (Cron Job)
**Schedule**: Toutes les heures ou quotidien
**Rôle**: Synchronise l'inventaire Wix → Supabase
**Appelle**: `POST /api/wix/sync`
**Connexions**:
- → luxura-inventory-api

### 3. luxura-blog-cron (Cron Job)
**Schedule**: Quotidien ou hebdomadaire
**Rôle**: Génère des articles de blog avec IA
**Appelle**: `POST /api/blog/auto-generate`
**Connexions**:
- → luxura-inventory-api
- → OpenAI GPT-4o-mini (texte)
- → DALL-E / gpt-image-1 (images)

### 4. Facebook Weekend Post (Cron Job)
**Schedule**: Vendredi/Samedi
**Rôle**: Publie des posts weekend sur Facebook
**Connexions**:
- → Facebook Graph API
- → OpenAI (génération texte/image)

### 5. Facebook Educational Posts (Cron Job)
**Schedule**: Mardi/Mercredi
**Rôle**: Publie des posts éducatifs sur Facebook
**Connexions**:
- → Facebook Graph API
- → OpenAI (génération texte/image)

### 6. Facebook Product Posts (Cron Job)
**Schedule**: Lundi/Jeudi
**Rôle**: Publie des posts produits sur Facebook
**Connexions**:
- → luxura-inventory-api (pour les produits)
- → Facebook Graph API
- → OpenAI (génération texte/image)

## Connexions Base de Données

```
┌──────────────────────────────────────────────────────────────┐
│                    SUPABASE POSTGRESQL                        │
│  Host: aws-1-ca-central-1.pooler.supabase.com                │
├──────────────────────────────────────────────────────────────┤
│  Tables:                                                      │
│  ├── products (id, wix_id, name, price, category, etc.)      │
│  ├── inventory (id, product_id, salon_id, quantity, etc.)    │
│  ├── salons (id, name, code, is_active)                      │
│  ├── blog_posts (id, title, content, image, wix_post_id)     │
│  ├── product_overrides (wix_id, custom_fields)               │
│  └── sync_runs (id, started_at, status, stats)               │
└──────────────────────────────────────────────────────────────┘
```

## Variables d'Environnement Requises

### luxura-inventory-api
```
DATABASE_URL=postgresql://...@aws-1-ca-central-1.pooler.supabase.com:5432/postgres
WIX_API_KEY=your_wix_api_key
WIX_SITE_ID=your_wix_site_id
EMERGENT_LLM_KEY=your_emergent_key
OPENAI_API_KEY=your_openai_key (optionnel si Emergent)
FACEBOOK_PAGE_ACCESS_TOKEN=your_fb_token
FACEBOOK_PAGE_ID=your_fb_page_id
```

## Flux de Données

### Sync Inventaire
```
Wix Catalog → luxura-inventory-sync-cron → luxura-inventory-api → Supabase
```

### Génération Blog
```
luxura-blog-cron → luxura-inventory-api → GPT-4o-mini (texte) → DALL-E (image) → Supabase → Wix Blog
```

### Facebook Posts
```
Cron FB → OpenAI (texte+image) → Facebook Graph API
```

## Tests de Santé

```bash
# Health check API
curl https://luxura-inventory-api.onrender.com/api/health

# Test produits
curl https://luxura-inventory-api.onrender.com/products

# Test inventaire
curl https://luxura-inventory-api.onrender.com/inventory/view

# Test blog
curl https://luxura-inventory-api.onrender.com/api/blog
```
