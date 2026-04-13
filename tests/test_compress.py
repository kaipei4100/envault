"""Tests for envault.compress."""

from __future__ import annotations

import pytest

from envault.compress import (
    ALGO_NONE,
    ALGO_ZLIB,
    CompressResult,
    best_algorithm,
    compress,
    decompress,
)

_SAMPLE = b"KEY=value\nFOO=bar\nBAZ=qux\n" * 40  # repetitive → compresses well
_SMALL = b"X=1\n"  # tiny → compression may not help


def test_compress_returns_compress_result():
    result = compress(_SAMPLE)
    assert isinstance(result, CompressResult)


def test_compress_zlib_reduces_size():
    result = compress(_SAMPLE, ALGO_ZLIB)
    assert result.compressed_size < result.original_size


def test_compress_none_preserves_size():
    result = compress(_SAMPLE, ALGO_NONE)
    # payload = prefix (4 bytes) + original
    assert result.compressed_size == len(_SAMPLE) + 4
    assert result.algorithm == ALGO_NONE


def test_compress_records_original_size():
    result = compress(_SAMPLE, ALGO_ZLIB)
    assert result.original_size == len(_SAMPLE)


def test_compress_ratio_between_zero_and_one_for_compressible_data():
    result = compress(_SAMPLE, ALGO_ZLIB)
    assert 0.0 < result.ratio < 1.0


def test_decompress_zlib_roundtrip():
    result = compress(_SAMPLE, ALGO_ZLIB)
    recovered = decompress(result.data)
    assert recovered == _SAMPLE


def test_decompress_none_roundtrip():
    result = compress(_SAMPLE, ALGO_NONE)
    recovered = decompress(result.data)
    assert recovered == _SAMPLE


def test_decompress_raises_on_bad_prefix():
    with pytest.raises(ValueError, match="Unrecognised compression prefix"):
        decompress(b"BAD:some data here")


def test_decompress_raises_on_empty_bytes():
    with pytest.raises(ValueError):
        decompress(b"")


def test_best_algorithm_returns_zlib_for_compressible_data():
    algo = best_algorithm(_SAMPLE)
    assert algo == ALGO_ZLIB


def test_best_algorithm_returns_none_for_incompressible_data():
    # Random-looking bytes won't compress below the 95% threshold
    import os
    random_data = os.urandom(512)
    algo = best_algorithm(random_data, threshold=0.95)
    assert algo == ALGO_NONE


def test_compress_empty_bytes_zlib():
    result = compress(b"", ALGO_ZLIB)
    assert decompress(result.data) == b""


def test_compress_empty_bytes_none():
    result = compress(b"", ALGO_NONE)
    assert decompress(result.data) == b""
