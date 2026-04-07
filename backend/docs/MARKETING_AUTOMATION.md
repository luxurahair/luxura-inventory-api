# Luxura Marketing Automation System

## Vue d'ensemble

Système d'automatisation publicitaire complet pour Luxura Distribution:
- Génération automatique de textes publicitaires via OpenAI
- Création de vidéos Story (9:16) et Feed (4:5) via Fal.ai
- Publication en brouillon sur Meta (Facebook/Instagram)
- Mini dashboard mobile pour gestion

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LUXURA MARKETING ENGINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Dashboard Expo]  ───▶  [FastAPI Backend]  ───▶  [Services]    │
│   /app/marketing         /api/marketing/*         - OpenAI      │
│                                                   - Fal.ai      │
│                                                   - Meta API    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  STOCKAGE: MongoDB (jobs)  |  Fal.ai (videos)  |  Meta (ads)    │
└─────────────────────────────────────────────────────────────────┘
```

## Endpoints API

### Health Check
```
GET /api/marketing/health
```

### Jobs

#### Créer un job
```
POST /api/marketing/jobs
Content-Type: application/json

{
  "offer_type": "direct_sale" | "salon_affilie",
  "product_name": "Rallonges premium Luxura",
  "hook": "Importateur direct de rallonges premium",
  "proof": "Qualité salon, rendu naturel",
  "cta": "Commander maintenant",
  "landing_url": "https://luxuradistribution.com",
  "images": ["https://..."],  // Optionnel
  "target_audience": "Femmes 23-45 Québec"  // Optionnel
}
```

#### Lister les jobs
```
GET /api/marketing/jobs?status=ready&offer_type=direct_sale&limit=20
```

#### Détails d'un job
```
GET /api/marketing/jobs/{job_id}
```

#### Rafraîchir le status
```
POST /api/marketing/jobs/{job_id}/refresh-status
```

#### Approuver un job
```
POST /api/marketing/jobs/{job_id}/approve
```

#### Supprimer un job
```
DELETE /api/marketing/jobs/{job_id}
```

## Types d'offres

### 1. Vente Directe (`direct_sale`)
- **Cible**: Femmes 23-45 ans, Québec
- **Angle**: Beauté, luxe, transformation, qualité premium
- **Ton**: Aspirationnel, émotionnel, résultat visible
- **Objectif Meta**: TRAFFIC

### 2. Salon Affilié (`salon_affilie`)
- **Cible**: Propriétaires de salon, coiffeuses, stylistes
- **Angle**: Marge, stabilité, image premium, approvisionnement
- **Ton**: Professionnel, business, opportunité
- **Objectif Meta**: LEADS
- **Avantages à mentionner**:
  - Base d'inventaire gratuite
  - Qualité importateur direct
  - Service rapide
  - Image de marque premium

## Workflow de génération

1. **Création du job** → Status: `draft`
2. **Génération textes** (OpenAI) → Status: `generating`
3. **Soumission vidéos** (Fal.ai)
4. **Polling status vidéos**
5. **Vidéos prêtes** → Status: `ready`
6. **Approbation manuelle**
7. **Publication Meta** → Status: `published`

## Structure des fichiers

```
/app/backend/
├── models/
│   └── ad_campaign.py        # Schémas Pydantic
├── services/
│   ├── copy_generator.py     # OpenAI via emergentintegrations
│   └── video_generator.py    # Fal.ai API
├── routes/
│   └── marketing/
│       ├── __init__.py
│       └── campaigns.py      # Endpoints FastAPI
└── exports/
    └── n8n_workflow_luxura.json  # Export n8n

/app/frontend/
└── app/
    └── marketing.tsx         # Dashboard Expo
```

## Variables d'environnement requises

```env
# OpenAI (via emergentintegrations)
EMERGENT_LLM_KEY=...

# Fal.ai
FAL_KEY=...

# Meta (Facebook)
FB_PAGE_ACCESS_TOKEN=...
FB_PAGE_ID=...
META_AD_ACCOUNT_ID=...  # Pour création de pubs
```

## Utilisation du Dashboard

1. Ouvrir l'app → Naviguer vers `/marketing`
2. Cliquer sur **+** pour créer une nouvelle pub
3. Remplir le formulaire:
   - Type d'offre
   - Nom du produit
   - Accroche
   - Preuve/bénéfice
   - CTA
   - URL
4. Cliquer **Générer la pub**
5. Attendre la génération (1-3 min)
6. Prévisualiser les vidéos
7. **Approuver** pour créer le brouillon Meta

## Export n8n

Le fichier `/app/backend/exports/n8n_workflow_luxura.json` peut être importé dans n8n pour une automatisation externe.

### Variables n8n à configurer:
- `LUXURA_BACKEND_URL`
- `FAL_KEY`
- `META_ACCESS_TOKEN`
- `META_AD_ACCOUNT_ID`
- `META_PAGE_ID`

## Règles business CRITIQUES

⚠️ **NE JAMAIS mentionner:**
- "pose d'extensions" comme service
- "support marketing" aux salons

✅ **TOUJOURS mentionner:**
- Luxura = Importateur / Vendeur DIRECT
- "Base d'inventaire gratuite" pour salons
- "Service rapide"
- Numéro: **418-222-3939**

## Exemples de prompts générés

### Vente directe
```
Texte: "Importateur direct de rallonges capillaires premium. 
Qualité salon, rendu naturel, texture riche. 
Luxura Distribution - La qualité au meilleur prix."

Vidéo: "Cinematic close-up of feminine hands with elegant 
manicured nails gently running through luxurious silky 
hair extensions..."
```

### Salon affilié
```
Texte: "Devenez salon affilié Luxura. Accès direct importateur, 
base d'inventaire gratuite, service rapide. 
Qualité premium pour vos clientes."

Vidéo: "Professional luxury hair salon interior. Elegant 
stylist hands styling premium blonde ombré hair extensions..."
```
