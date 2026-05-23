"""
Audit chain primitive: monotonic per-row hash chain.

Each row carries:
- content_hash: SHA-256(JCS(payload)) -- the per-row substrate hash.
- prev_hash: the previous row's content_hash, or null for the head row.
- chain_position: monotonically increasing integer starting at 0.

This is the structure AlgoVoi's production /compliance/attestation chain
exposes, with Object Lock COMPLIANCE retention to 2033-05-04. A year-five
supervisor reading retained bytes can recompute content_hash from the
payload + canon_version pin and verify prev_hash linkage walks back to the
chain head without trusting the operator or the registry.
"""

from __future__ import annotations

from typing import Any, Iterable, TypedDict

from algovoi_substrate.canonicalize import sha256_jcs


class AuditChainError(ValueError):
    """Raised when an audit chain row or sequence violates the discipline."""


class AuditChainRow(TypedDict):
    chain_position: int
    content_hash: str
    prev_hash: str | None
    payload: Any  # arbitrary JCS-canonicalisable payload


def _hash_payload(payload: Any) -> str:
    return sha256_jcs(payload)


def append_to_chain(
    *,
    payload: Any,
    prev_row: AuditChainRow | None,
) -> AuditChainRow:
    """Build the next row in an audit chain.

    If prev_row is None, the new row becomes the head:
        chain_position = 0, prev_hash = None
    Otherwise:
        chain_position = prev_row.chain_position + 1
        prev_hash = prev_row.content_hash

    The new row's content_hash is computed from the payload via JCS+SHA-256.
    """
    if prev_row is None:
        chain_position = 0
        prev_hash: str | None = None
    else:
        if not isinstance(prev_row.get("chain_position"), int) or isinstance(
            prev_row.get("chain_position"), bool
        ):
            raise AuditChainError(
                "prev_row.chain_position must be a non-negative integer"
            )
        if prev_row["chain_position"] < 0:
            raise AuditChainError(
                "prev_row.chain_position must be non-negative"
            )
        if not isinstance(prev_row.get("content_hash"), str) or not prev_row[
            "content_hash"
        ]:
            raise AuditChainError(
                "prev_row.content_hash must be a non-empty string"
            )
        chain_position = prev_row["chain_position"] + 1
        prev_hash = prev_row["content_hash"]

    return AuditChainRow(
        chain_position=chain_position,
        content_hash=_hash_payload(payload),
        prev_hash=prev_hash,
        payload=payload,
    )


def verify_audit_chain(rows: Iterable[AuditChainRow]) -> None:
    """Verify a chain of audit rows is well-formed and linkage-consistent.

    Checks:
    - chain_position starts at 0 and increments by exactly 1 per row.
    - prev_hash is None for the head row, otherwise equals the previous
      row's content_hash.
    - content_hash recomputes to SHA-256(JCS(payload)) of the carried
      payload.

    Raises AuditChainError on any violation; otherwise returns None.
    """
    expected_position = 0
    prev_content_hash: str | None = None

    for i, row in enumerate(rows):
        position = row.get("chain_position")
        if position != expected_position:
            raise AuditChainError(
                f"row {i}: chain_position {position} != expected "
                f"{expected_position}"
            )

        recomputed = _hash_payload(row.get("payload"))
        if row.get("content_hash") != recomputed:
            raise AuditChainError(
                f"row {i}: content_hash mismatch -- stored "
                f"{row.get('content_hash')!r} vs recomputed {recomputed!r}"
            )

        if expected_position == 0:
            if row.get("prev_hash") is not None:
                raise AuditChainError(
                    f"row 0 (head): prev_hash must be None, got "
                    f"{row.get('prev_hash')!r}"
                )
        else:
            if row.get("prev_hash") != prev_content_hash:
                raise AuditChainError(
                    f"row {i}: prev_hash {row.get('prev_hash')!r} "
                    f"!= previous content_hash {prev_content_hash!r}"
                )

        prev_content_hash = row["content_hash"]
        expected_position += 1
