# Luxura Inventory API v3.0

**API Backend pour Luxura Distribution - Importateur direct d'extensions capillaires premium au Québec**

🚀 Déployé sur [Render](https://luxura-inventory-api.onrender.com)

---

## 📋 Endpoints Disponibles

### Core
| Endpoint | Description |
|----------|-------------|
| `GET /` | Status de l'API |
| `GET /health` | Health check |
| `GET /docs` | Documentation Swagger |

### Produits & Inventaire
| Endpoint | Description |
|----------|-------------|
| `GET /products` | Liste des produits |
| `GET /inventory` | Inventaire actuel |
| `GET /salons` | Salons partenaires |

### Wix Integration
| Endpoint | Description |
|----------|-------------|
| `GET /wix/*` | Sync avec Wix Store |
| `POST /wix/token` | Obtenir token Wix |
| `POST /wix/seo/*` | Push SEO vers Wix |
| `GET /wix/images/list` | Lister images avec ALT |
| `POST /wix/images/generate-alts` | Générer ALT SEO |
| `POST /wix/images/update-alts` | Mettre à jour ALT sur Wix |

### Marketing Automation (NEW v3.0)
| Endpoint | Description |
|----------|-------------|
| `POST /facebook/post` | Publier sur Facebook |
| `POST /drive/upload` | Upload vidéo Google Drive |
| `POST /grok/image` | Générer image avec xAI |
| `POST /grok/video` | Générer vidéo avec xAI |
| `POST /cron/facebook/auto-post` | 🤖 Auto-post Facebook |
| `POST /cron/weekly-schedule` | Plan 7 jours |

---

## ⏰ CRON Jobs (Render)

| Job | Schedule | Description |
|-----|----------|-------------|
| Facebook Product Posts | `0 15 * * 1,3,5` | Lun/Mer/Ven 10h EST |
| Facebook Educational | `0 0 * * 2,4` | Mar/Jeu 19h EST |
| Facebook Weekend | `0 17 * * 6` | Sam 12h EST |

---

## 🔧 Variables d'Environnement

```env
# Database
DATABASE_URL=postgresql://...

# Wix
WIX_API_KEY=...
WIX_ACCESS_TOKEN=...

# Facebook
FB_PAGE_ACCESS_TOKEN=...
FB_PAGE_ID=...

# Google Drive
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_DRIVE_FOLDER_ID=...

# xAI / Grok
XAI_API_KEY=...
```

---

## 🏗️ Structure du Projet

```
luxura-inventory-api/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── db.py                # Connexion DB
│   ├── routes/
│   │   ├── products.py      # Gestion produits
│   │   ├── inventory.py     # Inventaire
│   │   ├── wix.py           # Wix Store sync
│   │   ├── wix_images.py    # SEO images ALT
│   │   ├── facebook.py      # Publication FB
│   │   ├── google_drive.py  # Upload Drive
│   │   ├── grok.py          # xAI generation
│   │   └── cron.py          # CRON automation
│   ├── models/
│   └── services/
├── requirements.txt
├── runtime.txt              # Python 3.11.9
├── render.yaml              # Config Render
└── README.md
```

---

## 📞 Contact

**Luxura Distribution**
- 📱 418-222-3939
- 🌐 luxuradistribution.com
- 📍 St-Georges, Québec
