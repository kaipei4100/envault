"""Checksum utilities for verifying vault file integrity."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

_CHECKSUM_SUFFIX = ".checksum.json"
_ALGORITHM = "sha256"


def _checksum_path(vault_path: Path) -> Path:
    """Return the path of the checksum file for *vault_path*."""
    return vault_path.with_suffix(_CHECKSUM_SUFFIX)


def compute(data: bytes, algorithm: str = _ALGORITHM) -> str:
    """Return a hex digest of *data* using *algorithm*."""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def save_checksum(vault_path: Path, data: bytes, algorithm: str = _ALGORITHM) -> Path:
    """Compute and persist the checksum for *vault_path* contents.

    Returns the path of the written checksum file.
    """
    digest = compute(data, algorithm)
    record = {"algorithm": algorithm, "digest": digest, "vault": vault_path.name}
    checksum_file = _checksum_path(vault_path)
    checksum_file.write_text(json.dumps(record, indent=2))
    return checksum_file


class ChecksumMismatch(Exception):
    """Raised when the stored checksum does not match the actual file content."""


def verify_checksum(vault_path: Path, data: Optional[bytes] = None) -> str:
    """Verify *vault_path* against its stored checksum.

    If *data* is provided it is used directly; otherwise the file is read.
    Returns the hex digest on success, raises *ChecksumMismatch* on failure.
    """
    checksum_file = _checksum_path(vault_path)
    if not checksum_file.exists():
        raise FileNotFoundError(f"No checksum file found for {vault_path}")

    record = json.loads(checksum_file.read_text())
    algorithm: str = record.get("algorithm", _ALGORITHM)
    stored_digest: str = record["digest"]

    actual_data = data if data is not None else vault_path.read_bytes()
    actual_digest = compute(actual_data, algorithm)

    if actual_digest != stored_digest:
        raise ChecksumMismatch(
            f"Checksum mismatch for {vault_path.name}: "
            f"expected {stored_digest}, got {actual_digest}"
        )
    return actual_digest


def checksum_exists(vault_path: Path) -> bool:
    """Return True if a checksum file exists for *vault_path*."""
    return _checksum_path(vault_path).exists()
