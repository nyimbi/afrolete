import httpx

from app.core.config import Settings


async def read_openbao_kv_secret(settings: Settings, path: str, field_name: str) -> str:
    base_url = settings.openbao_addr.rstrip("/")
    secret_path = path.lstrip("/")
    headers = {"X-Vault-Token": settings.openbao_token}
    if settings.openbao_namespace:
        headers["X-Vault-Namespace"] = settings.openbao_namespace
    async with httpx.AsyncClient(timeout=settings.openbao_timeout_seconds) as client:
        response = await client.get(f"{base_url}/v1/{secret_path}", headers=headers)
        response.raise_for_status()
    payload = response.json()
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]
    if not isinstance(data, dict):
        return ""
    return str(data.get(field_name) or "")
