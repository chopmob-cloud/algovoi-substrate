# algovoi-substrate (Python)

AlgoVoi agentic-payments substrate reference implementation.

JCS RFC 8785 canonicalisation, CAIP-2/10/19 chain-agnostic identifier
validation, `action_ref` atomic primitive, composite trust-query algorithm,
compliance receipt shape, and audit chain primitives that compose the
substrate underneath x402, AP2, A2A, and MPP receipts.

The substrate runs in production at `https://api.algovoi.co.uk/compliance`.
This package is the AlgoVoi-authored reference implementation; cross-validated
byte-for-byte against four other JCS implementations (JavaScript `canonicalize`,
Go `gowebpki/jcs`, Java `cyberphone`, Rust `serde_jcs`) on 53 conformance
vectors and 3 composite-trust-query vectors.

## Install

```bash
pip install algovoi-substrate
```

## Quickstart

```python
from algovoi_substrate import (
    canonicalize,
    sha256_jcs,
    action_ref,
    composite_trust_query_hash,
    build_compliance_receipt,
    append_to_chain,
    verify_audit_chain,
)

# Canonicalise an object to RFC 8785 JCS bytes.
canonicalize({"b": 1, "a": 2})  # -> '{"a":2,"b":1}'

# The action_ref atomic primitive:
# SHA-256(JCS({agent_id, action_type, scope, timestamp_ms}))
ref = action_ref(
    agent_id="agent-x",
    action_type="payment",
    scope="bilateral",
    timestamp_ms=1716460800000,
)

# Composite trust-query (PR #2440 in x402-foundation/x402).
# Aggregates multi-source attestations into a single canonical hash.
rows = [
    {"source_id": "trust-a", "score": 80, "sig": "sig-bytes"},
    {"source_id": "trust-b", "score": 75, "sig": "sig-bytes"},
]
composite_hash = composite_trust_query_hash(rows)

# Compliance receipt (AlgoVoi production schema).
receipt = build_compliance_receipt(
    payer_ref="sha256:abc123",
    screen_result="ALLOW",
    screen_timestamp_ms=1716460800000,
    screen_provider_did="did:web:api.algovoi.co.uk",
    jurisdiction_flags=["UK", "EU"],
)

# Audit chain: monotonic per-row hash chain with content_hash + prev_hash.
row0 = append_to_chain(payload=dict(receipt), prev_row=None)
row1 = append_to_chain(payload={"event": "next"}, prev_row=row0)
verify_audit_chain([row0, row1])
```

## CAIP identifiers (chain-agnostic)

`algovoi_substrate.caip` validates CAIP-2 chain ids, CAIP-10 account ids, and
CAIP-19 asset ids. When such an identifier is folded into a canonicalised,
content-addressed record it becomes part of the hash preimage, so it must be
byte-canonical or two verifiers' digests diverge. The validators anchor with
`\A` and `\Z`, never `^` and `$`: in Python `$` also matches just before a
trailing newline, so `"eip155:1\n"` would pass under `^...$` yet hash
differently on the verifying side. The strict `require_*` forms are the
pre-hash gate that fails a non-canonical identifier closed.

```python
from algovoi_substrate import (
    is_caip2, is_caip10, is_caip19,
    require_caip2, caip10_of, caip19_slip44,
)

is_caip2("eip155:1")                     # True
is_caip10("eip155:1:0xAb16a9...")        # True
is_caip19("eip155:1/slip44:60")          # True

caip10_of("eip155:1", "0xAb16a9...")     # "eip155:1:0xAb16a9..."
caip19_slip44("eip155:1", 60)            # "eip155:1/slip44:60"
require_caip2("eip155:1\n")              # raises CaipError (trailing newline)
```

Three opt-in tiers, additive and chain-agnostic by default:

1. **Grammar** -- `is_caip2/10/19`: the CAIP grammar only, so a future or
   not-yet-registered chain still validates.
2. **Registered namespace** -- `is_registered_caip2/10/19`: additionally
   requires a namespace registered in `ChainAgnostic/namespaces` (e.g.
   `eip155`, `solana`, `cosmos`, `xrpl`).
3. **Reference format** -- `is_valid_caip2/10/19`: strictest; additionally
   requires the chain reference to be well-formed for its namespace, so
   `eip155:abc` is rejected because `eip155` references are decimal.

Each tier has a `require_*` counterpart (`require_caip*`,
`require_registered_caip*`, `require_valid_caip*`) that returns the identifier
unchanged or raises `CaipError`.

## Substrate discipline

This package enforces the AlgoVoi-discipline rules authored by AlgoVoi and proposed in PR #2453
(x402-foundation/x402, sole AlgoVoi authorship; replaces closed PR #2436):

- **Rule 1.** `timestamp_ms` is an epoch-millisecond integer. Floats, ISO 8601
  strings, and negative values are rejected at the source-side.
- **Rule 4.** Type validation happens before canonicalisation. A field
  declared integer that receives a float is a hard validation failure, not
  a silent type-cast.
- **canon_version pin.** Receipts carry `canon_version: "jcs-rfc8785-v1"`
  as an in-band format-version pin, so a year-five re-canonicalisation
  knows which rule was active at emission without depending on an
  out-of-band rule registry.
- **Array element order preserved.** `["UK","EU"]` and `["EU","UK"]` are
  distinct canonical preimages per RFC 8785 §3.2.3 -- producer-side
  ordering is load-bearing.

The categorical screen result (`ALLOW` / `REFER` / `DENY`) is enforced as a
closed set. Under UK POCA 2002 s.330 a `REFER` carries a mandatory SAR
obligation that `DENY` does not; collapsing this to a score / tier
projection would lose the property and break year-five auditability.

## Cross-impl validation

The substrate has been byte-for-byte cross-validated across five
implementations on the AlgoVoi-authored vector sets:

- Python `rfc8785@0.1.4` (this package wraps it)
- JavaScript `canonicalize@3.0.0`
- Go `gowebpki/jcs v1.0.1`
- Java `cyberphone/json-canonicalization`
- Rust `serde_jcs@0.2.0`

Vector sets (Apache 2.0, AlgoVoi-authored):

- [AP2 OMH v0](https://gist.github.com/chopmob-cloud/1dca25fd6107db4b7a30bed5dbf2ded8) -- 10 vectors
- [CTEF + APS v1](https://gist.github.com/chopmob-cloud/5f35eaa527d292bf3ddc52f8725a85c9) -- 14 vectors
- [privacy_class v0.1](https://gist.github.com/chopmob-cloud/30bcbc717c86493f737feb92c415ba07) -- 10 vectors
- [per-chain envelope v0](https://gist.github.com/chopmob-cloud/e1bf4c9efde6f0e94b77c238cb33d78d) -- 19 vectors

Substrate matrix: <https://gist.github.com/chopmob-cloud/b327814c4e17ed9fc7b4f29c8bda523c>

Composite trust-query matrix:
<https://gist.github.com/chopmob-cloud/f2e9f0877b7d9fff70c8eca46e4ce636>

## Tests

```bash
pip install -e ".[test]"
pytest
```

## Production reference

The reference exhibit for this substrate is AlgoVoi's `/compliance/attestation`
audit chain, live at `https://api.algovoi.co.uk/compliance/attestation`.
Receipts retained under seven-year Object Lock COMPLIANCE retention (current
horizon 2033-05-04). The migration boundary (receipts before / after
2026-05-21) is observable directly from the chain.

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
