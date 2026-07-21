# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud)
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
from algovoi_substrate.caip import (
    REGISTERED_NAMESPACES,
    CaipError,
    caip10_of,
    caip19_slip44,
    is_caip2,
    is_caip10,
    is_caip19,
    is_registered_caip2,
    is_registered_caip10,
    is_registered_caip19,
    is_registered_namespace,
    is_valid_caip2,
    is_valid_caip10,
    is_valid_caip19,
    REFERENCE_FORMAT_NAMESPACES,
    registered_namespaces,
    require_caip2,
    require_caip10,
    require_caip19,
    require_registered_caip2,
    require_registered_caip10,
    require_registered_caip19,
    require_valid_caip2,
    require_valid_caip10,
    require_valid_caip19,
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
    # caip
    "REGISTERED_NAMESPACES",
    "CaipError",
    "caip10_of",
    "caip19_slip44",
    "is_caip2",
    "is_caip10",
    "is_caip19",
    "is_registered_caip2",
    "is_registered_caip10",
    "is_registered_caip19",
    "is_registered_namespace",
    "is_valid_caip2",
    "is_valid_caip10",
    "is_valid_caip19",
    "REFERENCE_FORMAT_NAMESPACES",
    "registered_namespaces",
    "require_caip2",
    "require_caip10",
    "require_caip19",
    "require_registered_caip2",
    "require_registered_caip10",
    "require_registered_caip19",
    "require_valid_caip2",
    "require_valid_caip10",
    "require_valid_caip19",
]

__version__ = "0.5.1"
