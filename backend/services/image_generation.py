# services/image_generation.py
"""
Wrapper pour le module image_generation existant.
Permet d'importer depuis services/ tout en utilisant le code existant.
"""

import logging

logger = logging.getLogger(__name__)

# Réexporter les fonctions du module existant
try:
    from image_generation import (
        generate_and_upload_blog_images,
        generate_blog_image_with_dalle,
        get_image_for_blog,
        upload_image_bytes_to_wix,
        get_fallback_unsplash_image,
        should_use_real_images,
        get_real_stock_image_with_logo,
        add_logo_watermark
    )
    logger.info("✅ Image generation module loaded via services wrapper")
except ImportError as e:
    logger.error(f"Failed to import image_generation: {e}")
    
    # Fallbacks
    async def generate_and_upload_blog_images(*args, **kwargs):
        return None, None
    
    async def generate_blog_image_with_dalle(*args, **kwargs):
        return None
    
    def get_fallback_unsplash_image():
        return "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200&h=630&fit=crop"
