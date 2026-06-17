"""Tests for settlement_binding module."""

from __future__ import annotations

import pytest

from algovoi_substrate.canonicalize import sha256_jcs
from algovoi_substrate.settlement_binding import (
    SettlementBindingError,
    settlement_action_binding,
    settlement_binding_preimage,
)

# Published reference vector sab-v1-001 from the public conformance set
# algovoi-jcs-conformance-vectors/settlement_action_binding_v1.
REF = {
    "action_ref": "7528529a8be2044488e603b7913efaa4f83620dbcc63010d4a1478cf7e9a473c",
    "transition_hash": "f49faa7c4f82bd842705374311f5f6af073826539d519d0b65de3263258eac5f",
    "settlement_ref": "0ead75bfe7fc74cc0421124903e56cb5c5006d02c393231a1d5f260fa87e96d3",
    "retention_chain_ref": "sha256:d23aeb006c5f3db9dd96315916410393904f56c4c871593065eb73b783fff35f",
}
REF_BINDING = "sha256:7dc4a2bf62b3c5eabd10fc875ff7fc10f188666f15838c4a51464cc72e80f6ca"


def _binding(**overrides: str) -> str:
    merged = dict(REF)
    merged.update(overrides)
    return settlement_action_binding(**merged)


class TestSettlementBindingPreimage:
    def test_builds_canonical_four_field_shape(self) -> None:
        assert settlement_binding_preimage(**REF) == {
            "action_ref": REF["action_ref"],
            "transition_hash": REF["transition_hash"],
            "settlement_ref": REF["settlement_ref"],
            "retention_chain_ref": REF["retention_chain_ref"],
        }

    def test_rejects_non_string_field(self) -> None:
        with pytest.raises(SettlementBindingError, match="action_ref must be str"):
            settlement_binding_preimage(
                action_ref=123,  # type: ignore[arg-type]
                transition_hash=REF["transition_hash"],
                settlement_ref=REF["settlement_ref"],
                retention_chain_ref=REF["retention_chain_ref"],
            )

    def test_rejects_short_hex(self) -> None:
        with pytest.raises(SettlementBindingError, match="64-character"):
            settlement_binding_preimage(
                action_ref="abc123",
                transition_hash=REF["transition_hash"],
                settlement_ref=REF["settlement_ref"],
                retention_chain_ref=REF["retention_chain_ref"],
            )

    def test_rejects_uppercase_hex(self) -> None:
        with pytest.raises(SettlementBindingError, match="lowercase"):
            settlement_binding_preimage(
                action_ref=REF["action_ref"].upper(),
                transition_hash=REF["transition_hash"],
                settlement_ref=REF["settlement_ref"],
                retention_chain_ref=REF["retention_chain_ref"],
            )

    def test_rejects_chain_ref_without_prefix(self) -> None:
        # A bare 64-hex digest (no "sha256:" prefix) is not a valid chain ref.
        bare = REF["retention_chain_ref"][len("sha256:"):]
        with pytest.raises(SettlementBindingError, match="sha256:"):
            settlement_binding_preimage(
                action_ref=REF["action_ref"],
                transition_hash=REF["transition_hash"],
                settlement_ref=REF["settlement_ref"],
                retention_chain_ref=bare,
            )

    def test_rejects_prefixed_action_ref(self) -> None:
        # action_ref is a BARE digest; the "sha256:" prefix belongs only to the
        # chain ref. A prefixed action_ref must be rejected.
        with pytest.raises(SettlementBindingError, match="64-character"):
            settlement_binding_preimage(
                action_ref=REF["retention_chain_ref"],  # carries sha256: prefix
                transition_hash=REF["transition_hash"],
                settlement_ref=REF["settlement_ref"],
                retention_chain_ref=REF["retention_chain_ref"],
            )


class TestSettlementActionBinding:
    def test_matches_published_reference_vector(self) -> None:
        # Load-bearing assertion: the substrate primitive reproduces the
        # published conformance binding_ref byte-for-byte (sab-v1-001).
        assert settlement_action_binding(**REF) == REF_BINDING

    def test_carries_sha256_prefix(self) -> None:
        assert settlement_action_binding(**REF).startswith("sha256:")

    def test_introduces_no_new_primitive(self) -> None:
        # binding_ref == "sha256:" + SHA-256(JCS(preimage)); no bespoke hashing.
        preimage = dict(settlement_binding_preimage(**REF))
        assert settlement_action_binding(**REF) == "sha256:" + sha256_jcs(preimage)

    def test_deterministic(self) -> None:
        assert _binding() == _binding()

    def test_settlement_binding_is_load_bearing(self) -> None:
        # sab-v1-003: a different settlement_ref must diverge.
        assert _binding(
            settlement_ref="e7777a9a77a9c3f02339594395bfb2620e07edc62d3dcb48c4f2e82a8c37a1c4"
        ) != REF_BINDING

    def test_action_binding_is_load_bearing(self) -> None:
        # sab-v1-004: a different action_ref must diverge.
        assert _binding(
            action_ref="57e861cb0929fe602823a15e2bc5a5587f0b9c3bd39147baa49819dd014c56a6"
        ) != REF_BINDING

    def test_state_binding_is_load_bearing(self) -> None:
        # sab-v1-005: only the exact COMMITTED transition binds; a PENDING
        # transition_hash must diverge.
        assert _binding(
            transition_hash="0957638b64c790292c11d90e9ae15576a6454f37f23a0aade222acf9e2ea18b0"
        ) != REF_BINDING

    def test_chain_binding_is_load_bearing(self) -> None:
        # sab-v1-006: a different retention_chain_ref must diverge.
        assert _binding(
            retention_chain_ref="sha256:43f888f00ea70e38fb8e38c205219b3fff51a90c62197d890b9f270f0f81fe42"
        ) != REF_BINDING
