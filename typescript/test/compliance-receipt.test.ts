import { describe, it, expect } from 'vitest';
import { sha256Jcs } from '../src/canonicalize.js';
import {
  SCREEN_RESULTS,
  ComplianceReceiptError,
  buildComplianceReceipt,
} from '../src/compliance-receipt.js';

describe('SCREEN_RESULTS', () => {
  it('is exactly ALLOW, REFER, DENY', () => {
    expect([...SCREEN_RESULTS]).toEqual(['ALLOW', 'REFER', 'DENY']);
  });
});

describe('buildComplianceReceipt', () => {
  const base = {
    payer_ref: 'sha256:abc123',
    screen_result: 'ALLOW',
    screen_timestamp_ms: 1716460800000,
    screen_provider_did: 'did:web:api.algovoi.co.uk',
    jurisdiction_flags: ['UK', 'EU'],
  };

  it('builds the canonical receipt shape', () => {
    const r = buildComplianceReceipt(base);
    expect(r).toEqual({ ...base, canon_version: 'jcs-rfc8785-v1' });
  });

  it('distinct jurisdiction orderings hash differently', () => {
    const a = buildComplianceReceipt({ ...base, jurisdiction_flags: ['UK', 'EU'] });
    const b = buildComplianceReceipt({ ...base, jurisdiction_flags: ['EU', 'UK'] });
    expect(sha256Jcs(a)).not.toBe(sha256Jcs(b));
  });

  it('rejects invalid screen_result', () => {
    expect(() =>
      buildComplianceReceipt({ ...base, screen_result: 'MAYBE' }),
    ).toThrow(/screen_result must be one of/);
  });

  it('rejects score-tier projection', () => {
    expect(() =>
      buildComplianceReceipt({ ...base, screen_result: 'score:75' }),
    ).toThrow(ComplianceReceiptError);
  });

  it('rejects float timestamp (Substrate Rule 1)', () => {
    expect(() =>
      buildComplianceReceipt({ ...base, screen_timestamp_ms: 1716460800000.5 }),
    ).toThrow(/Substrate Rule 1/);
  });

  it('rejects empty payer_ref', () => {
    expect(() =>
      buildComplianceReceipt({ ...base, payer_ref: '' }),
    ).toThrow(/payer_ref/);
  });

  it('rejects non-array jurisdiction_flags', () => {
    expect(() =>
      buildComplianceReceipt({
        ...base,
        jurisdiction_flags: 'UK' as unknown as string[],
      }),
    ).toThrow(/jurisdiction_flags must be array/);
  });

  it('rejects empty jurisdiction code', () => {
    expect(() =>
      buildComplianceReceipt({ ...base, jurisdiction_flags: ['UK', ''] }),
    ).toThrow(/jurisdiction_flags/);
  });

  it('canon_version defaults to jcs-rfc8785-v1', () => {
    expect(buildComplianceReceipt(base).canon_version).toBe('jcs-rfc8785-v1');
  });
});
