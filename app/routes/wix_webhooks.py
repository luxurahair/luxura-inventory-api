from fastapi import APIRouter, Request
import base64
import json

router = APIRouter(prefix="/wix/webhooks", tags=["wix-webhooks"])


def _decode_installed_jwt(token: str) -> dict:
    parts = token.split(".")
    if len(parts) < 2:
        return {"error": "not_a_jwt"}

    payload_b64 = parts[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
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

    payload = decoded["payload"]
    data = decoded["data"]

    payload_keys = list(payload.keys())
    data_keys = list(data.keys()) if isinstance(data, dict) else ["not_a_dict"]

    # 🔥 NEW: parse inner "data" field
    inner = {}
    try:
        inner_raw = data.get("data") if isinstance(data, dict) else None
        if isinstance(inner_raw, str):
            inner = json.loads(inner_raw)
        elif isinstance(inner_raw, dict):
            inner = inner_raw
    except Exception:
        inner = {"raw_inner": str(inner_raw)[:200] if inner_raw is not None else None}

    inner_keys = list(inner.keys()) if isinstance(inner, dict) else ["not_a_dict"]

    possible_app = (
        (data.get("appId") if isinstance(data, dict) else None)
        or (data.get("appDefId") if isinstance(data, dict) else None)
        or (inner.get("appId") if isinstance(inner, dict) else None)
        or (inner.get("appDefId") if isinstance(inner, dict) else None)
        or (inner.get("id") if isinstance(inner, dict) else None)
    )

    instance_id = (data.get("instanceId") if isinstance(data, dict) else None)
    event_type = (data.get("eventType") if isinstance(data, dict) else None)

    print("WIX INSTALLED DEBUG:", {
        "payload_keys": payload_keys,
        "data_keys": data_keys,
        "inner_keys": inner_keys,
        "possible_app": possible_app,
        "instanceId": instance_id,
        "eventType": event_type,
    })

    return {
        "ok": True,
        "possible_app": possible_app,
        "instanceId": instance_id,
        "eventType": event_type,
        "payload_keys": payload_keys,
        "data_keys": data_keys,
        "inner_keys": inner_keys,
    }


@router.post("/app-instance-removed")
async def app_instance_removed(request: Request):
    body = await request.body()
    preview = body[:500].decode("utf-8", errors="replace")
    print("=== WIX APP REMOVED WEBHOOK (preview) ===")
    print(preview)
    print("=== END ===")
    return {"ok": True, "len": len(body)}
