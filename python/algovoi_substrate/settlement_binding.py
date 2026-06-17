"""
Settlement-action binding (non-normative substrate extension).

An x402/AP2/A2A settlement attestation proves a *payment* occurred. It does
not, on its own, prove *which verified agent action* the payment corresponds
to, nor that the correspondence is recorded in a tamper-evident chain. This
module closes that post-settlement accountability gap with a single canonical
reference that binds four already-published substrate artifacts into one
record:

    binding_ref = "sha256:" + SHA-256(JCS({
        action_ref,            # the verified agent-action identity
        transition_hash,       # the COMMITTED lifecycle transition (the "once")
        settlement_ref,        # the settlement attestation content_hash
        retention_chain_ref,   # the tamper-evident chain position recording it
    }))

No new hashing primitive is introduced: the binding is the substrate's
existing JCS + SHA-256 over the four references. Because `action_ref` and
`transition_hash` are themselves computed from epoch-millisecond-integer
preimages (Substrate Rule 2), any upstream RFC 3339 string timestamp produces
a different `action_ref`, hence a different binding -- an implementation on a
non-conformant lineage cannot reproduce the binding bytes.

Substrate-level invariants:

1. Binding stability: identical (action_ref, transition_hash, settlement_ref,
   retention_chain_ref) reproduces the same binding_ref byte-for-byte.
2. Settlement-binding: changing settlement_ref changes binding_ref (a
   settlement cannot be re-pointed to another action's binding).
3. Action-binding: changing action_ref changes binding_ref (an action cannot
   claim another's settlement).
4. State-binding: changing transition_hash changes binding_ref -- only the
   exact COMMITTED transition binds; a PENDING/REVERSED transition_hash
   produces a distinct binding.
5. Chain-binding: changing retention_chain_ref changes binding_ref (the chain
   position recording the record is load-bearing).

The output carries the "sha256:" algorithm prefix, consistent with
`retention_chain_ref`, signalling a content-addressed reference.
"""

from __future__ import annotations

import re
from typing import TypedDict

from algovoi_substrate.canonicalize import sha256_jcs

# Lowercase 64-char SHA-256 hex digest (bare, no prefix).
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
# A retention_chain_ref is the bare digest with a "sha256:" algorithm prefix.
_SHA256_REF_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class SettlementBindingError(ValueError):
    """Raised when binding inputs violate the substrate discipline."""


class SettlementBindingPreimage(TypedDict):
    action_ref: str
    transition_hash: str
    settlement_ref: str
    retention_chain_ref: str


def _require_hex64(field: str, value: object) -> str:
    if not isinstance(value, str):
        raise SettlementBindingError(
            f"{field} must be str, got {type(value).__name__}"
        )
    if not _HEX64_RE.match(value):
        raise SettlementBindingError(
            f"{field} must be a lowercase 64-character SHA-256 hex string"
        )
    return value


def _require_chain_ref(value: object) -> str:
    if not isinstance(value, str):
        raise SettlementBindingError(
            f"retention_chain_ref must be str, got {type(value).__name__}"
        )
    if not _SHA256_REF_RE.match(value):
        raise SettlementBindingError(
            "retention_chain_ref must be of the form "
            "'sha256:<lowercase 64-char hex>'"
        )
    return value


def settlement_binding_preimage(
    action_ref: str,
    transition_hash: str,
    settlement_ref: str,
    retention_chain_ref: str,
) -> SettlementBindingPreimage:
    """Return the validated four-field binding preimage object.

    The shape is fixed at the substrate layer; each field cryptographically
    contributes to the binding so that no one component can be substituted
    without changing the binding_ref.
    """
    return SettlementBindingPreimage(
        action_ref=_require_hex64("action_ref", action_ref),
        transition_hash=_require_hex64("transition_hash", transition_hash),
        settlement_ref=_require_hex64("settlement_ref", settlement_ref),
        retention_chain_ref=_require_chain_ref(retention_chain_ref),
    )


def settlement_action_binding(
    action_ref: str,
    transition_hash: str,
    settlement_ref: str,
    retention_chain_ref: str,
) -> str:
    """Return the binding_ref as a "sha256:"-prefixed content-addressed reference.

    binding_ref = "sha256:" + SHA-256(JCS({action_ref, transition_hash,
                                           settlement_ref, retention_chain_ref}))
    """
    obj = settlement_binding_preimage(
        action_ref,
        transition_hash,
        settlement_ref,
        retention_chain_ref,
    )
    return "sha256:" + sha256_jcs(dict(obj))
