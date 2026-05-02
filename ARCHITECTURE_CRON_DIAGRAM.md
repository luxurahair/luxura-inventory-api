# 🏗️ ARCHITECTURE CRON LUXURA - DIAGRAMME DE CONNEXIONS
# ========================================================
# Ce fichier montre visuellement comment tous les services se connectent

```
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                           🏢 LUXURA DISTRIBUTION - ARCHITECTURE                           ║
╠══════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                          ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐    ║
║  │                              📡 SOURCES EXTERNES                                 │    ║
║  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    ║
║  │  │   WIX    │  │ FACEBOOK │  │  GROK    │  │  OPENAI  │  │ SUPABASE │          │    ║
║  │  │   API    │  │ Graph API│  │   xAI    │  │   GPT    │  │ Postgres │          │    ║
║  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │    ║
║  └───────┼─────────────┼─────────────┼─────────────┼─────────────┼──────────────────┘    ║
║          │             │             │             │             │                       ║
║          └──────────────────────────┬┴─────────────┴─────────────┘                       ║
║                                     │                                                    ║
║                                     ▼                                                    ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐    ║
║  │                     🌐 WEB SERVICES (API PRINCIPALES)                            │    ║
║  │                                                                                  │    ║
║  │   ┌─────────────────────────────────────────────────────────────────────────┐   │    ║
║  │   │  luxura-inventory-api (srv-d46bkg2li9v)                                 │   │    ║
║  │   │  ════════════════════════════════════════════                           │   │    ║
║  │   │  📍 URL: https://luxura-inventory-api.onrender.com                      │   │    ║
║  │   │                                                                         │   │    ║
║  │   │  ENDPOINTS PRINCIPAUX:                                                  │   │    ║
║  │   │  ├── /api/blog/auto-generate     → Génère blogs Wix                     │   │    ║
║  │   │  ├── /api/products               → Catalogue produits                   │   │    ║
║  │   │  ├── /wix/oauth/*                → Gestion token Wix                    │   │    ║
║  │   │  ├── /wix/sync                   → Sync inventaire                      │   │    ║
║  │   │  ├── /api/facebook/*             → Posts Facebook                       │   │    ║
║  │   │  └── /api/grok/*                 → Génération images Grok               │   │    ║
║  │   │                                                                         │   │    ║
║  │   │  CONNEXIONS:                                                            │   │    ║
║  │   │  → Wix API (WIX_API_KEY)                                                │   │    ║
║  │   │  → Facebook (FB_PAGE_ACCESS_TOKEN)                                      │   │    ║
║  │   │  → Grok xAI (XAI_API_KEY)                                               │   │    ║
║  │   │  → OpenAI (OPENAI_API_KEY)                                              │   │    ║
║  │   │  → Supabase (DATABASE_URL)                                              │   │    ║
║  │   └─────────────────────────────────────────────────────────────────────────┘   │    ║
║  │                                     ▲                                            │    ║
║  │                                     │ Appelé par les crons                       │    ║
║  └─────────────────────────────────────┼────────────────────────────────────────────┘    ║
║                                        │                                                 ║
║  ┌─────────────────────────────────────┼────────────────────────────────────────────┐    ║
║  │                         ⏰ CRON JOBS (AUTOMATISATION)                             │    ║
║  │                                     │                                             │    ║
║  │  ╔═══════════════════════════════════════════════════════════════════════════╗   │    ║
║  │  ║  📝 BLOGS WIX                                                              ║   │    ║
║  │  ╠═══════════════════════════════════════════════════════════════════════════╣   │    ║
║  │  ║  luxura-blog-cron                                                          ║   │    ║
║  │  ║  ├── Script: scripts/blog_cron.py                                          ║   │    ║
║  │  ║  ├── Schedule: 0 7,10,12,19,20 * * * (5x/jour)                             ║   │    ║
║  │  ║  ├── Action: POST /api/blog/auto-generate                                  ║   │    ║
║  │  ║  └── Génère 1 blog/jour selon calendrier éditorial                         ║   │    ║
║  │  ╚═══════════════════════════════════════════════════════════════════════════╝   │    ║
║  │                                                                                   │    ║
║  │  ╔═══════════════════════════════════════════════════════════════════════════╗   │    ║
║  │  ║  📘 FACEBOOK POSTS                                                         ║   │    ║
║  │  ╠═══════════════════════════════════════════════════════════════════════════╣   │    ║
║  │  ║  Facebook Product Posts                                                    ║   │    ║
║  │  ║  ├── Schedule: Lun-Ven 10h                                                 ║   │    ║
║  │  ║  └── Action: POST /api/auto-content/facebook-posts (catégorie: product)    ║   │    ║
║  │  ║                                                                            ║   │    ║
║  │  ║  Facebook Educational Posts                                                ║   │    ║
║  │  ║  ├── Schedule: Lun-Ven 14h                                                 ║   │    ║
║  │  ║  └── Action: POST /api/auto-content/facebook-posts (catégorie: education)  ║   │    ║
║  │  ║                                                                            ║   │    ║
║  │  ║  Facebook Weekend Posts                                                    ║   │    ║
║  │  ║  ├── Schedule: Sam-Dim 11h                                                 ║   │    ║
║  │  ║  └── Action: POST /api/auto-content/facebook-posts (catégorie: lifestyle)  ║   │    ║
║  │  ╚═══════════════════════════════════════════════════════════════════════════╝   │    ║
║  │                                                                                   │    ║
║  │  ╔═══════════════════════════════════════════════════════════════════════════╗   │    ║
║  │  ║  🔄 SYNC INVENTAIRE                                                        ║   │    ║
║  │  ╠═══════════════════════════════════════════════════════════════════════════╣   │    ║
║  │  ║  luxura-inventory-sync-cron                                                ║   │    ║
║  │  ║  ├── Schedule: */30 * * * * (toutes les 30 min)                            ║   │    ║
║  │  ║  └── Action: POST /wix/sync                                                ║   │    ║
║  │  ╚═══════════════════════════════════════════════════════════════════════════╝   │    ║
║  │                                                                                   │    ║
║  │  ╔═══════════════════════════════════════════════════════════════════════════╗   │    ║
║  │  ║  🔍 CONTENT SCAN                                                           ║   │    ║
║  │  ╠═══════════════════════════════════════════════════════════════════════════╣   │    ║
║  │  ║  luxura-content-scan                                                       ║   │    ║
║  │  ║  ├── Schedule: */15 * * * * (toutes les 15 min)                            ║   │    ║
║  │  ║  └── Action: Scan RSS magazines mode (Vogue, Elle, Harper's...)            ║   │    ║
║  │  ╚═══════════════════════════════════════════════════════════════════════════╝   │    ║
║  │                                                                                   │    ║
║  │  ╔═══════════════════════════════════════════════════════════════════════════╗   │    ║
║  │  ║  📰 KENBOT (NEWS)                                                          ║   │    ║
║  │  ╠═══════════════════════════════════════════════════════════════════════════╣   │    ║
║  │  ║  kenbot-news-scraper                                                       ║   │    ║
║  │  ║  └── Scrape actualités mode/beauté                                         ║   │    ║
║  │  ║                                                                            ║   │    ║
║  │  ║  kenbot-news-publisher                                                     ║   │    ║
║  │  ║  └── Publie contenu généré                                                 ║   │    ║
║  │  ║                                                                            ║   │    ║
║  │  ║  kenbot-runner                                                             ║   │    ║
║  │  ║  └── Orchestration générale Kenbot                                         ║   │    ║
║  │  ╚═══════════════════════════════════════════════════════════════════════════╝   │    ║
║  └───────────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                          ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐    ║
║  │                         🔑 TOKENS & AUTHENTIFICATION                             │    ║
║  │                                                                                  │    ║
║  │   TOKEN              │ STOCKAGE         │ EXPIRATION    │ RENOUVELLEMENT        │    ║
║  │   ═══════════════════╪══════════════════╪═══════════════╪════════════════════   │    ║
║  │   WIX_API_KEY        │ .secrets.env     │ 14 jours      │ /wix/oauth/start      │    ║
║  │   FB_PAGE_ACCESS     │ .secrets.env     │ ~60 jours     │ Manuel (Graph API)    │    ║
║  │   OPENAI_API_KEY     │ .secrets.env     │ Jamais        │ N/A                   │    ║
║  │   XAI_API_KEY        │ .secrets.env     │ Jamais        │ N/A                   │    ║
║  │   DATABASE_URL       │ .secrets.env     │ Jamais        │ N/A                   │    ║
║  │                                                                                  │    ║
║  │   ⚠️  STATUT ACTUEL:                                                            │    ║
║  │   • WIX OAuth: Token valide, expire dans 13 jours, PAS de refresh_token         │    ║
║  │   • Action: Aller sur /wix/oauth/start pour activer auto-renouvellement         │    ║
║  └─────────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝
```

## 📊 MATRICE DE CONNEXIONS

| CRON JOB                    | API APPELÉE              | ENDPOINT                      | SERVICES UTILISÉS              |
|-----------------------------|--------------------------|-------------------------------|--------------------------------|
| luxura-blog-cron            | luxura-inventory-api     | POST /api/blog/auto-generate  | Wix, OpenAI, Grok, Supabase    |
| Facebook Product Posts      | luxura-inventory-api     | POST /api/auto-content/...    | Facebook, Grok, Supabase       |
| Facebook Educational Posts  | luxura-inventory-api     | POST /api/auto-content/...    | Facebook, Grok, Supabase       |
| Facebook Weekend Posts      | luxura-inventory-api     | POST /api/auto-content/...    | Facebook, Grok, Supabase       |
| luxura-inventory-sync-cron  | luxura-inventory-api     | POST /wix/sync                | Wix, Supabase                  |
| luxura-content-scan         | luxura-inventory-api     | GET /api/content/scan         | RSS Feeds, Supabase            |
| kenbot-news-scraper         | kenbot-api               | POST /scrape                  | News APIs, Supabase            |
| kenbot-news-publisher       | kenbot-api               | POST /publish                 | Facebook, Supabase             |
| kenbot-runner               | kenbot-api               | POST /run                     | Orchestration                  |

## 🧪 POINTS DE TEST

Pour chaque connexion, voici ce qu'il faut vérifier:

### 1. API → Services Externes
```
luxura-inventory-api
├── → Wix API ............... Test: GET /api/ping (vérifie wix_api: ok)
├── → Facebook Graph API .... Test: GET /api/facebook/status
├── → Grok xAI .............. Test: POST /api/grok/test
├── → OpenAI ................ Test: (intégré dans blog generation)
└── → Supabase .............. Test: (vérifié via DATABASE_URL)
```

### 2. Crons → API
```
luxura-blog-cron → luxura-inventory-api
├── Connexion ............... Test: curl API_URL/api/ping
├── Authentification ........ Test: Variables env présentes
└── Endpoint ................ Test: POST /api/blog/auto-generate
```

## ⚠️ POINTS DE DÉFAILLANCE POTENTIELS

1. **Token Wix expiré** → Blog cron échoue silencieusement
2. **Variables env manquantes sur Render** → Cron retourne 0 résultats
3. **API en cold start** → Timeout du cron
4. **Rate limiting** → Facebook/Grok rejette les requêtes
