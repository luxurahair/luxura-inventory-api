# ==================== COLOR ENGINE API ====================
# Ajouter cet import en haut du fichier main.py :
from color_engine_api import process_color_engine

# Ajouter ce modèle Pydantic avec les autres modèles :
class ColorEngineRequest(BaseModel):
    """Requête pour le Color Engine"""
    gabarit1: str = Field(..., description="Image gabarit 1 en base64")
    gabarit2: Optional[str] = Field(None, description="Image gabarit 2 en base64 (optionnel)")
    reference: str = Field(..., description="Image référence couleur en base64")
    blend: float = Field(0.65, ge=0.3, le=0.9, description="Intensité du mélange")


# Ajouter ces endpoints :
@app.post("/color-engine/process")
async def color_engine_process(request: ColorEngineRequest):
    """
    Color Engine V2 - Recolorisation intelligente des extensions.
    
    Envoie les images en base64, reçoit les images recolorisées en base64.
    """
    try:
        result = await process_color_engine(
            gabarit1_b64=request.gabarit1,
            gabarit2_b64=request.gabarit2,
            reference_b64=request.reference,
            blend=request.blend
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/color-engine/status")
async def color_engine_status():
    """Vérifie que le Color Engine est disponible"""
    return {
        "status": "ready",
        "version": "2.0",
        "features": [
            "LAB color space recoloring",
            "Improved hair mask (rembg + skin detection)",
            "Ombré preservation",
            "Texture/highlight blending"
        ]
    }
