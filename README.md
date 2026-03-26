# Luxura Distribution - Blog Automation System

## 🎯 Vue d'ensemble

Système d'automatisation de blogs pour Luxura Distribution, le leader des extensions capillaires haut de gamme au Québec.

### Fonctionnalités principales:
- ✅ **Génération automatique** d'articles SEO avec OpenAI GPT-4
- ✅ **Images uniques DALL-E** générées pour chaque article (cover + contenu)
- ✅ **Publication automatique** sur Wix Blog
- ✅ **Notification par email** après chaque génération
- ✅ **CRON scheduling** pour publication 2x par jour
- 🚧 **Publication Facebook** (en cours)

---

## 🏗️ Architecture

```
/app/
├── backend/
│   ├── server.py              # API FastAPI principale (routes produits, blog, etc.)
│   ├── blog_automation.py     # Système de génération automatique de blogs
│   ├── image_generation.py    # Module de génération d'images DALL-E
│   ├── cron_scheduler.py      # Planificateur CRON pour exécution automatique
│   ├── .env                   # Variables d'environnement (API keys)
│   └── requirements.txt       # Dépendances Python
│
├── frontend/
│   ├── app/                   # Routes Expo Router
│   │   ├── index.tsx          # Page d'accueil
│   │   ├── category/          # Pages catégories
│   │   └── product/           # Pages produits
│   ├── components/            # Composants React Native
│   └── package.json           # Dépendances JavaScript
│
└── README.md                  # Ce fichier
```

---

## 🔄 Flux de génération de blog

```
1. CRON Job déclenche generate_daily_blogs()
         ↓
2. Sélection d'un topic (rotation automatique)
         ↓
3. Génération du contenu avec OpenAI GPT-4
         ↓
4. Génération de 2 images uniques avec DALL-E
   - Cover image (pour le feed du blog)
   - Content image (insérée au milieu de l'article)
         ↓
5. Upload des images vers Wix Media Manager
         ↓
6. Création du draft Wix avec:
   - media.wixMedia.image (cover)
   - displayed: true
   - richContent avec IMAGE nodes
         ↓
7. Publication du draft
         ↓
8. Envoi email de notification
         ↓
9. (Optionnel) Publication sur Facebook
```

---

## 📁 Fichiers clés

### `blog_automation.py`
Module principal de génération de blogs.

**Fonctions principales:**
- `generate_daily_blogs()` - Point d'entrée principal
- `generate_blog_with_ai()` - Génération du contenu avec GPT-4
- `create_wix_draft_post()` - Création du brouillon Wix
- `html_to_ricos()` - Conversion HTML → format Ricos (Wix)
- `import_image_with_retry()` - Import d'images avec retry automatique

**Configuration topics:**
```python
BLOG_TOPICS = [
    {"topic": "...", "category": "halo", "keywords": [...], "focus_product": "Halo Everly"},
    {"topic": "...", "category": "genius", "keywords": [...], "focus_product": "Genius Vivian"},
    {"topic": "...", "category": "tape", "keywords": [...], "focus_product": "Tape Aurora"},
    {"topic": "...", "category": "itip", "keywords": [...], "focus_product": "I-Tip Eleanor"},
]
```

### `image_generation.py`
Module de génération d'images avec DALL-E.

**Fonctions principales:**
- `generate_blog_image_with_dalle()` - Génère une image unique
- `upload_image_bytes_to_wix()` - Upload vers Wix Media
- `get_next_hair_color()` - Rotation des couleurs de cheveux

**Prompts par catégorie:**
- Cover: Portrait glamour avec cheveux longs
- Content: Détail technique de la méthode d'extension

### `cron_scheduler.py`
Planificateur pour exécution automatique 2x par jour.

---

## 🔑 Variables d'environnement

```env
# OpenAI / Emergent LLM
EMERGENT_LLM_KEY=sk-emergent-xxxxx

# Wix API
WIX_API_KEY=IST.xxxxx
WIX_SITE_ID=xxxxx

# Email (Gmail SMTP)
LUXURA_EMAIL=info@luxuradistribution.com
LUXURA_APP_PASSWORD=xxxxx

# Facebook (optionnel)
FB_ACCESS_TOKEN=xxxxx
FB_PAGE_ID=xxxxx
```

---

## 🚀 Endpoints API

### Blog
```
POST /api/blog/auto-generate
Body: {"count": 2}
Response: {"success": true, "posts": [...]}
```

### Produits
```
GET /api/products?category=halo&limit=20
GET /api/products/{id}
GET /api/categories
```

---

## ⏰ CRON Schedule

Le système est configuré pour générer des blogs automatiquement:

| Heure | Action |
|-------|--------|
| 08:00 | Génération de 2 blogs |
| 16:00 | Génération de 2 blogs |

**Total: 4 blogs/jour**

---

## 📊 Informations Produits Luxura

### Durées de vie (avec bon entretien)
| Produit | Durée |
|---------|-------|
| Genius Weft Vivian | 12+ mois |
| Halo Everly | 12+ mois |
| Tape Aurora | 12+ mois |
| I-Tip Eleanor | 12+ mois |

### Conseils entretien
- **Toutes les extensions**: Peuvent durer plus de 12 mois avec soins appropriés
- **Couleurs blondes**: Nécessitent plus de soins (procédé de décoloration)
- **Produits recommandés**: Sans sulfate, sans alcool
- **Chaleur**: Éviter les outils chauffants excessifs

---

## 🖼️ Génération d'images DALL-E

### Prompts optimisés par catégorie

**Cover (image de couverture):**
```
Professional beauty photography of a glamorous woman with very long flowing 
{hair_color} hair extensions, soft studio lighting, elegant pose, 
hair salon quality result, high-end luxury feel
```

**Content (image dans l'article):**
```
Close-up detail shot of beautiful long {hair_color} hair with {technique} 
extensions, showing natural blend, professional hair photography
```

### Couleurs de cheveux (rotation automatique)
- blonde
- brunette
- dark brown
- honey blonde
- caramel highlights
- auburn
- platinum blonde
- chocolate brown
- golden blonde
- ash brown
- balayage ombre
- rich chestnut

---

## 🐛 Résolution de problèmes

### Image de couverture Wix ne s'affiche pas
**Solution:** Utiliser le format avec `displayed: true` et `custom: true`:
```python
draft_post["media"] = {
    "wixMedia": {
        "image": {
            "id": file_id,  # Juste le file_id, pas wix:image://
            "width": 1200,
            "height": 630
        }
    },
    "displayed": True,
    "custom": True
}
```

### Format richContent pour images
**Solution:** Utiliser `type: "IMAGE"` (majuscule) avec `imageData`:
```python
{
    "type": "IMAGE",
    "imageData": {
        "image": {
            "src": {"url": image_url},
            "width": 1200,
            "height": 630
        },
        "altText": "Description"
    }
}
```

---

## 📧 Contact

**Luxura Distribution**
- Email: info@luxuradistribution.com
- Site: https://www.luxuradistribution.com

---

## 📜 Changelog

### v2.0.0 (Mars 2026)
- ✅ Génération d'images DALL-E uniques
- ✅ 2 images par article (cover + content)
- ✅ Fix du bug cover image Wix (displayed: true)
- ✅ Rotation des couleurs de cheveux
- ✅ Durées de vie corrigées (12+ mois)

### v1.5.0
- ✅ Images Unsplash avec retry automatique
- ✅ Email de notification

### v1.0.0
- ✅ Génération de blogs avec OpenAI
- ✅ Publication sur Wix Blog
