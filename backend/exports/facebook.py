# app/routes/facebook.py
"""
🔵 FACEBOOK ROUTER - Luxura Inventory API
==========================================
Endpoints pour publier sur la page Facebook Luxura Distribution.

Endpoints:
- GET  /facebook/status    : Vérifier le statut de connexion
- GET  /facebook/test      : Test rapide de connexion
- POST /facebook/post      : Publier un message/lien/image
- POST /facebook/post-blog : Publier un article de blog formaté
"""

import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/facebook", tags=["Facebook"])

# Configuration - Page Facebook Luxura
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "1838415193042352")


# ==================== MODELS ====================

class FacebookPostRequest(BaseModel):
    message: str
    link: Optional[str] = None
    image_url: Optional[str] = None


class FacebookBlogRequest(BaseModel):
    title: str
    excerpt: str
    url: str
    image_url: Optional[str] = None


# ==================== ENDPOINTS ====================

@router.get("/status")
async def facebook_status():
    """
    📊 Vérifier le statut de la connexion Facebook.
    
    Retourne si le token est configuré et valide.
    """
    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    
    status = {
        "configured": bool(fb_token),
        "token_valid": False,
        "page_id": FB_PAGE_ID,
        "page_name": None
    }
    
    if not fb_token:
        return status
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://graph.facebook.com/v25.0/{FB_PAGE_ID}",
                params={"access_token": fb_token, "fields": "name,id"}
            )
            result = response.json()
            
            if "error" not in result:
                status["token_valid"] = True
                status["page_name"] = result.get("name")
            else:
                status["error"] = result["error"].get("message")
                
    except Exception as e:
        status["error"] = str(e)
    
    return status


@router.get("/test")
async def test_facebook_connection():
    """
    🧪 Test rapide de la connexion Facebook.
    
    Vérifie que le token est valide sans rien publier.
    """
    status = await facebook_status()
    
    if status.get("token_valid"):
        return {
            "ok": True,
            "message": f"✅ Connecté à la page: {status.get('page_name')}",
            "page_id": status.get("page_id"),
            "ready_to_post": True
        }
    else:
        return {
            "ok": False,
            "message": f"❌ Connexion échouée: {status.get('error', 'Token non configuré')}",
            "ready_to_post": False,
            "fix": "Mettez à jour FB_PAGE_ACCESS_TOKEN dans les variables d'environnement Render"
        }


@router.post("/post")
async def post_to_facebook(request: FacebookPostRequest):
    """
    📘 Publier un message sur la page Facebook Luxura.
    
    Args:
        message: Le texte du post
        link: (optionnel) URL à partager
        image_url: (optionnel) URL d'une image à poster
    
    Returns:
        success: bool
        post_id: ID du post créé
        page_url: Lien vers la page Facebook
    """
    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    
    if not fb_token:
        raise HTTPException(
            status_code=400,
            detail="FB_PAGE_ACCESS_TOKEN non configuré dans les variables d'environnement Render"
        )
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Si image_url fournie, poster comme photo
            if request.image_url:
                response = await client.post(
                    f"https://graph.facebook.com/v25.0/{FB_PAGE_ID}/photos",
                    data={
                        "url": request.image_url,
                        "caption": request.message,
                        "access_token": fb_token
                    }
                )
            else:
                # Post texte/lien standard
                data = {
                    "message": request.message,
                    "access_token": fb_token
                }
                if request.link:
                    data["link"] = request.link
                
                response = await client.post(
                    f"https://graph.facebook.com/v25.0/{FB_PAGE_ID}/feed",
                    data=data
                )
            
            result = response.json()
            
            if "error" in result:
                error = result["error"]
                error_code = error.get("code")
                error_msg = error.get("message")
                
                if error_code == 190:
                    raise HTTPException(
                        status_code=401,
                        detail=f"Token Facebook expiré. Mettez à jour FB_PAGE_ACCESS_TOKEN sur Render. Erreur: {error_msg}"
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Erreur Facebook ({error_code}): {error_msg}"
                )
            
            post_id = result.get("id") or result.get("post_id")
            
            return {
                "success": True,
                "post_id": post_id,
                "page_url": f"https://www.facebook.com/{FB_PAGE_ID}",
                "post_url": f"https://www.facebook.com/{post_id}" if post_id else None
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post-blog")
async def post_blog_to_facebook(request: FacebookBlogRequest):
    """
    📰 Publier un article de blog sur Facebook avec formatage automatique.
    
    Crée un post formaté avec titre, extrait et lien vers l'article.
    
    Args:
        title: Titre de l'article
        excerpt: Extrait/résumé (sera tronqué à 200 caractères)
        url: URL de l'article complet
        image_url: (optionnel) Image de couverture
    """
    # Formater le message
    excerpt_clean = request.excerpt[:200] + "..." if len(request.excerpt) > 200 else request.excerpt
    
    message = f"""📰 NOUVEAU BLOG | {request.title}

{excerpt_clean}

👉 Lire l'article complet:
{request.url}

#LuxuraDistribution #ExtensionsCheveux #Quebec #Blog #Coiffure"""
    
    # Utiliser l'endpoint de post standard
    post_request = FacebookPostRequest(
        message=message,
        link=request.url,
        image_url=request.image_url
    )
    
    return await post_to_facebook(post_request)
