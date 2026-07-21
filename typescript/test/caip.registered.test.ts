import { describe, it, expect } from 'vitest';
import {
  REGISTERED_NAMESPACES,
  registeredNamespaces,
  isRegisteredNamespace,
  isRegisteredCaip2,
  isRegisteredCaip10,
  isRegisteredCaip19,
  requireRegisteredCaip2,
  requireRegisteredCaip10,
  requireRegisteredCaip19,
  isCaip2,
  CaipError,
} from '../src/caip.js';

const NS_RE = /^[-a-z0-9]{3,8}$/;

describe('registry shape', () => {
  it('has 41 grammar-valid namespaces including the ones that differ from their directory', () => {
    expect(registeredNamespaces()).toBe(REGISTERED_NAMESPACES);
    expect(REGISTERED_NAMESPACES.size).toBe(41);
    for (const ns of REGISTERED_NAMESPACES) expect(NS_RE.test(ns)).toBe(true);
    for (const ns of ['eip155', 'bip122', 'cosmos', 'solana', 'polkadot', 'avax', 'swift', 'xrpl', 'tvm']) {
      expect(REGISTERED_NAMESPACES.has(ns)).toBe(true);
    }
  });
});

describe('directory name is not the namespace', () => {
  it('registers avax, not avalanche', () => {
    expect(isRegisteredNamespace('avax')).toBe(true);
    expect(isRegisteredNamespace('avalanche')).toBe(false);
    expect(isCaip2('avalanche:1')).toBe(false); // 9 chars, not even grammar-valid
  });
});

describe('isRegisteredNamespace', () => {
  it('accepts registered, rejects unregistered / malformed / non-string', () => {
    expect(isRegisteredNamespace('eip155')).toBe(true);
    expect(isRegisteredNamespace('abc')).toBe(false);
    expect(isRegisteredNamespace('fakechain')).toBe(false);
    expect(isRegisteredNamespace('EIP155')).toBe(false);
    expect(isRegisteredNamespace('')).toBe(false);
    expect(isRegisteredNamespace(123)).toBe(false);
  });
});

describe('registered layer sits on top of grammar', () => {
  it('grammar accepts abc:1 but registry rejects it', () => {
    expect(isCaip2('abc:1')).toBe(true);
    expect(isRegisteredCaip2('abc:1')).toBe(false);
  });
  it('real chains pass', () => {
    for (const s of ['eip155:1', 'bip122:000000000019d6689c085ae165831e93', 'cosmos:cosmoshub-3',
      'solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp', 'avax:2q9e4r6mu']) {
      expect(isRegisteredCaip2(s)).toBe(true);
    }
  });
  it('malformed and fake still rejected', () => {
    expect(isRegisteredCaip2('eip155:1\n')).toBe(false);
    expect(isRegisteredCaip2('fakechain:1')).toBe(false);
    expect(isRegisteredCaip2(123)).toBe(false);
  });
  it('caip10 and caip19 registered checks', () => {
    expect(isRegisteredCaip10('eip155:1:0xabc')).toBe(true);
    expect(isRegisteredCaip10('abc:1:0xabc')).toBe(false);
    expect(isRegisteredCaip19('eip155:1/slip44:60')).toBe(true);
    expect(isRegisteredCaip19('abc:1/slip44:60')).toBe(false);
    expect(isRegisteredCaip19('swift:iso20022/iso4217:usd')).toBe(true);
  });
});

describe('require_registered gates', () => {
  it('pass valid, throw CaipError on unregistered/malformed', () => {
    expect(requireRegisteredCaip2('eip155:1')).toBe('eip155:1');
    expect(requireRegisteredCaip10('eip155:1:0xabc')).toBe('eip155:1:0xabc');
    expect(requireRegisteredCaip19('eip155:1/slip44:60')).toBe('eip155:1/slip44:60');
    expect(() => requireRegisteredCaip2('abc:1')).toThrow(CaipError);
    expect(() => requireRegisteredCaip2('eip155:1\n')).toThrow(CaipError);
    expect(() => requireRegisteredCaip10('abc:1:0xabc')).toThrow(CaipError);
    expect(() => requireRegisteredCaip19('abc:1/slip44:60')).toThrow(CaipError);
    expect(() => requireRegisteredCaip2(123 as unknown as string)).toThrow(CaipError);
  });
});
