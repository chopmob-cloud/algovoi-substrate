# Changelog

All notable changes to `algovoi-substrate` (Python) and `@algovoi/substrate`
(TypeScript) are documented here. Both packages ship in lockstep.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-05-23

### Added

- **Transactional `action_ref` lifecycle primitive.** New module
  `algovoi_substrate.transactional` (Python) / `@algovoi/substrate`
  re-exports `transitionHash`, `buildTransactionalActionChain` (TypeScript).
  Captures the substrate-level discipline that `action_ref` is the
  stable identity anchor across multi-state transactional flows
  (authorisation → settlement → refund; issuance → execution →
  revocation; admission → review → close), with per-transition
  lifecycle metadata sitting outside the `action_ref` preimage.

  New primitives:
  - `transition_hash(action_ref, state, transition_timestamp_ms,
    authority_verified_at_ms, revocation_check_at_ms) -> str` (Python)
    / `transitionHash(...)` (TypeScript). Returns the lowercase hex
    SHA-256 of the five-field transition preimage.
  - `build_transactional_action_chain(agent_id, action_type, scope,
    timestamp_ms, transitions) -> dict` (Python) /
    `buildTransactionalActionChain(...)` (TypeScript). Emits the chain
    shape `{action_ref, transitions: [{...transition_hash}]}` with
    `action_ref` byte-stable across every transition and each
    `transition_hash` cryptographically bound to it.

  All timestamp fields enforced as epoch-millisecond integers
  (Substrate Rule 2); RFC 3339 string forms are rejected at validation
  time. State value is a non-empty string with no closed enum at the
  canonicalisation layer; payment-lifecycle vocabularies
  (authorisation/settlement/refund) are recommended but not enforced.

  Byte-level reference digests pinned in the
  [`action_ref_transactional_v0`](https://github.com/chopmob-cloud/algovoi-jcs-conformance-vectors/tree/main/vectors/action_ref_transactional_v0)
  conformance vector set (8 vectors + 5 pair invariants), cross-validated
  byte-for-byte against Python and TypeScript reference impls.

  Spec authorship: AlgoVoi-authored, documented as the "Transactional
  `action_ref` lifecycle" non-normative section of the canonicalisation
  discipline in
  [x402-foundation/x402 PR #2436](https://github.com/x402-foundation/x402/pull/2436)
  (commit f81f2fe4).

### Tests

- 20 new Python tests + 16 new TypeScript tests for the transactional
  primitive: determinism, state-distinctness, action_ref binding,
  RFC 3339 string rejection, float / boolean / negative timestamp
  rejection, three-state payment lifecycle end-to-end, free-form state
  vocabularies. Full suite now 74 Python + 68 TypeScript tests pass.

### Unchanged from 0.2.1

- All existing primitives (`canonicalize`, `action_ref`,
  `composite_trust_query_hash`, `build_compliance_receipt`,
  `verify_audit_chain`) retain identical signatures and byte-for-byte
  output to 0.2.1 and earlier. The 0.3.0 release is additive only;
  existing pinned consumers (`==0.2.1`) can upgrade safely.

## [0.2.1] - 2026-05-23

### Fixed

- **Python**: `algovoi_substrate.__version__` constant now reports `0.2.1`,
  aligned with the package version. In v0.2.0 the constant was inadvertently
  left at `"0.1.0"` despite `pyproject.toml` reading `0.2.0`. Cosmetic only
  (no byte-level effect on any primitive output); the v0.2.0 release was
  cross-validated byte-for-byte against `@algovoi/substrate@0.2.0`.
- **TypeScript**: no source change; version bumped to 0.2.1 to keep PyPI
  and npm in lockstep per the project's standing release convention.

### Unchanged from 0.2.0

- Scope conventions section in README + Mintlify docs.
- All primitives (`canonicalize`, `action_ref`, `composite_trust_query_hash`,
  `build_compliance_receipt`, `verify_audit_chain`) retain identical
  signatures and byte-for-byte output to 0.2.0 and 0.1.0.

## [0.2.0] - 2026-05-23

### Added

- **Scope conventions for `action_ref` (non-normative)**. The substrate now
  documents the production convention emerging across its emitter set for
  `action_ref`'s `scope` field, plus a recommended `<emitter>:<scope>`
  namespacing form. The substrate-level constraint remains "non-empty
  string"; the recommendation is non-normative on values to preserve room
  for future emitters. See the `Scope conventions` section in the README
  and on [docs.algovoi.co.uk/canonicalisation-substrate](https://docs.algovoi.co.uk/canonicalisation-substrate).

  - Current production usage surveyed: `settlement` (Vauban Pay STARK
    receipts; AlgoVoi `/compliance/attestation`), `bilateral` (nobulex
    receipts; CTEF v0.3.1), `compliance_screen` (AlgoVoi
    `/compliance/screen`), `agent_os` (Agent OS COMMITTED Claim Engine
    8715), `payment` and `access` (AURA reputation dimensions).
  - Recommended portable form: `algovoi:compliance_screen`,
    `vauban:stark_settlement`, `agent_os:committed_claim`,
    `aura:reputation_observe`.
  - Convention also being proposed as a non-normative paragraph in the
    canonicalisation spec text
    ([x402#2436](https://github.com/x402-foundation/x402/pull/2436)).

  Authorship: AlgoVoi-authored, first published in response to AURA's
  scope-enum question on
  [x402#2332 comment 4526409528](https://github.com/x402-foundation/x402/issues/2332#issuecomment-4526409528).

### Changed

- `README.md` updated with `Scope conventions` section under the `action_ref`
  primitive documentation.

### Unchanged (no API breakage)

- All primitives (`canonicalize`, `action_ref`, `composite_trust_query_hash`,
  `build_compliance_receipt`, `verify_audit_chain`) retain identical
  signatures and byte-for-byte output to v0.1.0. The 0.2.0 release is
  documentation-additive only; existing pinned consumers (`==0.1.0`) can
  upgrade safely.
- The 53-vector substrate matrix produces identical digests under v0.2.0
  as under v0.1.0.

## [0.1.0] - 2026-05-22

### Added

- Initial release: Python (`algovoi-substrate` on PyPI) and TypeScript
  (`@algovoi/substrate` on npm) reference implementations of the AlgoVoi
  agentic-payments substrate.
- Primitives: JCS RFC 8785 canonicalisation with the AlgoVoi discipline
  rules, `action_ref` atomic primitive, composite trust-query algorithm
  (PR #2440), compliance receipt shape matching production
  `/compliance/screen` emission, audit chain primitive
  (`content_hash` + `prev_hash` linking).
- Cross-validated byte-for-byte against five JCS reference implementations:
  Python `rfc8785@0.1.4`, JS `canonicalize@3.0.0`, Go `gowebpki/jcs v1.0.1`,
  Java `cyberphone/json-canonicalization`, Rust `serde_jcs@0.2.0`.
