import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

import { canonicalize, sha256Jcs } from '../src/canonicalize.js';
import {
  REFUND_RESULTS,
  RefundReceiptError,
  buildRefundReceipt,
} from '../src/refund-receipt.js';

describe('REFUND_RESULTS', () => {
  it('is exactly FULL, PARTIAL, REJECTED', () => {
    expect([...REFUND_RESULTS]).toEqual(['FULL', 'PARTIAL', 'REJECTED']);
  });
});

describe('buildRefundReceipt', () => {
  const base = {
    original_payment_ref: 'sha256:abc123',
    refund_result: 'FULL',
    refund_timestamp_ms: 1716460800000,
    refund_provider_did: 'did:web:api.algovoi.co.uk',
    refund_amount: { amount_minor: '100000', asset_id: 'USDC.6' },
    jurisdiction_flags: ['UK', 'EU'],
  };

  it('builds the canonical receipt shape', () => {
    const r = buildRefundReceipt(base);
    expect(r).toEqual({ ...base, canon_version: 'jcs-rfc8785-v1' });
  });

  it('distinct refund_result values hash differently', () => {
    const full = buildRefundReceipt({ ...base, refund_result: 'FULL' });
    const partial = buildRefundReceipt({ ...base, refund_result: 'PARTIAL' });
    const rejected = buildRefundReceipt({ ...base, refund_result: 'REJECTED' });
    const hFull = sha256Jcs(full);
    const hPartial = sha256Jcs(partial);
    const hRejected = sha256Jcs(rejected);
    expect(hFull).not.toBe(hPartial);
    expect(hFull).not.toBe(hRejected);
    expect(hPartial).not.toBe(hRejected);
  });

  it('distinct jurisdiction orderings hash differently', () => {
    const a = buildRefundReceipt({ ...base, jurisdiction_flags: ['UK', 'EU'] });
    const b = buildRefundReceipt({ ...base, jurisdiction_flags: ['EU', 'UK'] });
    expect(sha256Jcs(a)).not.toBe(sha256Jcs(b));
  });

  it('rejects invalid refund_result', () => {
    expect(() =>
      buildRefundReceipt({ ...base, refund_result: 'MAYBE' }),
    ).toThrow(/refund_result must be one of/);
  });

  it('rejects score-tier projection', () => {
    expect(() =>
      buildRefundReceipt({ ...base, refund_result: 'partial:50%' }),
    ).toThrow(RefundReceiptError);
  });

  it('rejects float timestamp (Substrate Rule 2)', () => {
    expect(() =>
      buildRefundReceipt({ ...base, refund_timestamp_ms: 1716460800000.5 }),
    ).toThrow(/Substrate Rule 2/);
  });

  it('rejects string timestamp (Substrate Rule 2)', () => {
    expect(() =>
      buildRefundReceipt({
        ...base,
        refund_timestamp_ms: '2024-05-23T12:00:00Z' as unknown as number,
      }),
    ).toThrow(/Substrate Rule 2/);
  });

  it('rejects refund_amount with extra keys', () => {
    expect(() =>
      buildRefundReceipt({
        ...base,
        refund_amount: {
          amount_minor: '1',
          asset_id: 'USDC.6',
          extra: 'x',
        } as unknown as { amount_minor: string; asset_id: string },
      }),
    ).toThrow(/refund_amount must have exactly/);
  });

  it('rejects non-digit amount_minor', () => {
    expect(() =>
      buildRefundReceipt({
        ...base,
        refund_amount: { amount_minor: '0.1', asset_id: 'USDC.6' },
      }),
    ).toThrow(/decimal digits/);
  });

  it('rejects negative amount_minor', () => {
    expect(() =>
      buildRefundReceipt({
        ...base,
        refund_amount: { amount_minor: '-100', asset_id: 'USDC.6' },
      }),
    ).toThrow(/decimal digits/);
  });

  it('rejects empty original_payment_ref', () => {
    expect(() =>
      buildRefundReceipt({ ...base, original_payment_ref: '' }),
    ).toThrow(/original_payment_ref/);
  });

  it('rejects empty jurisdiction code', () => {
    expect(() =>
      buildRefundReceipt({ ...base, jurisdiction_flags: ['UK', ''] }),
    ).toThrow(/jurisdiction_flags/);
  });

  it('canon_version defaults to jcs-rfc8785-v1', () => {
    expect(buildRefundReceipt(base).canon_version).toBe('jcs-rfc8785-v1');
  });
});

describe('Conformance vector reproduction', () => {
  const VECTOR_PATH =
    'C:/algo/algovoi-jcs-conformance-vectors/vectors/refund_receipt_v1/refund_receipt_v1.json';

  it('reproduces vectors 001 to 005 byte-identical', () => {
    if (!existsSync(VECTOR_PATH)) {
      // Skip when conformance corpus not co-located
      return;
    }
    const data = JSON.parse(readFileSync(VECTOR_PATH, 'utf-8'));
    for (const v of data.vectors) {
      if (!v.receipt) continue;
      const canon = canonicalize(v.receipt);
      const canonBytes = Buffer.from(canon, 'utf-8');
      expect(canonBytes.toString('base64')).toBe(v.expected_jcs_bytes_b64);
      expect(createHash('sha256').update(canonBytes).digest('hex')).toBe(
        v.expected_content_hash,
      );
    }
  });
});
