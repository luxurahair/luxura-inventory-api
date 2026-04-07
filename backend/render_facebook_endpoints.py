"""
🔵 FACEBOOK ENDPOINTS POUR LUXURA-INVENTORY-API (RENDER)
=========================================================

Ajoute ce code dans ton fichier main.py sur GitHub (luxura-inventory-api)
pour avoir les endpoints Facebook accessibles depuis partout.

À ajouter dans luxurahair/luxura-inventory-api sur GitHub.
"""

# ==================== IMPORTS À AJOUTER ====================
# import os
# import httpx
# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import Optional

# ==================== MODELS ====================

class FacebookPostRequest(BaseModel):
    message: str
    link: Optional[str] = None
    image_url: Optional[str] = None

class FacebookPostResponse(BaseModel):
    success: bool
    post_id: Optional[str] = None
    error: Optional[str] = None
    page_url: Optional[str] = None

# ==================== ROUTER ====================

# Ajouter ce router dans main.py:
# facebook_router = APIRouter(prefix="/facebook", tags=["Facebook"])
# app.include_router(facebook_router)

# ==================== ENDPOINTS ====================

"""
@facebook_router.get("/status")
async def facebook_status():
    '''Vérifier le statut de la connexion Facebook'''
    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    fb_page_id = os.getenv("FB_PAGE_ID", "1838415193042352")
    
    status = {
        "configured": bool(fb_token),
        "page_id": fb_page_id,
        "token_valid": False,
        "page_name": None
    }
    
    if fb_token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://graph.facebook.com/v25.0/{fb_page_id}",
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


@facebook_router.post("/post", response_model=FacebookPostResponse)
async def post_to_facebook(request: FacebookPostRequest):
    '''Publier un message sur la page Facebook Luxura'''
    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    fb_page_id = os.getenv("FB_PAGE_ID", "1838415193042352")
    
    if not fb_token:
        raise HTTPException(status_code=400, detail="FB_PAGE_ACCESS_TOKEN non configuré")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            data = {"message": request.message, "access_token": fb_token}
            
            if request.link:
                data["link"] = request.link
            
            # Si image_url fournie, poster comme photo
            if request.image_url:
                response = await client.post(
                    f"https://graph.facebook.com/v25.0/{fb_page_id}/photos",
                    data={
                        "url": request.image_url,
                        "caption": request.message,
                        "access_token": fb_token
                    }
                )
            else:
                response = await client.post(
                    f"https://graph.facebook.com/v25.0/{fb_page_id}/feed",
                    data=data
                )
            
            result = response.json()
            
            if "error" in result:
                return FacebookPostResponse(
                    success=False,
                    error=result["error"].get("message")
                )
            
            return FacebookPostResponse(
                success=True,
                post_id=result.get("id") or result.get("post_id"),
                page_url=f"https://www.facebook.com/{fb_page_id}"
            )
            
    except Exception as e:
        return FacebookPostResponse(success=False, error=str(e))


@facebook_router.post("/post-blog")
async def post_blog_to_facebook(
    title: str,
    excerpt: str,
    url: str,
    image_url: Optional[str] = None
):
    '''Publier un article de blog sur Facebook avec formatage automatique'''
    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    fb_page_id = os.getenv("FB_PAGE_ID", "1838415193042352")
    
    if not fb_token:
        raise HTTPException(status_code=400, detail="FB_PAGE_ACCESS_TOKEN non configuré")
    
    # Formater le message
    message = f"📰 NOUVEAU BLOG | {title}\\n\\n{excerpt}\\n\\n👉 Lire l'article complet:\\n{url}\\n\\n#LuxuraDistribution #ExtensionsCheveux #Quebec #Blog"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://graph.facebook.com/v25.0/{fb_page_id}/feed",
                data={
                    "message": message,
                    "link": url,
                    "access_token": fb_token
                }
            )
            
            result = response.json()
            
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"].get("message"))
            
            return {
                "success": True,
                "post_id": result.get("id"),
                "message": "Blog publié sur Facebook!"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

# ==================== INSTRUCTIONS ====================
INSTRUCTIONS = """
📋 INSTRUCTIONS POUR AJOUTER CES ENDPOINTS SUR RENDER:

1. Va sur GitHub: https://github.com/luxurahair/luxura-inventory-api

2. Ouvre le fichier main.py (ou server.py)

3. Ajoute les imports en haut:
   import httpx
   from pydantic import BaseModel
   from typing import Optional

4. Ajoute les classes FacebookPostRequest et FacebookPostResponse

5. Crée le router:
   facebook_router = APIRouter(prefix="/facebook", tags=["Facebook"])

6. Ajoute les 3 endpoints (@facebook_router.get/post...)

7. Inclus le router:
   app.include_router(facebook_router)

8. Commit et push - Render va auto-déployer

9. Test: curl https://luxura-inventory-api.onrender.com/facebook/status
"""

if __name__ == "__main__":
    print(INSTRUCTIONS)
