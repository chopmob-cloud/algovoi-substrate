"""Tests for audit_chain module."""

from __future__ import annotations

import pytest

from algovoi_substrate.audit_chain import (
    AuditChainError,
    append_to_chain,
    verify_audit_chain,
)
from algovoi_substrate.canonicalize import sha256_jcs


class TestAppendToChain:
    def test_head_row_has_position_zero_and_no_prev_hash(self) -> None:
        row = append_to_chain(payload={"event": "first"}, prev_row=None)
        assert row["chain_position"] == 0
        assert row["prev_hash"] is None
        assert row["content_hash"] == sha256_jcs({"event": "first"})

    def test_next_row_links_to_prev(self) -> None:
        row0 = append_to_chain(payload={"event": "first"}, prev_row=None)
        row1 = append_to_chain(payload={"event": "second"}, prev_row=row0)
        assert row1["chain_position"] == 1
        assert row1["prev_hash"] == row0["content_hash"]
        assert row1["content_hash"] == sha256_jcs({"event": "second"})

    def test_three_row_chain(self) -> None:
        rows = []
        prev = None
        for i, payload in enumerate([{"i": 0}, {"i": 1}, {"i": 2}]):
            row = append_to_chain(payload=payload, prev_row=prev)
            assert row["chain_position"] == i
            rows.append(row)
            prev = row

        verify_audit_chain(rows)  # should not raise


class TestVerifyAuditChain:
    def test_empty_chain_is_valid(self) -> None:
        verify_audit_chain([])  # no rows means nothing to check

    def test_head_row_must_have_no_prev_hash(self) -> None:
        bad = [
            {
                "chain_position": 0,
                "content_hash": sha256_jcs({"x": 1}),
                "prev_hash": "should-be-none",
                "payload": {"x": 1},
            }
        ]
        with pytest.raises(AuditChainError, match="head.*prev_hash must be None"):
            verify_audit_chain(bad)

    def test_position_must_start_at_zero(self) -> None:
        bad = [
            {
                "chain_position": 1,
                "content_hash": sha256_jcs({"x": 1}),
                "prev_hash": None,
                "payload": {"x": 1},
            }
        ]
        with pytest.raises(AuditChainError, match="chain_position 1 != expected 0"):
            verify_audit_chain(bad)

    def test_detects_content_hash_tampering(self) -> None:
        row = append_to_chain(payload={"x": 1}, prev_row=None)
        # Tamper with the stored hash.
        tampered = dict(row)
        tampered["content_hash"] = "0" * 64
        with pytest.raises(AuditChainError, match="content_hash mismatch"):
            verify_audit_chain([tampered])  # type: ignore[list-item]

    def test_detects_prev_hash_break(self) -> None:
        row0 = append_to_chain(payload={"x": 1}, prev_row=None)
        row1 = append_to_chain(payload={"x": 2}, prev_row=row0)
        # Tamper with the linkage.
        broken = dict(row1)
        broken["prev_hash"] = "0" * 64
        with pytest.raises(AuditChainError, match="prev_hash"):
            verify_audit_chain([row0, broken])  # type: ignore[list-item]

    def test_detects_payload_tampering(self) -> None:
        row = append_to_chain(payload={"x": 1}, prev_row=None)
        tampered = dict(row)
        tampered["payload"] = {"x": 2}  # different payload, stored hash unchanged
        with pytest.raises(AuditChainError, match="content_hash mismatch"):
            verify_audit_chain([tampered])  # type: ignore[list-item]


class TestRoundTrip:
    def test_round_trip_three_rows(self) -> None:
        from algovoi_substrate.compliance_receipt import build_compliance_receipt

        rows = []
        prev = None
        for i in range(3):
            payload = build_compliance_receipt(
                payer_ref=f"sha256:row{i}",
                screen_result="ALLOW",
                screen_timestamp_ms=1716460800000 + i,
                screen_provider_did="did:web:api.algovoi.co.uk",
                jurisdiction_flags=["UK", "EU"],
            )
            row = append_to_chain(payload=dict(payload), prev_row=prev)
            rows.append(row)
            prev = row

        verify_audit_chain(rows)
        assert rows[0]["chain_position"] == 0
        assert rows[2]["chain_position"] == 2
        assert rows[2]["prev_hash"] == rows[1]["content_hash"]
