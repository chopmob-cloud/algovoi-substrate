# @algovoi/substrate (TypeScript)

AlgoVoi agentic-payments substrate reference implementation.

JCS RFC 8785 canonicalisation, `actionRef` atomic primitive, composite
trust-query algorithm, compliance receipt shape, and audit chain primitives
that compose the substrate underneath x402, AP2, A2A, and MPP receipts.

The substrate runs in production at `https://api.algovoi.co.uk/compliance`.
This package is the AlgoVoi-authored TypeScript reference implementation;
cross-validated byte-for-byte against four other JCS implementations
(Python `rfc8785`, Go `gowebpki/jcs`, Java `cyberphone`, Rust `serde_jcs`)
on 53 conformance vectors and 3 composite-trust-query vectors.

## Install

```bash
npm install @algovoi/substrate
```

## Quickstart

```typescript
import {
  canonicalize,
  sha256Jcs,
  actionRef,
  compositeTrustQueryHash,
  buildComplianceReceipt,
  appendToChain,
  verifyAuditChain,
} from '@algovoi/substrate';

// Canonicalise to RFC 8785 JCS string.
canonicalize({ b: 1, a: 2 }); // -> '{"a":2,"b":1}'

// action_ref atomic primitive:
// SHA-256(JCS({agent_id, action_type, scope, timestamp_ms}))
const ref = actionRef({
  agent_id: 'agent-x',
  action_type: 'payment',
  scope: 'bilateral',
  timestamp_ms: 1716460800000,
});

// Composite trust-query (PR #2440 in x402-foundation/x402).
const compositeHash = compositeTrustQueryHash([
  { source_id: 'trust-a', score: 80, sig: 'sig-bytes' },
  { source_id: 'trust-b', score: 75, sig: 'sig-bytes' },
]);

// Compliance receipt (AlgoVoi production schema).
const receipt = buildComplianceReceipt({
  payer_ref: 'sha256:abc123',
  screen_result: 'ALLOW',
  screen_timestamp_ms: 1716460800000,
  screen_provider_did: 'did:web:api.algovoi.co.uk',
  jurisdiction_flags: ['UK', 'EU'],
});

// Audit chain: monotonic per-row hash chain.
const row0 = appendToChain(receipt, null);
const row1 = appendToChain({ event: 'next' }, row0);
verifyAuditChain([row0, row1]);
```

## Substrate discipline

This package enforces the AlgoVoi-authored substrate-discipline rules
formalised in [IETF Internet-Draft `draft-hopley-x402-canonicalisation-jcs-v1`](https://datatracker.ietf.org/doc/draft-hopley-x402-canonicalisation-jcs-v1/)
(Independent Submission, Informational; sole AlgoVoi authorship) and
proposed for inclusion in `x402-foundation/x402` via [PR #2453](https://github.com/x402-foundation/x402/pull/2453)
(replaces closed [#2436](https://github.com/x402-foundation/x402/pull/2436)):

- **Rule 1.** `timestamp_ms` is an epoch-millisecond integer. Floats, ISO
  8601 strings, and negative values are rejected at the source-side.
- **Rule 4.** Type validation happens before canonicalisation. Schema-level
  fields that should be integers reject floats hard, not silent-cast.
- **`canon_version` pin.** Receipts carry `canon_version: "jcs-rfc8785-v1"`
  as an in-band format-version pin for year-five auditability.
- **Array element order preserved.** `["UK","EU"]` and `["EU","UK"]` hash
  differently per RFC 8785 §3.2.3 -- producer-side ordering is load-bearing.

The categorical screen result (`ALLOW` / `REFER` / `DENY`) is enforced as a
closed set.

## Cross-impl validation

This TypeScript package is byte-for-byte equivalent to the Python sibling
(`algovoi-substrate` on PyPI). The substrate has been validated across five
implementations:

- Python `rfc8785@0.1.4`
- JavaScript / TypeScript `canonicalize@3.0.0` (this package)
- Go `gowebpki/jcs v1.0.1`
- Java `cyberphone/json-canonicalization`
- Rust `serde_jcs@0.2.0`

Substrate matrix:
<https://gist.github.com/chopmob-cloud/b327814c4e17ed9fc7b4f29c8bda523c>

Composite trust-query matrix:
<https://gist.github.com/chopmob-cloud/f2e9f0877b7d9fff70c8eca46e4ce636>

## Tests

```bash
npm install
npm test
```

## Production reference

The reference exhibit for this substrate is AlgoVoi's
`/compliance/attestation` audit chain, live at
`https://api.algovoi.co.uk/compliance/attestation`. The migration boundary
(receipts before / after 2026-05-21) is observable directly from the chain.

## Spec references

- [draft-hopley-x402-canonicalisation-jcs-v1](https://datatracker.ietf.org/doc/draft-hopley-x402-canonicalisation-jcs-v1/) -- IETF I-D (Independent Submission, Informational, sole AlgoVoi authorship). Specifies `urn:x402:canonicalisation:jcs-rfc8785-v1`.
- [docs.algovoi.co.uk/canonicalisation-substrate](https://docs.algovoi.co.uk/canonicalisation-substrate) -- v1 discipline reference page.
- [docs.algovoi.co.uk/canonicalisation-substrate-v2](https://docs.algovoi.co.uk/canonicalisation-substrate-v2) -- v2 (PQC-aware) additive successor.
- [PR #2453](https://github.com/x402-foundation/x402/pull/2453) -- live upstream spec PR for the canonicalisation discipline (sole AlgoVoi authorship; replaces closed #2436).
- [draft-vauban-x402-stark-receipts](https://datatracker.ietf.org/doc/draft-vauban-x402-stark-receipts/) -- third-party adopter-authored receipt format that anchors to the AlgoVoi canonicalisation discipline.

## Conformance to the canonicalisation discipline

This package emits receipts pinned to `canon_version: jcs-rfc8785-v1` in-band. Downstream verifiers (`algovoi-audit-verifier` and any conformant third-party verifier) read the pin to select the canonicalisation rule applied at emission.

The pin is the load-bearing primitive for the [Substrate Adopters Registry](https://docs.algovoi.co.uk/adopters): adopters anchoring to this discipline pin the same `canon_version` value in their own publicly-citable artefacts. AlgoVoi maintains the registry as a neutral observer; this package is recorded there as the AlgoVoi reference implementation.

## Substrate adopters

AlgoVoi is recorded in the [Substrate Adopters Registry](https://docs.algovoi.co.uk/adopters) as the substrate author (v1 and v2). Parties anchoring their own services or specifications to `canon_version: jcs-rfc8785-v1` are recorded in the registry via the [submission process](https://docs.algovoi.co.uk/adopters#how-to-submit-an-adoption-entry). AlgoVoi validates submissions against the artefact's canonical bytes and adds qualifying entries.

## Licence

Apache 2.0. See `LICENSE`.

## Author

AlgoVoi (Christopher Hopley, GitHub `chopmob-cloud`).
