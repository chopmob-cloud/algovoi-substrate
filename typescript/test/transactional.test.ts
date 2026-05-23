/**
 * Tests for the transactional action_ref lifecycle primitive.
 *
 * Mirrors python/tests/test_transactional.py byte-for-byte so the
 * cross-impl conformance vector set produces identical digests.
 */

import { describe, expect, it } from 'vitest';

import {
  TransactionalError,
  actionRef,
  buildTransactionalActionChain,
  transitionHash,
} from '../src/index.js';

// Fixed identity preimage used across the suite.
const AGENT_ID = 'agent_alpha';
const ACTION_TYPE = 'payment';
const SCOPE = 'vauban:stark_settlement';
const TIMESTAMP_MS = 1716494400000;

function fixedActionRef(): string {
  return actionRef({
    agent_id: AGENT_ID,
    action_type: ACTION_TYPE,
    scope: SCOPE,
    timestamp_ms: TIMESTAMP_MS,
  });
}

describe('transitionHash', () => {
  it('is deterministic for identical preimage', () => {
    const ar = fixedActionRef();
    const a = transitionHash({
      action_ref: ar,
      state: 'authorisation',
      transition_timestamp_ms: 1716494400000,
      authority_verified_at_ms: 1716494400500,
      revocation_check_at_ms: 1716494400800,
    });
    const b = transitionHash({
      action_ref: ar,
      state: 'authorisation',
      transition_timestamp_ms: 1716494400000,
      authority_verified_at_ms: 1716494400500,
      revocation_check_at_ms: 1716494400800,
    });
    expect(a).toBe(b);
  });

  it('differs per state with otherwise identical inputs', () => {
    const ar = fixedActionRef();
    const common = {
      transition_timestamp_ms: 1716494400000,
      authority_verified_at_ms: 1716494400500,
      revocation_check_at_ms: 1716494400800,
    };
    const auth = transitionHash({ ...common, action_ref: ar, state: 'authorisation' });
    const settle = transitionHash({ ...common, action_ref: ar, state: 'settlement' });
    const refund = transitionHash({ ...common, action_ref: ar, state: 'refund' });
    expect(new Set([auth, settle, refund]).size).toBe(3);
  });

  it('is bound to action_ref (different action_ref => different digest)', () => {
    const ar1 = fixedActionRef();
    const ar2 = actionRef({
      agent_id: 'agent_beta',
      action_type: ACTION_TYPE,
      scope: SCOPE,
      timestamp_ms: TIMESTAMP_MS,
    });
    expect(ar1).not.toBe(ar2);
    const common = {
      state: 'settlement',
      transition_timestamp_ms: 1716494400000,
      authority_verified_at_ms: 1716494400500,
      revocation_check_at_ms: 1716494400800,
    };
    const t1 = transitionHash({ ...common, action_ref: ar1 });
    const t2 = transitionHash({ ...common, action_ref: ar2 });
    expect(t1).not.toBe(t2);
  });

  it('is byte-distinct from action_ref', () => {
    const ar = fixedActionRef();
    const th = transitionHash({
      action_ref: ar,
      state: 'authorisation',
      transition_timestamp_ms: 1716494400000,
      authority_verified_at_ms: 1716494400500,
      revocation_check_at_ms: 1716494400800,
    });
    expect(th).not.toBe(ar);
  });

  it('rejects RFC 3339 string for transition_timestamp_ms', () => {
    expect(() =>
      transitionHash({
        action_ref: fixedActionRef(),
        state: 'authorisation',
        transition_timestamp_ms: '2024-05-23T20:00:00Z' as unknown as number,
        authority_verified_at_ms: 1,
        revocation_check_at_ms: 1,
      }),
    ).toThrow(TransactionalError);
  });

  it('rejects float timestamp', () => {
    expect(() =>
      transitionHash({
        action_ref: fixedActionRef(),
        state: 'authorisation',
        transition_timestamp_ms: 1.5,
        authority_verified_at_ms: 1,
        revocation_check_at_ms: 1,
      }),
    ).toThrow(TransactionalError);
  });

  it('rejects negative timestamp', () => {
    expect(() =>
      transitionHash({
        action_ref: fixedActionRef(),
        state: 'authorisation',
        transition_timestamp_ms: -1,
        authority_verified_at_ms: 1,
        revocation_check_at_ms: 1,
      }),
    ).toThrow(TransactionalError);
  });

  it('rejects malformed action_ref hex', () => {
    expect(() =>
      transitionHash({
        action_ref: 'not-a-hash',
        state: 'authorisation',
        transition_timestamp_ms: 1,
        authority_verified_at_ms: 1,
        revocation_check_at_ms: 1,
      }),
    ).toThrow(TransactionalError);
  });

  it('rejects uppercase action_ref hex', () => {
    expect(() =>
      transitionHash({
        action_ref: fixedActionRef().toUpperCase(),
        state: 'authorisation',
        transition_timestamp_ms: 1,
        authority_verified_at_ms: 1,
        revocation_check_at_ms: 1,
      }),
    ).toThrow(TransactionalError);
  });

  it('rejects empty state', () => {
    expect(() =>
      transitionHash({
        action_ref: fixedActionRef(),
        state: '',
        transition_timestamp_ms: 1,
        authority_verified_at_ms: 1,
        revocation_check_at_ms: 1,
      }),
    ).toThrow(TransactionalError);
  });
});

describe('buildTransactionalActionChain', () => {
  it('builds a three-state payment lifecycle chain', () => {
    const chain = buildTransactionalActionChain({
      agent_id: AGENT_ID,
      action_type: ACTION_TYPE,
      scope: SCOPE,
      timestamp_ms: TIMESTAMP_MS,
      transitions: [
        {
          state: 'authorisation',
          transition_timestamp_ms: 1716494400000,
          authority_verified_at_ms: 1716494400500,
          revocation_check_at_ms: 1716494400800,
        },
        {
          state: 'settlement',
          transition_timestamp_ms: 1716494500000,
          authority_verified_at_ms: 1716494500300,
          revocation_check_at_ms: 1716494500500,
        },
        {
          state: 'refund',
          transition_timestamp_ms: 1716494600000,
          authority_verified_at_ms: 1716494600300,
          revocation_check_at_ms: 1716494600500,
        },
      ],
    });

    expect(chain.action_ref).toBe(fixedActionRef());
    expect(chain.transitions).toHaveLength(3);
    const hashes = new Set(chain.transitions.map((t) => t.transition_hash));
    expect(hashes.size).toBe(3);
    expect(hashes.has(chain.action_ref)).toBe(false);
  });

  it('keeps action_ref stable across different transition sets', () => {
    const transitions = [
      {
        state: 'authorisation',
        transition_timestamp_ms: 1716494400000,
        authority_verified_at_ms: 1716494400500,
        revocation_check_at_ms: 1716494400800,
      },
    ];
    const a = buildTransactionalActionChain({
      agent_id: AGENT_ID,
      action_type: ACTION_TYPE,
      scope: SCOPE,
      timestamp_ms: TIMESTAMP_MS,
      transitions,
    });
    const b = buildTransactionalActionChain({
      agent_id: AGENT_ID,
      action_type: ACTION_TYPE,
      scope: SCOPE,
      timestamp_ms: TIMESTAMP_MS,
      transitions: [
        {
          state: 'authorisation',
          transition_timestamp_ms: 9999999999999,
          authority_verified_at_ms: 9999999999998,
          revocation_check_at_ms: 9999999999997,
        },
      ],
    });
    expect(a.action_ref).toBe(b.action_ref);
  });

  it('rejects empty transitions array', () => {
    expect(() =>
      buildTransactionalActionChain({
        agent_id: AGENT_ID,
        action_type: ACTION_TYPE,
        scope: SCOPE,
        timestamp_ms: TIMESTAMP_MS,
        transitions: [],
      }),
    ).toThrow(TransactionalError);
  });

  it('rejects non-array transitions', () => {
    expect(() =>
      buildTransactionalActionChain({
        agent_id: AGENT_ID,
        action_type: ACTION_TYPE,
        scope: SCOPE,
        timestamp_ms: TIMESTAMP_MS,
        transitions: { state: 'x' } as unknown as never,
      }),
    ).toThrow(TransactionalError);
  });

  it('rejects transition missing a required field', () => {
    expect(() =>
      buildTransactionalActionChain({
        agent_id: AGENT_ID,
        action_type: ACTION_TYPE,
        scope: SCOPE,
        timestamp_ms: TIMESTAMP_MS,
        transitions: [
          {
            state: 'authorisation',
            transition_timestamp_ms: 1,
            // authority_verified_at_ms intentionally missing
            revocation_check_at_ms: 1,
          } as unknown as never,
        ],
      }),
    ).toThrow(TransactionalError);
  });

  it('accepts non-payment-lifecycle state vocabularies (free-form)', () => {
    const chain = buildTransactionalActionChain({
      agent_id: AGENT_ID,
      action_type: ACTION_TYPE,
      scope: SCOPE,
      timestamp_ms: TIMESTAMP_MS,
      transitions: [
        {
          state: 'issuance',
          transition_timestamp_ms: 1,
          authority_verified_at_ms: 1,
          revocation_check_at_ms: 1,
        },
        {
          state: 'execution',
          transition_timestamp_ms: 2,
          authority_verified_at_ms: 2,
          revocation_check_at_ms: 2,
        },
        {
          state: 'custom:emitter_specific_state',
          transition_timestamp_ms: 3,
          authority_verified_at_ms: 3,
          revocation_check_at_ms: 3,
        },
      ],
    });
    expect(chain.transitions).toHaveLength(3);
  });
});
