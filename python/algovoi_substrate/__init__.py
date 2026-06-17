"""
algovoi-substrate -- AlgoVoi agentic-payments substrate reference implementation.

This package provides the AlgoVoi-authored primitives that compose the substrate
underneath x402, AP2, A2A, and MPP agentic-payment flows:

- JCS RFC 8785 canonicalisation with the AlgoVoi-discipline rules
  (type-validation pre-canonicalisation, in-band canon_version pin).
- action_ref atomic primitive:
  SHA-256(JCS({agent_id, action_type, scope, timestamp_ms})).
- Composite trust-query algorithm (PR #2440 in x402-foundation/x402).
- Compliance receipt shape matching AlgoVoi's production /compliance/screen
  emission.
- Audit chain primitive: monotonic per-row hash chain with content_hash +
  prev_hash linking, year-five auditability under canon_version pin.

Substrate is cross-validated byte-for-byte across five JCS implementations
(Python rfc8785, JavaScript canonicalize, Go gowebpki/jcs, Java cyberphone,
Rust serde_jcs) against 53 conformance vectors and 3 composite-trust-query
vectors. See https://gist.github.com/chopmob-cloud/b327814c4e17ed9fc7b4f29c8bda523c

The substrate runs in production at https://api.algovoi.co.uk/compliance.

Licensed under Apache 2.0.
"""

from algovoi_substrate.canonicalize import (
    CANON_VERSION,
    CanonicalizationError,
    canonicalize,
    canonicalize_bytes,
    sha256_jcs,
)
from algovoi_substrate.action_ref import (
    ActionRefError,
    action_ref,
    action_ref_object,
)
from algovoi_substrate.composite_trust_query import (
    CompositeTrustQueryError,
    composite_trust_query_hash,
)
from algovoi_substrate.compliance_receipt import (
    SCREEN_RESULTS,
    ComplianceReceipt,
    ComplianceReceiptError,
    build_compliance_receipt,
)
from algovoi_substrate.audit_chain import (
    AuditChainError,
    AuditChainRow,
    append_to_chain,
    verify_audit_chain,
)
from algovoi_substrate.transactional import (
    TransactionalChain,
    TransactionalError,
    TransitionInput,
    TransitionPreimage,
    TransitionRecord,
    build_transactional_action_chain,
    transition_hash,
    transition_preimage,
)
from algovoi_substrate.settlement_binding import (
    SettlementBindingError,
    SettlementBindingPreimage,
    settlement_action_binding,
    settlement_binding_preimage,
)

__all__ = [
    # canonicalize
    "CANON_VERSION",
    "CanonicalizationError",
    "canonicalize",
    "canonicalize_bytes",
    "sha256_jcs",
    # action_ref
    "ActionRefError",
    "action_ref",
    "action_ref_object",
    # composite_trust_query
    "CompositeTrustQueryError",
    "composite_trust_query_hash",
    # compliance_receipt
    "SCREEN_RESULTS",
    "ComplianceReceipt",
    "ComplianceReceiptError",
    "build_compliance_receipt",
    # audit_chain
    "AuditChainError",
    "AuditChainRow",
    "append_to_chain",
    "verify_audit_chain",
    # transactional
    "TransactionalChain",
    "TransactionalError",
    "TransitionInput",
    "TransitionPreimage",
    "TransitionRecord",
    "build_transactional_action_chain",
    "transition_hash",
    "transition_preimage",
    # settlement_binding
    "SettlementBindingError",
    "SettlementBindingPreimage",
    "settlement_action_binding",
    "settlement_binding_preimage",
]

__version__ = "0.4.0"
