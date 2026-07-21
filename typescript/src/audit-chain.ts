// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud)
/**
 * Audit chain primitive: monotonic per-row hash chain.
 *
 * Each row carries:
 * - content_hash: SHA-256(JCS(payload))
 * - prev_hash: previous row's content_hash, or null for the head row
 * - chain_position: monotonically increasing integer starting at 0
 *
 * This is the structure AlgoVoi's production /compliance/attestation chain
 * exposes (Object Lock COMPLIANCE retention to 2033-05-04).
 */

import { sha256Jcs } from './canonicalize.js';

export class AuditChainError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuditChainError';
  }
}

export interface AuditChainRow {
  chain_position: number;
  content_hash: string;
  prev_hash: string | null;
  payload: unknown;
}

/**
 * Build the next row in an audit chain.
 *
 * If prevRow is null, the new row becomes the head (chain_position = 0,
 * prev_hash = null). Otherwise chain_position increments and prev_hash
 * links to prevRow.content_hash.
 */
export function appendToChain(
  payload: unknown,
  prevRow: AuditChainRow | null,
): AuditChainRow {
  let chainPosition: number;
  let prevHash: string | null;

  if (prevRow === null) {
    chainPosition = 0;
    prevHash = null;
  } else {
    if (
      typeof prevRow.chain_position !== 'number' ||
      !Number.isInteger(prevRow.chain_position) ||
      prevRow.chain_position < 0
    ) {
      throw new AuditChainError(
        'prevRow.chain_position must be a non-negative integer',
      );
    }
    if (
      typeof prevRow.content_hash !== 'string' ||
      prevRow.content_hash.length === 0
    ) {
      throw new AuditChainError(
        'prevRow.content_hash must be a non-empty string',
      );
    }
    chainPosition = prevRow.chain_position + 1;
    prevHash = prevRow.content_hash;
  }

  return {
    chain_position: chainPosition,
    content_hash: sha256Jcs(payload),
    prev_hash: prevHash,
    payload,
  };
}

/**
 * Verify a chain of audit rows is well-formed and linkage-consistent.
 *
 * Throws AuditChainError on any violation; otherwise returns void.
 */
export function verifyAuditChain(rows: readonly AuditChainRow[]): void {
  let expectedPosition = 0;
  let prevContentHash: string | null = null;

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i]!;

    if (row.chain_position !== expectedPosition) {
      throw new AuditChainError(
        `row ${i}: chain_position ${row.chain_position} != expected ${expectedPosition}`,
      );
    }

    const recomputed = sha256Jcs(row.payload);
    if (row.content_hash !== recomputed) {
      throw new AuditChainError(
        `row ${i}: content_hash mismatch -- stored ${row.content_hash} vs recomputed ${recomputed}`,
      );
    }

    if (expectedPosition === 0) {
      if (row.prev_hash !== null) {
        throw new AuditChainError(
          `row 0 (head): prev_hash must be null, got ${JSON.stringify(row.prev_hash)}`,
        );
      }
    } else {
      if (row.prev_hash !== prevContentHash) {
        throw new AuditChainError(
          `row ${i}: prev_hash ${JSON.stringify(row.prev_hash)} != previous content_hash ${JSON.stringify(prevContentHash)}`,
        );
      }
    }

    prevContentHash = row.content_hash;
    expectedPosition += 1;
  }
}
