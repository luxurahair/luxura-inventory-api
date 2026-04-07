#!/usr/bin/env python3
"""
Luxura Distribution - Fal.ai Video Generator avec Polling Asynchrone
Génère des vidéos Reels dynamiques pour Facebook/Instagram
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

FAL_KEY = os.getenv('FAL_KEY')
if not FAL_KEY:
    print("❌ ERREUR: FAL_KEY non trouvée dans .env")
    sys.exit(1)

# Configuration API Fal.ai
FAL_API_BASE = "https://queue.fal.run"
HEADERS = {
    "Authorization": f"Key {FAL_KEY}",
    "Content-Type": "application/json"
}

# Modèle TEXT-TO-VIDEO - pas besoin d'image source
MODEL_ID = "fal-ai/kling-video/v2.5-turbo/pro/text-to-video"  # Kling v2.5 Turbo Pro - text-to-video haute qualité


def submit_video_job(prompt: str, image_url: str = None, duration: str = "5", aspect_ratio: str = "9:16"):
    """
    Soumet une requête de génération vidéo à Fal.ai
    Retourne le request_id pour le polling
    """
    
    payload = {
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
    }
    
    # Si une image source est fournie (image-to-video)
    if image_url:
        payload["image_url"] = image_url
    
    print(f"🎬 Soumission du job vidéo...")
    print(f"📝 Prompt: {prompt[:100]}...")
    print(f"⏱️ Durée: {duration}s | Format: {aspect_ratio}")
    
    response = requests.post(
        f"{FAL_API_BASE}/{MODEL_ID}",
        headers=HEADERS,
        json=payload,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Erreur soumission: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    request_id = data.get("request_id")
    
    if request_id:
        print(f"✅ Job soumis! Request ID: {request_id}")
        return request_id
    else:
        print(f"❌ Pas de request_id dans la réponse: {data}")
        return None


def poll_video_status(request_id: str, max_attempts: int = 60, interval: int = 10):
    """
    Polling asynchrone du status de génération
    Attend jusqu'à 10 minutes (60 x 10s) pour la completion
    """
    
    # URL correcte selon la doc Fal.ai 2025
    status_url = f"{FAL_API_BASE}/{MODEL_ID}/requests/{request_id}/status"
    result_url = f"{FAL_API_BASE}/{MODEL_ID}/requests/{request_id}"
    
    # Alternative: URL directe qui retourne status + résultat
    direct_url = f"https://queue.fal.run/{MODEL_ID}/{request_id}"
    
    print(f"\n⏳ Polling du status (max {max_attempts * interval}s)...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Utiliser l'URL directe qui retourne status + résultat
            response = requests.get(direct_url, headers=HEADERS, timeout=15)
            
            if response.status_code != 200:
                print(f"  [{attempt}] ⚠️ Status check failed: {response.status_code}")
                print(f"      Response: {response.text[:200]}")
                time.sleep(interval)
                continue
            
            data = response.json()
            status = data.get("status", "unknown")
            
            # Afficher la progression
            if status == "IN_QUEUE":
                queue_pos = data.get("queue_position", "?")
                print(f"  [{attempt}] 🔄 En queue (position: {queue_pos})")
            elif status == "IN_PROGRESS":
                logs = data.get("logs", [])
                if logs:
                    last_log = logs[-1].get("message", "Processing...")
                    print(f"  [{attempt}] 🎥 En cours: {last_log[:50]}")
                else:
                    print(f"  [{attempt}] 🎥 Génération en cours...")
            elif status == "COMPLETED":
                print(f"\n✅ Vidéo générée avec succès!")
                
                # Récupérer le résultat final
                result_response = requests.get(result_url, headers=HEADERS, timeout=30)
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    return result_data
                else:
                    print(f"❌ Erreur récupération résultat: {result_response.status_code}")
                    return None
                    
            elif status == "FAILED":
                error = data.get("error", "Unknown error")
                print(f"\n❌ Génération échouée: {error}")
                return None
            else:
                print(f"  [{attempt}] ❓ Status inconnu: {status}")
            
            time.sleep(interval)
            
        except requests.exceptions.Timeout:
            print(f"  [{attempt}] ⏰ Timeout, retry...")
            time.sleep(interval)
        except Exception as e:
            print(f"  [{attempt}] ❌ Erreur: {str(e)}")
            time.sleep(interval)
    
    print(f"\n⏰ Timeout après {max_attempts * interval}s")
    print(f"💡 Vous pouvez vérifier manuellement avec request_id: {request_id}")
    return None


def generate_luxura_reel():
    """
    Génère un Reel vidéo pour Luxura Distribution
    Concept: Main qui glisse dans des cheveux soyeux
    """
    
    # Prompt ultra-optimisé pour mouvement dynamique et réaliste
    prompt = """
    Hyper-realistic cinematic close-up video: A feminine hand with elegant manicured nails 
    gently glides through long, lustrous, silky brown hair extensions. 
    
    The hair is incredibly smooth, shiny, and flows like liquid silk. 
    As the fingers run through the strands, the hair cascades and bounces naturally 
    with realistic physics. Soft golden hour lighting creates beautiful highlights 
    on the hair strands. 
    
    Camera follows the hand movement in smooth slow motion. 
    Shallow depth of field, professional beauty commercial quality. 
    The hair texture is premium quality human hair extensions - thick, healthy, glossy.
    Gentle breeze adds subtle movement to surrounding strands.
    
    Style: High-end luxury hair commercial, 4K cinematic, photorealistic.
    """
    
    print("=" * 60)
    print("🌟 LUXURA DISTRIBUTION - Génération Vidéo Reel")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Étape 1: Soumettre le job
    request_id = submit_video_job(
        prompt=prompt,
        duration="5",  # 5 secondes pour un Reel
        aspect_ratio="9:16"  # Format vertical Stories/Reels
    )
    
    if not request_id:
        print("❌ Échec de la soumission du job")
        return None
    
    # Sauvegarder le request_id pour récupération ultérieure si besoin
    with open('/app/backend/scripts/last_fal_request.json', 'w') as f:
        json.dump({
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": MODEL_ID,
            "status": "SUBMITTED"
        }, f, indent=2)
    
    # Étape 2: Polling du status
    result = poll_video_status(request_id)
    
    if result:
        # Extraire l'URL de la vidéo
        video_url = None
        
        # Structure peut varier selon le modèle
        if "video" in result:
            video_url = result["video"].get("url") if isinstance(result["video"], dict) else result["video"]
        elif "output" in result:
            video_url = result["output"].get("url") if isinstance(result["output"], dict) else result["output"]
        elif "url" in result:
            video_url = result["url"]
        
        if video_url:
            print(f"\n🎉 VIDÉO PRÊTE!")
            print(f"🔗 URL: {video_url}")
            
            # Mettre à jour le fichier de tracking
            with open('/app/backend/scripts/last_fal_request.json', 'w') as f:
                json.dump({
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                    "model": MODEL_ID,
                    "status": "COMPLETED",
                    "video_url": video_url
                }, f, indent=2)
            
            return video_url
        else:
            print(f"⚠️ Résultat reçu mais URL non trouvée: {json.dumps(result, indent=2)[:500]}")
            return result
    
    return None


def check_existing_job():
    """
    Vérifie si un job précédent est en cours et récupère le résultat
    """
    try:
        with open('/app/backend/scripts/last_fal_request.json', 'r') as f:
            data = json.load(f)
        
        if data.get("status") == "COMPLETED" and data.get("video_url"):
            print(f"✅ Dernier job déjà complété!")
            print(f"🔗 URL: {data['video_url']}")
            return data['video_url']
        
        request_id = data.get("request_id")
        if request_id:
            print(f"🔍 Job précédent trouvé: {request_id}")
            print("   Vérification du status...")
            return poll_video_status(request_id)
            
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        pass
    
    return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Luxura Fal.ai Video Generator")
    parser.add_argument("--check", action="store_true", help="Vérifier un job existant")
    parser.add_argument("--new", action="store_true", help="Générer une nouvelle vidéo")
    
    args = parser.parse_args()
    
    if args.check:
        check_existing_job()
    else:
        # Par défaut, générer une nouvelle vidéo
        generate_luxura_reel()
