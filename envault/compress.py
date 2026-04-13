"""Optional compression for vault payloads before encryption."""

from __future__ import annotations

import zlib
from dataclasses import dataclass
from typing import Literal

ALGO_ZLIB = "zlib"
ALGO_NONE = "none"

Algorithm = Literal["zlib", "none"]

_MAGIC = b"\x1f\x8b"  # gzip-style sentinel; we use our own prefix instead
_PREFIX_ZLIB = b"ZLB:"
_PREFIX_NONE = b"RAW:"


@dataclass(frozen=True)
class CompressResult:
    data: bytes
    algorithm: Algorithm
    original_size: int
    compressed_size: int

    @property
    def ratio(self) -> float:
        if self.original_size == 0:
            return 1.0
        return self.compressed_size / self.original_size


def compress(data: bytes, algorithm: Algorithm = ALGO_ZLIB) -> CompressResult:
    """Compress *data* and prepend a 4-byte algorithm prefix."""
    original_size = len(data)
    if algorithm == ALGO_ZLIB:
        compressed = zlib.compress(data, level=6)
        payload = _PREFIX_ZLIB + compressed
    else:
        payload = _PREFIX_NONE + data

    return CompressResult(
        data=payload,
        algorithm=algorithm,
        original_size=original_size,
        compressed_size=len(payload),
    )


def decompress(data: bytes) -> bytes:
    """Decompress *data* that was previously compressed with :func:`compress`."""
    if data.startswith(_PREFIX_ZLIB):
        return zlib.decompress(data[len(_PREFIX_ZLIB):])
    if data.startswith(_PREFIX_NONE):
        return data[len(_PREFIX_NONE):]
    raise ValueError(
        "Unrecognised compression prefix — data may be corrupt or uncompressed."
    )


def best_algorithm(data: bytes, threshold: float = 0.95) -> Algorithm:
    """Return the algorithm that yields the best ratio, falling back to 'none'."""
    result = compress(data, ALGO_ZLIB)
    return ALGO_ZLIB if result.ratio < threshold else ALGO_NONE
