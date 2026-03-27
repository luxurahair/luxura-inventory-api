# 🌟 Luxura Distribution - Système de Blog Automatisé

## 📋 Vue d'ensemble

Application mobile e-commerce + système de génération automatique de blogs SEO pour **Luxura Distribution**, distributeur d'extensions capillaires au Québec.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GÉNÉRATION DE BLOG                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. TEXTE BLOG          →  GPT-4o (blog_automation.py)          │
│     - Contenu SEO                                                │
│     - Anecdotes Luxura                                           │
│     - Français québécois                                         │
│                                                                  │
│  2. PROMPTS IMAGES      →  Mon code V11 (image_brief_generator) │
│     - 3 prompts distincts                                        │
│     - Variété anti-répétition                                    │
│     - Règles techniques par catégorie                            │
│                                                                  │
│  3. IMAGES              →  gpt-image-1 (image_generation.py)    │
│     - Cover: Installation/technique                              │
│     - Detail: Close-up (medium, pas macro)                       │
│     - Result: Glamour lifestyle                                  │
│                                                                  │
│  4. VIDÉO (optionnel)   →  FAL.AI/Kling (video_generator.py)    │
│     - Image-to-video                                             │
│     - 5 secondes                                                 │
│     - Mouvement naturel des cheveux                              │
│                                                                  │
│  5. PUBLICATION         →  Wix Blog API                          │
│     - Draft + Publish                                            │
│     - 3 images dans le contenu                                   │
│     - Cover sur le feed                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Variables d'environnement

### Backend (`/app/backend/.env`)

```env
# MongoDB (local)
MONGO_URL=mongodb://localhost:27017
DB_NAME=luxura_distribution

# OpenAI (texte + images)
OPENAI_API_KEY=votre_clé_openai

# Wix Blog
WIX_API_KEY=votre_clé_wix
WIX_SITE_ID=votre_site_id_wix
WIX_MEMBER_ID=votre_member_id_wix

# FAL.AI (vidéo) - Supporte les deux noms
FAL_KEY=votre_clé_fal_ai
# OU
FLA_AI_API_KEY=votre_clé_fal_ai

# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=votre_email
EMAIL_PASSWORD=votre_mot_de_passe_app
EMAIL_TO=info@luxuradistribution.com

# Facebook (optionnel)
FB_ACCESS_TOKEN=votre_token_facebook
FB_PAGE_ID=votre_page_id_facebook
```

---

## 📁 Structure des fichiers

```
/app/backend/
├── server.py                      # FastAPI + Endpoints + CRON
├── blog_automation.py             # Orchestrateur principal
├── image_brief_generator.py       # V11 - Prompts variés
├── image_generation.py            # gpt-image-1
├── logo_overlay.py                # Watermark Luxura
├── real_stock_images.py           # Fallback Unsplash
│
└── services/
    ├── blog_orchestrator.py       # Orchestrateur V8
    ├── blog_content_generator.py  # Génération texte
    ├── video_brief_generator.py   # Brief vidéo
    ├── video_generator.py         # FAL.AI/Kling
    └── wix_publisher.py           # Publication Wix
```

---

## 🎯 Catégories d'extensions

| Catégorie | Produit | Technique |
|-----------|---------|-----------|
| **Halo** | Everly | Fil invisible, pose maison, 1 motion |
| **I-Tip** | Eleanor | Microbilles + pince, mèche par mèche |
| **Tape-in** | Aurora | Méthode sandwich, bandes adhésives |
| **Genius** | Vivian | Couture sur rangée perlée |

---

## 🖼️ Système d'images V11

### 3 types d'images par blog :

| # | Type | Description | Placement |
|---|------|-------------|-----------|
| 1 | **Cover** | Installation/technique salon | Début du contenu + Feed |
| 2 | **Detail** | Close-up technique (medium) | 1/3 du contenu |
| 3 | **Result** | Résultat glamour lifestyle | 2/3 du contenu |

### Prompts hyper-réalistes :
- Instructions DSLR (Canon 5D, Sony A7R)
- Éclairage naturel
- Texture de peau réelle
- Cheveux très longs (taille minimum)
- 20+ scènes glamour variées

### Règles strictes par catégorie :
```python
TECHNIQUE_TRUTH = {
    "halo": {
        "method": "invisible wire halo",
        "NOT": "NO salon, NO stylist, NO glue, NO tape, NO microbeads"
    },
    "itip": {
        "method": "microbead strand by strand",
        "NOT": "NO tape, NO glue, NO sewn weft"
    },
    # etc.
}
```

---

## 🎬 Génération vidéo (FAL.AI)

### Configuration :
```env
FAL_KEY=votre_clé_fal_ai
```

### Fonctionnement :
1. Prend l'image de cover générée
2. Applique un mouvement naturel (cheveux qui bougent)
3. Génère une vidéo de 5 secondes
4. Upload vers Wix (si supporté)

### Prix estimé :
- ~$0.10 par vidéo de 5 secondes
- Kling 2.0 (qualité équivalente à Runway Gen-3)

---

## ⏰ CRON Scheduler

Le système génère automatiquement des blogs :

| Heure (EST) | Action |
|-------------|--------|
| **08:00** | 2 blogs générés |
| **16:00** | 2 blogs générés |
| **Total** | 4 blogs/jour |

---

## 🔌 API Endpoints

### Génération de blog

```bash
# Générer 1 blog (catégorie aléatoire)
POST /api/blog/auto-generate?count=1&publish_to_wix=true

# Forcer une catégorie
POST /api/blog/auto-generate?count=1&category=halo

# Sujet personnalisé
POST /api/blog/auto-generate?count=1&category=halo&custom_topic=Extensions%20Halo%20fil%20invisible
```

### Paramètres :
| Param | Type | Défaut | Description |
|-------|------|--------|-------------|
| `count` | int | 2 | Nombre de blogs |
| `publish_to_wix` | bool | true | Publier sur Wix |
| `publish_to_facebook` | bool | false | Publier sur Facebook |
| `category` | string | null | Forcer catégorie (halo, itip, tape, genius) |
| `custom_topic` | string | null | Sujet personnalisé |

---

## 🚀 Démarrage

### Backend :
```bash
cd /app/backend
sudo supervisorctl restart backend
```

### Frontend (Expo) :
```bash
cd /app/frontend
sudo supervisorctl restart expo
```

### Tester la génération :
```bash
curl -X POST "http://localhost:8001/api/blog/auto-generate?count=1&publish_to_wix=true"
```

---

## 📊 Logs

```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log

# Voir les prompts d'images
tail -100 /var/log/supervisor/backend.err.log | grep "Prompt V9\|Brief V11"

# Voir les images générées
tail -100 /var/log/supervisor/backend.err.log | grep "Image\|uploaded"
```

---

## ⚠️ Dépannage

### Images pas réalistes :
- Vérifier que `gpt-image-1` est utilisé (pas DALL-E 3)
- Les prompts V11 incluent des instructions DSLR

### Problème de clic sur images :
- Chaque image a un ID unique (`img1_xxx`, `img2_xxx`, `img3_xxx`)
- Vérifier que `disableExpand: false` dans le Ricos

### Vidéo ne se génère pas :
- Vérifier `FAL_KEY` dans `.env`
- La vidéo est optionnelle (non-bloquante)

### Blog pas publié sur Wix :
- Vérifier `WIX_API_KEY` et `WIX_SITE_ID`
- Vérifier les logs pour les erreurs API

---

## 📞 Support

**Luxura Distribution**
- Site : https://www.luxuradistribution.com
- Email : info@luxuradistribution.com
- Salle d'exposition : Saint-Georges, Québec

---

## 📝 Changelog

### V11 (2026-03-27)
- ✅ 20+ scènes glamour variées
- ✅ Close-up moins extrême (medium au lieu de macro)
- ✅ Système anti-répétition
- ✅ IDs uniques sur images
- ✅ Intégration FAL.AI/Kling pour vidéo

### V10 (2026-03-27)
- ✅ Prompts basés sur le contexte du blog
- ✅ Instructions DSLR pour réalisme

### V9 (2026-03-27)
- ✅ 3 images par blog
- ✅ Architecture 2 couches (technique + style)

### V8 (2026-03-26)
- ✅ Brief generator séparé
- ✅ Structure services/
