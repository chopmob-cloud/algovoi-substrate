import { describe, it, expect } from 'vitest';
import {
  AuditChainError,
  type AuditChainRow,
  appendToChain,
  verifyAuditChain,
} from '../src/audit-chain.js';
import { sha256Jcs } from '../src/canonicalize.js';
import { buildComplianceReceipt } from '../src/compliance-receipt.js';

describe('appendToChain', () => {
  it('head row has position 0 and no prev_hash', () => {
    const row = appendToChain({ event: 'first' }, null);
    expect(row.chain_position).toBe(0);
    expect(row.prev_hash).toBeNull();
    expect(row.content_hash).toBe(sha256Jcs({ event: 'first' }));
  });

  it('next row links to prev', () => {
    const row0 = appendToChain({ event: 'first' }, null);
    const row1 = appendToChain({ event: 'second' }, row0);
    expect(row1.chain_position).toBe(1);
    expect(row1.prev_hash).toBe(row0.content_hash);
    expect(row1.content_hash).toBe(sha256Jcs({ event: 'second' }));
  });

  it('three-row chain verifies', () => {
    const rows: AuditChainRow[] = [];
    let prev: AuditChainRow | null = null;
    for (let i = 0; i < 3; i++) {
      const row = appendToChain({ i }, prev);
      rows.push(row);
      prev = row;
    }
    expect(() => verifyAuditChain(rows)).not.toThrow();
  });
});

describe('verifyAuditChain', () => {
  it('accepts an empty chain', () => {
    expect(() => verifyAuditChain([])).not.toThrow();
  });

  it('head row prev_hash must be null', () => {
    const bad: AuditChainRow = {
      chain_position: 0,
      content_hash: sha256Jcs({ x: 1 }),
      prev_hash: 'should-be-null',
      payload: { x: 1 },
    };
    expect(() => verifyAuditChain([bad])).toThrow(/head.*prev_hash must be null/);
  });

  it('chain_position must start at 0', () => {
    const bad: AuditChainRow = {
      chain_position: 1,
      content_hash: sha256Jcs({ x: 1 }),
      prev_hash: null,
      payload: { x: 1 },
    };
    expect(() => verifyAuditChain([bad])).toThrow(/chain_position 1 != expected 0/);
  });

  it('detects content_hash tampering', () => {
    const row = appendToChain({ x: 1 }, null);
    const tampered: AuditChainRow = { ...row, content_hash: '0'.repeat(64) };
    expect(() => verifyAuditChain([tampered])).toThrow(/content_hash mismatch/);
  });

  it('detects prev_hash break', () => {
    const row0 = appendToChain({ x: 1 }, null);
    const row1 = appendToChain({ x: 2 }, row0);
    const broken: AuditChainRow = { ...row1, prev_hash: '0'.repeat(64) };
    expect(() => verifyAuditChain([row0, broken])).toThrow(/prev_hash/);
  });

  it('detects payload tampering', () => {
    const row = appendToChain({ x: 1 }, null);
    const tampered: AuditChainRow = { ...row, payload: { x: 2 } };
    expect(() => verifyAuditChain([tampered])).toThrow(/content_hash mismatch/);
  });
});

describe('round trip with compliance receipts', () => {
  it('round trip three compliance receipts in a chain', () => {
    const rows: AuditChainRow[] = [];
    let prev: AuditChainRow | null = null;
    for (let i = 0; i < 3; i++) {
      const payload = buildComplianceReceipt({
        payer_ref: `sha256:row${i}`,
        screen_result: 'ALLOW',
        screen_timestamp_ms: 1716460800000 + i,
        screen_provider_did: 'did:web:api.algovoi.co.uk',
        jurisdiction_flags: ['UK', 'EU'],
      });
      const row = appendToChain(payload, prev);
      rows.push(row);
      prev = row;
    }
    expect(() => verifyAuditChain(rows)).not.toThrow();
    expect(rows[0]!.chain_position).toBe(0);
    expect(rows[2]!.chain_position).toBe(2);
    expect(rows[2]!.prev_hash).toBe(rows[1]!.content_hash);
  });
});
