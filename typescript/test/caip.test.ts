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

// verbatim normative vectors from the CAIP-2/10/19 specs (ChainAgnostic/CAIPs)
const CAIP2_SPEC = [
  'eip155:1', 'bip122:000000000019d6689c085ae165831e93',
  'bip122:12a765e31ffd4059bada1e25190f6e98', 'bip122:fdbe99b90c90bae7505796461471d89a',
  'cosmos:cosmoshub-2', 'cosmos:cosmoshub-3', 'cosmos:Binance-Chain-Tigris',
  'cosmos:iov-mainnet', 'starknet:SN_GOERLI', 'lip9:9ee11e9df416b18b',
  'chainstd:8c3444cf8970a9e41a706fab93e7a6c4',
];
const CAIP10_SPEC = [
  'eip155:1:0xab16a96D359eC26a11e2C2b3d8f8B8942d5Bfcdb',
  'bip122:000000000019d6689c085ae165831e93:128Lkh3S7CkDTBZ8W7BbpsN3YYizJMp8p6',
  'cosmos:cosmoshub-3:cosmos1t2uflqwqe0fsj0shcfkrvpukewcw40yjj6hdc0',
  'polkadot:b0a8d493285c2df73290dfb7e61f870f:5hmuyxw9xdgbpptgypokw4thfyoe3ryenebr381z9iaegmfy',
  'starknet:SN_GOERLI:0x02dd1b492765c064eac4039e3841aa5f382773b598097a40073bd8b48170ab57',
  'chainstd:8c3444cf8970a9e41a706fab93e7a6c4:6d9b0b4b9994e8a6afbd3dc3ed983cd51c755afb27cd1dc7825ef59c134a39f7',
  'hedera:mainnet:0.0.1234567890-zbhlt',
];
const CAIP19_SPEC = [
  'eip155:1/slip44:60', 'bip122:000000000019d6689c085ae165831e93/slip44:0',
  'cosmos:cosmoshub-3/slip44:118', 'bip122:12a765e31ffd4059bada1e25190f6e98/slip44:2',
  'cosmos:Binance-Chain-Tigris/slip44:714', 'cosmos:iov-mainnet/slip44:234',
  'lip9:9ee11e9df416b18b/slip44:134',
  'eip155:1/erc20:0x6b175474e89094c44da98b954eedeac495271d0f',
  'eip155:1/erc721:0x06012c8cf97BEaD5deAe237070F9587f8E7A266d',
  'eip155:1/erc721:0x06012c8cf97BEaD5deAe237070F9587f8E7A266d/771769',
  'hedera:mainnet/nft:0.0.55492/12',
];

describe('CAIP spec vectors are accepted', () => {
  it.each(CAIP2_SPEC)('is_caip2 accepts %s', (v) => expect(isCaip2(v)).toBe(true));
  it.each(CAIP10_SPEC)('is_caip10 accepts %s', (v) => expect(isCaip10(v)).toBe(true));
  it.each(CAIP19_SPEC)('is_caip19 accepts %s', (v) => expect(isCaip19(v)).toBe(true));
});

describe('cross-level guards (no level confusion)', () => {
  it('rejects level mismatches', () => {
    expect(isCaip10('eip155:1')).toBe(false);
    expect(isCaip19('eip155:1')).toBe(false);
    expect(isCaip2('eip155:1:0xabc')).toBe(false);
    expect(isCaip2('eip155:1/slip44:60')).toBe(false);
    expect(isCaip19('eip155:1:0xabc')).toBe(false);
  });
});

describe('malformed forms are rejected', () => {
  const BAD2 = ['', 'ab:1', '123456789:1', 'EIP155:1', 'eip_155:1', 'eip155:', 'eip155',
    'eip155:' + 'a'.repeat(33), 'eip155:na@me', ' eip155:1', 'eip155:1 ',
    'eip155:1\n', 'eip155:1\r\n', 'eip155:1\t', 'eip155:1\x00'];
  it.each(BAD2)('is_caip2 rejects %j', (s) => expect(isCaip2(s)).toBe(false));
  it('is_caip2 rejects non-strings', () => {
    expect(isCaip2(123)).toBe(false);
    expect(isCaip2(null)).toBe(false);
    expect(isCaip2({ x: 1 })).toBe(false);
    expect(isCaip2(undefined)).toBe(false);
  });
  const BAD10 = ['eip155:1', 'eip155:1:', 'eip155:1:0x_ab', 'eip155:1:' + 'a'.repeat(129),
    'eip155:1:0xab\n', 'eip155:1:0x ab', 'eip155:1:0x/ab', 'eip155:1:0x:ab'];
  it.each(BAD10)('is_caip10 rejects %j', (s) => expect(isCaip10(s)).toBe(false));
  const BAD19 = ['eip155:1', 'eip155:1/', 'eip155:1/SLIP44:60', 'eip155:1/sl:60',
    'eip155:1/slip44:', 'eip155:1/slip44:60\n', 'eip155:1/slip44:60/' + 't'.repeat(79),
    'eip155:1/slip_44:60'];
  it.each(BAD19)('is_caip19 rejects %j', (s) => expect(isCaip19(s)).toBe(false));
});

describe('trailing-newline anchor: JS $ (no m flag) is end-of-input', () => {
  it('rejects trailing newline on all three, matching the Python \\A..\\Z sibling', () => {
    expect(isCaip2('eip155:1\n')).toBe(false);
    expect(isCaip2('eip155:1\r\n')).toBe(false);
    expect(isCaip10('eip155:1:0xabc\n')).toBe(false);
    expect(isCaip19('eip155:1/slip44:60\n')).toBe(false);
  });
});

describe('boundary lengths', () => {
  it('enforces the spec bounds exactly', () => {
    expect(isCaip2('abc:' + 'a'.repeat(32))).toBe(true);
    expect(isCaip2('abc:' + 'a'.repeat(33))).toBe(false);
    expect(isCaip2('abc:a')).toBe(true);
    expect(isCaip2('abcdefgh:a')).toBe(true);
    expect(isCaip2('ab:a')).toBe(false);
    expect(isCaip2('abcdefghi:a')).toBe(false);
    expect(isCaip10('abc:1:' + 'a'.repeat(128))).toBe(true);
    expect(isCaip10('abc:1:' + 'a'.repeat(129))).toBe(false);
    expect(isCaip19('abc:1/def:60/' + 't'.repeat(78))).toBe(true);
    expect(isCaip19('abc:1/def:60/' + 't'.repeat(79))).toBe(false);
  });
});

describe('require* gates', () => {
  it('pass valid through', () => {
    expect(requireCaip2('eip155:1')).toBe('eip155:1');
    expect(requireCaip10('eip155:1:0xabc')).toBe('eip155:1:0xabc');
    expect(requireCaip19('eip155:1/slip44:60')).toBe('eip155:1/slip44:60');
  });
  it('throw CaipError on non-canonical', () => {
    expect(() => requireCaip2('eip155:1\n')).toThrow(CaipError);
    expect(() => requireCaip10('eip155:1')).toThrow(CaipError);
    expect(() => requireCaip19('not/an:asset:x')).toThrow(CaipError);
  });
});

describe('builders', () => {
  it('caip19Slip44 builds and validates', () => {
    expect(caip19Slip44('eip155:1', 60)).toBe('eip155:1/slip44:60');
    expect(caip19Slip44('cosmos:cosmoshub-3', 118)).toBe('cosmos:cosmoshub-3/slip44:118');
    expect(() => caip19Slip44('not a chain', 60)).toThrow(CaipError);
    expect(() => caip19Slip44('eip155:1', -1)).toThrow(CaipError);
    expect(() => caip19Slip44('eip155:1', 1.5)).toThrow(CaipError);
  });
  it('caip10Of builds and validates', () => {
    expect(caip10Of('eip155:1', '0xab16a96D359eC26a11e2C2b3d8f8B8942d5Bfcdb')).toMatch(/^eip155:1:0x/);
    expect(() => caip10Of('eip155:1', '0x ab')).toThrow(CaipError);
    expect(() => caip10Of('not a chain', '0xabc')).toThrow(CaipError);
  });
});
