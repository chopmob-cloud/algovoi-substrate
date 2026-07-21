// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud)
/**
 * @algovoi/substrate
 *
 * AlgoVoi agentic-payments substrate reference implementation.
 *
 * - JCS RFC 8785 canonicalisation with the AlgoVoi-discipline rules
 *   (type-validation pre-canonicalisation, in-band canon_version pin).
 * - action_ref atomic primitive:
 *   SHA-256(JCS({agent_id, action_type, scope, timestamp_ms})).
 * - Composite trust-query algorithm (PR #2440 in x402-foundation/x402).
 * - Compliance receipt shape matching AlgoVoi's production
 *   /compliance/screen emission.
 * - Audit chain primitive: monotonic per-row hash chain with content_hash +
 *   prev_hash linking, year-five auditability under canon_version pin.
 *
 * The substrate runs in production at https://api.algovoi.co.uk/compliance.
 * Licensed under Apache 2.0.
 */

export {
  CANON_VERSION,
  CanonicalizationError,
  canonicalize,
  canonicalizeBytes,
  sha256Jcs,
} from './canonicalize.js';

export {
  ActionRefError,
  type ActionRefInput,
  type ActionRefObject,
  actionRef,
  actionRefObject,
} from './action-ref.js';

export {
  CompositeTrustQueryError,
  type EmitterRow,
  compositeTrustQueryHash,
} from './composite-trust-query.js';

export {
  SCREEN_RESULTS,
  type ScreenResult,
  ComplianceReceiptError,
  type ComplianceReceipt,
  type BuildComplianceReceiptInput,
  buildComplianceReceipt,
} from './compliance-receipt.js';

export {
  AuditChainError,
  type AuditChainRow,
  appendToChain,
  verifyAuditChain,
} from './audit-chain.js';

export {
  TransactionalError,
  type TransitionPreimage,
  type TransitionInput,
  type TransitionRecord,
  type TransactionalChain,
  type TransactionalChainInput,
  transitionPreimage,
  transitionHash,
  buildTransactionalActionChain,
} from './transactional.js';

export {
  SettlementBindingError,
  type SettlementBindingPreimage,
  settlementBindingPreimage,
  settlementActionBinding,
} from './settlement-binding.js';

export {
  CaipError,
  REGISTERED_NAMESPACES,
  isCaip2,
  isCaip10,
  isCaip19,
  requireCaip2,
  requireCaip10,
  requireCaip19,
  caip19Slip44,
  caip10Of,
  registeredNamespaces,
  isRegisteredNamespace,
  isRegisteredCaip2,
  isRegisteredCaip10,
  isRegisteredCaip19,
  requireRegisteredCaip2,
  requireRegisteredCaip10,
  requireRegisteredCaip19,
  REFERENCE_FORMAT_NAMESPACES,
  isValidCaip2,
  isValidCaip10,
  isValidCaip19,
  requireValidCaip2,
  requireValidCaip10,
  requireValidCaip19,
} from './caip.js';
