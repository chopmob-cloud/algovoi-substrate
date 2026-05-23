import { describe, it, expect } from 'vitest';
import { createHash } from 'node:crypto';
import {
  CANON_VERSION,
  CanonicalizationError,
  canonicalize,
  canonicalizeBytes,
  sha256Jcs,
} from '../src/canonicalize.js';

describe('CANON_VERSION', () => {
  it('is pinned to jcs-rfc8785-v1', () => {
    expect(CANON_VERSION).toBe('jcs-rfc8785-v1');
  });
});

describe('canonicalize', () => {
  it('sorts object keys', () => {
    expect(canonicalize({ b: 1, a: 2 })).toBe('{"a":2,"b":1}');
  });

  it('preserves array element order (RFC 8785 §3.2.3)', () => {
    expect(canonicalize(['UK', 'EU'])).not.toBe(canonicalize(['EU', 'UK']));
  });

  it('handles unicode', () => {
    expect(canonicalize({ name: 'Müller' })).toContain('Müller');
  });

  it('handles nested structures with sorted keys at every level', () => {
    expect(
      canonicalize({ outer: { inner: [1, 2, 3] }, list: [{ a: 1 }, { a: 2 }] }),
    ).toBe('{"list":[{"a":1},{"a":2}],"outer":{"inner":[1,2,3]}}');
  });

  it('returns same bytes via canonicalizeBytes', () => {
    expect(canonicalizeBytes({ a: 1 })).toEqual(new TextEncoder().encode('{"a":1}'));
  });

  it('accepts null', () => {
    expect(canonicalize({ a: null })).toBe('{"a":null}');
  });

  it('accepts bool', () => {
    expect(canonicalize({ a: true, b: false })).toBe('{"a":true,"b":false}');
  });
});

describe('sha256Jcs', () => {
  it('returns lowercase hex', () => {
    const h = sha256Jcs({ a: 1 });
    const expected = createHash('sha256').update('{"a":1}').digest('hex');
    expect(h).toBe(expected);
    expect(h).toMatch(/^[0-9a-f]+$/);
  });

  it('produces distinct hashes for distinct array orders', () => {
    expect(sha256Jcs({ jurisdiction_flags: ['UK', 'EU'] })).not.toBe(
      sha256Jcs({ jurisdiction_flags: ['EU', 'UK'] }),
    );
  });

  it('produces identical hashes regardless of object key order', () => {
    expect(sha256Jcs({ a: 1, b: 2 })).toBe(sha256Jcs({ b: 2, a: 1 }));
  });

  it('is deterministic', () => {
    const obj = { a: [1, 2, 3], b: 'x' };
    expect(sha256Jcs(obj)).toBe(sha256Jcs(obj));
  });
});

describe('cross-impl parity with Python', () => {
  // Vectors below were taken from the Python algovoi_substrate reference
  // implementation; the TS bundle must produce byte-for-byte matches.
  it('canonicalises {a:1,b:2} the same way', () => {
    expect(canonicalize({ a: 1, b: 2 })).toBe('{"a":1,"b":2}');
  });

  it('canonicalises empty object', () => {
    expect(canonicalize({})).toBe('{}');
  });

  it('canonicalises empty array', () => {
    expect(canonicalize([])).toBe('[]');
  });
});
