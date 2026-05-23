"""
action_ref atomic primitive.

action_ref = SHA-256(JCS({agent_id, action_type, scope, timestamp_ms}))

The action_ref is the AlgoVoi-authored canonical action identifier used
across the substrate: bilateral receipts, CTEF claims, audit chain rows,
composite trust queries. Two emitters describing the same logical action
produce the same action_ref by construction, allowing independent verifiers
to correlate receipts without relying on any registry.

Properties:
- timestamp_ms is enforced as an epoch-millisecond integer per Substrate
  Rule 1. Float, ISO 8601 strings, and negative values are rejected.
- agent_id, action_type, scope are required non-empty strings.
- The preimage shape is fixed at exactly these four fields; extension
  fields go into outer envelopes that reference the action_ref, not into
  the preimage itself.
"""

from __future__ import annotations

from typing import TypedDict

from algovoi_substrate.canonicalize import sha256_jcs


class ActionRefError(ValueError):
    """Raised when action_ref inputs violate the substrate discipline."""


class ActionRefObject(TypedDict):
    agent_id: str
    action_type: str
    scope: str
    timestamp_ms: int


def _require_str(field: str, value: object) -> str:
    if not isinstance(value, str):
        raise ActionRefError(
            f"{field} must be str, got {type(value).__name__}"
        )
    if not value:
        raise ActionRefError(f"{field} must be a non-empty string")
    return value


def _require_int_timestamp_ms(value: object) -> int:
    # Reject booleans explicitly (bool is subclass of int in Python).
    if isinstance(value, bool):
        raise ActionRefError("timestamp_ms must be int, got bool")
    if not isinstance(value, int):
        raise ActionRefError(
            f"timestamp_ms must be epoch-millisecond integer "
            f"(Substrate Rule 1), got {type(value).__name__}"
        )
    if value < 0:
        raise ActionRefError(
            f"timestamp_ms must be non-negative, got {value}"
        )
    return value


def action_ref_object(
    agent_id: str,
    action_type: str,
    scope: str,
    timestamp_ms: int,
) -> ActionRefObject:
    """Return the validated preimage object for action_ref.

    The four-field shape is fixed by the substrate; extending it produces
    a different primitive, not a different action_ref. Validation rejects
    non-string identifiers and non-integer timestamps eagerly.
    """
    return ActionRefObject(
        agent_id=_require_str("agent_id", agent_id),
        action_type=_require_str("action_type", action_type),
        scope=_require_str("scope", scope),
        timestamp_ms=_require_int_timestamp_ms(timestamp_ms),
    )


def action_ref(
    agent_id: str,
    action_type: str,
    scope: str,
    timestamp_ms: int,
) -> str:
    """Return the lowercase hex SHA-256 action_ref.

    action_ref = SHA-256(JCS({agent_id, action_type, scope, timestamp_ms}))

    Output is plain hex (no algorithm prefix). Callers that need
    "sha256:<hex>" form should prepend that prefix.
    """
    obj = action_ref_object(agent_id, action_type, scope, timestamp_ms)
    # mypy/pyright won't see TypedDict as Any-compatible; cast at call site.
    return sha256_jcs(dict(obj))
