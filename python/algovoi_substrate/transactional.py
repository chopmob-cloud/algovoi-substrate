"""
Transactional action_ref lifecycle (non-normative substrate extension).

For actions that traverse multiple state transitions (authorisation ->
settlement -> refund; issuance -> execution -> revocation; admission ->
review -> close), the action_ref four-field preimage is the STABLE
identity anchor across the full lifecycle, and per-transition lifecycle
metadata sits OUTSIDE the action_ref preimage.

This module exposes:

- transition_hash(action_ref, state, transition_timestamp_ms,
  authority_verified_at_ms, revocation_check_at_ms) -- the canonical
  hash of a single state transition. Bound to action_ref by including
  it in the preimage.

- build_transactional_action_chain(agent_id, action_type, scope,
  timestamp_ms, transitions) -- emits the full chain shape:
  {action_ref, transitions: [{...transition_hash}, ...]}.

The substrate-level invariants enforced:

1. action_ref is byte-stable across every transition of the same action
   (the four-field preimage does not change with lifecycle state).

2. transition_hash is byte-stable for any given (action_ref, state,
   transition_timestamp_ms, authority_verified_at_ms,
   revocation_check_at_ms) tuple. Re-emission with identical inputs
   produces an identical digest.

3. transition_hash differs per state for the same action_ref + same
   timestamps (state is part of the preimage).

4. action_ref and any transition_hash are byte-distinct (different
   preimage shapes; collision would require an underlying SHA-256
   weakness).

5. All timestamp fields MUST be epoch-millisecond integers per
   Substrate Rule 2. RFC 3339 string forms are rejected at validation
   time, not silently coerced.

The state value is typed as a non-empty string with no closed enum at
the canonicalisation layer, consistent with the scope-field treatment.
Conventional state vocabularies (authorisation/settlement/refund for
payment lifecycles; issuance/execution/revocation for committed-claim
lifecycles; admission/review/close for compliance lifecycles) are
recommended but not enforced.
"""

from __future__ import annotations

import re
from typing import TypedDict

from algovoi_substrate.action_ref import action_ref as _action_ref
from algovoi_substrate.canonicalize import sha256_jcs

# Hex regex for lowercase 64-char SHA-256 digest.
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class TransactionalError(ValueError):
    """Raised when transactional inputs violate the substrate discipline."""


class TransitionPreimage(TypedDict):
    action_ref: str
    state: str
    transition_timestamp_ms: int
    authority_verified_at_ms: int
    revocation_check_at_ms: int


class TransitionInput(TypedDict, total=False):
    """Input shape for a single transition passed into the chain builder."""

    state: str
    transition_timestamp_ms: int
    authority_verified_at_ms: int
    revocation_check_at_ms: int


class TransitionRecord(TypedDict):
    """Output shape for a single transition in the built chain."""

    state: str
    transition_timestamp_ms: int
    authority_verified_at_ms: int
    revocation_check_at_ms: int
    transition_hash: str


class TransactionalChain(TypedDict):
    action_ref: str
    transitions: list[TransitionRecord]


def _require_action_ref_hex(value: object) -> str:
    if not isinstance(value, str):
        raise TransactionalError(
            f"action_ref must be str, got {type(value).__name__}"
        )
    if not _HEX64_RE.match(value):
        raise TransactionalError(
            "action_ref must be a lowercase 64-character SHA-256 hex string"
        )
    return value


def _require_state(value: object) -> str:
    if not isinstance(value, str):
        raise TransactionalError(
            f"state must be str, got {type(value).__name__}"
        )
    if not value:
        raise TransactionalError("state must be a non-empty string")
    return value


def _require_int_ms(field: str, value: object) -> int:
    # Reject booleans explicitly (bool is subclass of int in Python).
    if isinstance(value, bool):
        raise TransactionalError(f"{field} must be int, got bool")
    if not isinstance(value, int):
        raise TransactionalError(
            f"{field} must be epoch-millisecond integer "
            f"(Substrate Rule 2), got {type(value).__name__}"
        )
    if value < 0:
        raise TransactionalError(
            f"{field} must be non-negative, got {value}"
        )
    return value


def transition_preimage(
    action_ref: str,
    state: str,
    transition_timestamp_ms: int,
    authority_verified_at_ms: int,
    revocation_check_at_ms: int,
) -> TransitionPreimage:
    """Return the validated preimage object for a single transition.

    The five-field shape is fixed at the substrate layer; the action_ref
    field cryptographically binds the transition to its action identity.
    """
    return TransitionPreimage(
        action_ref=_require_action_ref_hex(action_ref),
        state=_require_state(state),
        transition_timestamp_ms=_require_int_ms(
            "transition_timestamp_ms", transition_timestamp_ms
        ),
        authority_verified_at_ms=_require_int_ms(
            "authority_verified_at_ms", authority_verified_at_ms
        ),
        revocation_check_at_ms=_require_int_ms(
            "revocation_check_at_ms", revocation_check_at_ms
        ),
    )


def transition_hash(
    action_ref: str,
    state: str,
    transition_timestamp_ms: int,
    authority_verified_at_ms: int,
    revocation_check_at_ms: int,
) -> str:
    """Return the lowercase hex SHA-256 transition_hash.

    transition_hash = SHA-256(JCS({action_ref, state,
                                   transition_timestamp_ms,
                                   authority_verified_at_ms,
                                   revocation_check_at_ms}))
    """
    obj = transition_preimage(
        action_ref,
        state,
        transition_timestamp_ms,
        authority_verified_at_ms,
        revocation_check_at_ms,
    )
    return sha256_jcs(dict(obj))


def build_transactional_action_chain(
    agent_id: str,
    action_type: str,
    scope: str,
    timestamp_ms: int,
    transitions: list[TransitionInput],
) -> TransactionalChain:
    """Build a transactional action chain.

    Returns the chain shape:
        {
            "action_ref": "<lowercase 64-char hex>",
            "transitions": [
                {
                    "state": "<non-empty string>",
                    "transition_timestamp_ms": <int>,
                    "authority_verified_at_ms": <int>,
                    "revocation_check_at_ms": <int>,
                    "transition_hash": "<lowercase 64-char hex>",
                },
                ...
            ],
        }

    The action_ref is computed once from the four-field identity preimage
    (agent_id, action_type, scope, timestamp_ms) and is byte-stable across
    every transition. Each transition_hash is computed from the five-field
    transition preimage including the action_ref.

    Transitions are processed in the order supplied; the substrate does
    not impose a global ordering on state names. Callers that need a
    specific lifecycle ordering (authorisation -> settlement -> refund)
    are responsible for supplying the transitions in that order; the
    substrate verifies determinism, not lifecycle semantics.
    """
    if not isinstance(transitions, list):
        raise TransactionalError(
            f"transitions must be list, got {type(transitions).__name__}"
        )
    if not transitions:
        raise TransactionalError("transitions list must be non-empty")

    ar = _action_ref(agent_id, action_type, scope, timestamp_ms)

    records: list[TransitionRecord] = []
    for i, t in enumerate(transitions):
        if not isinstance(t, dict):
            raise TransactionalError(
                f"transitions[{i}] must be dict, got {type(t).__name__}"
            )
        try:
            state = t["state"]
            tts = t["transition_timestamp_ms"]
            avs = t["authority_verified_at_ms"]
            rcs = t["revocation_check_at_ms"]
        except KeyError as e:
            raise TransactionalError(
                f"transitions[{i}] missing required field {e.args[0]!r}"
            ) from e

        th = transition_hash(ar, state, tts, avs, rcs)
        records.append(
            TransitionRecord(
                state=state,
                transition_timestamp_ms=tts,
                authority_verified_at_ms=avs,
                revocation_check_at_ms=rcs,
                transition_hash=th,
            )
        )

    return TransactionalChain(action_ref=ar, transitions=records)
