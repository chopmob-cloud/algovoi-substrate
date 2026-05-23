/**
 * Compliance receipt shape matching AlgoVoi's production /compliance/screen.
 *
 * The categorical outcome (ALLOW / REFER / DENY) is load-bearing for the
 * retention layer (UK POCA 2002 s.330 SAR distinction). A score/tier
 * projection would lose that property and break year-five auditability.
 */

import { CANON_VERSION } from './canonicalize.js';

export const SCREEN_RESULTS = ['ALLOW', 'REFER', 'DENY'] as const;
export type ScreenResult = (typeof SCREEN_RESULTS)[number];

export class ComplianceReceiptError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ComplianceReceiptError';
  }
}

export interface ComplianceReceipt {
  payer_ref: string;
  screen_result: ScreenResult;
  screen_timestamp_ms: number;
  screen_provider_did: string;
  jurisdiction_flags: string[];
  canon_version: string;
}

export interface BuildComplianceReceiptInput {
  payer_ref: string;
  screen_result: string;
  screen_timestamp_ms: number;
  screen_provider_did: string;
  jurisdiction_flags: string[];
  canon_version?: string;
}

function requireNonEmptyString(field: string, value: unknown): string {
  if (typeof value !== 'string' || value.length === 0) {
    throw new ComplianceReceiptError(
      `${field} must be a non-empty string`,
    );
  }
  return value;
}

function requireIntTimestampMs(value: unknown): number {
  if (typeof value !== 'number') {
    throw new ComplianceReceiptError(
      `screen_timestamp_ms must be epoch-millisecond integer (Substrate Rule 1), got ${typeof value}`,
    );
  }
  if (!Number.isFinite(value) || !Number.isInteger(value)) {
    throw new ComplianceReceiptError(
      `screen_timestamp_ms must be epoch-millisecond integer (Substrate Rule 1), got ${value}`,
    );
  }
  if (value < 0) {
    throw new ComplianceReceiptError(
      `screen_timestamp_ms must be non-negative, got ${value}`,
    );
  }
  return value;
}

function requireJurisdictionFlags(value: unknown): string[] {
  if (!Array.isArray(value)) {
    throw new ComplianceReceiptError(
      `jurisdiction_flags must be array, got ${typeof value}`,
    );
  }
  for (let i = 0; i < value.length; i++) {
    const code = value[i];
    if (typeof code !== 'string' || code.length === 0) {
      throw new ComplianceReceiptError(
        `jurisdiction_flags[${i}] must be a non-empty string`,
      );
    }
  }
  return [...value] as string[];
}

/**
 * Build a validated compliance receipt object.
 *
 * screen_result must be one of ALLOW, REFER, DENY -- the categorical
 * outcome is load-bearing for downstream regulatory obligations.
 *
 * payer_ref is expected to be a content-addressed identity reference
 * (e.g. "sha256:<hex>") rather than cleartext identity content.
 *
 * jurisdiction_flags is treated as ordered -- ["UK","EU"] and ["EU","UK"]
 * produce distinct canonical bytes per RFC 8785 §3.2.3.
 */
export function buildComplianceReceipt(
  input: BuildComplianceReceiptInput,
): ComplianceReceipt {
  if (!SCREEN_RESULTS.includes(input.screen_result as ScreenResult)) {
    throw new ComplianceReceiptError(
      `screen_result must be one of ${JSON.stringify([...SCREEN_RESULTS])}, got ${JSON.stringify(input.screen_result)}`,
    );
  }

  return {
    payer_ref: requireNonEmptyString('payer_ref', input.payer_ref),
    screen_result: input.screen_result as ScreenResult,
    screen_timestamp_ms: requireIntTimestampMs(input.screen_timestamp_ms),
    screen_provider_did: requireNonEmptyString(
      'screen_provider_did',
      input.screen_provider_did,
    ),
    jurisdiction_flags: requireJurisdictionFlags(input.jurisdiction_flags),
    canon_version: requireNonEmptyString(
      'canon_version',
      input.canon_version ?? CANON_VERSION,
    ),
  };
}
