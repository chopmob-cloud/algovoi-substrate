"""Tests for canonicalize module."""

from __future__ import annotations

import hashlib

import pytest

from algovoi_substrate.canonicalize import (
    CANON_VERSION,
    CanonicalizationError,
    canonicalize,
    canonicalize_bytes,
    sha256_jcs,
)


class TestCanonVersion:
    def test_pinned_to_jcs_rfc8785_v1(self) -> None:
        assert CANON_VERSION == "jcs-rfc8785-v1"


class TestCanonicalize:
    def test_sorts_object_keys(self) -> None:
        assert canonicalize({"b": 1, "a": 2}) == '{"a":2,"b":1}'

    def test_preserves_array_element_order(self) -> None:
        # RFC 8785 §3.2.3: array element order is preserved.
        # ["UK","EU"] and ["EU","UK"] are distinct canonical preimages.
        assert canonicalize(["UK", "EU"]) != canonicalize(["EU", "UK"])

    def test_handles_unicode(self) -> None:
        # JCS preserves non-ASCII via UTF-8 without escaping printable chars.
        result = canonicalize({"name": "Müller"})
        assert "Müller" in result

    def test_handles_nested_structures(self) -> None:
        obj = {"outer": {"inner": [1, 2, 3]}, "list": [{"a": 1}, {"a": 2}]}
        result = canonicalize(obj)
        # Object keys sorted at every level.
        assert result == '{"list":[{"a":1},{"a":2}],"outer":{"inner":[1,2,3]}}'

    def test_canonicalize_bytes_returns_utf8(self) -> None:
        b = canonicalize_bytes({"a": 1})
        assert isinstance(b, bytes)
        assert b == b'{"a":1}'

    def test_rejects_non_string_dict_keys(self) -> None:
        with pytest.raises(CanonicalizationError, match="non-string object key"):
            canonicalize({1: "value"})

    def test_rejects_non_canonicalisable_types(self) -> None:
        with pytest.raises(CanonicalizationError, match="non-canonicalisable type"):
            canonicalize({"created": object()})

    def test_accepts_none(self) -> None:
        assert canonicalize({"a": None}) == '{"a":null}'

    def test_accepts_bool(self) -> None:
        assert canonicalize({"a": True, "b": False}) == '{"a":true,"b":false}'


class TestSha256Jcs:
    def test_returns_lowercase_hex(self) -> None:
        h = sha256_jcs({"a": 1})
        assert h == hashlib.sha256(b'{"a":1}').hexdigest()
        assert all(c in "0123456789abcdef" for c in h)

    def test_distinct_array_order_distinct_hash(self) -> None:
        # The known divergence pattern from the substrate discipline:
        # ["UK","EU"] vs ["EU","UK"] hash to different digests.
        h_uk_eu = sha256_jcs({"jurisdiction_flags": ["UK", "EU"]})
        h_eu_uk = sha256_jcs({"jurisdiction_flags": ["EU", "UK"]})
        assert h_uk_eu != h_eu_uk

    def test_key_order_irrelevant(self) -> None:
        # Object key order is canonicalised; input order does not affect hash.
        assert sha256_jcs({"a": 1, "b": 2}) == sha256_jcs({"b": 2, "a": 1})

    def test_deterministic(self) -> None:
        obj = {"a": [1, 2, 3], "b": "x"}
        assert sha256_jcs(obj) == sha256_jcs(obj)
