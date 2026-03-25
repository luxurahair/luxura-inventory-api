# Problème Wix Blog API - Images ne s'affichent pas

## Contexte
Application de génération automatique de blogs pour Luxura Distribution (extensions cheveux).
- Backend: FastAPI (Python)
- Publication: Wix Blog API v3
- Images: Importées depuis Unsplash → Wix Media Manager

## Problème
Les images de couverture (cover/hero) ne s'affichent pas malgré HTTP 200 OK sur tous les appels API.

## Flux actuel (4 étapes)

```
1. Créer brouillon (POST /blog/v3/draft-posts) → 200 OK ✅
2. Importer image (POST /site-media/v1/files/import) → 200 OK ✅
3. Attacher image au draft (PATCH /blog/v3/draft-posts/{id}) → 200 OK ✅
4. Publier (POST /blog/v3/draft-posts/{id}/publish) → 200 OK ✅
```

## Réponse de l'import Wix Media (étape 2)
```json
{
  "file": {
    "id": "f1b961_160b83a62cc74364bef8fa3546985d3a~mv2.jpg",
    "url": "https://static.wixstatic.com/media/f1b961_160b83a62cc74364bef8fa3546985d3a~mv2.jpg",
    "displayName": "blog-218cf0fe-cover.jpg",
    "mediaType": "IMAGE",
    "mimeType": "image/jpeg",
    "sizeInBytes": "195581",
    "state": "OK"
  }
}
```

## Payload PATCH pour attacher l'image (étape 3)
```python
# Format testé 1 - coverMedia avec dimensions
{
    "draftPost": {
        "coverMedia": {
            "enabled": True,
            "displayed": True,
            "image": {
                "id": "f1b961_160b83a62cc74364bef8fa3546985d3a~mv2.jpg",
                "url": "https://static.wixstatic.com/media/f1b961_160b83a62cc74364bef8fa3546985d3a~mv2.jpg",
                "width": 1200,
                "height": 800,
                "filename": "f1b961_160b83a62cc74364bef8fa3546985d3a~mv2.jpg"
            }
        }
    }
}
# Résultat: 200 OK mais image ne s'affiche pas

# Format testé 2 - media.wixMedia
{
    "draftPost": {
        "media": {
            "wixMedia": {
                "image": {...}
            },
            "displayed": True
        }
    }
}
# Résultat: 400 Bad Request "Expected an object"

# Format testé 3 - heroImage
{
    "draftPost": {
        "heroImage": {...}
    }
}
# Résultat: 200 OK mais image ne s'affiche pas
```

## Logs backend
```
2026-03-25 23:42:46,936 - INFO - Wix Media import successful
2026-03-25 23:42:47,309 - INFO - HTTP Request: PATCH .../draft-posts/218cf0fe-... "HTTP/1.1 200 OK"
2026-03-25 23:42:47,310 - INFO - Image attached with coverMedia + dimensions
2026-03-25 23:42:47,689 - INFO - HTTP Request: POST .../publish "HTTP/1.1 200 OK"
```

## Capture écran Wix
Toutes les images montrent l'icône "image cassée" (montagne avec X) dans le panneau admin Wix.

## Bug connu Wix
Forum Wix: https://forum.wixstudio.com/t/api-import-file-create-draft-post-bug-for-the-cover-image/58540
> "After API creation, the Wix GUI shows w_NaN,h_NaN placeholders"
> "Manually reassigning in the panel fixes display"

## Variables d'environnement
```
WIX_API_KEY=IST.eyJra...
WIX_SITE_ID=6e62c946-d068-45c1-8f5f-7af998f0d7b3
```

## Question pour ChatGPT
Quel est le format exact du payload PATCH pour que l'image coverMedia s'affiche réellement dans le blog Wix après publication ?

Le fichier `blog_automation.py` complet est joint.
