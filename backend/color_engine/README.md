# Luxura Color Engine V2 🚀

Micro-service de recolorisation intelligente pour les extensions capillaires Luxura.

## Fonctionnalités

- ✅ Masque cheveux PRO (rembg + détection peau + nettoyage morphologique)
- ✅ Extraction réelle de l'ombré + mèches de la référence
- ✅ Recolorisation en espace LAB (plus naturel que HSV)
- ✅ Préservation des reflets et textures
- ✅ Affichage du masque pour debug

## Installation locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déploiement Render

1. Push ce repo sur GitHub
2. Connecte-le à Render.com
3. Le fichier `render.yaml` configure tout automatiquement

## Utilisation

1. Upload **Gabarit 1** (photo modèle complet)
2. Upload **Gabarit 2** (extension seule)
3. Upload **Référence** (couleur + ombré + mèches à copier)
4. Ajuste le slider de mélange
5. Clique "Générer" → télécharge les résultats

## Structure

```
├── app.py              # Interface Streamlit
├── requirements.txt    # Dépendances Python
├── render.yaml         # Config déploiement Render
└── outputs/            # Images générées (auto-créé)
```
