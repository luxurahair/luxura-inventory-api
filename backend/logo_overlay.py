# =====================================================
# LOGO OVERLAY MODULE - Luxura Distribution
# Ajoute le logo Luxura sur les images de blog
# Position: Coin bas-droit, Taille: ~15-20%
# =====================================================

import os
import io
import httpx
import asyncio
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# URL du logo Luxura (PNG avec fond transparent)
LUXURA_LOGO_URL = "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/i7uo40l8_Luxura%20Distribution%20-%20OR%20-%20PNG.png"

# Cache du logo pour éviter de le re-télécharger
_logo_cache = None


async def download_image(url: str) -> Image.Image:
    """Télécharge une image depuis une URL et retourne un objet PIL Image."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            else:
                logger.error(f"Failed to download image: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None


async def get_luxura_logo() -> Image.Image:
    """Récupère le logo Luxura (avec cache)."""
    global _logo_cache
    
    if _logo_cache is not None:
        return _logo_cache.copy()
    
    logo = await download_image(LUXURA_LOGO_URL)
    if logo:
        # Convertir en RGBA pour la transparence
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        _logo_cache = logo
        logger.info(f"Logo cached: {logo.size}")
        return logo.copy()
    
    return None


def add_logo_to_image(
    base_image: Image.Image,
    logo: Image.Image,
    position: str = "bottom-right",
    size_percent: float = 0.15,
    padding: int = 20
) -> Image.Image:
    """
    Ajoute le logo sur l'image de base.
    
    Args:
        base_image: Image principale
        logo: Image du logo (avec transparence)
        position: "bottom-right", "bottom-left", "top-right", "top-left"
        size_percent: Taille du logo en % de la largeur de l'image (0.15 = 15%)
        padding: Marge en pixels depuis le bord
    
    Returns:
        Image avec logo intégré
    """
    # Convertir l'image de base en RGBA si nécessaire
    if base_image.mode != 'RGBA':
        base_image = base_image.convert('RGBA')
    
    base_width, base_height = base_image.size
    
    # Redimensionner le logo proportionnellement
    logo_target_width = int(base_width * size_percent)
    logo_ratio = logo.width / logo.height
    logo_target_height = int(logo_target_width / logo_ratio)
    
    logo_resized = logo.resize(
        (logo_target_width, logo_target_height),
        Image.Resampling.LANCZOS
    )
    
    # Calculer la position
    if position == "bottom-right":
        x = base_width - logo_target_width - padding
        y = base_height - logo_target_height - padding
    elif position == "bottom-left":
        x = padding
        y = base_height - logo_target_height - padding
    elif position == "top-right":
        x = base_width - logo_target_width - padding
        y = padding
    elif position == "top-left":
        x = padding
        y = padding
    else:
        # Default: bottom-right
        x = base_width - logo_target_width - padding
        y = base_height - logo_target_height - padding
    
    # Créer une copie de l'image de base
    result = base_image.copy()
    
    # Coller le logo avec transparence
    result.paste(logo_resized, (x, y), logo_resized)
    
    # Convertir en RGB pour la compatibilité JPEG
    if result.mode == 'RGBA':
        # Créer un fond blanc pour les zones transparentes
        background = Image.new('RGB', result.size, (255, 255, 255))
        background.paste(result, mask=result.split()[3])  # Utiliser le canal alpha comme masque
        result = background
    
    return result


async def process_image_with_logo(
    image_url: str,
    position: str = "bottom-right",
    size_percent: float = 0.15,
    padding: int = 20
) -> bytes:
    """
    Télécharge une image, ajoute le logo Luxura, et retourne les bytes JPEG.
    
    Args:
        image_url: URL de l'image source
        position: Position du logo
        size_percent: Taille du logo (0.15 = 15%)
        padding: Marge en pixels
    
    Returns:
        Bytes de l'image JPEG avec logo
    """
    try:
        # Télécharger l'image de base
        logger.info(f"Downloading base image: {image_url[:60]}...")
        base_image = await download_image(image_url)
        if not base_image:
            logger.error("Failed to download base image")
            return None
        
        # Récupérer le logo
        logo = await get_luxura_logo()
        if not logo:
            logger.warning("Logo not available, returning original image")
            # Retourner l'image originale sans logo
            output = io.BytesIO()
            if base_image.mode == 'RGBA':
                base_image = base_image.convert('RGB')
            base_image.save(output, format='JPEG', quality=90)
            return output.getvalue()
        
        # Ajouter le logo
        logger.info(f"Adding logo at {position}, size {size_percent*100}%")
        result_image = add_logo_to_image(
            base_image, 
            logo, 
            position=position,
            size_percent=size_percent,
            padding=padding
        )
        
        # Convertir en bytes JPEG
        output = io.BytesIO()
        result_image.save(output, format='JPEG', quality=90)
        logger.info(f"Image with logo created: {len(output.getvalue())} bytes")
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error processing image with logo: {e}")
        return None


async def upload_image_with_logo_to_wix(
    api_key: str,
    site_id: str,
    source_image_url: str,
    file_name: str = None,
    position: str = "bottom-right",
    size_percent: float = 0.15
) -> dict:
    """
    Télécharge une image, ajoute le logo, et l'upload sur Wix Media.
    
    Returns:
        Dict avec les informations Wix (file_id, static_url, etc.)
    """
    import uuid
    
    try:
        # Générer un nom de fichier unique
        if not file_name:
            file_name = f"luxura-blog-{uuid.uuid4().hex[:8]}.jpg"
        
        # Créer l'image avec logo
        image_bytes = await process_image_with_logo(
            source_image_url,
            position=position,
            size_percent=size_percent
        )
        
        if not image_bytes:
            logger.error("Failed to create image with logo")
            return None
        
        # Upload vers Wix Media Manager
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Étape 1: Générer une URL d'upload
            logger.info("Requesting Wix upload URL...")
            
            generate_payload = {
                "mimeType": "image/jpeg",
                "fileName": file_name,
                "parentFolderId": "media-root"  # Dossier racine
            }
            
            response = await client.post(
                "https://www.wixapis.com/site-media/v1/files/generate-file-upload-url",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=generate_payload
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to generate upload URL: {response.status_code} - {response.text}")
                return None
            
            upload_data = response.json()
            upload_url = upload_data.get("uploadUrl")
            
            if not upload_url:
                logger.error("No upload URL returned")
                return None
            
            # Étape 2: Upload direct
            logger.info(f"Uploading image to Wix...")
            
            upload_response = await client.put(
                upload_url,
                content=image_bytes,
                headers={
                    "Content-Type": "image/jpeg"
                }
            )
            
            if upload_response.status_code not in (200, 201):
                logger.error(f"Upload failed: {upload_response.status_code} - {upload_response.text}")
                return None
            
            # Extraire le file_id depuis l'URL d'upload ou la réponse
            file_info = upload_data.get("file", {})
            file_id = file_info.get("id")
            
            if not file_id:
                # Essayer d'extraire depuis la réponse d'upload
                try:
                    upload_result = upload_response.json()
                    file_id = upload_result.get("file", {}).get("id") or upload_result.get("id")
                except:
                    pass
            
            if not file_id:
                logger.error("Could not determine file_id after upload")
                return None
            
            # Attendre que le fichier soit prêt
            logger.info(f"Waiting for file {file_id} to be ready...")
            await asyncio.sleep(2)  # Court délai avant de vérifier
            
            # Vérifier le statut du fichier
            for attempt in range(30):
                status_response = await client.get(
                    f"https://www.wixapis.com/site-media/v1/files/{file_id}",
                    headers={
                        "Authorization": api_key,
                        "wix-site-id": site_id
                    }
                )
                
                if status_response.status_code == 200:
                    file_data = status_response.json().get("file", {})
                    status = file_data.get("operationStatus")
                    
                    if status == "READY":
                        logger.info(f"File {file_id} is READY!")
                        
                        # Construire les URLs
                        static_url = f"https://static.wixstatic.com/media/{file_id}"
                        
                        return {
                            "file_id": file_id,
                            "static_url": static_url,
                            "width": 1200,
                            "height": 630,
                            "source_url": source_image_url
                        }
                    
                    if status == "FAILED":
                        logger.error(f"File processing failed for {file_id}")
                        return None
                
                await asyncio.sleep(1)
            
            logger.error(f"Timeout waiting for file {file_id} to be ready")
            return None
            
    except Exception as e:
        logger.error(f"Error in upload_image_with_logo_to_wix: {e}")
        import traceback
        traceback.print_exc()
        return None


# Test standalone
if __name__ == "__main__":
    async def test():
        # Test avec une image Unsplash
        test_url = "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop"
        
        image_bytes = await process_image_with_logo(
            test_url,
            position="bottom-right",
            size_percent=0.15
        )
        
        if image_bytes:
            with open("/tmp/test_logo_overlay.jpg", "wb") as f:
                f.write(image_bytes)
            print(f"Test image saved to /tmp/test_logo_overlay.jpg ({len(image_bytes)} bytes)")
        else:
            print("Failed to create test image")
    
    asyncio.run(test())
