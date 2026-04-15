# app/routes/google_drive.py
"""
📁 GOOGLE DRIVE ROUTER - Luxura Inventory API
==============================================
Endpoints pour uploader des vidéos marketing vers Google Drive.

Endpoints:
- GET  /drive/status     : Vérifier la connexion Google Drive
- GET  /drive/files      : Lister les fichiers du dossier Marketing
- POST /drive/upload     : Uploader une vidéo depuis une URL

Variables d'environnement requises:
- GOOGLE_SERVICE_ACCOUNT_JSON : Credentials JSON du service account
- GOOGLE_DRIVE_FOLDER_ID : ID du Shared Drive "Luxura_Marketing"
"""

import os
import io
import json
import logging
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Google Drive imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

router = APIRouter(prefix="/drive", tags=["Google Drive"])

# Configuration
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "0AP66guFE3lalUk9PVA")
SCOPES = ['https://www.googleapis.com/auth/drive']

logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class DriveUploadRequest(BaseModel):
    video_url: str
    filename: Optional[str] = None
    offer_type: Optional[str] = "direct_sale"  # direct_sale ou salon_affilie
    video_format: Optional[str] = "story"  # story ou feed


# ==================== HELPERS ====================

def get_drive_service():
    """Crée et retourne un service Google Drive authentifié"""
    if not GDRIVE_AVAILABLE:
        raise Exception("Google Drive SDK non installé (pip install google-api-python-client google-auth)")
    
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise Exception("GOOGLE_SERVICE_ACCOUNT_JSON non configuré")
    
    try:
        creds_dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except json.JSONDecodeError as e:
        raise Exception(f"Credentials JSON invalide: {e}")
    except Exception as e:
        raise Exception(f"Erreur création service Drive: {e}")


def download_video(url: str, timeout: int = 120) -> bytes:
    """Télécharge une vidéo depuis une URL"""
    response = requests.get(url, timeout=timeout)
    if response.status_code != 200:
        raise Exception(f"Erreur téléchargement: {response.status_code}")
    return response.content


def generate_filename(offer_type: str, video_format: str, product_name: str = "luxura") -> str:
    """Génère un nom de fichier standardisé"""
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    type_label = "vente" if offer_type == "direct_sale" else "salon"
    format_label = "story_9x16" if video_format == "story" else "feed_4x5"
    clean_name = product_name.lower().replace(" ", "_").replace("-", "_")[:30]
    return f"luxura_{type_label}_{format_label}_{clean_name}_{date_str}.mp4"


# ==================== ENDPOINTS ====================

@router.get("/status")
def drive_status():
    """
    📊 Vérifier le statut de la connexion Google Drive.
    
    Vérifie que les credentials sont valides et que le dossier est accessible.
    """
    if not GDRIVE_AVAILABLE:
        return {
            "success": False,
            "error": "Google Drive SDK non installé",
            "fix": "pip install google-api-python-client google-auth"
        }
    
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        return {
            "success": False,
            "error": "GOOGLE_SERVICE_ACCOUNT_JSON non configuré",
            "fix": "Ajoutez la variable d'environnement avec le JSON du service account"
        }
    
    try:
        service = get_drive_service()
        
        # Vérifier l'accès au dossier
        folder = service.files().get(
            fileId=GOOGLE_DRIVE_FOLDER_ID,
            fields='id, name',
            supportsAllDrives=True
        ).execute()
        
        return {
            "success": True,
            "folder_name": folder.get('name'),
            "folder_id": folder.get('id'),
            "message": f"✅ Connecté au dossier: {folder.get('name')}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Erreur connexion: {e}"
        }


@router.get("/files")
def list_drive_files(limit: int = 20):
    """
    📋 Lister les fichiers dans le dossier Marketing.
    
    Args:
        limit: Nombre maximum de fichiers à retourner (défaut: 20)
    """
    if not GDRIVE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Google Drive SDK non installé")
    
    try:
        service = get_drive_service()
        
        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
        
        results = service.files().list(
            q=query,
            pageSize=limit,
            fields="files(id, name, mimeType, createdTime, webViewLink, size)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        files = results.get('files', [])
        
        return {
            "success": True,
            "count": len(files),
            "files": files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
def upload_to_drive(request: DriveUploadRequest):
    """
    📤 Uploader une vidéo vers Google Drive.
    
    Télécharge une vidéo depuis une URL (ex: Fal.ai) et l'upload 
    dans le Shared Drive Luxura_Marketing.
    
    Args:
        video_url: URL de la vidéo à télécharger
        filename: Nom du fichier (optionnel, généré automatiquement)
        offer_type: "direct_sale" ou "salon_affilie"
        video_format: "story" (9:16) ou "feed" (4:5)
    
    Returns:
        id: ID du fichier sur Google Drive
        name: Nom du fichier
        driveUrl: Lien pour voir le fichier
        webContentLink: Lien de téléchargement direct
    """
    if not GDRIVE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Google Drive SDK non installé")
    
    try:
        # 1. Générer le nom de fichier
        if request.filename:
            filename = request.filename
        else:
            filename = generate_filename(request.offer_type, request.video_format)
        
        logger.info(f"📥 Téléchargement de {request.video_url}...")
        
        # 2. Télécharger la vidéo
        video_content = download_video(request.video_url)
        size_mb = len(video_content) / 1024 / 1024
        
        logger.info(f"✅ Téléchargé: {size_mb:.2f} MB")
        
        # 3. Upload sur Google Drive
        service = get_drive_service()
        
        file_metadata = {
            'name': filename,
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(video_content),
            mimetype="video/mp4",
            resumable=True
        )
        
        logger.info(f"📤 Upload vers Google Drive: {filename}")
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, webContentLink',
            supportsAllDrives=True
        ).execute()
        
        logger.info(f"✅ Fichier uploadé: {file.get('name')}")
        
        return {
            "success": True,
            "message": "Vidéo uploadée sur Google Drive!",
            "id": file.get('id'),
            "name": file.get('name'),
            "webViewLink": file.get('webViewLink'),
            "webContentLink": file.get('webContentLink'),
            "driveUrl": f"https://drive.google.com/file/d/{file.get('id')}/view",
            "size_mb": round(size_mb, 2)
        }
        
    except Exception as e:
        logger.error(f"Erreur upload Drive: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{file_id}")
def delete_drive_file(file_id: str):
    """
    🗑️ Supprimer un fichier de Google Drive.
    
    Args:
        file_id: ID du fichier à supprimer
    """
    if not GDRIVE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Google Drive SDK non installé")
    
    try:
        service = get_drive_service()
        service.files().delete(
            fileId=file_id,
            supportsAllDrives=True
        ).execute()
        
        return {
            "success": True,
            "message": f"Fichier {file_id} supprimé"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
