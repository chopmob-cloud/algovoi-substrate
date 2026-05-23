"""Tests for composite_trust_query module."""

from __future__ import annotations

import pytest

from algovoi_substrate.composite_trust_query import (
    CompositeTrustQueryError,
    composite_trust_query_hash,
)


def _row(source_id: str, score: int = 50, sig: str | None = "sig-bytes") -> dict:
    r = {"source_id": source_id, "score": score}
    if sig is not None:
        r["sig"] = sig
    return r


class TestCompositeTrustQueryHash:
    def test_row_ordering_invariance(self) -> None:
        """Two queries with the same row set in different emission order
        produce the same composite_hash (sort-by-source_id is canonical)."""
        rows_a = [_row("src-c"), _row("src-a"), _row("src-b")]
        rows_b = [_row("src-a"), _row("src-b"), _row("src-c")]
        assert composite_trust_query_hash(rows_a) == composite_trust_query_hash(rows_b)

    def test_set_semantics_subset_distinct(self) -> None:
        """A strict subset of the row set produces a distinct composite_hash."""
        rows_full = [_row("src-a"), _row("src-b"), _row("src-c")]
        rows_partial = [_row("src-a"), _row("src-c")]
        assert composite_trust_query_hash(rows_full) != composite_trust_query_hash(rows_partial)

    def test_sig_excluded_from_hash(self) -> None:
        """sig field is dropped before serialisation; signed vs unsigned same hash."""
        rows_signed = [_row("src-a", sig="signature-1"), _row("src-b", sig="signature-2")]
        rows_unsigned = [_row("src-a", sig=None), _row("src-b", sig=None)]
        assert composite_trust_query_hash(rows_signed) == composite_trust_query_hash(rows_unsigned)

    def test_sig_change_does_not_affect_hash(self) -> None:
        """Two queries differing only in sig produce the same composite_hash."""
        rows_a = [_row("src-a", sig="alice-sig"), _row("src-b", sig="bob-sig")]
        rows_b = [_row("src-a", sig="DIFFERENT"), _row("src-b", sig="DIFFERENT")]
        assert composite_trust_query_hash(rows_a) == composite_trust_query_hash(rows_b)

    def test_payload_change_changes_hash(self) -> None:
        rows_a = [_row("src-a", score=50), _row("src-b", score=70)]
        rows_b = [_row("src-a", score=51), _row("src-b", score=70)]
        assert composite_trust_query_hash(rows_a) != composite_trust_query_hash(rows_b)

    def test_rejects_empty_rows(self) -> None:
        with pytest.raises(CompositeTrustQueryError, match="at least one"):
            composite_trust_query_hash([])

    def test_rejects_row_without_source_id(self) -> None:
        with pytest.raises(CompositeTrustQueryError, match="source_id"):
            composite_trust_query_hash([{"score": 50}])

    def test_rejects_row_with_non_string_source_id(self) -> None:
        with pytest.raises(CompositeTrustQueryError, match="source_id"):
            composite_trust_query_hash([{"source_id": 123, "score": 50}])

    def test_rejects_non_mapping_row(self) -> None:
        with pytest.raises(CompositeTrustQueryError, match="must be a mapping"):
            composite_trust_query_hash([["not", "a", "mapping"]])  # type: ignore[list-item]
