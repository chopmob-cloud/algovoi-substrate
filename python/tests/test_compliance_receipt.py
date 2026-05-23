"""Tests for compliance_receipt module."""

from __future__ import annotations

import pytest

from algovoi_substrate.canonicalize import CANON_VERSION, sha256_jcs
from algovoi_substrate.compliance_receipt import (
    SCREEN_RESULTS,
    ComplianceReceiptError,
    build_compliance_receipt,
)


class TestScreenResults:
    def test_only_allow_refer_deny(self) -> None:
        assert SCREEN_RESULTS == frozenset({"ALLOW", "REFER", "DENY"})


class TestBuildComplianceReceipt:
    def test_builds_canonical_receipt(self) -> None:
        r = build_compliance_receipt(
            payer_ref="sha256:abc123",
            screen_result="ALLOW",
            screen_timestamp_ms=1716460800000,
            screen_provider_did="did:web:api.algovoi.co.uk",
            jurisdiction_flags=["UK", "EU"],
        )
        assert r["payer_ref"] == "sha256:abc123"
        assert r["screen_result"] == "ALLOW"
        assert r["screen_timestamp_ms"] == 1716460800000
        assert r["screen_provider_did"] == "did:web:api.algovoi.co.uk"
        assert r["jurisdiction_flags"] == ["UK", "EU"]
        assert r["canon_version"] == CANON_VERSION

    def test_distinct_jurisdiction_orders_distinct_hashes(self) -> None:
        """RFC 8785 §3.2.3: ["UK","EU"] and ["EU","UK"] hash differently."""
        r_uk_eu = build_compliance_receipt(
            payer_ref="sha256:abc123",
            screen_result="REFER",
            screen_timestamp_ms=1716460800000,
            screen_provider_did="did:web:api.algovoi.co.uk",
            jurisdiction_flags=["UK", "EU"],
        )
        r_eu_uk = build_compliance_receipt(
            payer_ref="sha256:abc123",
            screen_result="REFER",
            screen_timestamp_ms=1716460800000,
            screen_provider_did="did:web:api.algovoi.co.uk",
            jurisdiction_flags=["EU", "UK"],
        )
        assert sha256_jcs(dict(r_uk_eu)) != sha256_jcs(dict(r_eu_uk))

    def test_rejects_invalid_screen_result(self) -> None:
        with pytest.raises(ComplianceReceiptError, match="screen_result must be one of"):
            build_compliance_receipt(
                payer_ref="sha256:x",
                screen_result="MAYBE",
                screen_timestamp_ms=0,
                screen_provider_did="did:web:x",
                jurisdiction_flags=["UK"],
            )

    def test_rejects_score_tier_projection(self) -> None:
        """The categorical ALLOW/REFER/DENY is load-bearing; score is not
        an acceptable substitute (would lose UK POCA s.330 SAR distinction)."""
        with pytest.raises(ComplianceReceiptError):
            build_compliance_receipt(
                payer_ref="sha256:x",
                screen_result="score:75",
                screen_timestamp_ms=0,
                screen_provider_did="did:web:x",
                jurisdiction_flags=["UK"],
            )

    def test_rejects_float_timestamp(self) -> None:
        with pytest.raises(ComplianceReceiptError, match="Substrate Rule 1"):
            build_compliance_receipt(
                payer_ref="sha256:x",
                screen_result="ALLOW",
                screen_timestamp_ms=1716460800000.5,  # type: ignore[arg-type]
                screen_provider_did="did:web:x",
                jurisdiction_flags=["UK"],
            )

    def test_rejects_empty_payer_ref(self) -> None:
        with pytest.raises(ComplianceReceiptError, match="payer_ref"):
            build_compliance_receipt(
                payer_ref="",
                screen_result="ALLOW",
                screen_timestamp_ms=0,
                screen_provider_did="did:web:x",
                jurisdiction_flags=["UK"],
            )

    def test_rejects_non_list_jurisdiction_flags(self) -> None:
        with pytest.raises(ComplianceReceiptError, match="jurisdiction_flags must be list"):
            build_compliance_receipt(
                payer_ref="sha256:x",
                screen_result="ALLOW",
                screen_timestamp_ms=0,
                screen_provider_did="did:web:x",
                jurisdiction_flags="UK",  # type: ignore[arg-type]
            )

    def test_rejects_empty_jurisdiction_code(self) -> None:
        with pytest.raises(ComplianceReceiptError, match="jurisdiction_flags"):
            build_compliance_receipt(
                payer_ref="sha256:x",
                screen_result="ALLOW",
                screen_timestamp_ms=0,
                screen_provider_did="did:web:x",
                jurisdiction_flags=["UK", ""],
            )

    def test_canon_version_default_is_jcs_rfc8785_v1(self) -> None:
        r = build_compliance_receipt(
            payer_ref="sha256:x",
            screen_result="DENY",
            screen_timestamp_ms=0,
            screen_provider_did="did:web:x",
            jurisdiction_flags=["UK"],
        )
        assert r["canon_version"] == "jcs-rfc8785-v1"
