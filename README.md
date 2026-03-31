# 🌟 Luxura Distribution - Système d'Automatisation Wix & SEO

> **Plateforme complète** de gestion automatisée pour extensions capillaires professionnelles au Québec.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Capacités SEO Wix](#capacités-seo-wix)
3. [Gestion des produits](#gestion-des-produits)
4. [Blog Automation](#blog-automation)
5. [Scripts disponibles](#scripts-disponibles)
6. [API Endpoints](#api-endpoints)
7. [Configuration](#configuration)
8. [Commandes utiles](#commandes-utiles)

---

## 🎯 Vue d'ensemble

Ce système permet de :
- ✅ **Modifier automatiquement les produits Wix** (noms, descriptions, SKUs)
- ✅ **Générer et publier des articles de blog** SEO-optimisés
- ✅ **Synchroniser l'inventaire** entre Wix et la base locale
- ✅ **Gérer les collections/catégories** de produits
- ✅ **Appliquer des descriptions SEO** riches en HTML
- ✅ **Générer des images** avec DALL-E et overlay logo

---

## 🔧 Capacités SEO Wix

### 1. Modification des produits

| Capacité | Commande/Script | Description |
|----------|-----------------|-------------|
| **Renommer produits** | `rename_handtied_products.py` | Change les noms en masse par collection |
| **Modifier SKUs** | `fix_genius_skus_wix.py` | Corrige et standardise les SKUs |
| **Descriptions SEO** | `wix_seo_push_corrected.py` | Applique descriptions HTML riches |
| **Push SEO global** | API `/api/seo-push` | Met à jour tous les produits d'un coup |

### 2. Types de produits supportés

```python
TYPE_META = {
    "halo": {"label": "Halo", "series": "Everly"},
    "genius": {"label": "Genius", "series": "Vivian"},
    "tape": {"label": "Tape", "series": "Aurora"},
    "i-tip": {"label": "I-Tip", "series": "Eleanor"},
    "ponytail": {"label": "Ponytail", "series": "Victoria"},
    "clip-in": {"label": "Clip-In", "series": "Sophia"},
    "hand-tied": {"label": "Hand-Tied", "series": "Aurora"},
}
```

### 3. Descriptions SEO générées

Chaque produit reçoit une description HTML complète avec :
- ✅ Qualité Russe exceptionnelle
- ✅ Caractéristiques techniques (trame, cuticules, etc.)
- ✅ Avantages uniques du type de produit
- ✅ Instructions d'application
- ✅ Mots-clés SEO locaux (Québec, Montréal, Laval, etc.)
- ✅ Marque Luxura stylisée en couleur or (#D4AF37)

### 4. Système de couleurs

```python
# Fichier: color_system.py
# 40+ couleurs avec noms luxueux français

"1": {"luxe": "Onyx Noir", "base": "Noir", "category": "dark"}
"18/22": {"luxe": "Champagne Doré", "base": "Blond", "category": "blonde"}
"CB": {"luxe": "Miel Sauvage Ombré", "base": "Ombré", "category": "ombre"}
# etc.
```

---

## 📦 Gestion des produits

### Renommer une collection complète

```bash
# Mode simulation (dry_run)
python3 /app/scripts/rename_handtied_products.py

# Mode production (applique les changements)
python3 /app/scripts/rename_handtied_products.py --apply
```

### Push SEO sur tous les produits

```bash
# Via l'API Render
curl -X POST "https://luxura-inventory-api.onrender.com/seo/push-all"

# Via le script local
python3 /app/scripts/wix_seo_push_corrected.py
```

### Récupérer les produits d'une collection

```python
# Collection IDs disponibles
COLLECTIONS = {
    "genius": "df309160-f8c2-4bfb-8b96-4c7167d6ca80",
    "halo": "8a9a11e9-f98c-4846-b70e-0d169ed89454",
    "tape": "ba5a0f74-5828-4baa-be83-78991547e1ed",
    "i-tip": "f8926eac-b11e-4dff-ae76-59b3f727cdbf",
    "hand-tied": "ffa67c64-ec16-1770-6aef-03dfc39a166c",
    "liquidation": "32f3916d-5c98-4b4f-acca-c29256d4f253",
    "ponytails": "d6adc071-c1cd-4190-9691-9466377cd4cf",
    "clips": "e6f52b5b-fb69-4d04-b0c4-b8704b50fc86",
    "essentiels": "0ffe1b2c-4408-47bd-b1f8-6fbbfa5cb96b",
}
```

---

## 📝 Blog Automation

### Calendrier éditorial

Rotation sur 2 semaines :

| Jour | Semaine 1 | Semaine 2 |
|------|-----------|------------|
| Lundi | consommateur | entretien |
| Mercredi | comparatif | guide |
| Vendredi | B2B salon | B2B salon |
| Samedi/Dimanche | ❌ Aucune publication | ❌ Aucune publication |

### Génération manuelle

```bash
# Générer un brouillon
curl -X POST "http://localhost:8001/api/blog/generate" \
  -H "Content-Type: application/json" \
  -d '{"category": "entretien", "auto_publish": false}'

# Publier un brouillon
curl -X POST "http://localhost:8001/api/blog/publish/{draft_id}"
```

### Fonctionnalités du blog

- ✅ Génération de contenu SEO avec GPT-4o
- ✅ Images générées avec DALL-E 3
- ✅ Overlay logo Luxura automatique
- ✅ Maillage interne SEO (liens vers autres articles)
- ✅ Anti-doublon intelligent (similarité de contenu)
- ✅ Publication Wix via API
- ✅ Notification email après génération

---

## 📂 Scripts disponibles

### /app/scripts/

| Script | Description | Utilisation |
|--------|-------------|-------------|
| `wix_seo_push_corrected.py` | Push SEO complet sur tous les produits | `python3 wix_seo_push_corrected.py` |
| `rename_handtied_products.py` | Renomme les Hand-Tied Weft | `python3 rename_handtied_products.py --apply` |
| `fix_genius_skus_wix.py` | Corrige les SKUs Genius | `python3 fix_genius_skus_wix.py` |

### /app/backend/

| Module | Description |
|--------|-------------|
| `server.py` | API principale FastAPI |
| `blog_automation.py` | Génération et publication de blogs |
| `color_system.py` | Système de noms de couleurs luxueux |
| `editorial_calendar.py` | Calendrier éditorial 2 semaines |
| `editorial_guard.py` | Anti-doublon et contrôle qualité |
| `image_generation.py` | Génération DALL-E + upload Wix |
| `internal_linking.py` | Maillage interne SEO |
| `logo_overlay.py` | Overlay logo sur images |

---

## 🔌 API Endpoints

### Blog

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/blog/generate` | POST | Génère un brouillon |
| `/api/blog/publish/{id}` | POST | Publie un brouillon |
| `/api/blog/drafts` | GET | Liste les brouillons |
| `/api/blog/posts` | GET | Liste les articles publiés |
| `/api/blog/calendar` | GET | Statut du calendrier |

### Produits

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/products` | GET | Liste tous les produits |
| `/api/products/{id}` | GET | Détails d'un produit |
| `/api/categories` | GET | Liste les catégories |
| `/api/colors` | GET | Liste les couleurs disponibles |

### SEO (via Render API)

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/seo/push-all` | POST | Push SEO sur tous les produits |
| `/seo/status` | GET | Statut du dernier push |
| `/products` | GET | Liste produits synchronisés |

---

## ⚙️ Configuration

### Variables d'environnement (/app/backend/.env)

```env
# Wix API
WIX_API_KEY=IST.eyJ...
WIX_SITE_ID=6e62c946-d068-45c1-8f5f-7af998f0d7b3
WIX_INSTANCE_ID=...

# OpenAI (génération contenu + images)
EMERGENT_LLM_KEY=...

# MongoDB local
MONGO_URL=mongodb://...
DB_NAME=luxura_db

# Email notifications
LUXURA_EMAIL=info@luxuradistribution.com
LUXURA_APP_PASSWORD=...

# API externe
LUXURA_API_URL=https://luxura-inventory-api.onrender.com
```

---

## 🚀 Commandes utiles

### Redémarrer les services

```bash
# Backend
sudo supervisorctl restart backend

# Frontend Expo
sudo supervisorctl restart expo
```

### Vérifier les logs

```bash
# Backend
tail -f /var/log/supervisor/backend.err.log

# Expo
tail -f /var/log/supervisor/expo.err.log
```

### Tester l'API Wix

```bash
# Vérifier la connexion
curl -X POST "https://www.wixapis.com/stores/v1/products/query" \
  -H "Authorization: IST.eyJ..." \
  -H "wix-site-id: 6e62c946-d068-45c1-8f5f-7af998f0d7b3" \
  -H "Content-Type: application/json" \
  -d '{"query": {"paging": {"limit": 1}}}'
```

---

## 📞 Support

- **Email:** info@luxuradistribution.com
- **Téléphone:** 418-774-4315
- **Adresse:** 8905 Boulevard Lacroix, Saint-Georges, QC G5Y 1T4

---

*Dernière mise à jour: Mars 2025*
