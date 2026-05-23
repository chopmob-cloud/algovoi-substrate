# Changelog

All notable changes to `algovoi-substrate` (Python) and `@algovoi/substrate`
(TypeScript) are documented here. Both packages ship in lockstep.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
