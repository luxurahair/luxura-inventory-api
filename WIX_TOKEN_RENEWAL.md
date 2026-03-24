# 🔑 Renouvellement du Token Wix - Luxura Distribution

## Étape 1 : Lancer le Flow OAuth

**Cliquez sur ce lien** (vous devez être connecté à votre compte Wix) :

👉 **[CLIQUER ICI POUR AUTORISER](https://www.wix.com/oauth/authorize?client_id=1969322e-ef8d-4aa4-90e1-d6fd3eb994ff&response_type=code&redirect_uri=https%3A%2F%2Fluxura-inventory-api.onrender.com%2Fwix%2Foauth%2Fcallback&scope=SCOPE.DC-STORES-MEGA.MANAGE-STORES)**

---

## Étape 2 : Autoriser l'Application

1. Wix vous demandera d'autoriser "Luxura Inventory API" à accéder à votre boutique
2. Cliquez sur **"Autoriser"** ou **"Allow"**
3. Vous serez redirigé vers `https://luxura-inventory-api.onrender.com/wix/oauth/callback?...`

---

## Étape 3 : Récupérer le Nouveau Instance ID

Après la redirection, la page affichera un JSON avec le nouveau `instance_id`.

**Exemple de réponse :**
```json
{
  "success": true,
  "instance_id": "abc123-def456-...",
  "message": "Token saved successfully"
}
```

---

## Étape 4 : Tester le Token

Une fois le token renouvelé, testez avec cette commande :

```bash
curl -X POST "https://luxura-inventory-api.onrender.com/wix/token?instance_id=VOTRE_INSTANCE_ID"
```

---

## Informations Techniques

| Paramètre | Valeur |
|-----------|--------|
| Client ID (App Def ID) | `1969322e-ef8d-4aa4-90e1-d6fd3eb994ff` |
| Redirect URI | `https://luxura-inventory-api.onrender.com/wix/oauth/callback` |
| Scope | `SCOPE.DC-STORES-MEGA.MANAGE-STORES` |
| Ancien Instance ID (expiré) | `a2cf4379-e654-4bfa-a498-6b11c32b6b87` |

---

## Produit à Tester Après Renouvellement

**Halo Everly Brun Châtaigne #3/3T24**
- Wix Product ID: `c2e7afd1-810f-4003-9693-839d1912a818`
- Supabase ID: `1237`
- Variantes:
  - 16" 120 grammes → SKU attendu: `H-16-120-3/3T24`
  - 20" 140 grammes → SKU attendu: `H-20-140-3/3T24`

---

## Commande de Test des SKU (après token renouvelé)

```bash
# Preview du push SEO pour ce produit spécifique
curl -X POST "https://luxura-inventory-api.onrender.com/wix/seo/push_preview" \
  -H "Content-Type: application/json" \
  -d '{"product_ids": [1237], "confirm": false}'

# Appliquer le push SEO (avec confirm=true)
curl -X POST "https://luxura-inventory-api.onrender.com/wix/seo/push_apply" \
  -H "Content-Type: application/json" \
  -d '{"product_ids": [1237], "confirm": true}'
```

---

*Fichier créé le 24 Mars 2026*
