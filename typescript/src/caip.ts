/**
 * Chain Agnostic Improvement Proposal (CAIP) identifier grammar: CAIP-2 chain ids,
 * CAIP-10 account ids, CAIP-19 asset ids.
 *
 * These identifiers name the chain, account, and asset a receipt refers to in a
 * chain-agnostic way. When such an identifier is folded into a canonicalised,
 * content-addressed record (see ./canonicalize.js), it becomes part of the preimage:
 * two verifiers must agree on its exact bytes or their hashes diverge and the record
 * stops recomputing. So the identifier is not merely valid or not, it must be
 * BYTE-CANONICAL. The strict require* forms are the pre-hash gate an offline verifier
 * uses to refuse a non-canonical identifier before it reaches the digest.
 *
 * Anchor discipline (cross-language note): these validators anchor with ^ and $ and
 * are compiled WITHOUT the multiline (m) flag. In JavaScript, $ without m matches only
 * the end of input, so "eip155:1\n" is correctly rejected. This differs from Python,
 * whose $ also matches just before a trailing \n; the Python sibling therefore anchors
 * with \A and \Z instead. Same grammar, byte-identical accept/reject set, arrived at by
 * language-appropriate anchors. A validator matrix that missed this would let some
 * implementations accept a trailing-newline identifier that others reject.
 *
 * Grammar (verbatim from CAIP-2/10/19, ChainAgnostic/CAIPs):
 *   chain_id    = namespace ":" reference     namespace [-a-z0-9]{3,8}  reference [-_a-zA-Z0-9]{1,32}
 *   account_id  = chain_id ":" address        address   [-.%a-zA-Z0-9]{1,128}
 *   asset_type  = chain_id "/" ns ":" ref     asset ns [-a-z0-9]{3,8}   asset ref [-.%a-zA-Z0-9]{1,128}
 *   asset_id    = asset_type "/" token_id     token_id  [-.%a-zA-Z0-9]{1,78}
 *
 * Licensed under Apache 2.0.
 */

const CHAIN = '[-a-z0-9]{3,8}:[-_a-zA-Z0-9]{1,32}';
const CAIP2_RE = new RegExp(`^${CHAIN}$`);
const CAIP10_RE = new RegExp(`^${CHAIN}:[-.%a-zA-Z0-9]{1,128}$`);
const CAIP19_RE = new RegExp(`^${CHAIN}/[-a-z0-9]{3,8}:[-.%a-zA-Z0-9]{1,128}(/[-.%a-zA-Z0-9]{1,78})?$`);

/** Raised by the require* gates when an identifier is not byte-canonical CAIP. */
export class CaipError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CaipError';
  }
}

// Hostile-input-safe rendering for error messages. JSON.stringify throws on a BigInt and
// String() throws on a Symbol, so neither is safe alone for an arbitrary rejected value.
function show(x: unknown): string {
  switch (typeof x) {
    case 'string': return JSON.stringify(x);
    case 'bigint': return `${x}n`;
    case 'symbol': return x.toString();
    case 'function': return 'function';
    default:
      try { return JSON.stringify(x) ?? String(x); } catch { return Object.prototype.toString.call(x); }
  }
}

/** True iff `s` is a byte-canonical CAIP-2 chain id. */
export function isCaip2(s: unknown): boolean {
  return typeof s === 'string' && CAIP2_RE.test(s);
}

/** True iff `s` is a byte-canonical CAIP-10 account id. */
export function isCaip10(s: unknown): boolean {
  return typeof s === 'string' && CAIP10_RE.test(s);
}

/** True iff `s` is a byte-canonical CAIP-19 asset type or asset id. */
export function isCaip19(s: unknown): boolean {
  return typeof s === 'string' && CAIP19_RE.test(s);
}

/**
 * Return `s` unchanged if it is a canonical CAIP-2, else throw {@link CaipError}.
 * The pre-hash gate: call it on any chain id before it is folded into a canonicalised
 * record, so a non-canonical identifier fails closed rather than silently producing a
 * non-reproducible digest.
 */
export function requireCaip2(s: unknown): string {
  if (!isCaip2(s)) throw new CaipError(`not a canonical CAIP-2 chain id: ${show(s)}`);
  return s as string;
}

/** Return `s` if it is a canonical CAIP-10 account id, else throw {@link CaipError}. */
export function requireCaip10(s: unknown): string {
  if (!isCaip10(s)) throw new CaipError(`not a canonical CAIP-10 account id: ${show(s)}`);
  return s as string;
}

/** Return `s` if it is a canonical CAIP-19 asset type or id, else throw {@link CaipError}. */
export function requireCaip19(s: unknown): string {
  if (!isCaip19(s)) throw new CaipError(`not a canonical CAIP-19 asset id: ${show(s)}`);
  return s as string;
}

/**
 * Build the CAIP-19 asset type for a chain's native coin via the slip44 namespace.
 * `caip19Slip44("eip155:1", 60)` -> `"eip155:1/slip44:60"`. The chain id is gated with
 * {@link requireCaip2} and the result with {@link requireCaip19}, so the output is
 * guaranteed byte-canonical.
 */
export function caip19Slip44(chainCaip2: string, coinType: number): string {
  if (typeof coinType !== 'number' || !Number.isInteger(coinType) || coinType < 0) {
    throw new CaipError(`slip44 coinType must be a non-negative integer: ${show(coinType)}`);
  }
  return requireCaip19(`${requireCaip2(chainCaip2)}/slip44:${coinType}`);
}

/**
 * Build the CAIP-10 account id for `address` on `chainCaip2`.
 * `caip10Of("eip155:1", "0xab..")` -> `"eip155:1:0xab.."`. The chain id is gated with
 * {@link requireCaip2} and the result with {@link requireCaip10}. Throws {@link CaipError}
 * when the address is not a canonical CAIP-10 account address.
 */
export function caip10Of(chainCaip2: string, address: string): string {
  if (typeof address !== 'string') {
    throw new CaipError(`address must be a string: ${show(address)}`);
  }
  return requireCaip10(`${requireCaip2(chainCaip2)}:${address}`);
}

// Registered CAIP-2 namespaces, vendored from ChainAgnostic/namespaces (main, verified
// 2026-07-19): every registry directory that defines a caip2.md, using its declared
// namespace-identifier (minus the "-caip2" suffix, lowercased per the CAIP-2 lowercase rule)
// or, for prose-only entries, the directory name. The namespace is NOT always the directory
// name: the "avalanche" directory registers the namespace "avax". OPT-IN realness layer; the
// grammar validators above stay namespace-agnostic so future/unregistered chains still
// validate. Refresh from the registry as new namespaces land.
export const REGISTERED_NAMESPACES: ReadonlySet<string> = new Set([
  'aleo', 'alephium', 'algorand', 'antelope', 'aptos', 'arweave', 'avax', 'bip122', 'casper',
  'ccd', 'chia', 'conflux', 'cosmos', 'eip155', 'ergo', 'fil', 'flow', 'haneul', 'hedera',
  'hive', 'iota', 'koinos', 'mina', 'monero', 'mvx', 'partisia', 'polkadot', 'quai', 'reef',
  'solana', 'stacks', 'starknet', 'stellar', 'sui', 'swift', 'tezos', 'tvm', 'vechain',
  'wallet', 'waves', 'xrpl',
]);

/** The set of CAIP-2 namespaces registered in ChainAgnostic/namespaces (vendored). */
export function registeredNamespaces(): ReadonlySet<string> {
  return REGISTERED_NAMESPACES;
}

/** True iff `ns` is a registered CAIP-2 namespace (e.g. "eip155", "avax", "swift"). */
export function isRegisteredNamespace(ns: unknown): boolean {
  return typeof ns === 'string' && REGISTERED_NAMESPACES.has(ns);
}

/** True iff `s` is a canonical CAIP-2 AND its namespace is registered. */
export function isRegisteredCaip2(s: unknown): boolean {
  return isCaip2(s) && REGISTERED_NAMESPACES.has((s as string).split(':')[0] ?? '');
}

/** True iff `s` is a canonical CAIP-10 AND its chain namespace is registered. */
export function isRegisteredCaip10(s: unknown): boolean {
  return isCaip10(s) && REGISTERED_NAMESPACES.has((s as string).split(':')[0] ?? '');
}

/** True iff `s` is a canonical CAIP-19 AND its chain namespace is registered. */
export function isRegisteredCaip19(s: unknown): boolean {
  return isCaip19(s) && REGISTERED_NAMESPACES.has((s as string).split(':')[0] ?? '');
}

/** Return `s` if it is a canonical CAIP-2 on a registered namespace, else throw. */
export function requireRegisteredCaip2(s: unknown): string {
  if (!isRegisteredCaip2(s)) throw new CaipError(`not a canonical CAIP-2 on a registered namespace: ${show(s)}`);
  return s as string;
}

/** Return `s` if it is a canonical CAIP-10 on a registered namespace, else throw. */
export function requireRegisteredCaip10(s: unknown): string {
  if (!isRegisteredCaip10(s)) throw new CaipError(`not a canonical CAIP-10 on a registered namespace: ${show(s)}`);
  return s as string;
}

/** Return `s` if it is a canonical CAIP-19 on a registered namespace, else throw. */
export function requireRegisteredCaip19(s: unknown): string {
  if (!isRegisteredCaip19(s)) throw new CaipError(`not a canonical CAIP-19 on a registered namespace: ${show(s)}`);
  return s as string;
}

// Per-namespace CAIP-2 reference formats, verified against each namespace's caip2.md in
// ChainAgnostic/namespaces (2026-07-19). Strictest OPT-IN tier: rejects a grammar-valid,
// registered identifier whose reference is not well-formed for its namespace (e.g.
// "eip155:abc"). Only namespaces with a clear spec-defined format are listed; a registered
// namespace without a rule is accepted, keeping the layer additive and chain-agnostic.
const REFERENCE_FORMATS: Record<string, RegExp> = {
  eip155: /^[0-9]{1,32}$/,                    // decimal chain id (EIP-155)
  bip122: /^[0-9a-f]{32}$/,                   // first 16 bytes of genesis hash, lowercase hex
  polkadot: /^[0-9a-f]{32}$/,                 // spec regex [0-9a-f]{32}
  solana: /^[1-9A-HJ-NP-Za-km-z]{32}$/,       // first 32 chars of base58 genesis hash
  starknet: /^SN_[A-Z0-9]{1,29}$/,            // ASCII-decoded chain id, e.g. SN_MAIN
};

/** Namespaces for which a per-reference format rule is enforced by the is_valid_* tier. */
export const REFERENCE_FORMAT_NAMESPACES: ReadonlySet<string> = new Set(Object.keys(REFERENCE_FORMATS));

function nsRef(s: string): [string, string] {
  const c = s.indexOf(':');
  if (c < 0) return [s, ''];
  const rest = s.slice(c + 1);
  let cut = rest.length;
  for (const d of [':', '/']) {
    const i = rest.indexOf(d);
    if (i >= 0) cut = Math.min(cut, i);
  }
  return [s.slice(0, c), rest.slice(0, cut)];
}

function referenceFormatOk(s: string): boolean {
  const [ns, ref] = nsRef(s);
  const rule = REFERENCE_FORMATS[ns];
  return rule === undefined || rule.test(ref);
}

/** True iff `s` is a canonical CAIP-2 on a registered namespace whose reference is also
 *  well-formed for that namespace (strictest tier; e.g. rejects "eip155:abc"). */
export function isValidCaip2(s: unknown): boolean {
  return isRegisteredCaip2(s) && referenceFormatOk(s as string);
}

/** CAIP-10 whose chain is registered and whose chain reference matches its namespace format. */
export function isValidCaip10(s: unknown): boolean {
  return isRegisteredCaip10(s) && referenceFormatOk(s as string);
}

/** CAIP-19 whose chain is registered and whose chain reference matches its namespace format. */
export function isValidCaip19(s: unknown): boolean {
  return isRegisteredCaip19(s) && referenceFormatOk(s as string);
}

/** Return `s` if it is a valid CAIP-2 (registered namespace + conformant reference), else throw. */
export function requireValidCaip2(s: unknown): string {
  if (!isValidCaip2(s)) throw new CaipError(`not a valid CAIP-2 (registered namespace + conformant reference): ${show(s)}`);
  return s as string;
}

/** Return `s` if it is a valid CAIP-10, else throw. */
export function requireValidCaip10(s: unknown): string {
  if (!isValidCaip10(s)) throw new CaipError(`not a valid CAIP-10 (registered namespace + conformant reference): ${show(s)}`);
  return s as string;
}

/** Return `s` if it is a valid CAIP-19, else throw. */
export function requireValidCaip19(s: unknown): string {
  if (!isValidCaip19(s)) throw new CaipError(`not a valid CAIP-19 (registered namespace + conformant reference): ${show(s)}`);
  return s as string;
}
