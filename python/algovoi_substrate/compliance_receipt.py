"""
Compliance receipt shape matching AlgoVoi's production /compliance/screen.

This shape is what an AlgoVoi-discipline screening provider emits when it
records a compliance decision. The categorical outcome (ALLOW / REFER / DENY)
is load-bearing for the retention layer: under UK POCA 2002 s.330 a REFER
carries a mandatory SAR obligation that DENY does not. A score/tier
projection would lose that property and break year-five auditability.

Shape:
- payer_ref: content-addressed identity reference (does not leak cleartext).
- screen_result: one of ALLOW, REFER, DENY.
- screen_timestamp_ms: epoch-millisecond integer (Substrate Rule 1).
- screen_provider_did: did:web of the screening provider.
- jurisdiction_flags: ordered list of jurisdiction codes (e.g. ["UK","EU"]).
  Element order is load-bearing per RFC 8785 array-element-order discipline.
- canon_version: in-band format-version pin ("jcs-rfc8785-v1").

This shape lands as the compliance-receipt-fixture in x402-foundation/x402
PR #2434 (renamed from risk-check-attestation-sample, layer-split with
RiskCheckResult in PR #2422 / #2423).
"""

from __future__ import annotations

from typing import TypedDict

from algovoi_substrate.canonicalize import CANON_VERSION

SCREEN_RESULTS = frozenset({"ALLOW", "REFER", "DENY"})


class ComplianceReceiptError(ValueError):
    """Raised when compliance receipt inputs violate the substrate discipline."""


class ComplianceReceipt(TypedDict):
    payer_ref: str
    screen_result: str
    screen_timestamp_ms: int
    screen_provider_did: str
    jurisdiction_flags: list[str]
    canon_version: str


def _require_str(field: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ComplianceReceiptError(f"{field} must be a non-empty string")
    return value


def _require_int_timestamp_ms(value: object) -> int:
    if isinstance(value, bool):
        raise ComplianceReceiptError("screen_timestamp_ms must be int, got bool")
    if not isinstance(value, int):
        raise ComplianceReceiptError(
            f"screen_timestamp_ms must be epoch-millisecond integer "
            f"(Substrate Rule 1), got {type(value).__name__}"
        )
    if value < 0:
        raise ComplianceReceiptError(
            f"screen_timestamp_ms must be non-negative, got {value}"
        )
    return value


def _require_jurisdiction_flags(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ComplianceReceiptError(
            f"jurisdiction_flags must be list, got {type(value).__name__}"
        )
    for i, code in enumerate(value):
        if not isinstance(code, str) or not code:
            raise ComplianceReceiptError(
                f"jurisdiction_flags[{i}] must be a non-empty string"
            )
    return list(value)


def build_compliance_receipt(
    *,
    payer_ref: str,
    screen_result: str,
    screen_timestamp_ms: int,
    screen_provider_did: str,
    jurisdiction_flags: list[str],
    canon_version: str = CANON_VERSION,
) -> ComplianceReceipt:
    """Build a validated compliance receipt object.

    All fields are required (keyword-only) except canon_version which
    defaults to the current substrate version (jcs-rfc8785-v1).

    screen_result must be one of ALLOW, REFER, DENY -- the categorical
    outcome is load-bearing for downstream regulatory obligations and
    must not be projected to a score/tier representation.

    payer_ref is expected to be a content-addressed identity reference
    (e.g. "sha256:<hex>") rather than cleartext identity content. The
    discipline does not enforce the prefix shape here; that constraint
    lives at the schema layer above.

    jurisdiction_flags is treated as ordered -- ["UK","EU"] and ["EU","UK"]
    produce distinct canonical bytes per RFC 8785 §3.2.3.
    """
    if screen_result not in SCREEN_RESULTS:
        raise ComplianceReceiptError(
            f"screen_result must be one of {sorted(SCREEN_RESULTS)}, "
            f"got {screen_result!r}"
        )

    return ComplianceReceipt(
        payer_ref=_require_str("payer_ref", payer_ref),
        screen_result=screen_result,
        screen_timestamp_ms=_require_int_timestamp_ms(screen_timestamp_ms),
        screen_provider_did=_require_str("screen_provider_did", screen_provider_did),
        jurisdiction_flags=_require_jurisdiction_flags(jurisdiction_flags),
        canon_version=_require_str("canon_version", canon_version),
    )
