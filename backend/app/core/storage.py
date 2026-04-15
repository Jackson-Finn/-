from __future__ import annotations

import hashlib
import io
import json
import re
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from minio import Minio

from app.core.config import get_settings
from app.core.errors import AppError


class BaseStorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_object_key(self, owner_id: int, filename: str) -> str:
        suffix = Path(filename).suffix.lower() or ".bin"
        stem = Path(filename).stem.lower()
        safe_stem = re.sub(r"[^a-z0-9_-]+", "-", stem).strip("-") or "asset"
        return f"{owner_id}/{uuid4().hex[:12]}-{safe_stem}{suffix}"

    def public_url(self, object_key: str) -> str:
        base = self.settings.media_public_base_url.rstrip("/")
        return f"{base}/uploads/{object_key}"

    def bootstrap(self) -> None:
        return None

    def save_upload(self, upload_file: UploadFile, object_key: str) -> dict:
        raise NotImplementedError

    def save_bytes(self, object_key: str, content: bytes, content_type: str) -> dict:
        raise NotImplementedError

    def load_bytes(self, object_key: str) -> bytes:
        raise NotImplementedError


class LocalStorageService(BaseStorageService):
    def __init__(self) -> None:
        super().__init__()
        self.base_dir = Path(self.settings.media_storage_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload_file: UploadFile, object_key: str) -> dict:
        content = upload_file.file.read()
        return self.save_bytes(object_key, content, upload_file.content_type or "application/octet-stream")

    def save_bytes(self, object_key: str, content: bytes, content_type: str) -> dict:
        destination = self.base_dir / object_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        return {
            "path": str(destination),
            "sha256": digest,
            "size": len(content),
            "url": self.public_url(object_key),
            "storage_backend": "local",
            "content_type": content_type,
        }

    def load_bytes(self, object_key: str) -> bytes:
        return (self.base_dir / object_key).read_bytes()


class MinioStorageService(BaseStorageService):
    def __init__(self) -> None:
        super().__init__()
        self.client = Minio(
            self.settings.minio_endpoint,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=self.settings.minio_secure,
        )

    def bootstrap(self) -> None:
        bucket = self.settings.minio_bucket
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                }
            ],
        }
        self.client.set_bucket_policy(bucket, json.dumps(policy))

    def save_upload(self, upload_file: UploadFile, object_key: str) -> dict:
        content = upload_file.file.read()
        content_type = upload_file.content_type or "application/octet-stream"
        return self.save_bytes(object_key, content, content_type)

    def save_bytes(self, object_key: str, content: bytes, content_type: str) -> dict:
        size = len(content)
        digest = hashlib.sha256(content).hexdigest()
        self.client.put_object(
            self.settings.minio_bucket,
            object_key,
            io.BytesIO(content),
            size,
            content_type=content_type,
        )
        return {
            "path": object_key,
            "sha256": digest,
            "size": size,
            "url": self.public_url(object_key),
            "storage_backend": "minio",
            "content_type": content_type,
        }

    def load_bytes(self, object_key: str) -> bytes:
        response = self.client.get_object(self.settings.minio_bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


@lru_cache
def get_storage_service() -> BaseStorageService:
    backend = get_settings().storage_backend.lower()
    if backend == "minio":
        return MinioStorageService()
    if backend == "local":
        return LocalStorageService()
    raise AppError(f"Unsupported storage backend: {backend}", status_code=500)
