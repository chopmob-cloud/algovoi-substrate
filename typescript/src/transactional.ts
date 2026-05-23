/**
 * Transactional action_ref lifecycle (non-normative substrate extension).
 *
 * For actions that traverse multiple state transitions
 * (authorisation -> settlement -> refund; issuance -> execution ->
 * revocation; admission -> review -> close), the action_ref four-field
 * preimage is the STABLE identity anchor across the full lifecycle, and
 * per-transition lifecycle metadata sits OUTSIDE the action_ref preimage.
 *
 * Invariants:
 *
 * 1. action_ref is byte-stable across every transition of the same action.
 * 2. transition_hash is byte-stable for identical preimage tuples.
 * 3. transition_hash differs per state for the same action_ref + timestamps.
 * 4. action_ref and any transition_hash are byte-distinct.
 * 5. All timestamp fields MUST be epoch-millisecond integers per
 *    Substrate Rule 2. RFC 3339 string forms are rejected.
 *
 * State value is a non-empty string with no closed enum at the
 * canonicalisation layer, consistent with the scope-field treatment.
 */

import { actionRef } from './action-ref.js';
import { sha256Jcs } from './canonicalize.js';

const HEX64_RE = /^[0-9a-f]{64}$/;

export class TransactionalError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TransactionalError';
  }
}

export interface TransitionPreimage {
  action_ref: string;
  state: string;
  transition_timestamp_ms: number;
  authority_verified_at_ms: number;
  revocation_check_at_ms: number;
}

export interface TransitionInput {
  state: string;
  transition_timestamp_ms: number;
  authority_verified_at_ms: number;
  revocation_check_at_ms: number;
}

export interface TransitionRecord extends TransitionInput {
  transition_hash: string;
}

export interface TransactionalChain {
  action_ref: string;
  transitions: TransitionRecord[];
}

export interface TransactionalChainInput {
  agent_id: string;
  action_type: string;
  scope: string;
  timestamp_ms: number;
  transitions: TransitionInput[];
}

function requireActionRefHex(value: unknown): string {
  if (typeof value !== 'string') {
    throw new TransactionalError(
      `action_ref must be string, got ${typeof value}`,
    );
  }
  if (!HEX64_RE.test(value)) {
    throw new TransactionalError(
      'action_ref must be a lowercase 64-character SHA-256 hex string',
    );
  }
  return value;
}

function requireState(value: unknown): string {
  if (typeof value !== 'string') {
    throw new TransactionalError(`state must be string, got ${typeof value}`);
  }
  if (value.length === 0) {
    throw new TransactionalError('state must be a non-empty string');
  }
  return value;
}

function requireIntMs(field: string, value: unknown): number {
  if (typeof value !== 'number') {
    throw new TransactionalError(
      `${field} must be epoch-millisecond integer (Substrate Rule 2), got ${typeof value}`,
    );
  }
  if (!Number.isFinite(value)) {
    throw new TransactionalError(
      `${field} must be a finite number, got ${value}`,
    );
  }
  if (!Number.isInteger(value)) {
    throw new TransactionalError(
      `${field} must be epoch-millisecond integer (Substrate Rule 2), got float ${value}`,
    );
  }
  if (value < 0) {
    throw new TransactionalError(`${field} must be non-negative, got ${value}`);
  }
  return value;
}

/**
 * Return the validated preimage object for a single transition.
 *
 * The five-field shape is fixed at the substrate layer; the action_ref
 * field cryptographically binds the transition to its action identity.
 */
export function transitionPreimage(input: {
  action_ref: string;
  state: string;
  transition_timestamp_ms: number;
  authority_verified_at_ms: number;
  revocation_check_at_ms: number;
}): TransitionPreimage {
  return {
    action_ref: requireActionRefHex(input.action_ref),
    state: requireState(input.state),
    transition_timestamp_ms: requireIntMs(
      'transition_timestamp_ms',
      input.transition_timestamp_ms,
    ),
    authority_verified_at_ms: requireIntMs(
      'authority_verified_at_ms',
      input.authority_verified_at_ms,
    ),
    revocation_check_at_ms: requireIntMs(
      'revocation_check_at_ms',
      input.revocation_check_at_ms,
    ),
  };
}

/**
 * Return the lowercase hex SHA-256 transition_hash.
 *
 * transition_hash = SHA-256(JCS({action_ref, state,
 *                                transition_timestamp_ms,
 *                                authority_verified_at_ms,
 *                                revocation_check_at_ms}))
 */
export function transitionHash(input: {
  action_ref: string;
  state: string;
  transition_timestamp_ms: number;
  authority_verified_at_ms: number;
  revocation_check_at_ms: number;
}): string {
  const obj = transitionPreimage(input);
  return sha256Jcs(obj);
}

/**
 * Build a transactional action chain.
 *
 * Returns the chain shape:
 *     {
 *         action_ref: "<lowercase 64-char hex>",
 *         transitions: [
 *             {
 *                 state, transition_timestamp_ms,
 *                 authority_verified_at_ms, revocation_check_at_ms,
 *                 transition_hash
 *             },
 *             ...
 *         ]
 *     }
 *
 * The action_ref is computed once and is byte-stable across every
 * transition. Each transition_hash is bound to the action_ref by
 * including it in the transition preimage. Transitions are processed
 * in the order supplied; the substrate verifies determinism, not
 * lifecycle semantics.
 */
export function buildTransactionalActionChain(
  input: TransactionalChainInput,
): TransactionalChain {
  if (!Array.isArray(input.transitions)) {
    throw new TransactionalError('transitions must be an array');
  }
  if (input.transitions.length === 0) {
    throw new TransactionalError('transitions array must be non-empty');
  }

  const ar = actionRef({
    agent_id: input.agent_id,
    action_type: input.action_type,
    scope: input.scope,
    timestamp_ms: input.timestamp_ms,
  });

  const records: TransitionRecord[] = input.transitions.map((t, i) => {
    if (t === null || typeof t !== 'object') {
      throw new TransactionalError(
        `transitions[${i}] must be object, got ${typeof t}`,
      );
    }
    const required = [
      'state',
      'transition_timestamp_ms',
      'authority_verified_at_ms',
      'revocation_check_at_ms',
    ] as const;
    for (const k of required) {
      if (!(k in t)) {
        throw new TransactionalError(
          `transitions[${i}] missing required field '${k}'`,
        );
      }
    }
    const th = transitionHash({
      action_ref: ar,
      state: t.state,
      transition_timestamp_ms: t.transition_timestamp_ms,
      authority_verified_at_ms: t.authority_verified_at_ms,
      revocation_check_at_ms: t.revocation_check_at_ms,
    });
    return {
      state: t.state,
      transition_timestamp_ms: t.transition_timestamp_ms,
      authority_verified_at_ms: t.authority_verified_at_ms,
      revocation_check_at_ms: t.revocation_check_at_ms,
      transition_hash: th,
    };
  });

  return {
    action_ref: ar,
    transitions: records,
  };
}
