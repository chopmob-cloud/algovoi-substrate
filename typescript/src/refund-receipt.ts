/**
 * Refund receipt shape — companion to compliance-receipt.
 *
 * The categorical outcome (FULL / PARTIAL / REJECTED) is load-bearing
 * for downstream consumer-rights and PSD2 obligations: a REJECTED
 * outcome carries dispute-evidence obligations distinct from
 * FULL/PARTIAL, and the receipt format preserves the operational
 * distinction at the canonical-bytes level rather than collapsing it
 * to a score or tier projection.
 *
 * Specified in IETF Internet-Draft draft-hopley-x402-refund-receipt-00
 * (Independent Submission, Informational; AlgoVoi-authored).
 */

import { CANON_VERSION } from './canonicalize.js';

export const REFUND_RESULTS = ['FULL', 'PARTIAL', 'REJECTED'] as const;
export type RefundResult = (typeof REFUND_RESULTS)[number];

export class RefundReceiptError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'RefundReceiptError';
  }
}

export interface RefundAmount {
  amount_minor: string;
  asset_id: string;
}

export interface RefundReceipt {
  canon_version: string;
  jurisdiction_flags: string[];
  original_payment_ref: string;
  refund_amount: RefundAmount;
  refund_provider_did: string;
  refund_result: RefundResult;
  refund_timestamp_ms: number;
}

export interface BuildRefundReceiptInput {
  original_payment_ref: string;
  refund_result: string;
  refund_timestamp_ms: number;
  refund_provider_did: string;
  refund_amount: RefundAmount;
  jurisdiction_flags: string[];
  canon_version?: string;
}

function requireNonEmptyString(field: string, value: unknown): string {
  if (typeof value !== 'string' || value.length === 0) {
    throw new RefundReceiptError(`${field} must be a non-empty string`);
  }
  return value;
}

function requireIntTimestampMs(value: unknown): number {
  if (typeof value !== 'number') {
    throw new RefundReceiptError(
      `refund_timestamp_ms must be epoch-millisecond integer (Substrate Rule 2), got ${typeof value}`,
    );
  }
  if (!Number.isFinite(value) || !Number.isInteger(value)) {
    throw new RefundReceiptError(
      `refund_timestamp_ms must be epoch-millisecond integer (Substrate Rule 2), got ${value}`,
    );
  }
  if (value < 0) {
    throw new RefundReceiptError(
      `refund_timestamp_ms must be non-negative, got ${value}`,
    );
  }
  return value;
}

function requireJurisdictionFlags(value: unknown): string[] {
  if (!Array.isArray(value)) {
    throw new RefundReceiptError(
      `jurisdiction_flags must be array, got ${typeof value}`,
    );
  }
  for (let i = 0; i < value.length; i++) {
    const code = value[i];
    if (typeof code !== 'string' || code.length === 0) {
      throw new RefundReceiptError(
        `jurisdiction_flags[${i}] must be a non-empty string`,
      );
    }
  }
  return [...value] as string[];
}

function requireRefundAmount(value: unknown): RefundAmount {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new RefundReceiptError(
      `refund_amount must be object, got ${Array.isArray(value) ? 'array' : typeof value}`,
    );
  }
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  const expected = ['amount_minor', 'asset_id'];
  if (
    keys.length !== expected.length ||
    keys[0] !== expected[0] ||
    keys[1] !== expected[1]
  ) {
    throw new RefundReceiptError(
      `refund_amount must have exactly the keys ${JSON.stringify(expected)}, got ${JSON.stringify(keys)}`,
    );
  }
  const amount_minor = obj.amount_minor;
  const asset_id = obj.asset_id;
  if (typeof amount_minor !== 'string' || amount_minor.length === 0) {
    throw new RefundReceiptError(
      'refund_amount.amount_minor must be a non-empty string (decimal digits in the asset\'s minor unit; string-typed to avoid float-precision and JS-integer-overflow concerns)',
    );
  }
  if (!/^[0-9]+$/.test(amount_minor)) {
    throw new RefundReceiptError(
      `refund_amount.amount_minor must be decimal digits only, got ${JSON.stringify(amount_minor)}`,
    );
  }
  if (typeof asset_id !== 'string' || asset_id.length === 0) {
    throw new RefundReceiptError(
      'refund_amount.asset_id must be a non-empty string',
    );
  }
  return { amount_minor, asset_id };
}

/**
 * Build a validated refund receipt object.
 *
 * refund_result MUST be one of FULL, PARTIAL, REJECTED — the categorical
 * outcome is load-bearing for downstream consumer-rights and PSD2
 * obligations and must not be projected to a score/tier representation.
 *
 * original_payment_ref is expected to be a content-addressed reference
 * (e.g. "sha256:<hex>") to the original payment record. When refunding
 * a payment admitted under a compliance receipt, the conventional
 * choice is the compliance receipt's content_hash.
 *
 * refund_amount carries the refunded value as {amount_minor: string,
 * asset_id: string}. amount_minor is a decimal-digit string in the
 * asset's minor unit (e.g. "100000" for 0.1 USDC under asset_id
 * "USDC.6"). String typing avoids float-precision loss and JS-integer
 * overflow for large values.
 *
 * jurisdiction_flags is treated as ordered — ["UK","EU"] and
 * ["EU","UK"] produce distinct canonical bytes per RFC 8785 §3.2.3.
 */
export function buildRefundReceipt(
  input: BuildRefundReceiptInput,
): RefundReceipt {
  if (!REFUND_RESULTS.includes(input.refund_result as RefundResult)) {
    throw new RefundReceiptError(
      `refund_result must be one of ${JSON.stringify([...REFUND_RESULTS])}, got ${JSON.stringify(input.refund_result)}`,
    );
  }

  return {
    canon_version: requireNonEmptyString(
      'canon_version',
      input.canon_version ?? CANON_VERSION,
    ),
    jurisdiction_flags: requireJurisdictionFlags(input.jurisdiction_flags),
    original_payment_ref: requireNonEmptyString(
      'original_payment_ref',
      input.original_payment_ref,
    ),
    refund_amount: requireRefundAmount(input.refund_amount),
    refund_provider_did: requireNonEmptyString(
      'refund_provider_did',
      input.refund_provider_did,
    ),
    refund_result: input.refund_result as RefundResult,
    refund_timestamp_ms: requireIntTimestampMs(input.refund_timestamp_ms),
  };
}
