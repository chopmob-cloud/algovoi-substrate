# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud)
"""
Composite trust-query algorithm (PR #2440 in x402-foundation/x402).

composite_hash = SHA-256(JCS([emitter_rows sorted by source_id, sig excluded]))

Aggregates trust evidence from multiple emitters into a single canonical hash
that any verifier can recompute from retained bytes. Properties the algorithm
establishes:

- Row ordering invariance. Two queries with the same row set in different
  emission order produce the same composite_hash. Sort-by-source_id is the
  canonicalising primitive.
- Set semantics. A strict subset of the row set produces a distinct
  composite_hash. Aggregation is non-collapsing.
- Signature exclusion. The sig field is dropped from each row before
  serialisation. The composite hash is over the substrate content, not the
  per-row attestation envelope.

5-implementation cross-validation:
https://gist.github.com/chopmob-cloud/f2e9f0877b7d9fff70c8eca46e4ce636
(15 / 15 byte-for-byte agreements: Python rfc8785, JavaScript canonicalize,
Go gowebpki/jcs, Java cyberphone, Rust serde_jcs.)
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from algovoi_substrate.canonicalize import sha256_jcs


class CompositeTrustQueryError(ValueError):
    """Raised when composite trust-query inputs violate the substrate discipline."""


def _strip_sig(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return a shallow copy of row with the sig field removed."""
    return {k: v for k, v in row.items() if k != "sig"}


def _require_source_id(row: Mapping[str, Any]) -> str:
    src = row.get("source_id")
    if not isinstance(src, str) or not src:
        raise CompositeTrustQueryError(
            "every emitter row must carry a non-empty string source_id"
        )
    return src


def composite_trust_query_hash(rows: Iterable[Mapping[str, Any]]) -> str:
    """Return the lowercase hex composite_hash for a set of emitter rows.

    Steps (per PR #2440 §composite-hash):
      1. Strip the sig field from each row.
      2. Sort rows by source_id (lexicographic).
      3. JCS-canonicalise the resulting array.
      4. SHA-256 the canonical bytes.

    Output is plain hex without an algorithm prefix.

    Raises CompositeTrustQueryError if any row lacks a non-empty source_id.
    """
    rows_list = list(rows)
    if not rows_list:
        raise CompositeTrustQueryError(
            "composite trust-query requires at least one emitter row"
        )

    stripped: list[dict[str, Any]] = []
    for row in rows_list:
        if not isinstance(row, Mapping):
            raise CompositeTrustQueryError(
                f"emitter row must be a mapping, got {type(row).__name__}"
            )
        _require_source_id(row)
        stripped.append(_strip_sig(row))

    stripped.sort(key=lambda r: r["source_id"])
    return sha256_jcs(stripped)
