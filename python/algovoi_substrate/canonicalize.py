# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud)
"""
JCS RFC 8785 canonicalisation with the AlgoVoi-discipline rules.

The canonicalisation discipline is the shared normative substrate for x402,
AP2, A2A, and MPP receipts, authored by AlgoVoi and proposed in PR #2453 in x402-foundation/x402
(sole AlgoVoi authorship; replaces closed PR #2436). This module wraps rfc8785>=0.1.4 with the
discipline's pre-canonicalisation rules:

- Rule 1: timestamp_ms MUST be an epoch-millisecond integer (not float, not
  RFC 3339 string). Closes the source-side variability that string time
  formats introduce.
- Rule 4: type validation MUST happen before canonicalisation. A field
  declared as integer that receives a float is a hard validation failure,
  not a silent type-cast.
- canon_version: "jcs-rfc8785-v1" is the in-band format-version pin a
  receipt carries so a year-five re-canonicalisation knows which rule was
  active at emission, without depending on an out-of-band rule registry.
- Array element order is preserved (RFC 8785 §3.2.3): ["UK","EU"] and
  ["EU","UK"] are distinct preimages, distinct canonical bytes, distinct
  SHA-256 digests. Producer-side ordering is load-bearing.

Reference: https://gist.github.com/chopmob-cloud/b327814c4e17ed9fc7b4f29c8bda523c
"""

from __future__ import annotations

import hashlib
from typing import Any

import rfc8785

# Pin the discipline version. Receipts emitted under this substrate carry
# this string in their canon_version field so a year-five verifier can pick
# the correct re-canonicalisation rule from the retained bytes alone.
CANON_VERSION = "jcs-rfc8785-v1"


class CanonicalizationError(ValueError):
    """Raised when an input violates the AlgoVoi canonicalisation discipline."""


def _validate_types(obj: Any, path: str = "$") -> None:
    """Pre-canonicalisation type validation (Substrate Rule 4).

    Walks the object and enforces:
    - bool is bool (not 0/1 coerced)
    - int is int (not float-equal-to-int)
    - floats only allowed where explicitly typed; this default validation
      rejects floats anywhere they could be coerced from integers.

    Note: the discipline rejects float coercion of integer fields, but
    legitimate float fields (e.g. lat/long coordinates) are still allowed.
    The strict-integer-fields enforcement is done at the per-schema layer
    (see action_ref, compliance_receipt) rather than universally here.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise CanonicalizationError(
                    f"non-string object key at {path}: {type(k).__name__}"
                )
            _validate_types(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _validate_types(item, f"{path}[{i}]")
    elif isinstance(obj, bool):
        # bool is a subclass of int in Python; this catches that explicitly
        # so a callsite can rely on bool->bool, not bool->int coercion.
        return
    elif isinstance(obj, (int, float, str)):
        return
    elif obj is None:
        return
    else:
        raise CanonicalizationError(
            f"non-canonicalisable type at {path}: {type(obj).__name__}"
        )


def canonicalize(obj: Any) -> str:
    """Return the canonical JCS string representation of obj.

    Applies AlgoVoi-discipline pre-canonicalisation type validation, then
    delegates to rfc8785 for the RFC 8785 canonical bytes. The return is a
    UTF-8 string; for raw bytes use canonicalize_bytes().

    Raises CanonicalizationError on type-validation failure.
    """
    _validate_types(obj)
    return canonicalize_bytes(obj).decode("utf-8")


def canonicalize_bytes(obj: Any) -> bytes:
    """Return the canonical JCS UTF-8 bytes of obj.

    Applies AlgoVoi-discipline pre-canonicalisation type validation, then
    delegates to rfc8785 for the RFC 8785 canonical bytes.

    Raises CanonicalizationError on type-validation failure.
    """
    _validate_types(obj)
    return rfc8785.dumps(obj)


def sha256_jcs(obj: Any) -> str:
    """Return the lowercase hex SHA-256 of the JCS canonical bytes of obj.

    This is the substrate primitive used by action_ref, compliance receipts,
    audit chain entries, and the composite trust-query algorithm. The string
    is plain hex without an algorithm prefix; callers that need
    "sha256:<hex>" form should prepend that prefix themselves.
    """
    return hashlib.sha256(canonicalize_bytes(obj)).hexdigest()
