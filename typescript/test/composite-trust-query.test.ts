import { describe, it, expect } from 'vitest';
import {
  CompositeTrustQueryError,
  compositeTrustQueryHash,
  type EmitterRow,
} from '../src/composite-trust-query.js';

function row(source_id: string, score = 50, sig: string | null = 'sig-bytes'): EmitterRow {
  const r: EmitterRow = { source_id, score };
  if (sig !== null) r.sig = sig;
  return r;
}

describe('compositeTrustQueryHash', () => {
  it('is invariant under row ordering (sort-by-source_id)', () => {
    expect(
      compositeTrustQueryHash([row('src-c'), row('src-a'), row('src-b')]),
    ).toBe(compositeTrustQueryHash([row('src-a'), row('src-b'), row('src-c')]));
  });

  it('produces distinct hash for strict subset (set semantics)', () => {
    expect(
      compositeTrustQueryHash([row('src-a'), row('src-b'), row('src-c')]),
    ).not.toBe(compositeTrustQueryHash([row('src-a'), row('src-c')]));
  });

  it('excludes sig field from hash', () => {
    expect(
      compositeTrustQueryHash([row('src-a', 50, 'sig-1'), row('src-b', 70, 'sig-2')]),
    ).toBe(
      compositeTrustQueryHash([row('src-a', 50, null), row('src-b', 70, null)]),
    );
  });

  it('different sig values do not affect hash', () => {
    expect(
      compositeTrustQueryHash([row('src-a', 50, 'alice'), row('src-b', 70, 'bob')]),
    ).toBe(
      compositeTrustQueryHash([row('src-a', 50, 'DIFF'), row('src-b', 70, 'DIFF')]),
    );
  });

  it('payload change changes hash', () => {
    expect(
      compositeTrustQueryHash([row('src-a', 50), row('src-b', 70)]),
    ).not.toBe(compositeTrustQueryHash([row('src-a', 51), row('src-b', 70)]));
  });

  it('rejects empty rows', () => {
    expect(() => compositeTrustQueryHash([])).toThrow(CompositeTrustQueryError);
  });

  it('rejects row without source_id', () => {
    expect(() =>
      compositeTrustQueryHash([{ score: 50 } as unknown as EmitterRow]),
    ).toThrow(/source_id/);
  });

  it('rejects row with non-string source_id', () => {
    expect(() =>
      compositeTrustQueryHash([
        { source_id: 123 as unknown as string, score: 50 },
      ]),
    ).toThrow(/source_id/);
  });
});
