"""Archive old vault versions to a compressed bundle."""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

from envault.snapshot import _snapshot_dir, list_snapshots


@dataclass
class ArchiveResult:
    path: Path
    versions: List[int]
    size_bytes: int


def _archive_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".archive.zip")


def create_archive(vault_path: Path, password: str, keep_latest: int = 3) -> ArchiveResult:
    """Bundle old snapshots into a zip archive and remove them."""
    snapshots = list_snapshots(vault_path)
    if len(snapshots) <= keep_latest:
        return ArchiveResult(path=_archive_path(vault_path), versions=[], size_bytes=0)

    to_archive = snapshots[:-keep_latest]
    snap_dir = _snapshot_dir(vault_path)
    archive_path = _archive_path(vault_path)
    archived_versions: List[int] = []

    with zipfile.ZipFile(archive_path, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        for entry in to_archive:
            ver = entry["version"]
            snap_file = snap_dir / f"v{ver}.enc"
            if snap_file.exists():
                zf.write(snap_file, arcname=snap_file.name)
                archived_versions.append(ver)
                snap_file.unlink()

    size = archive_path.stat().st_size if archive_path.exists() else 0
    return ArchiveResult(path=archive_path, versions=archived_versions, size_bytes=size)


def list_archived(vault_path: Path) -> List[int]:
    """Return list of version numbers stored in the archive."""
    archive_path = _archive_path(vault_path)
    if not archive_path.exists():
        return []
    with zipfile.ZipFile(archive_path, "r") as zf:
        versions = []
        for name in zf.namelist():
            stem = Path(name).stem  # e.g. 'v2'
            if stem.startswith("v") and stem[1:].isdigit():
                versions.append(int(stem[1:]))
        return sorted(versions)


def restore_from_archive(vault_path: Path, version: int) -> Path:
    """Extract a single snapshot from the archive back to the snapshot dir."""
    archive_path = _archive_path(vault_path)
    if not archive_path.exists():
        raise FileNotFoundError("No archive found")
    snap_dir = _snapshot_dir(vault_path)
    snap_dir.mkdir(parents=True, exist_ok=True)
    target_name = f"v{version}.enc"
    with zipfile.ZipFile(archive_path, "r") as zf:
        if target_name not in zf.namelist():
            raise KeyError(f"Version {version} not in archive")
        zf.extract(target_name, path=snap_dir)
    return snap_dir / target_name
