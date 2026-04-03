# 🎨 Luxura Color Engine V2 - Instructions d'intégration Render

## Fichiers à ajouter à ton repo `luxura-inventory-api`

### 1. `color_engine_api.py` (nouveau fichier)
Copie le fichier `color_engine_api.py` à la racine de ton repo.

### 2. `requirements.txt` (modifier)
Ajoute ces lignes à ton requirements.txt existant :
```
rembg[cpu]>=2.0.50
opencv-python-headless>=4.8.0
```

### 3. `main.py` (modifier)
Ajoute en haut du fichier :
```python
from color_engine_api import process_color_engine
```

Ajoute le modèle Pydantic :
```python
class ColorEngineRequest(BaseModel):
    gabarit1: str
    gabarit2: Optional[str] = None
    reference: str
    blend: float = 0.65
```

Ajoute les endpoints (voir `endpoint_code.py`).

## Après déploiement

Ton API aura ces nouveaux endpoints :
- `GET /color-engine/status` - Vérifier le statut
- `POST /color-engine/process` - Traiter les images

## Utilisation

```bash
# Vérifier le statut
curl https://luxura-inventory-api.onrender.com/color-engine/status

# Traiter des images (en base64)
curl -X POST https://luxura-inventory-api.onrender.com/color-engine/process \
  -H "Content-Type: application/json" \
  -d '{
    "gabarit1": "base64_image...",
    "reference": "base64_image...",
    "blend": 0.65
  }'
```

## Note importante
Le premier appel après déploiement sera lent (~30s) car rembg télécharge le modèle U2Net.
Les appels suivants seront beaucoup plus rapides.
