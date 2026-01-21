from fastapi import APIRouter, Request
import base64
import json

router = APIRouter(prefix="/wix/webhooks", tags=["wix-webhooks"])


def _decode_installed_jwt(token: str) -> dict:
    """
    Wix envoie un JWT (header.payload.signature).
    Le champ 'data' dans le payload est un JSON string contenant instanceId/appId/etc.
    Ici: on décode SANS vérifier la signature (debug). On sécurisera après.
    """
    parts = token.split(".")
    if len(parts) < 2:
        return {"error": "not_a_jwt"}

    payload_b64 = parts[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)  # padding base64url
    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))

    data_raw = payload.get("data")
    if isinstance(data_raw, str):
        try:
            data = json.loads(data_raw)
        except Exception:
            data = {"raw_data": data_raw}
    else:
        data = data_raw or {}

    return {"payload": payload, "data": data}


@router.post("/app-instance-installed")
async def app_instance_installed(request: Request):
    token = (await request.body()).decode("utf-8", errors="replace").strip()
    decoded = _decode_installed_jwt(token)

    if decoded.get("error"):
        print("WIX INSTALLED WEBHOOK: invalid payload")
        return {"ok": False, "error": decoded["error"]}

    data = decoded["data"]

    # 👇 Les 2 champs qui nous intéressent pour débloquer /wix/token
    app_id = data.get("appId")
    instance_id = data.get("instanceId")
    origin_instance_id = data.get("originInstanceId")
    event_type = data.get("eventType")

    print("WIX INSTALLED:", {"appId": app_id, "instanceId": instance_id, "originInstanceId": origin_instance_id})

    return {
        "ok": True,
        "appId": app_id,
        "instanceId": instance_id,
        "originInstanceId": origin_instance_id,
        "eventType": event_type,
    }


@router.post("/app-instance-removed")
async def app_instance_removed(request: Request):
    # On laisse simple: juste confirmer la réception.
    body = await request.body()
    preview = body[:500].decode("utf-8", errors="replace")
    print("=== WIX APP REMOVED WEBHOOK (preview) ===")
    print(preview)
    print("=== END ===")
    return {"ok": True, "len": len(body)}
