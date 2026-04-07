"""
Luxura Marketing - Générateur de vidéos publicitaires via Fal.ai
"""

import os
import json
import asyncio
import logging
import httpx
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

FAL_KEY = os.getenv("FAL_KEY")
FAL_API_BASE = "https://queue.fal.run"

# Modèles disponibles
MODELS = {
    "text_to_video": "fal-ai/kling-video/v2.5-turbo/pro/text-to-video",
    "image_to_video": "fal-ai/kling-video/v1.6/pro/image-to-video"
}


async def submit_video_job(
    prompt: str,
    aspect_ratio: str = "9:16",
    duration: str = "5",
    image_url: Optional[str] = None
) -> dict:
    """
    Soumet un job de génération vidéo à Fal.ai
    
    Args:
        prompt: Description de la vidéo à générer
        aspect_ratio: "9:16" pour Story, "4:5" pour Feed
        duration: Durée en secondes
        image_url: URL image source (optionnel, pour image-to-video)
    
    Returns:
        dict avec request_id et URLs de status
    """
    
    if not FAL_KEY:
        raise Exception("FAL_KEY non configurée")
    
    # Choisir le modèle
    if image_url:
        model = MODELS["image_to_video"]
        payload = {
            "prompt": prompt,
            "image_url": image_url,
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }
    else:
        model = MODELS["text_to_video"]
        payload = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }
    
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{FAL_API_BASE}/{model}",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"Erreur Fal.ai submit: {response.status_code} - {response.text}")
            raise Exception(f"Erreur Fal.ai: {response.status_code}")
        
        data = response.json()
        
        logger.info(f"Job Fal.ai soumis: {data.get('request_id')}")
        
        return {
            "request_id": data.get("request_id"),
            "status_url": data.get("status_url"),
            "response_url": data.get("response_url"),
            "model": model,
            "aspect_ratio": aspect_ratio
        }


async def check_video_status(request_id: str, model: str = None) -> dict:
    """
    Vérifie le status d'un job Fal.ai
    
    Returns:
        dict avec status et video_url si complété
    """
    
    if not FAL_KEY:
        raise Exception("FAL_KEY non configurée")
    
    if not model:
        model = MODELS["text_to_video"]
    
    headers = {
        "Authorization": f"Key {FAL_KEY}"
    }
    
    status_url = f"{FAL_API_BASE}/{model}/requests/{request_id}/status"
    response_url = f"{FAL_API_BASE}/{model}/requests/{request_id}"
    
    async with httpx.AsyncClient(timeout=15) as client:
        # Vérifier le status
        status_resp = await client.get(status_url, headers=headers)
        
        if status_resp.status_code != 200:
            # Essayer l'URL générique
            status_url = f"https://queue.fal.run/fal-ai/kling-video/requests/{request_id}/status"
            status_resp = await client.get(status_url, headers=headers)
        
        status_data = status_resp.json()
        status = status_data.get("status", "unknown")
        
        result = {
            "status": status,
            "request_id": request_id,
            "video_url": None,
            "file_size": None
        }
        
        if status == "COMPLETED":
            # Récupérer le résultat
            response_url = f"https://queue.fal.run/fal-ai/kling-video/requests/{request_id}"
            result_resp = await client.get(response_url, headers=headers)
            
            if result_resp.status_code == 200:
                result_data = result_resp.json()
                video = result_data.get("video", {})
                result["video_url"] = video.get("url")
                result["file_size"] = video.get("file_size")
        
        return result


async def generate_video_with_polling(
    prompt: str,
    aspect_ratio: str = "9:16",
    duration: str = "5",
    image_url: Optional[str] = None,
    max_wait_seconds: int = 300,
    poll_interval: int = 10
) -> dict:
    """
    Génère une vidéo et attend le résultat via polling
    
    Returns:
        dict avec video_url ou erreur
    """
    
    # Soumettre le job
    job = await submit_video_job(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        duration=duration,
        image_url=image_url
    )
    
    request_id = job["request_id"]
    model = job["model"]
    
    logger.info(f"Polling vidéo {request_id}...")
    
    # Polling
    elapsed = 0
    while elapsed < max_wait_seconds:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        
        result = await check_video_status(request_id, model)
        status = result["status"]
        
        logger.info(f"[{elapsed}s] Status: {status}")
        
        if status == "COMPLETED":
            return {
                "success": True,
                "request_id": request_id,
                "video_url": result["video_url"],
                "file_size": result["file_size"],
                "aspect_ratio": aspect_ratio
            }
        elif status == "FAILED":
            return {
                "success": False,
                "request_id": request_id,
                "error": "Génération échouée"
            }
    
    # Timeout
    return {
        "success": False,
        "request_id": request_id,
        "error": f"Timeout après {max_wait_seconds}s",
        "status": "timeout"
    }


async def generate_ad_videos(
    story_prompt: str,
    feed_prompt: str,
    image_url: Optional[str] = None
) -> Tuple[dict, dict]:
    """
    Génère les deux formats vidéo (Story + Feed) en parallèle
    
    Returns:
        Tuple (story_result, feed_result)
    """
    
    # Soumettre les deux jobs
    story_job = await submit_video_job(
        prompt=story_prompt,
        aspect_ratio="9:16",
        duration="5",
        image_url=image_url
    )
    
    feed_job = await submit_video_job(
        prompt=feed_prompt,
        aspect_ratio="4:5",
        duration="5",
        image_url=image_url
    )
    
    return {
        "story": {
            "request_id": story_job["request_id"],
            "model": story_job["model"],
            "status": "IN_QUEUE"
        },
        "feed": {
            "request_id": feed_job["request_id"],
            "model": feed_job["model"],
            "status": "IN_QUEUE"
        }
    }
