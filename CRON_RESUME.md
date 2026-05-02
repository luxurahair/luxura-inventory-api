# 🔄 RÉSUMÉ DES CRONS LUXURA

## 📊 VUE D'ENSEMBLE

| Service Render | Script | Fonction | Fréquence |
|----------------|--------|----------|-----------|
| **kenbot** | `render_cron.py` | Sync Wix + Blog auto | `0 7,10,12,19,20 * * *` |
| **luxura-inventory-api** | API principale | Reçoit les appels cron | 24/7 |

---

## 📝 BLOG AUTOMATIQUE - Calendrier Éditorial

### Nombre de blogs par semaine: **7 blogs** (1 par jour)

| Jour | Heure (Montréal) | Semaine 1 | Semaine 2 |
|------|------------------|-----------|-----------|
| Lundi | 7h | Transformation capillaire | Entretien extensions |
| Mardi | 12h | Solutions cheveux fins | Guide complet achat |
| Mercredi | 19h | Comparatif méthodes | Occasions spéciales |
| Jeudi | 7h | B2B Salons partenaires | B2B Programme inventaire |
| Vendredi | 12h | Tendances coiffure | Guide couleurs |
| Samedi | 10h | Inspiration weekend | Tutoriel coiffure |
| Dimanche | 20h | Témoignages clientes | Self-care beauté |

---

## 🔍 DIAGNOSTIC - Pourquoi pas de blog depuis 2 jours?

### Causes possibles:
1. **Cron Render désactivé** - Vérifier dans Render Dashboard → kenbot → Cron Jobs
2. **Heure incorrecte** - Le cron vérifie si c'est l'heure ±1h
3. **API en cold start** - L'API Render peut être endormie
4. **Erreur silencieuse** - Pas de logs si le cron échoue

### À vérifier sur Render:
1. `kenbot` → Settings → Cron Jobs → Actif?
2. `kenbot` → Logs → Erreurs récentes?
3. `luxura-inventory-api` → Logs → Appels `/api/blog/auto-generate`?

---

## 📡 ENDPOINTS IMPORTANTS

```bash
# Déclencher manuellement un blog
POST https://luxura-inventory-api.onrender.com/api/blog/auto-generate
Body: {"count": 1, "publish_to_wix": true, "category": "transformation"}

# Vérifier le statut du cron
GET https://luxura-inventory-api.onrender.com/api/cron/status

# Ping pour réveiller l'API
GET https://luxura-inventory-api.onrender.com/api/ping
```

---

## 🛠️ SCRIPTS SUR MAC (dgauto-agent)

Basé sur les captures d'écran, votre Mac a un script de monitoring :

```bash
# Voir les logs du wake-watcher
tail -50 ~/.dgauto-agent/wake-watcher.log

# Forcer un git pull
cd ~/kenebec-ai 2>/dev/null || cd ~/Desktop/beauce-publisher 2>/dev/null
git pull --rebase --autostash
```

---

## ✅ TEST RAPIDE

Pour tester que tout fonctionne :

```bash
# 1. Réveiller l'API
curl https://luxura-inventory-api.onrender.com/api/ping

# 2. Attendre 5 secondes puis générer un blog test
curl -X POST "https://luxura-inventory-api.onrender.com/api/blog/auto-generate" \
  -H "Content-Type: application/json" \
  -d '{"count": 1, "publish_to_wix": true, "category": "transformation"}'
```

---

## 📋 CHECKLIST DE DÉPANNAGE

- [ ] Render Dashboard → `kenbot` → Cron Job est "Enabled"?
- [ ] Render Dashboard → `kenbot` → Dernière exécution réussie?
- [ ] Render Dashboard → `luxura-inventory-api` → Service "Running"?
- [ ] Wix API Key valide? (expires tous les 14 jours)
- [ ] Variables d'env correctes sur Render? (SEO_SECRET, API_URL)

---

*Dernière mise à jour: 1 Mai 2026*
