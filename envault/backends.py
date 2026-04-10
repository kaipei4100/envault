"""Storage backends for envault: local filesystem and S3."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Protocol


class Backend(Protocol):
    """Interface that all storage backends must implement."""

    def upload(self, local_path: Path, remote_key: str) -> None:
        ...

    def download(self, remote_key: str, local_path: Path) -> None:
        ...

    def exists(self, remote_key: str) -> bool:
        ...

    def list_keys(self, prefix: str = "") -> list[str]:
        ...


class LocalBackend:
    """Stores vault files in a local directory (useful for testing / single-user)."""

    def __init__(self, store_dir: str | Path) -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _full_path(self, key: str) -> Path:
        return self.store_dir / key

    def upload(self, local_path: Path, remote_key: str) -> None:
        dest = self._full_path(remote_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, dest)

    def download(self, remote_key: str, local_path: Path) -> None:
        src = self._full_path(remote_key)
        if not src.exists():
            raise FileNotFoundError(f"Remote key not found: {remote_key}")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, local_path)

    def exists(self, remote_key: str) -> bool:
        return self._full_path(remote_key).exists()

    def list_keys(self, prefix: str = "") -> list[str]:
        results = []
        for p in self.store_dir.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(self.store_dir))
                if rel.startswith(prefix):
                    results.append(rel)
        return sorted(results)


class S3Backend:
    """Stores vault files in an AWS S3 bucket."""

    def __init__(self, bucket: str, prefix: str = "") -> None:
        try:
            import boto3  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("boto3 is required for S3 backend: pip install boto3") from exc
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self._s3 = boto3.client("s3")

    def _remote_key(self, key: str) -> str:
        return f"{self.prefix}/{key}" if self.prefix else key

    def upload(self, local_path: Path, remote_key: str) -> None:
        self._s3.upload_file(str(local_path), self.bucket, self._remote_key(remote_key))

    def download(self, remote_key: str, local_path: Path) -> None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self._s3.download_file(self.bucket, self._remote_key(remote_key), str(local_path))

    def exists(self, remote_key: str) -> bool:
        from botocore.exceptions import ClientError  # type: ignore
        try:
            self._s3.head_object(Bucket=self.bucket, Key=self._remote_key(remote_key))
            return True
        except ClientError:
            return False

    def list_keys(self, prefix: str = "") -> list[str]:
        full_prefix = self._remote_key(prefix) if prefix else (self.prefix + "/" if self.prefix else "")
        paginator = self._s3.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=full_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if self.prefix:
                    key = key[len(self.prefix) + 1:]
                keys.append(key)
        return sorted(keys)
