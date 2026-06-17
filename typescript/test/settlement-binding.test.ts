import { describe, it, expect } from 'vitest';
import {
  SettlementBindingError,
  settlementActionBinding,
  settlementBindingPreimage,
} from '../src/settlement-binding.js';
import { sha256Jcs } from '../src/canonicalize.js';

// Published reference vector sab-v1-001 from the public conformance set
// algovoi-jcs-conformance-vectors/settlement_action_binding_v1.
const REF = {
  action_ref:
    '7528529a8be2044488e603b7913efaa4f83620dbcc63010d4a1478cf7e9a473c',
  transition_hash:
    'f49faa7c4f82bd842705374311f5f6af073826539d519d0b65de3263258eac5f',
  settlement_ref:
    '0ead75bfe7fc74cc0421124903e56cb5c5006d02c393231a1d5f260fa87e96d3',
  retention_chain_ref:
    'sha256:d23aeb006c5f3db9dd96315916410393904f56c4c871593065eb73b783fff35f',
};
const REF_BINDING =
  'sha256:7dc4a2bf62b3c5eabd10fc875ff7fc10f188666f15838c4a51464cc72e80f6ca';

describe('settlementBindingPreimage', () => {
  it('builds the canonical four-field shape', () => {
    expect(settlementBindingPreimage(REF)).toEqual({
      action_ref: REF.action_ref,
      transition_hash: REF.transition_hash,
      settlement_ref: REF.settlement_ref,
      retention_chain_ref: REF.retention_chain_ref,
    });
  });

  it('rejects a non-string field', () => {
    expect(() =>
      settlementBindingPreimage({
        ...REF,
        action_ref: 123 as unknown as string,
      }),
    ).toThrow(SettlementBindingError);
  });

  it('rejects a short hex digest', () => {
    expect(() =>
      settlementBindingPreimage({ ...REF, action_ref: 'abc123' }),
    ).toThrow(/64-character/);
  });

  it('rejects an uppercase hex digest', () => {
    expect(() =>
      settlementBindingPreimage({
        ...REF,
        action_ref: REF.action_ref.toUpperCase(),
      }),
    ).toThrow(/lowercase/);
  });

  it('rejects a retention_chain_ref without the sha256: prefix', () => {
    const bare = REF.retention_chain_ref.slice('sha256:'.length);
    expect(() =>
      settlementBindingPreimage({ ...REF, retention_chain_ref: bare }),
    ).toThrow(/sha256:/);
  });

  it('rejects a sha256:-prefixed action_ref (bare digest expected)', () => {
    expect(() =>
      settlementBindingPreimage({ ...REF, action_ref: REF.retention_chain_ref }),
    ).toThrow(/64-character/);
  });
});

describe('settlementActionBinding', () => {
  it('reproduces the published reference vector byte-for-byte (sab-v1-001)', () => {
    expect(settlementActionBinding(REF)).toBe(REF_BINDING);
  });

  it('carries the sha256: algorithm prefix', () => {
    expect(settlementActionBinding(REF).startsWith('sha256:')).toBe(true);
  });

  it('introduces no new primitive (sha256: + SHA-256(JCS(preimage)))', () => {
    const preimage = settlementBindingPreimage(REF);
    expect(settlementActionBinding(REF)).toBe(`sha256:${sha256Jcs(preimage)}`);
  });

  it('is deterministic', () => {
    expect(settlementActionBinding(REF)).toBe(settlementActionBinding(REF));
  });

  it('settlement_ref is load-bearing (sab-v1-003)', () => {
    expect(
      settlementActionBinding({
        ...REF,
        settlement_ref:
          'e7777a9a77a9c3f02339594395bfb2620e07edc62d3dcb48c4f2e82a8c37a1c4',
      }),
    ).not.toBe(REF_BINDING);
  });

  it('action_ref is load-bearing (sab-v1-004)', () => {
    expect(
      settlementActionBinding({
        ...REF,
        action_ref:
          '57e861cb0929fe602823a15e2bc5a5587f0b9c3bd39147baa49819dd014c56a6',
      }),
    ).not.toBe(REF_BINDING);
  });

  it('transition_hash is load-bearing: only COMMITTED binds (sab-v1-005)', () => {
    expect(
      settlementActionBinding({
        ...REF,
        transition_hash:
          '0957638b64c790292c11d90e9ae15576a6454f37f23a0aade222acf9e2ea18b0',
      }),
    ).not.toBe(REF_BINDING);
  });

  it('retention_chain_ref is load-bearing (sab-v1-006)', () => {
    expect(
      settlementActionBinding({
        ...REF,
        retention_chain_ref:
          'sha256:43f888f00ea70e38fb8e38c205219b3fff51a90c62197d890b9f270f0f81fe42',
      }),
    ).not.toBe(REF_BINDING);
  });
});
