import { describe, it, expect } from 'vitest';
import {
  REFERENCE_FORMAT_NAMESPACES,
  isValidCaip2,
  isValidCaip10,
  isValidCaip19,
  requireValidCaip2,
  requireValidCaip10,
  requireValidCaip19,
  isCaip2,
  isRegisteredCaip2,
  CaipError,
} from '../src/caip.js';

describe('tier 3: per-namespace reference format', () => {
  it('rule set', () => {
    expect(new Set(REFERENCE_FORMAT_NAMESPACES)).toEqual(
      new Set(['eip155', 'bip122', 'polkadot', 'solana', 'starknet']));
  });

  it('the goal: eip155:abc rejected only at the valid tier', () => {
    expect(isCaip2('eip155:abc')).toBe(true);
    expect(isRegisteredCaip2('eip155:abc')).toBe(true);
    expect(isValidCaip2('eip155:abc')).toBe(false);
  });

  it('real references pass', () => {
    for (const s of ['eip155:1', 'eip155:15000', 'bip122:000000000019d6689c085ae165831e93',
      'polkadot:91b171bb158e2d3848fa23a9f1c25182', 'solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp',
      'starknet:SN_GOERLI', 'starknet:SN_MAIN']) {
      expect(isValidCaip2(s), s).toBe(true);
    }
  });

  it('malformed references rejected (still grammar-valid)', () => {
    for (const s of ['eip155:abc', 'eip155:0x1', 'eip155:-1', 'bip122:ZZZZ',
      'bip122:000000000019d6689c085ae165831e9', 'polkadot:91B171BB158E2D3848FA23A9F1C25182',
      'solana:abc', 'solana:0OIl1111111111111111111111111111', 'starknet:sn_goerli', 'starknet:MAINNET']) {
      expect(isCaip2(s), `${s} grammar`).toBe(true);
      expect(isValidCaip2(s), `${s} valid`).toBe(false);
    }
  });

  it('rule-less registered namespace still valid (cover-all)', () => {
    for (const s of ['cosmos:cosmoshub-3', 'tezos:NetXdQprcVkpaWU', 'hedera:mainnet', 'avax:2q9e4r']) {
      expect(isValidCaip2(s), s).toBe(true);
    }
    expect(isValidCaip2('abc:1')).toBe(false);        // unregistered
    expect(isValidCaip2('fakechain:1')).toBe(false);
  });

  it('caip10 / caip19 apply the embedded chain reference rule', () => {
    expect(isValidCaip10('eip155:1:0xabc')).toBe(true);
    expect(isValidCaip10('eip155:abc:0xdeadbeef')).toBe(false);
    expect(isValidCaip19('eip155:1/slip44:60')).toBe(true);
    expect(isValidCaip19('eip155:abc/slip44:60')).toBe(false);
  });

  it('require_valid gates', () => {
    expect(requireValidCaip2('eip155:1')).toBe('eip155:1');
    expect(requireValidCaip10('eip155:1:0xabc')).toBe('eip155:1:0xabc');
    expect(requireValidCaip19('eip155:1/slip44:60')).toBe('eip155:1/slip44:60');
    expect(() => requireValidCaip2('eip155:abc')).toThrow(CaipError);
    expect(() => requireValidCaip2('abc:1')).toThrow(CaipError);
    expect(() => requireValidCaip10('eip155:abc:0xdeadbeef')).toThrow(CaipError);
    expect(() => requireValidCaip2(123 as unknown as string)).toThrow(CaipError);
  });
});
