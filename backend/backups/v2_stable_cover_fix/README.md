# Backup V2 - Cover Image Fix Stable (2026-03-29)

## Ce qui fonctionne

### Payload PATCH pour cover image Wix
```python
payload = {
    "draftPost": {
        "media": {
            "wixMedia": {
                "image": {
                    "id": "f1b961_xxx~mv2.png"  # Simple file_id, PAS wix:image://
                }
            },
            "displayed": True,
            "custom": True  # CRUCIAL!
        }
    }
}
```

### Règles
1. `file_id` simple (ex: `f1b961_xxx~mv2.png`)
2. `custom: True` obligatoire
3. Pas de `wix:image://v1/...#originWidth=...`
4. Pas de `.replace(".png", ".jpg")`

### Flux de création blog
1. `create_wix_draft_post()` - crée draft avec richContent (images inline)
2. `attach_cover_image_to_wix_draft()` - PATCH séparé pour cover
3. `add_seo_metadata_to_draft()` - ajoute meta
4. `publish_wix_draft()` - publie

### Fichiers modifiés
- `image_generation.py` - V5 avec brief complet
- `image_brief_generator.py` - V7 aligné Luxura
- `blog_automation.py` - generate_blog_with_ai, generate_daily_blogs, attach_cover_image_to_wix_draft

### 12 Titres Stratégiques
Ratio: 40% guides, 30% comparatifs, 30% B2B salons
