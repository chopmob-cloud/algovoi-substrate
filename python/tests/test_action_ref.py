"""Tests for action_ref module."""

from __future__ import annotations

import pytest

from algovoi_substrate.action_ref import (
    ActionRefError,
    action_ref,
    action_ref_object,
)
from algovoi_substrate.canonicalize import sha256_jcs


class TestActionRefObject:
    def test_builds_canonical_shape(self) -> None:
        obj = action_ref_object(
            agent_id="agent-x",
            action_type="payment",
            scope="bilateral",
            timestamp_ms=1716460800000,
        )
        assert obj == {
            "agent_id": "agent-x",
            "action_type": "payment",
            "scope": "bilateral",
            "timestamp_ms": 1716460800000,
        }

    def test_rejects_non_string_agent_id(self) -> None:
        with pytest.raises(ActionRefError, match="agent_id must be str"):
            action_ref_object(agent_id=123, action_type="p", scope="s", timestamp_ms=0)  # type: ignore[arg-type]

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ActionRefError, match="must be a non-empty string"):
            action_ref_object(agent_id="", action_type="p", scope="s", timestamp_ms=0)

    def test_rejects_float_timestamp(self) -> None:
        # Substrate Rule 1: timestamp_ms MUST be an epoch-millisecond integer.
        with pytest.raises(ActionRefError, match="Substrate Rule 1"):
            action_ref_object(
                agent_id="a", action_type="p", scope="s", timestamp_ms=1716460800000.5  # type: ignore[arg-type]
            )

    def test_rejects_bool_timestamp(self) -> None:
        # bool is a subclass of int in Python; explicit rejection.
        with pytest.raises(ActionRefError, match="timestamp_ms must be int, got bool"):
            action_ref_object(agent_id="a", action_type="p", scope="s", timestamp_ms=True)  # type: ignore[arg-type]

    def test_rejects_string_timestamp(self) -> None:
        with pytest.raises(ActionRefError, match="Substrate Rule 1"):
            action_ref_object(
                agent_id="a", action_type="p", scope="s", timestamp_ms="2026-05-23"  # type: ignore[arg-type]
            )

    def test_rejects_negative_timestamp(self) -> None:
        with pytest.raises(ActionRefError, match="non-negative"):
            action_ref_object(
                agent_id="a", action_type="p", scope="s", timestamp_ms=-1
            )

    def test_accepts_zero_timestamp(self) -> None:
        # Epoch zero is a valid timestamp.
        obj = action_ref_object(
            agent_id="a", action_type="p", scope="s", timestamp_ms=0
        )
        assert obj["timestamp_ms"] == 0


class TestActionRef:
    def test_matches_jcs_sha256_of_preimage(self) -> None:
        # action_ref = SHA-256(JCS({agent_id, action_type, scope, timestamp_ms}))
        ref = action_ref(
            agent_id="agent-x",
            action_type="payment",
            scope="bilateral",
            timestamp_ms=1716460800000,
        )
        expected = sha256_jcs({
            "agent_id": "agent-x",
            "action_type": "payment",
            "scope": "bilateral",
            "timestamp_ms": 1716460800000,
        })
        assert ref == expected

    def test_distinct_inputs_distinct_refs(self) -> None:
        a = action_ref(
            agent_id="agent-x",
            action_type="payment",
            scope="bilateral",
            timestamp_ms=1716460800000,
        )
        b = action_ref(
            agent_id="agent-x",
            action_type="payment",
            scope="bilateral",
            timestamp_ms=1716460800001,  # 1ms later
        )
        assert a != b

    def test_deterministic(self) -> None:
        a = action_ref(
            agent_id="agent-x",
            action_type="payment",
            scope="bilateral",
            timestamp_ms=1716460800000,
        )
        b = action_ref(
            agent_id="agent-x",
            action_type="payment",
            scope="bilateral",
            timestamp_ms=1716460800000,
        )
        assert a == b
