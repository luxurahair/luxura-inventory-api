"""
Luxura Marketing - Google Drive Integration
Upload des vidéos marketing vers Google Drive
"""

import os
import json
import logging
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Google Drive imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
    import io
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False
    logger.warning("Google Drive SDK non disponible")


# Configuration
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1w0tX9-V_Y39Vi8ZDqxmF-Hy9eoMvsAs1")

SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_drive_service():
    """
    Crée et retourne un service Google Drive authentifié
    """
    if not GDRIVE_AVAILABLE:
        raise Exception("Google Drive SDK non installé")
    
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise Exception("GOOGLE_SERVICE_ACCOUNT_JSON non configuré")
    
    try:
        # Parser le JSON des credentials
        creds_dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        
        service = build('drive', 'v3', credentials=credentials)
        return service
        
    except json.JSONDecodeError as e:
        logger.error(f"Erreur parsing credentials JSON: {e}")
        raise Exception(f"Credentials JSON invalide: {e}")
    except Exception as e:
        logger.error(f"Erreur création service Drive: {e}")
        raise


async def download_video_from_url(url: str) -> bytes:
    """
    Télécharge une vidéo depuis une URL (ex: Fal.ai)
    """
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise Exception(f"Erreur téléchargement: {response.status_code}")
        return response.content


def upload_file_to_drive(
    file_content: bytes,
    filename: str,
    mimetype: str = "video/mp4",
    folder_id: str = None
) -> dict:
    """
    Upload un fichier vers Google Drive
    
    Args:
        file_content: Contenu du fichier en bytes
        filename: Nom du fichier
        mimetype: Type MIME (video/mp4, image/jpeg, etc.)
        folder_id: ID du dossier destination (défaut: Marketing_Ads)
    
    Returns:
        dict avec id, name, webViewLink
    """
    
    service = get_drive_service()
    
    if not folder_id:
        folder_id = GOOGLE_DRIVE_FOLDER_ID
    
    # Métadonnées du fichier
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    # Créer le media upload depuis les bytes
    media = MediaIoBaseUpload(
        io.BytesIO(file_content),
        mimetype=mimetype,
        resumable=True
    )
    
    # Upload
    logger.info(f"📤 Upload vers Google Drive: {filename}")
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink, webContentLink'
    ).execute()
    
    logger.info(f"✅ Fichier uploadé: {file.get('name')} (ID: {file.get('id')})")
    
    return {
        'id': file.get('id'),
        'name': file.get('name'),
        'webViewLink': file.get('webViewLink'),
        'webContentLink': file.get('webContentLink'),
        'driveUrl': f"https://drive.google.com/file/d/{file.get('id')}/view"
    }


async def upload_video_from_url(
    video_url: str,
    filename: str,
    folder_id: str = None
) -> dict:
    """
    Télécharge une vidéo depuis une URL et l'upload sur Google Drive
    
    Args:
        video_url: URL de la vidéo (ex: Fal.ai)
        filename: Nom du fichier (ex: "luxura_story_vente_directe_2024.mp4")
        folder_id: ID du dossier (optionnel)
    
    Returns:
        dict avec les infos du fichier uploadé
    """
    
    logger.info(f"📥 Téléchargement de {video_url}...")
    
    # Télécharger la vidéo
    video_content = await download_video_from_url(video_url)
    
    logger.info(f"✅ Téléchargé: {len(video_content) / 1024 / 1024:.2f} MB")
    
    # Upload sur Drive
    result = upload_file_to_drive(
        file_content=video_content,
        filename=filename,
        mimetype="video/mp4",
        folder_id=folder_id
    )
    
    return result


async def upload_marketing_video(
    video_url: str,
    offer_type: str,
    video_format: str,
    product_name: str = "luxura"
) -> dict:
    """
    Upload une vidéo marketing avec un nom standardisé
    
    Args:
        video_url: URL Fal.ai de la vidéo
        offer_type: "direct_sale" ou "salon_affilie"
        video_format: "story" ou "feed"
        product_name: Nom du produit
    
    Returns:
        dict avec les infos du fichier
    """
    
    from datetime import datetime
    
    # Générer un nom de fichier standardisé
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    
    type_label = "vente" if offer_type == "direct_sale" else "salon"
    format_label = "story_9x16" if video_format == "story" else "feed_4x5"
    
    # Nettoyer le nom du produit
    clean_name = product_name.lower().replace(" ", "_").replace("-", "_")[:30]
    
    filename = f"luxura_{type_label}_{format_label}_{clean_name}_{date_str}.mp4"
    
    logger.info(f"🎬 Upload vidéo marketing: {filename}")
    
    result = await upload_video_from_url(video_url, filename)
    
    return result


def list_marketing_files(limit: int = 20) -> list:
    """
    Liste les fichiers dans le dossier Marketing_Ads
    """
    
    service = get_drive_service()
    
    query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
    
    results = service.files().list(
        q=query,
        pageSize=limit,
        fields="files(id, name, mimeType, createdTime, webViewLink, size)"
    ).execute()
    
    files = results.get('files', [])
    
    return files


def delete_file(file_id: str) -> bool:
    """
    Supprime un fichier de Google Drive
    """
    
    service = get_drive_service()
    
    try:
        service.files().delete(fileId=file_id).execute()
        logger.info(f"🗑️ Fichier supprimé: {file_id}")
        return True
    except Exception as e:
        logger.error(f"Erreur suppression: {e}")
        return False


# Test de connexion
def test_drive_connection() -> dict:
    """
    Teste la connexion à Google Drive
    """
    
    try:
        service = get_drive_service()
        
        # Vérifier l'accès au dossier
        folder = service.files().get(
            fileId=GOOGLE_DRIVE_FOLDER_ID,
            fields='id, name'
        ).execute()
        
        return {
            'success': True,
            'folder_name': folder.get('name'),
            'folder_id': folder.get('id'),
            'message': f"✅ Connecté au dossier: {folder.get('name')}"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"❌ Erreur connexion: {e}"
        }
