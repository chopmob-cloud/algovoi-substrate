"""Tests for refund_receipt module."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from algovoi_substrate.canonicalize import CANON_VERSION, canonicalize, sha256_jcs
from algovoi_substrate.refund_receipt import (
    REFUND_RESULTS,
    RefundReceiptError,
    build_refund_receipt,
)


class TestRefundResults:
    def test_only_full_partial_rejected(self) -> None:
        assert REFUND_RESULTS == frozenset({"FULL", "PARTIAL", "REJECTED"})


class TestBuildRefundReceipt:
    def test_builds_canonical_receipt(self) -> None:
        r = build_refund_receipt(
            original_payment_ref="sha256:abc123",
            refund_result="FULL",
            refund_timestamp_ms=1716460800000,
            refund_provider_did="did:web:api.algovoi.co.uk",
            refund_amount={"amount_minor": "100000", "asset_id": "USDC.6"},
            jurisdiction_flags=["UK", "EU"],
        )
        assert r["original_payment_ref"] == "sha256:abc123"
        assert r["refund_result"] == "FULL"
        assert r["refund_timestamp_ms"] == 1716460800000
        assert r["refund_provider_did"] == "did:web:api.algovoi.co.uk"
        assert r["refund_amount"] == {"amount_minor": "100000", "asset_id": "USDC.6"}
        assert r["jurisdiction_flags"] == ["UK", "EU"]
        assert r["canon_version"] == CANON_VERSION

    def test_distinct_result_distinct_hashes(self) -> None:
        """Closed enum is byte-load-bearing under JCS canonicalisation."""
        common = dict(
            original_payment_ref="sha256:x",
            refund_timestamp_ms=1716460800000,
            refund_provider_did="did:web:x",
            refund_amount={"amount_minor": "100000", "asset_id": "USDC.6"},
            jurisdiction_flags=["UK"],
        )
        full = build_refund_receipt(refund_result="FULL", **common)
        partial = build_refund_receipt(refund_result="PARTIAL", **common)
        rejected = build_refund_receipt(refund_result="REJECTED", **common)
        h_full = sha256_jcs(dict(full))
        h_partial = sha256_jcs(dict(partial))
        h_rejected = sha256_jcs(dict(rejected))
        assert h_full != h_partial
        assert h_full != h_rejected
        assert h_partial != h_rejected

    def test_distinct_jurisdiction_orders_distinct_hashes(self) -> None:
        common = dict(
            original_payment_ref="sha256:x",
            refund_result="FULL",
            refund_timestamp_ms=1716460800000,
            refund_provider_did="did:web:x",
            refund_amount={"amount_minor": "100000", "asset_id": "USDC.6"},
        )
        r_uk_eu = build_refund_receipt(jurisdiction_flags=["UK", "EU"], **common)
        r_eu_uk = build_refund_receipt(jurisdiction_flags=["EU", "UK"], **common)
        assert sha256_jcs(dict(r_uk_eu)) != sha256_jcs(dict(r_eu_uk))

    def test_rejects_invalid_result(self) -> None:
        with pytest.raises(RefundReceiptError, match="refund_result must be one of"):
            build_refund_receipt(
                original_payment_ref="sha256:x",
                refund_result="MAYBE",
                refund_timestamp_ms=0,
                refund_provider_did="did:web:x",
                refund_amount={"amount_minor": "1", "asset_id": "USDC.6"},
                jurisdiction_flags=["UK"],
            )

    def test_rejects_score_projection(self) -> None:
        with pytest.raises(RefundReceiptError):
            build_refund_receipt(
                original_payment_ref="sha256:x",
                refund_result="partial:50%",
                refund_timestamp_ms=0,
                refund_provider_did="did:web:x",
                refund_amount={"amount_minor": "1", "asset_id": "USDC.6"},
                jurisdiction_flags=["UK"],
            )

    def test_rejects_float_timestamp(self) -> None:
        with pytest.raises(RefundReceiptError, match="Substrate Rule 2"):
            build_refund_receipt(
                original_payment_ref="sha256:x",
                refund_result="FULL",
                refund_timestamp_ms=1716460800000.5,  # type: ignore[arg-type]
                refund_provider_did="did:web:x",
                refund_amount={"amount_minor": "1", "asset_id": "USDC.6"},
                jurisdiction_flags=["UK"],
            )

    def test_rejects_string_timestamp(self) -> None:
        with pytest.raises(RefundReceiptError, match="Substrate Rule 2"):
            build_refund_receipt(
                original_payment_ref="sha256:x",
                refund_result="FULL",
                refund_timestamp_ms="2024-05-23T12:00:00Z",  # type: ignore[arg-type]
                refund_provider_did="did:web:x",
                refund_amount={"amount_minor": "1", "asset_id": "USDC.6"},
                jurisdiction_flags=["UK"],
            )

    def test_rejects_amount_with_extra_keys(self) -> None:
        with pytest.raises(RefundReceiptError, match="refund_amount must have exactly"):
            build_refund_receipt(
                original_payment_ref="sha256:x",
                refund_result="FULL",
                refund_timestamp_ms=0,
                refund_provider_did="did:web:x",
                refund_amount={"amount_minor": "1", "asset_id": "USDC.6", "extra": "x"},  # type: ignore[arg-type]
                jurisdiction_flags=["UK"],
            )

    def test_rejects_non_digit_amount_minor(self) -> None:
        with pytest.raises(RefundReceiptError, match="decimal digits"):
            build_refund_receipt(
                original_payment_ref="sha256:x",
                refund_result="FULL",
                refund_timestamp_ms=0,
                refund_provider_did="did:web:x",
                refund_amount={"amount_minor": "0.1", "asset_id": "USDC.6"},
                jurisdiction_flags=["UK"],
            )

    def test_rejects_negative_amount(self) -> None:
        with pytest.raises(RefundReceiptError, match="decimal digits"):
            build_refund_receipt(
                original_payment_ref="sha256:x",
                refund_result="FULL",
                refund_timestamp_ms=0,
                refund_provider_did="did:web:x",
                refund_amount={"amount_minor": "-100", "asset_id": "USDC.6"},
                jurisdiction_flags=["UK"],
            )

    def test_rejects_empty_jurisdiction_code(self) -> None:
        with pytest.raises(RefundReceiptError, match="jurisdiction_flags"):
            build_refund_receipt(
                original_payment_ref="sha256:x",
                refund_result="FULL",
                refund_timestamp_ms=0,
                refund_provider_did="did:web:x",
                refund_amount={"amount_minor": "1", "asset_id": "USDC.6"},
                jurisdiction_flags=["UK", ""],
            )

    def test_canon_version_default_is_jcs_rfc8785_v1(self) -> None:
        r = build_refund_receipt(
            original_payment_ref="sha256:x",
            refund_result="REJECTED",
            refund_timestamp_ms=0,
            refund_provider_did="did:web:x",
            refund_amount={"amount_minor": "1", "asset_id": "USDC.6"},
            jurisdiction_flags=["UK"],
        )
        assert r["canon_version"] == "jcs-rfc8785-v1"


class TestConformanceVectorReproduction:
    """Verify the refund_receipt_v1 conformance vectors reproduce byte-identical.

    Reads C:/algo/algovoi-jcs-conformance-vectors/vectors/refund_receipt_v1/
    refund_receipt_v1.json when present and asserts every vector's canonical
    bytes + content_hash matches what build_refund_receipt() produces.
    """

    VECTOR_PATH = Path(
        "C:/algo/algovoi-jcs-conformance-vectors/vectors/refund_receipt_v1/refund_receipt_v1.json"
    )

    def test_vectors_001_to_005_reproduce(self) -> None:
        if not self.VECTOR_PATH.exists():
            pytest.skip("conformance vectors not co-located")
        data = json.loads(self.VECTOR_PATH.read_text(encoding="utf-8"))
        for v in data["vectors"]:
            if "receipt" not in v:
                continue
            canon = canonicalize(v["receipt"])
            canon_bytes = canon.encode("utf-8") if isinstance(canon, str) else canon
            assert (
                base64.b64encode(canon_bytes).decode("ascii")
                == v["expected_jcs_bytes_b64"]
            ), f"{v['vector_id']}: JCS bytes mismatch"
            assert (
                hashlib.sha256(canon_bytes).hexdigest()
                == v["expected_content_hash"]
            ), f"{v['vector_id']}: content_hash mismatch"
