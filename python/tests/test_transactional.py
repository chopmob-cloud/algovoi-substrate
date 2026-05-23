"""Tests for the transactional action_ref lifecycle primitive."""
from __future__ import annotations

import pytest

from algovoi_substrate import (
    TransactionalError,
    action_ref,
    build_transactional_action_chain,
    transition_hash,
)


# Fixed identity preimage used across the suite. Same values used in the
# action_ref_transactional_v0 conformance vector set.
AGENT_ID = "agent_alpha"
ACTION_TYPE = "payment"
SCOPE = "vauban:stark_settlement"
TIMESTAMP_MS = 1716494400000  # 2024-05-23T20:00:00Z


def fixed_action_ref() -> str:
    return action_ref(AGENT_ID, ACTION_TYPE, SCOPE, TIMESTAMP_MS)


# ---------------------------------------------------------------------
# transition_hash determinism + binding
# ---------------------------------------------------------------------


def test_transition_hash_deterministic() -> None:
    ar = fixed_action_ref()
    a = transition_hash(ar, "authorisation", 1716494400000, 1716494400500, 1716494400800)
    b = transition_hash(ar, "authorisation", 1716494400000, 1716494400500, 1716494400800)
    assert a == b


def test_transition_hash_per_state_distinct() -> None:
    """transition_hash differs per state when other fields are identical."""
    ar = fixed_action_ref()
    auth = transition_hash(ar, "authorisation", 1716494400000, 1716494400500, 1716494400800)
    settle = transition_hash(ar, "settlement", 1716494400000, 1716494400500, 1716494400800)
    refund = transition_hash(ar, "refund", 1716494400000, 1716494400500, 1716494400800)
    digests = {auth, settle, refund}
    assert len(digests) == 3, "states must produce distinct digests"


def test_transition_hash_action_ref_bound() -> None:
    """Same state + timestamps under different action_ref produce different digests."""
    ar1 = fixed_action_ref()
    ar2 = action_ref("agent_beta", ACTION_TYPE, SCOPE, TIMESTAMP_MS)
    assert ar1 != ar2
    t1 = transition_hash(ar1, "settlement", 1716494400000, 1716494400500, 1716494400800)
    t2 = transition_hash(ar2, "settlement", 1716494400000, 1716494400500, 1716494400800)
    assert t1 != t2


def test_transition_hash_distinct_from_action_ref() -> None:
    ar = fixed_action_ref()
    th = transition_hash(ar, "authorisation", 1716494400000, 1716494400500, 1716494400800)
    assert th != ar


# ---------------------------------------------------------------------
# Substrate Rule 2: integer timestamps required, RFC 3339 strings rejected
# ---------------------------------------------------------------------


def test_transition_hash_rejects_rfc3339_string_transition_ts() -> None:
    ar = fixed_action_ref()
    with pytest.raises(TransactionalError, match="transition_timestamp_ms"):
        transition_hash(ar, "authorisation", "2024-05-23T20:00:00Z", 1, 1)  # type: ignore[arg-type]


def test_transition_hash_rejects_rfc3339_string_authority_ts() -> None:
    ar = fixed_action_ref()
    with pytest.raises(TransactionalError, match="authority_verified_at_ms"):
        transition_hash(ar, "authorisation", 1, "2024-05-23T20:00:00Z", 1)  # type: ignore[arg-type]


def test_transition_hash_rejects_rfc3339_string_revocation_ts() -> None:
    ar = fixed_action_ref()
    with pytest.raises(TransactionalError, match="revocation_check_at_ms"):
        transition_hash(ar, "authorisation", 1, 1, "2024-05-23T20:00:00Z")  # type: ignore[arg-type]


def test_transition_hash_rejects_float_timestamp() -> None:
    ar = fixed_action_ref()
    with pytest.raises(TransactionalError, match="transition_timestamp_ms"):
        transition_hash(ar, "authorisation", 1.5, 1, 1)  # type: ignore[arg-type]


def test_transition_hash_rejects_bool_timestamp() -> None:
    ar = fixed_action_ref()
    with pytest.raises(TransactionalError, match="transition_timestamp_ms"):
        transition_hash(ar, "authorisation", True, 1, 1)  # type: ignore[arg-type]


def test_transition_hash_rejects_negative_timestamp() -> None:
    ar = fixed_action_ref()
    with pytest.raises(TransactionalError, match="must be non-negative"):
        transition_hash(ar, "authorisation", -1, 1, 1)


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------


def test_transition_hash_rejects_bad_action_ref() -> None:
    with pytest.raises(TransactionalError, match="action_ref"):
        transition_hash("not-a-hash", "authorisation", 1, 1, 1)


def test_transition_hash_rejects_uppercase_action_ref() -> None:
    ar = fixed_action_ref().upper()
    with pytest.raises(TransactionalError, match="action_ref"):
        transition_hash(ar, "authorisation", 1, 1, 1)


def test_transition_hash_rejects_empty_state() -> None:
    ar = fixed_action_ref()
    with pytest.raises(TransactionalError, match="state"):
        transition_hash(ar, "", 1, 1, 1)


def test_transition_hash_rejects_non_string_state() -> None:
    ar = fixed_action_ref()
    with pytest.raises(TransactionalError, match="state"):
        transition_hash(ar, 42, 1, 1, 1)  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# build_transactional_action_chain end-to-end
# ---------------------------------------------------------------------


def test_build_chain_three_state_payment_lifecycle() -> None:
    chain = build_transactional_action_chain(
        AGENT_ID,
        ACTION_TYPE,
        SCOPE,
        TIMESTAMP_MS,
        transitions=[
            {
                "state": "authorisation",
                "transition_timestamp_ms": 1716494400000,
                "authority_verified_at_ms": 1716494400500,
                "revocation_check_at_ms": 1716494400800,
            },
            {
                "state": "settlement",
                "transition_timestamp_ms": 1716494500000,
                "authority_verified_at_ms": 1716494500300,
                "revocation_check_at_ms": 1716494500500,
            },
            {
                "state": "refund",
                "transition_timestamp_ms": 1716494600000,
                "authority_verified_at_ms": 1716494600300,
                "revocation_check_at_ms": 1716494600500,
            },
        ],
    )
    assert chain["action_ref"] == fixed_action_ref()
    assert len(chain["transitions"]) == 3
    # action_ref stable across all transitions; transition_hashes distinct
    hashes = {t["transition_hash"] for t in chain["transitions"]}
    assert len(hashes) == 3
    # transition_hashes are all distinct from action_ref
    assert chain["action_ref"] not in hashes


def test_build_chain_action_ref_stable_across_transitions() -> None:
    """The substrate's load-bearing property: action_ref does not change."""
    transitions = [
        {
            "state": s,
            "transition_timestamp_ms": ts,
            "authority_verified_at_ms": ts + 500,
            "revocation_check_at_ms": ts + 800,
        }
        for s, ts in [
            ("authorisation", 1716494400000),
            ("settlement", 1716494500000),
            ("refund", 1716494600000),
        ]
    ]
    chain_a = build_transactional_action_chain(
        AGENT_ID, ACTION_TYPE, SCOPE, TIMESTAMP_MS, transitions
    )
    # Rebuild with the same identity inputs but a different transition set.
    chain_b = build_transactional_action_chain(
        AGENT_ID,
        ACTION_TYPE,
        SCOPE,
        TIMESTAMP_MS,
        transitions=[
            {
                "state": "authorisation",
                "transition_timestamp_ms": 9999999999999,
                "authority_verified_at_ms": 9999999999998,
                "revocation_check_at_ms": 9999999999997,
            }
        ],
    )
    assert chain_a["action_ref"] == chain_b["action_ref"]


def test_build_chain_rejects_empty_transitions() -> None:
    with pytest.raises(TransactionalError, match="non-empty"):
        build_transactional_action_chain(
            AGENT_ID, ACTION_TYPE, SCOPE, TIMESTAMP_MS, transitions=[]
        )


def test_build_chain_rejects_non_list_transitions() -> None:
    with pytest.raises(TransactionalError, match="list"):
        build_transactional_action_chain(
            AGENT_ID,
            ACTION_TYPE,
            SCOPE,
            TIMESTAMP_MS,
            transitions={"state": "x"},  # type: ignore[arg-type]
        )


def test_build_chain_rejects_missing_transition_field() -> None:
    with pytest.raises(TransactionalError, match="missing required field"):
        build_transactional_action_chain(
            AGENT_ID,
            ACTION_TYPE,
            SCOPE,
            TIMESTAMP_MS,
            transitions=[
                {
                    "state": "authorisation",
                    "transition_timestamp_ms": 1,
                    # authority_verified_at_ms missing
                    "revocation_check_at_ms": 1,
                }  # type: ignore[list-item]
            ],
        )


def test_build_chain_state_value_is_free_form() -> None:
    """state is a non-empty string with no closed enum at the substrate layer."""
    chain = build_transactional_action_chain(
        AGENT_ID,
        ACTION_TYPE,
        SCOPE,
        TIMESTAMP_MS,
        transitions=[
            {
                "state": "issuance",  # not in the payment-lifecycle vocabulary
                "transition_timestamp_ms": 1,
                "authority_verified_at_ms": 1,
                "revocation_check_at_ms": 1,
            },
            {
                "state": "execution",
                "transition_timestamp_ms": 2,
                "authority_verified_at_ms": 2,
                "revocation_check_at_ms": 2,
            },
            {
                "state": "custom:emitter_specific_state",  # namespace-prefixed convention
                "transition_timestamp_ms": 3,
                "authority_verified_at_ms": 3,
                "revocation_check_at_ms": 3,
            },
        ],
    )
    assert len(chain["transitions"]) == 3
