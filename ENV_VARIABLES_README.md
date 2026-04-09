# 🔐 Variables d'Environnement - Luxura Inventory API

## 📋 Configuration Render (Cron Job: luxura-inventory-sync-cron)

### Base de données
| Variable | Description | Exemple |
|----------|-------------|---------|
| `DATABASE_URL` | Connection PostgreSQL Supabase | `postgresql+psycopg://postgres.xxx:PASSWORD@aws-1-ca-central-1.pooler.supabase.com:5432/postgres?sslmode=require` |

### Python
| Variable | Valeur | Description |
|----------|--------|-------------|
| `PYTHON_VERSION` | `3.12.7` | Version Python |
| `PYTHONUNBUFFERED` | `1` | Logs en temps réel |

### Wix API
| Variable | Description |
|----------|-------------|
| `WIX_API_KEY` | Clé API Wix (format IST.xxx) |
| `WIX_CLIENT_ID` | ID Client OAuth Wix |
| `WIX_CLIENT_SECRET` | Secret Client OAuth Wix |
| `WIX_INSTANCE_ID` | ID Instance du site Wix |
| `WIX_PUSH_SECRET` | Secret pour les webhooks Wix |
| `WIX_SITE_ID` | ID du site Wix |

---

## 🔄 Services Render

### 1. luxura-inventory-api (Web Service)
- **Type**: Web Service
- **Runtime**: Python 3.11.9 (via runtime.txt)
- **Build**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2. luxura-inventory-sync-cron (Cron Job)
- **Type**: Cron Job
- **Schedule**: `every 15 minutes`
- **Command**: `python scripts/sync_wix_to_luxura.py`
- **Purpose**: Synchronise les produits Wix → PostgreSQL

---

## 📊 Base de données PostgreSQL (Supabase)

### Tables principales
| Table | Description |
|-------|-------------|
| `product` | Produits synchronisés depuis Wix |
| `salon` | Salons partenaires |
| `blog_posts` | Articles de blog |
| `product_description_backup` | Backups des descriptions |

### Contraintes importantes
- `product_sku_unique` - SKU doit être unique par produit
- `product_wix_id_key` - wix_id doit être unique

---

## 🔧 Dépannage

### Erreur: UniqueViolation SKU
```
duplicate key value violates unique constraint "product_sku_unique"
```

**Cause**: Deux produits ont le même SKU
**Solution**: 
```sql
-- Trouver les doublons
SELECT sku, COUNT(*) FROM product GROUP BY sku HAVING COUNT(*) > 1;

-- Renommer un doublon
UPDATE product SET sku = sku || '-DUP1' WHERE id = XXX;
```

### Erreur: Egress Quota Exceeded
**Cause**: Trop de données transférées depuis Supabase
**Solution**: 
- Réduire la fréquence du cron (15min → 1h)
- Optimiser les requêtes SELECT
- Upgrader le plan Supabase

---

## 📁 Structure du projet

```
luxura-inventory-api/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── db/
│   │   └── session.py       # Connection PostgreSQL
│   ├── models/
│   │   └── product.py       # Modèle SQLModel Product
│   ├── routes/
│   │   ├── wix_images.py    # SEO ALT text generator
│   │   ├── wix_token.py     # Gestion tokens Wix
│   │   └── cron.py          # Endpoints CRON
│   └── services/
│       ├── wix_client.py    # Client API Wix
│       └── catalog_normalizer.py
├── scripts/
│   └── sync_wix_to_luxura.py  # Script de sync (CRON)
├── requirements.txt
├── runtime.txt              # Python 3.11.9
└── render.yaml              # Blueprint Render
```

---

## 🚀 Déploiement

### Auto-Deploy
Le déploiement se fait automatiquement à chaque push sur `main`.

### Manual Deploy
1. Render Dashboard → Service
2. Manual Deploy → Deploy latest commit

### Blueprint Sync
Le fichier `render.yaml` définit l'infrastructure. 
⚠️ Ne pas inclure `pythonVersion` dans render.yaml (utiliser runtime.txt)

---

## 📞 Support

- **Supabase**: https://supabase.com/dashboard
- **Render**: https://dashboard.render.com
- **Wix Dev Center**: https://dev.wix.com

---

*Dernière mise à jour: Avril 2026*
