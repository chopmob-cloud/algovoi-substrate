/**
 * action_ref atomic primitive.
 *
 * action_ref = SHA-256(JCS({agent_id, action_type, scope, timestamp_ms}))
 *
 * The action_ref is the AlgoVoi-authored canonical action identifier used
 * across the substrate. Two emitters describing the same logical action
 * produce the same action_ref by construction.
 *
 * - timestamp_ms is enforced as an epoch-millisecond integer per Substrate
 *   Rule 1. Float, ISO 8601 strings, and negative values are rejected.
 * - agent_id, action_type, scope are required non-empty strings.
 * - The preimage shape is fixed at exactly these four fields.
 */

import { sha256Jcs } from './canonicalize.js';

export class ActionRefError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ActionRefError';
  }
}

export interface ActionRefObject {
  agent_id: string;
  action_type: string;
  scope: string;
  timestamp_ms: number;
}

function requireString(field: string, value: unknown): string {
  if (typeof value !== 'string') {
    throw new ActionRefError(`${field} must be string, got ${typeof value}`);
  }
  if (value.length === 0) {
    throw new ActionRefError(`${field} must be a non-empty string`);
  }
  return value;
}

function requireIntTimestampMs(value: unknown): number {
  if (typeof value !== 'number') {
    throw new ActionRefError(
      `timestamp_ms must be epoch-millisecond integer (Substrate Rule 1), got ${typeof value}`,
    );
  }
  if (!Number.isFinite(value)) {
    throw new ActionRefError(
      `timestamp_ms must be a finite number, got ${value}`,
    );
  }
  if (!Number.isInteger(value)) {
    throw new ActionRefError(
      `timestamp_ms must be epoch-millisecond integer (Substrate Rule 1), got float ${value}`,
    );
  }
  if (value < 0) {
    throw new ActionRefError(`timestamp_ms must be non-negative, got ${value}`);
  }
  return value;
}

export interface ActionRefInput {
  agent_id: string;
  action_type: string;
  scope: string;
  timestamp_ms: number;
}

/**
 * Return the validated preimage object for action_ref.
 *
 * The four-field shape is fixed by the substrate; extending it produces
 * a different primitive, not a different action_ref.
 */
export function actionRefObject(input: ActionRefInput): ActionRefObject {
  return {
    agent_id: requireString('agent_id', input.agent_id),
    action_type: requireString('action_type', input.action_type),
    scope: requireString('scope', input.scope),
    timestamp_ms: requireIntTimestampMs(input.timestamp_ms),
  };
}

/**
 * Return the lowercase hex SHA-256 action_ref.
 *
 * action_ref = SHA-256(JCS({agent_id, action_type, scope, timestamp_ms}))
 *
 * Output is plain hex (no algorithm prefix).
 */
export function actionRef(input: ActionRefInput): string {
  const obj = actionRefObject(input);
  return sha256Jcs(obj);
}
