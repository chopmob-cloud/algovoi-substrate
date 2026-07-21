import { describe, it, expect } from 'vitest';
import {
  CaipError,
  isCaip2,
  isCaip10,
  isCaip19,
  requireCaip2,
  requireCaip10,
  requireCaip19,
  caip19Slip44,
  caip10Of,
} from '../src/caip.js';

// Error-path completeness and robustness. isCaip* must return a boolean for ANY input and
// never throw; requireCaip* and the builders must reject every non-canonical input by
// throwing CaipError and NEVER leak another error type (TypeError from Symbol coercion,
// RangeError, etc.). A large fuzz corpus of hostile strings and non-string values exercises
// this, alongside an explicit error catalogue.

function fuzzStrings(): string[] {
  const out: string[] = [];
  const base = 'eip155:1';
  for (let cp = 0x00; cp <= 0x1f; cp++) {
    const ch = String.fromCharCode(cp);
    out.push(ch, base + ch, ch + base, 'eip155' + ch + ':1', base + ch + 'x');
  }
  out.push('\x7f', base + '\x7f');
  for (const ch of "!\"#$%&'()*+,-./:;<=>?@[\\]^`{|}~") {
    out.push(ch, base + ch, ch + base, 'eip155' + ch + '1', 'eip' + ch + '155:1',
      'eip155:1:0xab' + ch, 'eip155:1/slip44:60' + ch, 'eip155:1/slip44:60/' + ch);
  }
  for (const cp of [0x85, 0xa0, 0x1680, 0x2000, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000,
    0x200b, 0x200e, 0x202e, 0xfeff, 0xff11, 0xff45, 0x0435, 0x0301, 0x00b2, 0x1f600]) {
    const ch = String.fromCodePoint(cp);
    out.push(ch, base + ch, ch + base, 'eip155:' + ch, 'eip155:1:0x' + ch, 'eip155:1/slip44:' + ch);
  }
  out.push('', ' ', '\n', 'a'.repeat(10000), 'eip155:' + 'a'.repeat(10000), ':', '::', '/', '//',
    'eip155:1:' + 'a'.repeat(10000), 'eip155:1/slip44:60/' + 't'.repeat(10000));
  return out;
}

const FUZZ = fuzzStrings();
const NON_STRING: unknown[] = [123, -1, 0, 1.5, NaN, Infinity, true, false, null, undefined,
  {}, [], ['eip155:1'], Symbol('x'), 10n, new Date(0), () => 0];
const IS = [isCaip2, isCaip10, isCaip19];
const REQUIRE = [requireCaip2, requireCaip10, requireCaip19];

describe('isCaip* never throw and always return a boolean', () => {
  it('on hostile strings', () => {
    for (const s of FUZZ) for (const fn of IS) expect(typeof fn(s)).toBe('boolean');
  });
  it('on non-string values', () => {
    for (const x of NON_STRING) for (const fn of IS) expect(fn(x)).toBe(false);
  });
});

describe('requireCaip* throw only CaipError', () => {
  it('never leaks another error type', () => {
    for (const x of [...FUZZ, ...NON_STRING]) {
      for (const fn of REQUIRE) {
        try { fn(x); } catch (e) {
          expect(e, `${fn.name}(${String(typeof x)}) leaked ${(e as Error)?.constructor?.name}`)
            .toBeInstanceOf(CaipError);
        }
      }
    }
  });
});

describe('builders throw only CaipError', () => {
  it('caip19Slip44 and caip10Of never leak another error type', () => {
    const chains = [...FUZZ.slice(0, 200), ...NON_STRING];
    for (const c of chains) {
      for (const coin of [60, -1, 1.5, NaN, true, null, undefined, '60', Symbol('c'), 10n]) {
        try { caip19Slip44(c as string, coin as number); }
        catch (e) { expect(e).toBeInstanceOf(CaipError); }
      }
      for (const addr of ['0xabc', '', '0x ab', 123, null, undefined, Symbol('a'), {}]) {
        try { caip10Of(c as string, addr as string); }
        catch (e) { expect(e).toBeInstanceOf(CaipError); }
      }
    }
  });
});

describe('isCaip* and requireCaip* agree on every fuzz input', () => {
  it('accept-set equality', () => {
    const kinds = [
      [isCaip2, requireCaip2],
      [isCaip10, requireCaip10],
      [isCaip19, requireCaip19],
    ] as const;
    for (const s of FUZZ) {
      for (const [isFn, reqFn] of kinds) {
        if (isFn(s)) expect(reqFn(s)).toBe(s);
        else expect(() => reqFn(s)).toThrow(CaipError);
      }
    }
  });
});

describe('error catalogue: every distinct error condition throws CaipError', () => {
  const conditions: Record<string, () => unknown> = {
    'requireCaip2 rejects non-string': () => requireCaip2(123 as unknown as string),
    'requireCaip2 rejects malformed': () => requireCaip2('EIP155:1'),
    'requireCaip2 rejects trailing newline': () => requireCaip2('eip155:1\n'),
    'requireCaip10 rejects a bare caip2': () => requireCaip10('eip155:1'),
    'requireCaip10 rejects bad address char': () => requireCaip10('eip155:1:0x_a'),
    'requireCaip19 rejects a bare caip2': () => requireCaip19('eip155:1'),
    'requireCaip19 rejects missing token colon': () => requireCaip19('eip155:1/slip4460'),
    'caip19Slip44 rejects bad chain': () => caip19Slip44('not a chain', 60),
    'caip19Slip44 rejects negative coin': () => caip19Slip44('eip155:1', -1),
    'caip19Slip44 rejects float coin': () => caip19Slip44('eip155:1', 1.5),
    'caip19Slip44 rejects NaN coin': () => caip19Slip44('eip155:1', NaN),
    'caip19Slip44 rejects non-number coin': () => caip19Slip44('eip155:1', '60' as unknown as number),
    'caip19Slip44 rejects symbol coin': () => caip19Slip44('eip155:1', Symbol('x') as unknown as number),
    'caip10Of rejects bad chain': () => caip10Of('not a chain', '0xabc'),
    'caip10Of rejects bad address': () => caip10Of('eip155:1', '0x ab'),
    'caip10Of rejects non-string address': () => caip10Of('eip155:1', 123 as unknown as string),
    'caip10Of rejects symbol address (no TypeError leak)': () => caip10Of('eip155:1', Symbol('a') as unknown as string),
  };
  for (const [name, thunk] of Object.entries(conditions)) {
    it(name, () => expect(thunk).toThrow(CaipError));
  }
});

describe('CaipError contract', () => {
  it('is an Error and named CaipError', () => {
    try { requireCaip2('bad'); } catch (e) {
      expect(e).toBeInstanceOf(Error);
      expect((e as Error).name).toBe('CaipError');
    }
  });
});
