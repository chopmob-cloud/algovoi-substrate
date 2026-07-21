import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { isCaip2, isCaip10, isCaip19 } from '../src/caip.js';

// A regex-free oracle in JS, counting UTF-16 code units to match RegExp quantifier semantics.
const lower = (c: string) => c >= 'a' && c <= 'z';
const upper = (c: string) => c >= 'A' && c <= 'Z';
const digit = (c: string) => c >= '0' && c <= '9';
const nsC = (c: string) => lower(c) || digit(c) || c === '-';
const refC = (c: string) => lower(c) || upper(c) || digit(c) || c === '-' || c === '_';
const addrC = (c: string) => lower(c) || upper(c) || digit(c) || c === '-' || c === '.' || c === '%';
function cls(s: string, f: (c: string) => boolean, lo: number, hi: number): boolean {
  if (s.length < lo || s.length > hi) return false;
  for (let i = 0; i < s.length; i++) if (!f(s[i]!)) return false;
  return true;
}
function o2(s: string): boolean {
  const p = s.split(':');
  return p.length === 2 && cls(p[0]!, nsC, 3, 8) && cls(p[1]!, refC, 1, 32);
}
function o10(s: string): boolean {
  const p = s.split(':');
  return p.length === 3 && cls(p[0]!, nsC, 3, 8) && cls(p[1]!, refC, 1, 32) && cls(p[2]!, addrC, 1, 128);
}
function o19(s: string): boolean {
  const sl = s.split('/');
  let chain: string, ap: string, tok: string | undefined;
  if (sl.length === 2) { chain = sl[0]!; ap = sl[1]!; tok = undefined; }
  else if (sl.length === 3) { chain = sl[0]!; ap = sl[1]!; tok = sl[2]!; }
  else return false;
  if (!o2(chain)) return false;
  const a = ap.split(':');
  if (a.length !== 2 || !cls(a[0]!, nsC, 3, 8) || !cls(a[1]!, addrC, 1, 128)) return false;
  return tok === undefined || cls(tok, addrC, 1, 78);
}

const ALPHA = [...'abcxyzABCXYZ0159-_.%:/@ \n\r\t\x00\u2028\uffff\uff11\u0435'];
const near = fc.string({ unit: fc.constantFrom(...ALPHA),  maxLength: 45  });

describe('property: regex validator equals the regex-free oracle', () => {
  it('caip2 (near-boundary alphabet)', () => {
    fc.assert(fc.property(near, (s) => isCaip2(s) === o2(s)), { numRuns: 5000 });
  });
  it('caip10 (near-boundary alphabet)', () => {
    fc.assert(fc.property(near, (s) => isCaip10(s) === o10(s)), { numRuns: 5000 });
  });
  it('caip19 (near-boundary alphabet)', () => {
    fc.assert(fc.property(near, (s) => isCaip19(s) === o19(s)), { numRuns: 5000 });
  });
  it('all three on arbitrary unicode text', () => {
    fc.assert(fc.property(fc.string({ maxLength: 60 }), (s) =>
      isCaip2(s) === o2(s) && isCaip10(s) === o10(s) && isCaip19(s) === o19(s)), { numRuns: 4000 });
  });
});

describe('property: constructed valid identifiers are always accepted', () => {
  const nsA = fc.string({ unit: fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz0123456789-'),  minLength: 3, maxLength: 8  });
  const refA = fc.string({ unit: fc.constantFrom(...'abcABC013-_'),  minLength: 1, maxLength: 32  });
  const addrA = fc.string({ unit: fc.constantFrom(...'abcABC013-.%'),  minLength: 1, maxLength: 128  });
  const tokA = fc.string({ unit: fc.constantFrom(...'abcABC013-.%'),  minLength: 1, maxLength: 78  });
  it('caip2', () => {
    fc.assert(fc.property(nsA, refA, (ns, ref) => isCaip2(`${ns}:${ref}`)), { numRuns: 3000 });
  });
  it('caip10', () => {
    fc.assert(fc.property(nsA, refA, addrA, (ns, ref, addr) => isCaip10(`${ns}:${ref}:${addr}`)), { numRuns: 3000 });
  });
  it('caip19 with and without token', () => {
    fc.assert(fc.property(nsA, refA, nsA, addrA, tokA, fc.boolean(),
      (ns, ref, ans, aref, tok, withTok) =>
        isCaip19(`${ns}:${ref}/${ans}:${aref}` + (withTok ? `/${tok}` : ''))), { numRuns: 3000 });
  });
});

describe('property: is* never throw', () => {
  it('returns a boolean for any string', () => {
    fc.assert(fc.property(fc.string(), (s) =>
      typeof isCaip2(s) === 'boolean' && typeof isCaip10(s) === 'boolean' && typeof isCaip19(s) === 'boolean'),
      { numRuns: 3000 });
  });
});
