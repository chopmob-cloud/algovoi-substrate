> **AlgoVoi is available for acquisition** — [docs.algovoi.co.uk/acquisition](https://docs.algovoi.co.uk/acquisition)

---

# algovoi-substrate

[![PyPI](https://img.shields.io/pypi/v/algovoi-substrate?label=PyPI)](https://pypi.org/project/algovoi-substrate/)
[![npm](https://img.shields.io/npm/v/@algovoi/substrate?label=npm)](https://www.npmjs.com/package/@algovoi/substrate)
[![IETF I-D](https://img.shields.io/badge/IETF--I--D-draft--hopley--x402--compliance--receipt--00-blue)](https://datatracker.ietf.org/doc/draft-hopley-x402-compliance-receipt/)
[![Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-green)](./LICENSE)

AlgoVoi agentic-payments substrate reference implementation.

The compliance receipt format and canonicalisation discipline specified by
this substrate are documented in IETF Internet-Draft
[`draft-hopley-x402-compliance-receipt`](https://datatracker.ietf.org/doc/draft-hopley-x402-compliance-receipt/)
(Independent Submission, Informational; posted to the IETF datatracker
2026-05-23). The Python and TypeScript packages here are the reference
implementations of the discipline the I-D specifies; the conformance vector
corpus is at
[`chopmob-cloud/algovoi-jcs-conformance-vectors`](https://github.com/chopmob-cloud/algovoi-jcs-conformance-vectors).

Python (`algovoi-substrate` on PyPI) and TypeScript (`@algovoi/substrate` on
npm) reference implementations of the AlgoVoi-authored primitives that
compose the substrate underneath x402, AP2, A2A, and MPP receipts:

- JCS RFC 8785 canonicalisation with the AlgoVoi-discipline rules
  (type-validation pre-canonicalisation, in-band `canon_version` pin).
- `action_ref` atomic primitive:
  `SHA-256(JCS({agent_id, action_type, scope, timestamp_ms}))`.
  `scope` is a non-empty string. See [Scope conventions](#scope-conventions)
  below for the recommended `<emitter>:<scope>` namespacing form.
- Composite trust-query algorithm (PR #2440 in `x402-foundation/x402`).
- Compliance receipt shape matching AlgoVoi's production
  `/compliance/screen` emission.
- Audit chain primitive: monotonic per-row hash chain with
  `content_hash` + `prev_hash` linking.
- Transactional `action_ref` lifecycle primitives:
  `transition_hash` + `build_transactional_action_chain`. `action_ref`
  stable across multi-state transitions (authorisation → settlement →
  refund); per-transition lifecycle metadata outside the preimage.
  See [Transactional lifecycle](#transactional-action_ref-lifecycle)
  below.

## Packages

- **Python**: [`python/`](./python/) -- `pip install algovoi-substrate`
- **TypeScript**: [`typescript/`](./typescript/) -- `npm install @algovoi/substrate`

Python and TypeScript produce **byte-for-byte identical** hashes on the same
input. Cross-validated against **six additional** JCS implementations from
non-overlapping authoring entities, including the RFC 8785 author himself
(Anders Rundgren via the Java implementation):

| Language | Package | Version | Author |
|---|---|---|---|
| Go | `gowebpki/jcs` | v1.0.1 | Web PKI Working Group |
| Rust | `serde_jcs` | 0.2.0 | l1h3r |
| Java | `erdtman/java-json-canonicalization` | 1.1 | Anders Rundgren + Samuel Erdtman |
| PHP | inline pure-stdlib JCS | AlgoVoi |
| C# / .NET | `Baqhub.Packages.JsonCanonicalization` | 1.0.1 | Baqhub |
| Ruby | `json-canonicalization` | 1.0.0 | RubyGems community |

**Latest 8-implementation attestation run (2026-05-24): 192/192
byte-for-byte agreements** across 24 vectors × 8 impls. See the
[full attestation record](https://github.com/chopmob-cloud/algovoi-jcs-conformance-vectors/blob/main/_attestations/2026-05-24-8-impl-cross-validation.md).

## Substrate matrices

- **53-vector substrate matrix** (Apache 2.0, AlgoVoi-authored):
  <https://gist.github.com/chopmob-cloud/b327814c4e17ed9fc7b4f29c8bda523c>
- **Composite trust-query 5-impl matrix** (15 / 15 byte-for-byte):
  <https://gist.github.com/chopmob-cloud/f2e9f0877b7d9fff70c8eca46e4ce636>

## Production reference

The substrate runs in production at <https://api.algovoi.co.uk/compliance>.
The `/compliance/attestation` audit chain is the reference exhibit for the
`canon_version` migration boundary (pre-/post-2026-05-21) and retains
receipts under seven-year Object Lock COMPLIANCE retention. The `action_ref` canonical hash computation is also available as a standalone public verifier at [`verify.algovoi.co.uk/action-ref`](https://verify.algovoi.co.uk/action-ref) — returns the RFC 8785 JCS canonical form and SHA-256 digest, verified byte-identical across 8 independent implementations.

## Scope conventions

`action_ref`'s `scope` field is typed as a non-empty string at the
canonicalisation layer. The cross-impl matrix validates the byte-equivalence
of the canonical form across the five reference implementations, not the
value-space.

A convention is emerging across the substrate's production emitter set, and
AlgoVoi documents it here as a non-normative recommendation.

**Today**: `scope` is a free-form non-empty string. Any non-empty string
derives a valid `action_ref`. The substrate does not impose a closed enum.

**Current production usage** across the substrate's emitter set:

| `scope` value | Emitter | Surface |
| --- | --- | --- |
| `settlement` | Vauban Pay STARK receipts; AlgoVoi `/compliance/attestation` | Settlement |
| `bilateral` | nobulex bilateral receipts; CTEF v0.3.1 bilateral framing | Bilateral |
| `compliance_screen` | AlgoVoi `/compliance/screen` | Admission |
| `agent_os` | Agent OS COMMITTED Claim Engine (8715) | Onboarding |
| `payment` | AURA `financial_integrity` reputation dimension | Reputation observe |
| `access` | AURA `security_compliance` reputation dimension | Reputation observe |

**Recommended portable form**: `<emitter>:<scope>` namespacing. As more
emitters compose against the substrate, an unprefixed value risks collision.
The portable form AlgoVoi recommends is:

- `algovoi:compliance_screen`
- `vauban:stark_settlement`
- `agent_os:committed_claim`
- `aura:reputation_observe`

The namespaced value is still hashed into `action_ref`, preserving the
dedup / idempotency property. The substrate-level constraint remains
"non-empty string"; closing the value-space at the spec level would lock out
future emitters arriving with valid new scopes.

**Authorship**: AlgoVoi-authored. First published in response to AURA's
scope-enum question on
[x402#2332 comment 4526409528](https://github.com/x402-foundation/x402/issues/2332#issuecomment-4526409528).
Also being proposed as a non-normative paragraph in the canonicalisation spec
text ([x402#2436](https://github.com/x402-foundation/x402/pull/2436)). The
canonical home is this README plus the linked spec PR; downstream forks and
adopter projects are welcome to cite the convention.

## Transactional `action_ref` lifecycle

For actions traversing multiple state transitions (authorisation →
settlement → refund; issuance → execution → revocation; admission →
review → close), `action_ref` serves as a **stable identity anchor
across the full lifecycle**. The four-field preimage
`{ agent_id, action_type, scope, timestamp_ms }` is fixed when the
action is first declared and does not change as the action progresses
through state transitions. Per-transition lifecycle metadata
(`authority_verified_at_ms`, `revocation_check_at_ms`, settlement-proof
timestamps, refund-window expiry) lives **outside** the `action_ref`
preimage as separate claims that evolve with the state.

The substrate ships two primitives for this:

```python
from algovoi_substrate import transition_hash, build_transactional_action_chain

# Single transition: cryptographic binding of a state transition to its action.
th = transition_hash(
    action_ref="<lowercase 64-char hex>",
    state="authorisation",
    transition_timestamp_ms=1716494400000,
    authority_verified_at_ms=1716494400500,
    revocation_check_at_ms=1716494400800,
)
# th = SHA-256(JCS({action_ref, state, transition_timestamp_ms,
#                   authority_verified_at_ms, revocation_check_at_ms}))

# Full chain: action_ref stable across all transitions; each transition
# bound to it. Emits {action_ref, transitions: [{...transition_hash}, ...]}.
chain = build_transactional_action_chain(
    agent_id="agent_alpha",
    action_type="payment",
    scope="vauban:stark_settlement",
    timestamp_ms=1716494400000,
    transitions=[
        {"state": "authorisation",
         "transition_timestamp_ms": 1716494400000,
         "authority_verified_at_ms": 1716494400500,
         "revocation_check_at_ms": 1716494400800},
        {"state": "settlement",
         "transition_timestamp_ms": 1716494500000,
         "authority_verified_at_ms": 1716494500300,
         "revocation_check_at_ms": 1716494500500},
        {"state": "refund",
         "transition_timestamp_ms": 1716494600000,
         "authority_verified_at_ms": 1716494600300,
         "revocation_check_at_ms": 1716494600500},
    ],
)
```

TypeScript exposes the same primitives as `transitionHash(...)` and
`buildTransactionalActionChain(...)` with byte-for-byte identical
output.

Load-bearing invariants:

1. `action_ref` is byte-stable across every transition of the same
   action.
2. `transition_hash` is bound to its `action_ref` (action_ref is part
   of the five-field transition preimage).
3. `transition_hash` differs per state under identical other-field
   values; `state` is byte-load-bearing in the preimage.
4. All timestamp fields are epoch-millisecond integers (Substrate
   Rule 2). RFC 3339 string forms are rejected at validation time.
5. `state` is typed as a non-empty string with no closed enum at the
   canonicalisation layer (consistent with the scope-field treatment).
   Payment-lifecycle vocabularies (authorisation/settlement/refund)
   are recommended but not enforced.

Byte-level reference digests are pinned in the
[`action_ref_transactional_v0`](https://github.com/chopmob-cloud/algovoi-jcs-conformance-vectors/tree/main/vectors/action_ref_transactional_v0)
conformance vector set: 8 vectors + 5 pair invariants, cross-validated
byte-for-byte against the Python and TypeScript reference impls.

Spec authorship: AlgoVoi-authored, documented as the "Transactional
`action_ref` lifecycle" non-normative section of the canonicalisation
discipline in
[x402-foundation/x402 PR #2436](https://github.com/x402-foundation/x402/pull/2436)
(commit f81f2fe4).

## Spec references

- [draft-hopley-x402-canonicalisation-jcs-v1](https://datatracker.ietf.org/doc/draft-hopley-x402-canonicalisation-jcs-v1/) -- IETF Internet-Draft (Independent Submission, Informational, sole AlgoVoi authorship). Specifies `urn:x402:canonicalisation:jcs-rfc8785-v1`.
- [docs.algovoi.co.uk/canonicalisation-substrate](https://docs.algovoi.co.uk/canonicalisation-substrate) -- v1 discipline reference page.
- [docs.algovoi.co.uk/canonicalisation-substrate-v2](https://docs.algovoi.co.uk/canonicalisation-substrate-v2) -- v2 (PQC-aware) additive successor.
- [x402#2453](https://github.com/x402-foundation/x402/pull/2453) -- live upstream spec PR for the canonicalisation discipline (sole AlgoVoi authorship; replaces closed [#2436](https://github.com/x402-foundation/x402/pull/2436)).
## Adopters

Parties pinning `canon_version: jcs-rfc8785-v1` in publicly-citable artefacts are recorded in the [Substrate Adopters Registry](https://docs.algovoi.co.uk/adopters). Current adopters:

- **AlgoVoi** -- production gateway + this reference implementation
- **PEAC Protocol** -- AP2 `open_mandate_hash` v0 fixture set ([peacprotocol/peac](https://github.com/peacprotocol/peac))

To request listing as an adopter, follow the [submission process](https://docs.algovoi.co.uk/adopters#how-to-submit-an-adoption-entry). AlgoVoi validates submissions against the artefact's canonical bytes and adds qualifying entries.

## Acknowledgments

This discipline is AlgoVoi-authored under sole authorship. The byte-for-byte cross-validation that anchors it is empirically possible only because of the independent JCS implementations and conformance work contributed by other parties. AlgoVoi acknowledges with thanks:

**Reference JCS implementations cross-validated in the matrix** (192/192 byte-for-byte agreements across all eight):

- Python [`rfc8785`](https://pypi.org/project/rfc8785/) -- Trail of Bits
- TypeScript [`canonicalize`](https://www.npmjs.com/package/canonicalize) -- Samuel Erdtman
- Go [`gowebpki/jcs`](https://github.com/gowebpki/jcs) -- Web PKI Working Group
- Rust [`serde_jcs`](https://crates.io/crates/serde_jcs) -- [l1h3r](https://github.com/l1h3r)
- Java [`cyberphone/json-canonicalization`](https://github.com/cyberphone/json-canonicalization) -- **Anders Rundgren** (RFC 8785 author) and Samuel Erdtman
- PHP -- inline pure-stdlib JCS (AlgoVoi-authored, no external dependency)
- .NET [`Baqhub.Packages.JsonCanonicalization`](https://www.nuget.org/packages/Baqhub.Packages.JsonCanonicalization) -- Baqhub
- Ruby [`json-canonicalization`](https://rubygems.org/gems/json-canonicalization) -- RubyGems community

The discipline is validated by the editor of the canonicalisation standard it pins (Anders Rundgren via the Java implementation).

**Independent vector-set authors** (substrate-anchored vectors that AlgoVoi cross-validated against the matrix):

- [feedoracle](https://github.com/feedoracle) (FeedOracle) -- hybrid-PQC receipt-core vectors ([x402#2411](https://github.com/x402-foundation/x402/pull/2411))
- [arian-gogani](https://github.com/arian-gogani) (Nobulex) -- bilateral-receipt vectors using the AlgoVoi `action_ref` derivation ([discussed on x402#2322](https://github.com/x402-foundation/x402/pull/2322))

**Discussion contributor:**

- [feedoracle](https://github.com/feedoracle) (FeedOracle) -- proposed the retention-property scoping (MiCA Art. 80 / AMLR Art. 56 / DORA Art. 14) for the `canon_version` MUST clause; refined and incorporated into the discipline by AlgoVoi.

These roles describe validation, mirror, and discussion work relative to the AlgoVoi-authored discipline. They are not discipline co-authorship; see the [Version governance](https://docs.algovoi.co.uk/canonicalisation-substrate#version-governance) section. The substrate-author position rests on the byte-for-byte agreement these independent parties collectively confirm.

## Tests

```bash
# Python (74 tests)
pip install -e python/[dev]
python -m pytest python/tests/ -v

# TypeScript (68 tests)
cd typescript && npm install && npm test
```

## Licence

Apache 2.0. See [`LICENSE`](./LICENSE).

## Author

AlgoVoi (Christopher Hopley, GitHub [`chopmob-cloud`](https://github.com/chopmob-cloud)).
