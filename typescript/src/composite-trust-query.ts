/**
 * Composite trust-query algorithm (PR #2440 in x402-foundation/x402).
 *
 * composite_hash = SHA-256(JCS([emitter_rows sorted by source_id, sig excluded]))
 *
 * Aggregates trust evidence from multiple emitters into a single canonical
 * hash. Properties:
 * - Row ordering invariance (sort-by-source_id).
 * - Set semantics (subset rows produce a distinct hash).
 * - Signature exclusion (sig field dropped before serialisation).
 *
 * 5-implementation cross-validation:
 * https://gist.github.com/chopmob-cloud/f2e9f0877b7d9fff70c8eca46e4ce636
 */

import { sha256Jcs } from './canonicalize.js';

export class CompositeTrustQueryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CompositeTrustQueryError';
  }
}

export interface EmitterRow {
  source_id: string;
  // Arbitrary additional fields (score, tier, jurisdictions, etc.)
  [key: string]: unknown;
  // sig is optional; when present it is stripped before hashing.
  sig?: unknown;
}

function stripSig(row: Record<string, unknown>): Record<string, unknown> {
  const { sig, ...rest } = row;
  void sig;
  return rest;
}

function requireSourceId(row: Record<string, unknown>): string {
  const src = row['source_id'];
  if (typeof src !== 'string' || src.length === 0) {
    throw new CompositeTrustQueryError(
      'every emitter row must carry a non-empty string source_id',
    );
  }
  return src;
}

/**
 * Return the lowercase hex composite_hash for a set of emitter rows.
 *
 * Steps (per PR #2440 §composite-hash):
 *   1. Strip the sig field from each row.
 *   2. Sort rows by source_id (lexicographic).
 *   3. JCS-canonicalise the resulting array.
 *   4. SHA-256 the canonical bytes.
 *
 * Output is plain hex without an algorithm prefix.
 */
export function compositeTrustQueryHash(rows: readonly EmitterRow[]): string {
  if (rows.length === 0) {
    throw new CompositeTrustQueryError(
      'composite trust-query requires at least one emitter row',
    );
  }

  const stripped: Record<string, unknown>[] = [];
  for (const row of rows) {
    if (row === null || typeof row !== 'object' || Array.isArray(row)) {
      throw new CompositeTrustQueryError(
        `emitter row must be an object, got ${Array.isArray(row) ? 'array' : typeof row}`,
      );
    }
    requireSourceId(row as Record<string, unknown>);
    stripped.push(stripSig(row as Record<string, unknown>));
  }

  stripped.sort((a, b) => {
    const sa = a['source_id'] as string;
    const sb = b['source_id'] as string;
    return sa < sb ? -1 : sa > sb ? 1 : 0;
  });
  return sha256Jcs(stripped);
}
