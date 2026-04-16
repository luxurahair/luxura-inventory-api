# 🏗️ Architecture Luxura Distribution - Services Render

**Dernière mise à jour:** 16 avril 2026

## Vue d'ensemble des 10 Services

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           RENDER SERVICES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────┐     ┌─────────────────────┐                    │
│  │ luxura-inventory-   │────▶│  luxura-inventory-  │◀──── Wix Catalog   │
│  │ sync-cron           │     │  api                │◀──── Supabase DB   │
│  │ (Cron: Sync Wix)    │     │  (API Principale)   │◀──── OpenAI/DALL-E │
│  └─────────────────────┘     └─────────────────────┘                    │
│                                       │                                  │
│  ┌─────────────────────┐              │                                  │
│  │ luxura-blog-cron    │──────────────┤                                  │
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
│  ┌─────────────────────┐     ┌─────────────────────┐                    │
│  │ Facebook Product    │     │ AUTO-REPAIR SYSTEM  │                    │
│  │ Posts (Cron)        │     │ (GitHub Actions)    │                    │
│  └─────────────────────┘     └─────────────────────┘                    │
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

---

## 🖼️ SYSTÈME D'IMAGES BLOG WIX (Implémenté Mars 2026)

### Architecture des Images

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FLUX DE GÉNÉRATION D'IMAGES BLOG                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. GÉNÉRATION IMAGE                                                     │
│     ┌─────────────┐      ┌─────────────┐      ┌─────────────┐           │
│     │  DALL-E 3   │  OR  │  Unsplash   │  OR  │  Images     │           │
│     │  (OpenAI)   │      │  (Fallback) │      │  Locales    │           │
│     └──────┬──────┘      └──────┬──────┘      └──────┬──────┘           │
│            │                    │                    │                   │
│            └────────────────────┼────────────────────┘                   │
│                                 ▼                                        │
│  2. IMPORT WIX MEDIA                                                     │
│     ┌────────────────────────────────────────┐                          │
│     │  POST /site-media/v1/files/import      │                          │
│     │  {                                      │                          │
│     │    "url": "https://...",               │                          │
│     │    "displayName": "blog-cover.png"     │                          │
│     │  }                                      │                          │
│     └──────────────────┬─────────────────────┘                          │
│                        ▼                                                 │
│  3. ATTENDRE PROCESSING                                                  │
│     ┌────────────────────────────────────────┐                          │
│     │  GET /site-media/v1/files/{file_id}    │                          │
│     │  Wait until operationStatus == "READY" │                          │
│     └──────────────────┬─────────────────────┘                          │
│                        ▼                                                 │
│  4. CRÉER BROUILLON WIX AVEC IMAGE                                       │
│     ┌────────────────────────────────────────┐                          │
│     │  POST /blog/v3/draft-posts             │                          │
│     │  {                                      │                          │
│     │    "draftPost": {                       │                          │
│     │      "title": "...",                   │                          │
│     │      "memberId": "xxx",                │                          │
│     │      "media": {                        │  ◀── FORMAT CRITIQUE!    │
│     │        "wixMedia": {                   │                          │
│     │          "image": {                    │                          │
│     │            "id": "f1b961_xxx~mv2.png"  │  ◀── OBJET avec "id"     │
│     │          }                             │      PAS une string!     │
│     │        },                              │                          │
│     │        "displayed": true,              │                          │
│     │        "custom": true                  │                          │
│     │      }                                 │                          │
│     │    }                                   │                          │
│     │  }                                      │                          │
│     └──────────────────┬─────────────────────┘                          │
│                        ▼                                                 │
│  5. EMAIL APPROBATION                                                    │
│     ┌────────────────────────────────────────┐                          │
│     │  SMTP Gmail → info@luxuradistribution  │                          │
│     │  Lien: manage.wix.com/.../blog/{id}    │                          │
│     └────────────────────────────────────────┘                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Fonctions Clés (blog_automation.py)

| Fonction | Description |
|----------|-------------|
| `import_image_and_get_wix_uri()` | Importe image → Wix Media, retourne file_id |
| `wait_until_wix_file_ready()` | Attend que l'image soit READY (max 90s) |
| `attach_cover_image_to_wix_draft()` | PATCH pour attacher l'image au brouillon |
| `build_wix_image_uri()` | Construit le format `wix:image://v1/{id}/...` |
| `generate_and_upload_blog_images()` | Génère DALL-E + upload |
| `send_blog_approval_email()` | Envoie email d'approbation |

### Format Correct pour Image Wix (CRITIQUE!)

```python
# ✅ CORRECT - L'image est un OBJET avec "id"
"media": {
    "wixMedia": {
        "image": {
            "id": "f1b961_xxx~mv2.png"  # <-- OBJET!
        }
    },
    "displayed": True,
    "custom": True
}

# ❌ INCORRECT - String directe
"media": {
    "wixMedia": {
        "image": "f1b961_xxx~mv2.png"  # <-- NE FONCTIONNE PAS!
    }
}

# ❌ INCORRECT - Format wix:image://
"media": {
    "wixMedia": {
        "image": "wix:image://v1/f1b961_xxx/cover.png"  # <-- NE FONCTIONNE PAS!
    }
}
```

### URLs d'Images Wix

| Format | Usage | Exemple |
|--------|-------|---------|
| `file_id` | Pour `media.wixMedia.image.id` | `f1b961_xxx~mv2.png` |
| `static_url` | Pour affichage web | `https://static.wixstatic.com/media/f1b961_xxx~mv2.png` |
| `wix_uri` | Pour richContent inline | `wix:image://v1/f1b961_xxx/name.png#originWidth=1200&originHeight=630` |

---

## 🔧 SYSTÈME AUTO-REPAIR (Implémenté Avril 2026)

### Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        AUTO-REPAIR SYSTEM                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  GitHub Actions (toutes les 5 minutes)                                   │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                                                                    │ │
│  │    ┌───────────────┐                                              │ │
│  │    │  Health Check │                                              │ │
│  │    │  - /api/health│                                              │ │
│  │    │  - /products  │                                              │ │
│  │    │  - /salons    │                                              │ │
│  │    └───────┬───────┘                                              │ │
│  │            │                                                       │ │
│  │      ┌─────┴─────┐                                                │ │
│  │      ▼           ▼                                                │ │
│  │  ┌────────┐  ┌────────┐                                          │ │
│  │  │HEALTHY │  │  DOWN  │                                          │ │
│  │  └────┬───┘  └────┬───┘                                          │ │
│  │       │           │                                               │ │
│  │       ▼           ▼                                               │ │
│  │  ┌─────────┐  ┌─────────────────────────────────┐                │ │
│  │  │  SAVE   │  │  AUTO-REPAIR                    │                │ │
│  │  │ STABLE  │  │  1. Analyze error               │                │ │
│  │  │ COMMIT  │  │  2. Fix dependencies OR         │                │ │
│  │  └─────────┘  │  3. Rollback to stable          │                │ │
│  │               │  4. Send email notification     │                │ │
│  │               └─────────────────────────────────┘                │ │
│  │                                                                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Fichiers

| Fichier | Description |
|---------|-------------|
| `monitoring/auto_repair.py` | Script Python de monitoring et réparation |
| `monitoring/multi_service_monitor.py` | Vérifie TOUS les services Render |
| `.github/workflows/auto-repair.yml` | GitHub Actions workflow |
| `.last_stable_commit` | Dernier commit fonctionnel (auto-généré) |

### Patterns d'Erreurs Détectés

| Pattern | Action Automatique |
|---------|-------------------|
| `numpy.core.multiarray failed to import` | Update numpy/opencv versions |
| `ModuleNotFoundError: No module named` | Ajouter module manquant |
| `No open ports detected` | Rollback vers stable |
| `connection.*timeout` | Restart service |

### Commandes Manuelles

```bash
# Vérifier tous les services
python monitoring/multi_service_monitor.py

# Vérifier avec rapport email
python monitoring/multi_service_monitor.py --report

# Forcer une réparation
python monitoring/auto_repair.py --repair

# Rollback manuel
python monitoring/auto_repair.py --rollback

# Mode surveillance continue
python monitoring/auto_repair.py --watch
```

---

## 📧 SYSTÈME EMAIL APPROBATION BLOG

### Flux

```
Blog généré → Brouillon Wix (non publié) → Email admin → Click "Publier"
```

### Configuration SMTP

```
LUXURA_EMAIL=info@luxuradistribution.com
LUXURA_APP_PASSWORD=zgvsfiajermjqpgh  # App password Gmail
ADMIN_EMAIL=info@luxuradistribution.com
```

### Contenu Email

- 📌 Titre du blog
- 📝 Extrait
- 🖼️ Image de couverture
- 🔗 Bouton "OUVRIR DANS WIX"
- 🤖 Bouton "Demander modification"

---

## Détail des Services LUXURA

### 1. luxura-inventory-api (Web Service - Principal)
**URL**: `https://luxura-inventory-api.onrender.com`
**Rôle**: API Backend principale
**Endpoints critiques**:
- `/api/health` - Health check
- `/products` - Liste produits (187 items)
- `/inventory/view` - Vue inventaire
- `/salons` - Liste salons
- `/api/blog` - Articles de blog
- `/api/blog/{id}` - Article individuel
- `/api/blog/auto-generate` - Génération IA
- `/api/blog-images/{filename}` - Images DALL-E

**Connexions**:
- ← Supabase PostgreSQL (DATABASE_URL)
- ← Wix API (WIX_API_KEY, WIX_SITE_ID)
- ← OpenAI/DALL-E (OPENAI_API_KEY)
- ← Emergent (Expo App)

### 2. luxura-inventory-sync-cron (Cron Job)
**Schedule**: Toutes les heures ou quotidien
**Rôle**: Synchronise l'inventaire Wix → Supabase
**Appelle**: `POST /api/wix/sync`

### 3. luxura-blog-cron (Cron Job)
**Schedule**: Quotidien
**Rôle**: Génère des articles de blog avec IA
**Paramètres**:
- `publish_to_wix=False` → Brouillon seulement
- `send_email=True` → Email approbation
- `count=2` → 2 blogs/jour

### 4-6. Facebook Crons
- **Weekend Post**: Vendredi/Samedi
- **Educational Posts**: Mardi/Mercredi
- **Product Posts**: Lundi/Jeudi

---

## Connexions Base de Données

```
┌──────────────────────────────────────────────────────────────┐
│                    SUPABASE POSTGRESQL                        │
│  Host: aws-1-ca-central-1.pooler.supabase.com                │
│  Pool: pool_pre_ping=True, pool_recycle=300                  │
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

---

## Variables d'Environnement

### luxura-inventory-api
```
# Database
DATABASE_URL=postgresql://...@aws-1-ca-central-1.pooler.supabase.com:5432/postgres

# Wix
WIX_API_KEY=your_wix_api_key
WIX_SITE_ID=6e62c946-d068-45c1-8f5f-7af998f0d7b3

# AI
OPENAI_API_KEY=your_openai_key

# Facebook
FB_PAGE_ACCESS_TOKEN=your_fb_token
FB_PAGE_ID=your_fb_page_id

# Email
LUXURA_EMAIL=info@luxuradistribution.com
LUXURA_APP_PASSWORD=your_app_password

# Config
ENABLE_SCHEDULER=false
```

### GitHub Secrets (pour Auto-Repair)
```
LUXURA_EMAIL
LUXURA_APP_PASSWORD
ADMIN_EMAIL
```

---

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

# Multi-service monitor
python monitoring/multi_service_monitor.py
```

---

## Historique des Fonctionnalités

| Date | Fonctionnalité |
|------|---------------|
| Mars 25, 2026 | Blog automation avec images Unsplash |
| Mars 28, 2026 | Images Wix cover fonctionnelles |
| Avril 15, 2026 | DALL-E 3 pour images artistiques |
| Avril 16, 2026 | Auto-Repair System + Multi-Service Monitor |
| Avril 16, 2026 | Email approbation avant publication Wix |
