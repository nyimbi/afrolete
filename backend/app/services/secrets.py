import httpx
from fastapi import HTTPException

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


def read_openbao_kv_secret_sync(settings: Settings, path: str, field_name: str) -> str:
    base_url = settings.openbao_addr.rstrip("/")
    secret_path = path.lstrip("/")
    headers = {"X-Vault-Token": settings.openbao_token}
    if settings.openbao_namespace:
        headers["X-Vault-Namespace"] = settings.openbao_namespace
    with httpx.Client(timeout=settings.openbao_timeout_seconds) as client:
        response = client.get(f"{base_url}/v1/{secret_path}", headers=headers)
        response.raise_for_status()
    payload = response.json()
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]
    if not isinstance(data, dict):
        return ""
    return str(data.get(field_name) or "")


def resolve_secret_sync(
    settings: Settings,
    *,
    env_value: str,
    path: str,
    field_name: str,
    label: str,
) -> str:
    if env_value:
        return env_value
    if not path:
        return ""
    if not settings.openbao_addr or not settings.openbao_token:
        raise HTTPException(
            status_code=500,
            detail=f"{label} is configured for OpenBao but OpenBao address/token is missing",
        )
    try:
        secret = read_openbao_kv_secret_sync(settings, path, field_name)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"OpenBao {label} fetch failed: {exc}") from exc
    if not secret:
        raise HTTPException(status_code=500, detail=f"OpenBao {label} secret field is empty")
    return secret
