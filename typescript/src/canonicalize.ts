/**
 * JCS RFC 8785 canonicalisation with the AlgoVoi-discipline rules.
 *
 * The canonicalisation discipline is the shared normative substrate for
 * x402, AP2, A2A, and MPP receipts, authored by AlgoVoi and proposed in PR #2453 in
 * x402-foundation/x402 (sole AlgoVoi authorship; replaces closed PR #2436). This module
 * wraps the `canonicalize` npm package (v3.0.0) with the discipline's
 * pre-canonicalisation rules.
 *
 * Reference matrix: https://gist.github.com/chopmob-cloud/b327814c4e17ed9fc7b4f29c8bda523c
 */

import canonicalizeLib from 'canonicalize';
import { createHash } from 'node:crypto';

/**
 * Pin the discipline version. Receipts emitted under this substrate carry
 * this string in their canon_version field so a year-five verifier can pick
 * the correct re-canonicalisation rule from the retained bytes alone.
 */
export const CANON_VERSION = 'jcs-rfc8785-v1' as const;

export class CanonicalizationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CanonicalizationError';
  }
}

/**
 * Walk obj and enforce AlgoVoi-discipline pre-canonicalisation type rules:
 * - object keys must be strings
 * - only JSON-canonicalisable types are accepted (null, boolean, number,
 *   string, array, plain object)
 *
 * Strict-integer-fields enforcement (timestamp_ms etc.) is done at the
 * per-schema layer rather than universally here.
 */
function validateTypes(obj: unknown, path = '$'): void {
  if (obj === null) return;
  if (typeof obj === 'boolean') return;
  if (typeof obj === 'number') return;
  if (typeof obj === 'string') return;
  if (Array.isArray(obj)) {
    for (let i = 0; i < obj.length; i++) {
      validateTypes(obj[i], `${path}[${i}]`);
    }
    return;
  }
  if (typeof obj === 'object') {
    for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
      // Object.entries always yields string keys; this guard is for safety
      // around prototype-pollution edge cases in user-supplied objects.
      if (typeof k !== 'string') {
        throw new CanonicalizationError(
          `non-string object key at ${path}: ${typeof k}`,
        );
      }
      validateTypes(v, `${path}.${k}`);
    }
    return;
  }
  throw new CanonicalizationError(
    `non-canonicalisable type at ${path}: ${typeof obj}`,
  );
}

/**
 * Return the canonical JCS string representation of obj.
 *
 * Applies AlgoVoi-discipline pre-canonicalisation type validation, then
 * delegates to canonicalize (RFC 8785) for the canonical bytes.
 *
 * Throws CanonicalizationError on type-validation failure.
 */
export function canonicalize(obj: unknown): string {
  validateTypes(obj);
  const out = canonicalizeLib(obj);
  if (out === undefined) {
    // canonicalize() returns undefined for values that JSON.stringify would
    // also drop (e.g. functions, undefined values at the root). The
    // discipline does not allow those at any level; this is belt-and-braces.
    throw new CanonicalizationError(
      'object is not JCS-canonicalisable (canonicalize returned undefined)',
    );
  }
  return out;
}

/**
 * Return the canonical JCS UTF-8 bytes of obj as a Uint8Array.
 */
export function canonicalizeBytes(obj: unknown): Uint8Array {
  return new TextEncoder().encode(canonicalize(obj));
}

/**
 * Return the lowercase hex SHA-256 of the JCS canonical bytes of obj.
 *
 * This is the substrate primitive used by action_ref, compliance receipts,
 * audit chain entries, and the composite trust-query algorithm. The string
 * is plain hex without an algorithm prefix.
 */
export function sha256Jcs(obj: unknown): string {
  return createHash('sha256').update(canonicalize(obj)).digest('hex');
}
