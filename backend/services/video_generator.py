# services/video_generator.py
"""
Génération de vidéos courtes avec Runway Gen-3
Version V1 - Structure de base (MOCK pour l'instant)

Note: Nécessite RUNWAY_API_KEY dans .env pour fonctionner réellement
"""

import os
import logging
import asyncio
from typing import Dict, Optional

logger = logging.getLogger(__name__)

RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")
RUNWAY_ENABLED = bool(RUNWAY_API_KEY)


async def generate_short_video(
    video_brief: Dict,
    image_url: Optional[str] = None
) -> Optional[str]:
    """
    Génère une vidéo courte avec Runway Gen-3 Alpha Turbo.
    
    Args:
        video_brief: Brief de la vidéo (scene, motion, duration, etc.)
        image_url: URL de l'image source pour image-to-video (optionnel)
    
    Returns:
        URL de la vidéo générée ou None si échec
    """
    if not RUNWAY_ENABLED:
        logger.info("🎥 Video generation skipped (RUNWAY_API_KEY not configured)")
        return None
    
    try:
        import httpx
        
        # Construire le prompt
        scene = video_brief.get("scene", "")
        motion = video_brief.get("motion", "")
        style = video_brief.get("style", "")
        safety = video_brief.get("safety_rules", "")
        
        prompt = f"{scene} {motion}. {style}. {safety}"
        
        logger.info(f"🎥 Generating video: {video_brief.get('video_mode')}")
        logger.info(f"   Duration: {video_brief.get('duration_seconds')}s")
        logger.info(f"   Aspect: {video_brief.get('aspect_ratio')}")
        
        # Payload Runway Gen-3
        payload = {
            "prompt": prompt,
            "duration": video_brief.get("duration_seconds", 10),
            "aspect_ratio": video_brief.get("aspect_ratio", "9:16"),
            "model": "gen-3-alpha-turbo"
        }
        
        # Ajouter l'image source si disponible (image-to-video)
        if image_url and video_brief.get("use_image_to_video", True):
            payload["image_url"] = image_url
            logger.info(f"   Using image-to-video with: {image_url[:60]}...")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Lancer la génération
            response = await client.post(
                "https://api.runwayml.com/v1/generations",
                headers={
                    "Authorization": f"Bearer {RUNWAY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code not in (200, 201):
                logger.error(f"Runway API error: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            job_id = result.get("id")
            
            if not job_id:
                logger.error("No job ID returned from Runway")
                return None
            
            logger.info(f"   Job started: {job_id}")
            
            # Polling pour attendre le résultat (max ~3.5 minutes)
            for attempt in range(42):
                await asyncio.sleep(5)
                
                status_response = await client.get(
                    f"https://api.runwayml.com/v1/generations/{job_id}",
                    headers={"Authorization": f"Bearer {RUNWAY_API_KEY}"}
                )
                
                if status_response.status_code != 200:
                    continue
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                if status == "SUCCEEDED":
                    video_url = status_data.get("output", {}).get("video_url")
                    if video_url:
                        logger.info(f"✅ Video generated: {video_url[:60]}...")
                        return video_url
                    else:
                        logger.error("Video succeeded but no URL returned")
                        return None
                
                elif status == "FAILED":
                    error = status_data.get("error", "Unknown error")
                    logger.error(f"Video generation failed: {error}")
                    return None
                
                elif status in ("PENDING", "PROCESSING"):
                    if attempt % 6 == 0:  # Log every 30 seconds
                        logger.info(f"   Still processing... ({attempt * 5}s)")
                    continue
            
            logger.error("Video generation timed out")
            return None
            
    except ImportError:
        logger.error("httpx not available for video generation")
        return None
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def upload_video_to_wix(
    api_key: str,
    site_id: str,
    video_url: str,
    file_name: str = "luxura-video.mp4"
) -> Optional[Dict]:
    """
    Upload une vidéo vers Wix Media Manager.
    
    Note: À implémenter si nécessaire pour l'intégration blog.
    """
    # TODO: Implémenter l'upload vidéo vers Wix si nécessaire
    logger.info(f"📹 Video upload to Wix: {video_url[:50]}...")
    return {"video_url": video_url}
