from fastapi import APIRouter, Request

router = APIRouter(prefix="/wix/webhooks", tags=["wix-webhooks"])

@router.post("/app-instance-installed")
async def app_instance_installed(request: Request):
    body = await request.body()
    preview = body[:2000].decode("utf-8", errors="replace")
    print("=== WIX APP INSTALLED WEBHOOK (preview) ===")
    print(preview)
    print("=== END ===")
    return {"ok": True, "len": len(body)}

@router.post("/app-instance-removed")
async def app_instance_removed(request: Request):
    body = await request.body()
    preview = body[:2000].decode("utf-8", errors="replace")
    print("=== WIX APP REMOVED WEBHOOK (preview) ===")
    print(preview)
    print("=== END ===")
    return {"ok": True, "len": len(body)}
