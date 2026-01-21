# app/routes/wix_webhooks.py
from fastapi import APIRouter, Request

router = APIRouter(prefix="/wix/webhooks", tags=["wix-webhooks"])

@router.post("/app-instance-installed")
async def app_instance_installed(request: Request):
    body = await request.body()
    # Pour debug: on renvoie juste ok
    # (Plus tard: on validera la signature et on extraira instanceId)
    return {"ok": True, "len": len(body)}
