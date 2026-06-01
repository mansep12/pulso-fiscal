"""Cloudflare R2 storage client (S3-compatible).

Reads credentials from environment variables. Call load_dotenv() before
instantiating R2Client if using a .env.local file.

Environment variables required:
    R2_ACCOUNT_ID
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_PUBLIC_BASE_URL
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value or value == "REEMPLAZAR":
        msg = f"Variable de entorno {name!r} no configurada. Revisa etl/.env.local."
        raise RuntimeError(msg)
    return value


class R2Client:
    """Cliente para subir y verificar archivos en Cloudflare R2."""

    def __init__(self) -> None:
        account_id = _require_env("R2_ACCOUNT_ID")
        access_key_id = _require_env("R2_ACCESS_KEY_ID")
        secret_access_key = _require_env("R2_SECRET_ACCESS_KEY")
        self._public_base_url = os.environ.get("R2_PUBLIC_BASE_URL", "").rstrip("/")

        self._client: Any = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    def upload_file(self, local_path: Path, bucket: str, r2_key: str) -> None:
        """Sube un archivo local a R2."""
        content_type = _guess_content_type(local_path)
        self._client.upload_file(
            Filename=str(local_path),
            Bucket=bucket,
            Key=r2_key,
            ExtraArgs={"ContentType": content_type},
        )

    def upload_bytes(self, data: bytes, bucket: str, r2_key: str, content_type: str = "application/octet-stream") -> None:
        """Sube bytes en memoria a R2."""
        self._client.put_object(
            Bucket=bucket,
            Key=r2_key,
            Body=data,
            ContentType=content_type,
        )

    def object_exists(self, bucket: str, r2_key: str) -> bool:
        """Retorna True si el objeto ya existe en R2."""
        try:
            self._client.head_object(Bucket=bucket, Key=r2_key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "404":
                return False
            raise

    def build_public_url(self, r2_key: str) -> str:
        """Construye la URL publica de un objeto en el bucket publico."""
        if not self._public_base_url:
            return ""
        return f"{self._public_base_url}/{r2_key}"


def _guess_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    types: dict[str, str] = {
        ".json": "application/json",
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".html": "text/html",
        ".pdf": "application/pdf",
    }
    return types.get(suffix, "application/octet-stream")
