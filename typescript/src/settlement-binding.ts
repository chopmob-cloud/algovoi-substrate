// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud)
/**
 * Settlement-action binding (non-normative substrate extension).
 *
 * An x402/AP2/A2A settlement attestation proves a *payment* occurred. It does
 * not, on its own, prove *which verified agent action* the payment corresponds
 * to, nor that the correspondence is recorded in a tamper-evident chain. This
 * module closes that post-settlement accountability gap with a single canonical
 * reference binding four already-published substrate artifacts into one record:
 *
 *   binding_ref = "sha256:" + SHA-256(JCS({
 *       action_ref,            // the verified agent-action identity
 *       transition_hash,       // the COMMITTED lifecycle transition (the "once")
 *       settlement_ref,        // the settlement attestation content_hash
 *       retention_chain_ref,   // the tamper-evident chain position recording it
 *   }))
 *
 * No new hashing primitive is introduced: the binding is the substrate's
 * existing JCS + SHA-256 over the four references. Because action_ref and
 * transition_hash are themselves computed from epoch-millisecond-integer
 * preimages (Substrate Rule 2), any upstream RFC 3339 string timestamp produces
 * a different action_ref, hence a different binding -- a non-conformant lineage
 * cannot reproduce the binding bytes.
 *
 * The output carries the "sha256:" algorithm prefix, consistent with
 * retention_chain_ref, signalling a content-addressed reference.
 */

import { sha256Jcs } from './canonicalize.js';

const HEX64_RE = /^[0-9a-f]{64}$/;
const SHA256_REF_RE = /^sha256:[0-9a-f]{64}$/;

export class SettlementBindingError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SettlementBindingError';
  }
}

export interface SettlementBindingPreimage {
  action_ref: string;
  transition_hash: string;
  settlement_ref: string;
  retention_chain_ref: string;
}

function requireHex64(field: string, value: unknown): string {
  if (typeof value !== 'string') {
    throw new SettlementBindingError(
      `${field} must be string, got ${typeof value}`,
    );
  }
  if (!HEX64_RE.test(value)) {
    throw new SettlementBindingError(
      `${field} must be a lowercase 64-character SHA-256 hex string`,
    );
  }
  return value;
}

function requireChainRef(value: unknown): string {
  if (typeof value !== 'string') {
    throw new SettlementBindingError(
      `retention_chain_ref must be string, got ${typeof value}`,
    );
  }
  if (!SHA256_REF_RE.test(value)) {
    throw new SettlementBindingError(
      "retention_chain_ref must be of the form 'sha256:<lowercase 64-char hex>'",
    );
  }
  return value;
}

/**
 * Return the validated four-field binding preimage object.
 *
 * The shape is fixed at the substrate layer; each field cryptographically
 * contributes to the binding so that no one component can be substituted
 * without changing the binding_ref.
 */
export function settlementBindingPreimage(input: {
  action_ref: string;
  transition_hash: string;
  settlement_ref: string;
  retention_chain_ref: string;
}): SettlementBindingPreimage {
  return {
    action_ref: requireHex64('action_ref', input.action_ref),
    transition_hash: requireHex64('transition_hash', input.transition_hash),
    settlement_ref: requireHex64('settlement_ref', input.settlement_ref),
    retention_chain_ref: requireChainRef(input.retention_chain_ref),
  };
}

/**
 * Return the binding_ref as a "sha256:"-prefixed content-addressed reference.
 *
 * binding_ref = "sha256:" + SHA-256(JCS({action_ref, transition_hash,
 *                                        settlement_ref, retention_chain_ref}))
 */
export function settlementActionBinding(input: {
  action_ref: string;
  transition_hash: string;
  settlement_ref: string;
  retention_chain_ref: string;
}): string {
  const obj = settlementBindingPreimage(input);
  return `sha256:${sha256Jcs(obj)}`;
}
