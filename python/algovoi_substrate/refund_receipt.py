"""
Refund receipt shape — companion to compliance_receipt.

This shape is the AlgoVoi-discipline refund-event record. It composes
with `compliance_receipt` via the `original_payment_ref` linkage so a
verifier can walk the full payment lifecycle (admission decision ->
settlement -> refund event) under one canonicalisation pin.

The categorical outcome (FULL / PARTIAL / REJECTED) is load-bearing
for downstream consumer-rights and PSD2 obligations: a REJECTED
outcome carries dispute-evidence obligations distinct from FULL/PARTIAL,
and the receipt format preserves the operational distinction at the
canonical-bytes level rather than collapsing it to a score or tier
projection.

Shape:
- canon_version: in-band format-version pin ("jcs-rfc8785-v1").
- jurisdiction_flags: ordered list of jurisdiction codes (e.g. ["UK","EU"]).
- original_payment_ref: content-addressed reference to the original
  payment ("sha256:<hex>"). When refunding a compliance-admitted payment,
  this MAY equal the compliance receipt's content_hash.
- refund_amount: two-field object {"amount_minor": str, "asset_id": str}
  representing the refunded value in the asset's minor unit.
- refund_provider_did: did:web of the refund-issuing entity.
- refund_result: one of FULL, PARTIAL, REJECTED.
- refund_timestamp_ms: epoch-millisecond integer (Substrate Rule 2).

Specified in IETF Internet-Draft `draft-hopley-x402-refund-receipt-00`
(Independent Submission, Informational; AlgoVoi-authored).
"""

from __future__ import annotations

from typing import TypedDict

from algovoi_substrate.canonicalize import CANON_VERSION

REFUND_RESULTS = frozenset({"FULL", "PARTIAL", "REJECTED"})


class RefundReceiptError(ValueError):
    """Raised when refund receipt inputs violate the substrate discipline."""


class RefundAmount(TypedDict):
    amount_minor: str
    asset_id: str


class RefundReceipt(TypedDict):
    canon_version: str
    jurisdiction_flags: list[str]
    original_payment_ref: str
    refund_amount: RefundAmount
    refund_provider_did: str
    refund_result: str
    refund_timestamp_ms: int


def _require_str(field: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise RefundReceiptError(f"{field} must be a non-empty string")
    return value


def _require_int_timestamp_ms(value: object) -> int:
    if isinstance(value, bool):
        raise RefundReceiptError("refund_timestamp_ms must be int, got bool")
    if not isinstance(value, int):
        raise RefundReceiptError(
            f"refund_timestamp_ms must be epoch-millisecond integer "
            f"(Substrate Rule 2), got {type(value).__name__}"
        )
    if value < 0:
        raise RefundReceiptError(
            f"refund_timestamp_ms must be non-negative, got {value}"
        )
    return value


def _require_jurisdiction_flags(value: object) -> list[str]:
    if not isinstance(value, list):
        raise RefundReceiptError(
            f"jurisdiction_flags must be list, got {type(value).__name__}"
        )
    for i, code in enumerate(value):
        if not isinstance(code, str) or not code:
            raise RefundReceiptError(
                f"jurisdiction_flags[{i}] must be a non-empty string"
            )
    return list(value)


def _require_refund_amount(value: object) -> RefundAmount:
    if not isinstance(value, dict):
        raise RefundReceiptError(
            f"refund_amount must be dict, got {type(value).__name__}"
        )
    expected_keys = {"amount_minor", "asset_id"}
    if set(value.keys()) != expected_keys:
        raise RefundReceiptError(
            f"refund_amount must have exactly the keys {sorted(expected_keys)}, "
            f"got {sorted(value.keys())}"
        )
    amount_minor = value["amount_minor"]
    asset_id = value["asset_id"]
    if not isinstance(amount_minor, str) or not amount_minor:
        raise RefundReceiptError(
            "refund_amount.amount_minor must be a non-empty string "
            "(decimal digits in the asset's minor unit; string-typed to avoid "
            "float-precision and JS-integer-overflow concerns)"
        )
    if not amount_minor.isdigit():
        raise RefundReceiptError(
            f"refund_amount.amount_minor must be decimal digits only, "
            f"got {amount_minor!r}"
        )
    if not isinstance(asset_id, str) or not asset_id:
        raise RefundReceiptError(
            "refund_amount.asset_id must be a non-empty string"
        )
    return RefundAmount(amount_minor=amount_minor, asset_id=asset_id)


def build_refund_receipt(
    *,
    original_payment_ref: str,
    refund_result: str,
    refund_timestamp_ms: int,
    refund_provider_did: str,
    refund_amount: RefundAmount,
    jurisdiction_flags: list[str],
    canon_version: str = CANON_VERSION,
) -> RefundReceipt:
    """Build a validated refund receipt object.

    All fields are required (keyword-only) except canon_version which
    defaults to the current substrate version (jcs-rfc8785-v1).

    refund_result MUST be one of FULL, PARTIAL, REJECTED — the
    categorical outcome is load-bearing for downstream consumer-rights
    and PSD2 obligations and must not be projected to a score/tier
    representation.

    original_payment_ref is expected to be a content-addressed reference
    (e.g. "sha256:<hex>") to the original payment record. When refunding
    a payment admitted under a compliance receipt, the conventional
    choice is the compliance receipt's content_hash.

    refund_amount carries the refunded value as {"amount_minor": str,
    "asset_id": str}. amount_minor is a decimal-digit string in the
    asset's minor unit (e.g. "100000" for 0.1 USDC under asset_id
    "USDC.6"). String typing avoids float-precision loss and JS-integer
    overflow for large values.

    jurisdiction_flags is treated as ordered — ["UK","EU"] and
    ["EU","UK"] produce distinct canonical bytes per RFC 8785 §3.2.3.
    """
    if refund_result not in REFUND_RESULTS:
        raise RefundReceiptError(
            f"refund_result must be one of {sorted(REFUND_RESULTS)}, "
            f"got {refund_result!r}"
        )

    return RefundReceipt(
        canon_version=_require_str("canon_version", canon_version),
        jurisdiction_flags=_require_jurisdiction_flags(jurisdiction_flags),
        original_payment_ref=_require_str("original_payment_ref", original_payment_ref),
        refund_amount=_require_refund_amount(refund_amount),
        refund_provider_did=_require_str("refund_provider_did", refund_provider_did),
        refund_result=refund_result,
        refund_timestamp_ms=_require_int_timestamp_ms(refund_timestamp_ms),
    )
