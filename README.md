# algovoi-substrate

AlgoVoi agentic-payments substrate reference implementation.

Python (`algovoi-substrate` on PyPI) and TypeScript (`@algovoi/substrate` on
npm) reference implementations of the AlgoVoi-authored primitives that
compose the substrate underneath x402, AP2, A2A, and MPP receipts:

- JCS RFC 8785 canonicalisation with the AlgoVoi-discipline rules
  (type-validation pre-canonicalisation, in-band `canon_version` pin).
- `action_ref` atomic primitive:
  `SHA-256(JCS({agent_id, action_type, scope, timestamp_ms}))`.
- Composite trust-query algorithm (PR #2440 in `x402-foundation/x402`).
- Compliance receipt shape matching AlgoVoi's production
  `/compliance/screen` emission.
- Audit chain primitive: monotonic per-row hash chain with
  `content_hash` + `prev_hash` linking.

## Packages

- **Python**: [`python/`](./python/) -- `pip install algovoi-substrate`
- **TypeScript**: [`typescript/`](./typescript/) -- `npm install @algovoi/substrate`

Python and TypeScript produce **byte-for-byte identical** hashes on the same
input. Cross-validated against three additional JCS implementations (Go
`gowebpki/jcs v1.0.1`, Java `cyberphone/json-canonicalization`, Rust
`serde_jcs@0.2.0`).

## Substrate matrices

- **53-vector substrate matrix** (Apache 2.0, AlgoVoi-authored):
  <https://gist.github.com/chopmob-cloud/b327814c4e17ed9fc7b4f29c8bda523c>
- **Composite trust-query 5-impl matrix** (15 / 15 byte-for-byte):
  <https://gist.github.com/chopmob-cloud/f2e9f0877b7d9fff70c8eca46e4ce636>

## Production reference

The substrate runs in production at <https://api.algovoi.co.uk/compliance>.
The `/compliance/attestation` audit chain is the reference exhibit for the
`canon_version` migration boundary (pre-/post-2026-05-21) and retains
receipts under seven-year Object Lock COMPLIANCE retention.

## Spec references

- [PR #2436](https://github.com/x402-foundation/x402/pull/2436) -- canonicalisation discipline (three-voice coalition co-signed)
- [PR #2440](https://github.com/x402-foundation/x402/pull/2440) -- composite trust-query (tri-party co-signed)
- [PR #2434](https://github.com/x402-foundation/x402/pull/2434) -- compliance-receipt-fixture
- [draft-vauban-x402-stark-receipts](https://datatracker.ietf.org/doc/draft-vauban-x402-stark-receipts/) -- IETF I-D referencing the substrate (`urn:x402:canonicalisation:jcs-rfc8785-v1`)

## Licence

Apache 2.0. See [`LICENSE`](./LICENSE).

## Author

AlgoVoi (Christopher Hopley, GitHub [`chopmob-cloud`](https://github.com/chopmob-cloud)).
