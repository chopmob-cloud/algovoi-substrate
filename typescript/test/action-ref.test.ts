import { describe, it, expect } from 'vitest';
import { ActionRefError, actionRef, actionRefObject } from '../src/action-ref.js';
import { sha256Jcs } from '../src/canonicalize.js';

describe('actionRefObject', () => {
  it('builds the canonical four-field shape', () => {
    expect(
      actionRefObject({
        agent_id: 'agent-x',
        action_type: 'payment',
        scope: 'bilateral',
        timestamp_ms: 1716460800000,
      }),
    ).toEqual({
      agent_id: 'agent-x',
      action_type: 'payment',
      scope: 'bilateral',
      timestamp_ms: 1716460800000,
    });
  });

  it('rejects non-string agent_id', () => {
    expect(() =>
      actionRefObject({
        agent_id: 123 as unknown as string,
        action_type: 'p',
        scope: 's',
        timestamp_ms: 0,
      }),
    ).toThrow(ActionRefError);
  });

  it('rejects empty string', () => {
    expect(() =>
      actionRefObject({
        agent_id: '',
        action_type: 'p',
        scope: 's',
        timestamp_ms: 0,
      }),
    ).toThrow(/non-empty/);
  });

  it('rejects float timestamp (Substrate Rule 1)', () => {
    expect(() =>
      actionRefObject({
        agent_id: 'a',
        action_type: 'p',
        scope: 's',
        timestamp_ms: 1716460800000.5,
      }),
    ).toThrow(/Substrate Rule 1/);
  });

  it('rejects negative timestamp', () => {
    expect(() =>
      actionRefObject({
        agent_id: 'a',
        action_type: 'p',
        scope: 's',
        timestamp_ms: -1,
      }),
    ).toThrow(/non-negative/);
  });

  it('accepts zero timestamp', () => {
    expect(
      actionRefObject({
        agent_id: 'a',
        action_type: 'p',
        scope: 's',
        timestamp_ms: 0,
      }).timestamp_ms,
    ).toBe(0);
  });
});

describe('actionRef', () => {
  it('matches SHA-256(JCS(preimage))', () => {
    const ref = actionRef({
      agent_id: 'agent-x',
      action_type: 'payment',
      scope: 'bilateral',
      timestamp_ms: 1716460800000,
    });
    const expected = sha256Jcs({
      agent_id: 'agent-x',
      action_type: 'payment',
      scope: 'bilateral',
      timestamp_ms: 1716460800000,
    });
    expect(ref).toBe(expected);
  });

  it('distinct inputs produce distinct refs', () => {
    const a = actionRef({
      agent_id: 'agent-x',
      action_type: 'payment',
      scope: 'bilateral',
      timestamp_ms: 1716460800000,
    });
    const b = actionRef({
      agent_id: 'agent-x',
      action_type: 'payment',
      scope: 'bilateral',
      timestamp_ms: 1716460800001,
    });
    expect(a).not.toBe(b);
  });

  it('is deterministic', () => {
    const input = {
      agent_id: 'agent-x',
      action_type: 'payment',
      scope: 'bilateral',
      timestamp_ms: 1716460800000,
    };
    expect(actionRef(input)).toBe(actionRef(input));
  });
});
