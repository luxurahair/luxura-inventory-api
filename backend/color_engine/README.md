# Luxura Color Engine 🎨

Micro-service de recolorisation intelligente pour extensions capillaires Luxura.

## Principe

- **Gabarit = intact** : on ne régénère jamais le visuel complet
- **Masque cheveux** : rembg isole uniquement la mèche
- **Transfert couleur** : on copie le profil vertical LAB de la référence (ombré inclus)
- **Watermark protégé** : hors du masque, jamais touché

## Fichiers

```
luxura-color-engine/
├── app.py              # Interface Streamlit
├── requirements.txt    # Dépendances
├── render.yaml         # Config déploiement Render
├── README.md           # Ce fichier
└── outputs/            # Images générées (auto-créé)
```

## Installation locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déploiement Render

1. Push ce dossier sur GitHub
2. Connecte le repo à Render.com
3. Le `render.yaml` configure tout automatiquement
4. URL : `https://luxura-color-engine.onrender.com`

## Utilisation

1. **Gabarit 1** : photo produit avec watermark
2. **Gabarit 2** : autre vue (optionnel)
3. **Référence** : photo avec la couleur à copier (ombré, mèches, etc.)
4. **Force** : slider pour doser le transfert (0.65 = équilibré)
5. **Générer** → télécharge les résultats

## Limitations

- Pour extensions seules sur fond propre : excellent
- Pour modèles complets (visage, mains) : masque manuel recommandé
- Watermark doit être hors zone cheveux pour être 100% protégé

## Améliorations futures

- [ ] Masque verrouillé pour extensions produit
- [ ] Watermark replaqué net après traitement
- [ ] Export automatique par SKU
- [ ] Interface plus clean
