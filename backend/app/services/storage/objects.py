from __future__ import annotations

import hmac
from base64 import b64encode
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import md5, sha256
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings
from app.services.secrets import read_openbao_kv_secret_sync


@dataclass(frozen=True)
class StoredObject:
    url: str
    path: str
    key: str


@dataclass(frozen=True)
class S3Credentials:
    access_key: str
    secret_key: str
    source: str


def put_object(
    settings: Settings,
    *,
    local_root: str,
    local_url_prefix: str,
    key: str,
    content: bytes,
    content_type: str,
) -> StoredObject:
    if settings.object_storage_mode == "s3":
        return put_s3_object(settings, key=key, content=content, content_type=content_type)
    return put_local_object(local_root, local_url_prefix, key, content)


def get_object(
    settings: Settings,
    *,
    local_root: str,
    key: str,
) -> bytes:
    if settings.object_storage_mode == "s3":
        return get_s3_object(settings, key)
    path = Path(local_root) / key
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")
    return path.read_bytes()


def put_local_object(local_root: str, local_url_prefix: str, key: str, content: bytes) -> StoredObject:
    destination = Path(local_root) / key
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return StoredObject(
        url=f"{local_url_prefix}/{Path(key).as_posix()}",
        path=str(destination),
        key=key,
    )


def put_s3_object(settings: Settings, *, key: str, content: bytes, content_type: str) -> StoredObject:
    credentials = ensure_s3_configured(settings)
    url = s3_object_url(settings, key)
    headers = {
        "content-type": content_type,
        "host": host_header(url),
        "x-amz-content-sha256": sha256(content).hexdigest(),
        "x-amz-date": amz_date(),
    }
    headers["authorization"] = s3_authorization(
        settings,
        credentials,
        method="PUT",
        url=url,
        headers=headers,
        payload_hash=headers["x-amz-content-sha256"],
    )
    try:
        response = httpx.put(url, content=content, headers=headers, timeout=10.0)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Object storage write failed: {exc}") from exc
    if not 200 <= response.status_code < 300:
        raise HTTPException(
            status_code=502,
            detail=f"Object storage write failed: {response.status_code} {response.text[:300]}",
        )
    public_base = settings.object_storage_public_url.rstrip("/") or s3_bucket_url(settings).rstrip("/")
    return StoredObject(
        url=f"{public_base}/{quote(key, safe='/')}",
        path=f"s3://{settings.object_storage_bucket}/{key}",
        key=key,
    )


def get_s3_object(settings: Settings, key: str) -> bytes:
    credentials = ensure_s3_configured(settings)
    url = s3_object_url(settings, key)
    payload_hash = "UNSIGNED-PAYLOAD"
    headers = {
        "host": host_header(url),
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date(),
    }
    headers["authorization"] = s3_authorization(
        settings,
        credentials,
        method="GET",
        url=url,
        headers=headers,
        payload_hash=payload_hash,
    )
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Object storage read failed: {exc}") from exc
    if response.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")
    if not 200 <= response.status_code < 300:
        raise HTTPException(
            status_code=502,
            detail=f"Object storage read failed: {response.status_code} {response.text[:300]}",
        )
    return response.content


def put_s3_bucket_lifecycle(
    settings: Settings,
    *,
    prefixes: list[str],
    expiration_days: int,
) -> dict[str, object]:
    credentials = ensure_s3_configured(settings)
    normalized_prefixes = [prefix.lstrip("/") for prefix in prefixes if prefix.strip()]
    if not normalized_prefixes:
        normalized_prefixes = [""]
    content = s3_lifecycle_configuration_xml(
        normalized_prefixes,
        expiration_days=max(expiration_days, 1),
    )
    url = f"{s3_bucket_url(settings).rstrip('/')}?lifecycle="
    headers = {
        "content-md5": b64encode(md5(content).digest()).decode(),
        "content-type": "application/xml",
        "host": host_header(url),
        "x-amz-content-sha256": sha256(content).hexdigest(),
        "x-amz-date": amz_date(),
    }
    headers["authorization"] = s3_authorization(
        settings,
        credentials,
        method="PUT",
        url=url,
        headers=headers,
        payload_hash=headers["x-amz-content-sha256"],
    )
    try:
        response = httpx.put(url, content=content, headers=headers, timeout=10.0)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Object lifecycle policy write failed: {exc}") from exc
    if not 200 <= response.status_code < 300:
        raise HTTPException(
            status_code=502,
            detail=f"Object lifecycle policy write failed: {response.status_code} {response.text[:300]}",
        )
    return {
        "bucket": settings.object_storage_bucket,
        "prefix_count": len(normalized_prefixes),
        "expiration_days": max(expiration_days, 1),
        "status_code": response.status_code,
    }


def ensure_s3_configured(settings: Settings) -> S3Credentials:
    credentials = resolve_s3_credentials(settings)
    if not credentials.access_key or not credentials.secret_key:
        raise HTTPException(
            status_code=500,
            detail="Object storage is set to s3 but access credentials are not configured",
        )
    return credentials


def resolve_s3_credentials(settings: Settings) -> S3Credentials:
    access_key = settings.object_storage_access_key
    secret_key = settings.object_storage_secret_key
    source = "env" if access_key and secret_key else "unset"
    if settings.object_storage_access_key_secret_path:
        access_key = resolve_openbao_storage_secret(
            settings,
            settings.object_storage_access_key_secret_path,
            settings.object_storage_access_key_secret_field,
            "access key",
        )
        source = "openbao"
    if settings.object_storage_secret_key_secret_path:
        secret_key = resolve_openbao_storage_secret(
            settings,
            settings.object_storage_secret_key_secret_path,
            settings.object_storage_secret_key_secret_field,
            "secret key",
        )
        source = "openbao"
    return S3Credentials(access_key=access_key, secret_key=secret_key, source=source)


def s3_lifecycle_configuration_xml(prefixes: list[str], expiration_days: int) -> bytes:
    rules = []
    for index, prefix in enumerate(prefixes, start=1):
        safe_prefix = xml_escape(prefix)
        rules.append(
            "".join(
                [
                    "<Rule>",
                    f"<ID>afrolete-retention-{index}</ID>",
                    "<Status>Enabled</Status>",
                    "<Filter>",
                    f"<Prefix>{safe_prefix}</Prefix>",
                    "</Filter>",
                    "<Expiration>",
                    f"<Days>{expiration_days}</Days>",
                    "</Expiration>",
                    "</Rule>",
                ]
            )
        )
    return (
        '<LifecycleConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
        + "".join(rules)
        + "</LifecycleConfiguration>"
    ).encode()


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def resolve_openbao_storage_secret(
    settings: Settings,
    path: str,
    field_name: str,
    label: str,
) -> str:
    if not settings.openbao_addr or not settings.openbao_token:
        raise HTTPException(
            status_code=500,
            detail=f"Object storage {label} is configured for OpenBao but OpenBao address/token is missing",
        )
    try:
        secret = read_openbao_kv_secret_sync(settings, path, field_name)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OpenBao object storage {label} fetch failed: {exc}",
        ) from exc
    if not secret:
        raise HTTPException(
            status_code=500,
            detail=f"OpenBao object storage {label} secret field is empty",
        )
    return secret


def s3_object_url(settings: Settings, key: str) -> str:
    return f"{s3_bucket_url(settings).rstrip('/')}/{quote(key, safe='/')}"


def s3_bucket_url(settings: Settings) -> str:
    endpoint = settings.object_storage_endpoint.rstrip("/") + "/"
    return urljoin(endpoint, f"{settings.object_storage_bucket}/")


def host_header(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc


def amz_date() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def s3_authorization(
    settings: Settings,
    credentials: S3Credentials,
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    payload_hash: str,
) -> str:
    parsed = urlparse(url)
    date_stamp = headers["x-amz-date"][:8]
    credential_scope = f"{date_stamp}/{settings.object_storage_region}/s3/aws4_request"
    signed_header_names = sorted(name.lower() for name in headers)
    canonical_headers = "".join(
        f"{name}:{' '.join(headers[name].strip().split())}\n" for name in signed_header_names
    )
    canonical_request = "\n".join(
        [
            method,
            parsed.path or "/",
            parsed.query,
            canonical_headers,
            ";".join(signed_header_names),
            payload_hash,
        ]
    )
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            headers["x-amz-date"],
            credential_scope,
            sha256(canonical_request.encode()).hexdigest(),
        ]
    )
    signing_key = s3_signing_key(
        credentials.secret_key,
        date_stamp,
        settings.object_storage_region,
    )
    signature = hmac.new(signing_key, string_to_sign.encode(), sha256).hexdigest()
    return (
        "AWS4-HMAC-SHA256 "
        f"Credential={credentials.access_key}/{credential_scope}, "
        f"SignedHeaders={';'.join(signed_header_names)}, "
        f"Signature={signature}"
    )


def s3_signing_key(secret_key: str, date_stamp: str, region: str) -> bytes:
    date_key = hmac.new(f"AWS4{secret_key}".encode(), date_stamp.encode(), sha256).digest()
    region_key = hmac.new(date_key, region.encode(), sha256).digest()
    service_key = hmac.new(region_key, b"s3", sha256).digest()
    return hmac.new(service_key, b"aws4_request", sha256).digest()
