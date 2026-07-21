# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christopher Hopley / AlgoVoi (chopmob-cloud)
"""
Chain Agnostic Improvement Proposal (CAIP) identifier grammar: CAIP-2 chain ids,
CAIP-10 account ids, CAIP-19 asset ids.

These identifiers name the chain, account, and asset a receipt refers to in a
chain-agnostic way. When such an identifier is folded into a canonicalised,
content-addressed record (see :mod:`algovoi_substrate.canonicalize`), it becomes
part of the preimage: two verifiers must agree on its exact bytes or their hashes
diverge and the record stops recomputing. So the identifier is not merely "valid
or not", it must be BYTE-CANONICAL. This module validates against the CAIP grammar
and, in the strict ``require_*`` forms, is the pre-hash gate an offline verifier
uses to refuse a non-canonical identifier before it reaches the digest.

Anchor discipline (load-bearing): the validators anchor with ``\\A`` and ``\\Z``,
never ``^`` and ``$``. In Python ``$`` also matches just before a trailing ``\\n``,
so ``"eip155:1\\n"`` would validate under ``^...$`` yet differ byte-for-byte from
the clean identifier on the verifying side. ``\\Z`` has no trailing-newline
exception. This trap is language-dependent (a real cross-implementation divergence,
not a Python quirk), which is exactly why it belongs pinned in the substrate.

Grammar (verbatim from CAIP-2/10/19, ChainAgnostic/CAIPs):
  chain_id    = namespace ":" reference     namespace [-a-z0-9]{3,8}  reference [-_a-zA-Z0-9]{1,32}
  account_id  = chain_id ":" address        address   [-.%a-zA-Z0-9]{1,128}
  asset_type  = chain_id "/" ns ":" ref     asset ns [-a-z0-9]{3,8}   asset ref [-.%a-zA-Z0-9]{1,128}
  asset_id    = asset_type "/" token_id     token_id  [-.%a-zA-Z0-9]{1,78}

Pure standard library (``re`` only); no new dependency on the substrate.

Licensed under Apache 2.0.
"""
from __future__ import annotations

import re

_CHAIN = r"[-a-z0-9]{3,8}:[-_a-zA-Z0-9]{1,32}"
_CAIP2_RE = re.compile(rf"\A{_CHAIN}\Z")
_CAIP10_RE = re.compile(rf"\A{_CHAIN}:[-.%a-zA-Z0-9]{{1,128}}\Z")
_CAIP19_RE = re.compile(rf"\A{_CHAIN}/[-a-z0-9]{{3,8}}:[-.%a-zA-Z0-9]{{1,128}}(/[-.%a-zA-Z0-9]{{1,78}})?\Z")


class CaipError(ValueError):
    """Raised by the ``require_*`` gates when an identifier is not byte-canonical CAIP."""


def is_caip2(s: object) -> bool:
    """True iff ``s`` is a byte-canonical CAIP-2 chain id."""
    return isinstance(s, str) and bool(_CAIP2_RE.match(s))


def is_caip10(s: object) -> bool:
    """True iff ``s`` is a byte-canonical CAIP-10 account id."""
    return isinstance(s, str) and bool(_CAIP10_RE.match(s))


def is_caip19(s: object) -> bool:
    """True iff ``s`` is a byte-canonical CAIP-19 asset type or asset id."""
    return isinstance(s, str) and bool(_CAIP19_RE.match(s))


def require_caip2(s: object) -> str:
    """Return ``s`` unchanged if it is a canonical CAIP-2, else raise :class:`CaipError`.

    This is the pre-hash gate: call it on any chain id before it is folded into a
    canonicalised record, so a non-canonical identifier fails closed rather than
    silently producing a non-reproducible digest."""
    if not is_caip2(s):
        raise CaipError(f"not a canonical CAIP-2 chain id: {s!r}")
    return s  # type: ignore[return-value]


def require_caip10(s: object) -> str:
    """Return ``s`` if it is a canonical CAIP-10 account id, else raise :class:`CaipError`."""
    if not is_caip10(s):
        raise CaipError(f"not a canonical CAIP-10 account id: {s!r}")
    return s  # type: ignore[return-value]


def require_caip19(s: object) -> str:
    """Return ``s`` if it is a canonical CAIP-19 asset type or id, else raise :class:`CaipError`."""
    if not is_caip19(s):
        raise CaipError(f"not a canonical CAIP-19 asset id: {s!r}")
    return s  # type: ignore[return-value]


def caip19_slip44(chain_caip2: str, coin_type: int) -> str:
    """Build the CAIP-19 asset type for a chain's native coin via the slip44 namespace.

    ``caip19_slip44("eip155:1", 60) -> "eip155:1/slip44:60"``. The chain id is gated
    with :func:`require_caip2` and the result with :func:`require_caip19`, so the
    output is guaranteed byte-canonical."""
    if not isinstance(coin_type, int) or isinstance(coin_type, bool) or coin_type < 0:
        raise CaipError(f"slip44 coin_type must be a non-negative int: {coin_type!r}")
    return require_caip19(f"{require_caip2(chain_caip2)}/slip44:{coin_type}")


def caip10_of(chain_caip2: str, address: str) -> str:
    """Build the CAIP-10 account id for ``address`` on ``chain_caip2``.

    ``caip10_of("eip155:1", "0xab..") -> "eip155:1:0xab.."``. The chain id is gated
    with :func:`require_caip2` and the result with :func:`require_caip10`. Raises
    :class:`CaipError` when the address is not a canonical CAIP-10 account address
    (e.g. it contains a character outside ``[-.%a-zA-Z0-9]``). A non-string address is
    rejected rather than silently coerced."""
    if not isinstance(address, str):
        raise CaipError(f"address must be a str: {address!r}")
    return require_caip10(f"{require_caip2(chain_caip2)}:{address}")


# Registered CAIP-2 namespaces, vendored from ChainAgnostic/namespaces (main, verified
# 2026-07-19): every registry directory that defines a caip2.md, using its declared
# namespace-identifier (minus the "-caip2" suffix, lowercased per the CAIP-2 lowercase rule)
# or, for prose-only entries, the directory name. The namespace is NOT always the directory
# name: the "avalanche" directory registers the namespace "avax". This is the OPT-IN realness
# layer. The grammar validators above stay namespace-agnostic on purpose, so a future or
# not-yet-registered chain still validates; is_registered_* additionally requires a known
# namespace. Refresh from the registry as new namespaces land.
REGISTERED_NAMESPACES = frozenset({
    "aleo", "alephium", "algorand", "antelope", "aptos", "arweave", "avax", "bip122", "casper",
    "ccd", "chia", "conflux", "cosmos", "eip155", "ergo", "fil", "flow", "haneul", "hedera",
    "hive", "iota", "koinos", "mina", "monero", "mvx", "partisia", "polkadot", "quai", "reef",
    "solana", "stacks", "starknet", "stellar", "sui", "swift", "tezos", "tvm", "vechain",
    "wallet", "waves", "xrpl",
})


def registered_namespaces() -> frozenset:
    """The set of CAIP-2 namespaces registered in ChainAgnostic/namespaces (vendored)."""
    return REGISTERED_NAMESPACES


def is_registered_namespace(ns: object) -> bool:
    """True iff ``ns`` is a registered CAIP-2 namespace (e.g. "eip155", "avax", "swift")."""
    return isinstance(ns, str) and ns in REGISTERED_NAMESPACES


def is_registered_caip2(s: object) -> bool:
    """True iff ``s`` is a canonical CAIP-2 AND its namespace is registered."""
    return is_caip2(s) and s.split(":", 1)[0] in REGISTERED_NAMESPACES  # type: ignore[union-attr]


def is_registered_caip10(s: object) -> bool:
    """True iff ``s`` is a canonical CAIP-10 AND its chain namespace is registered."""
    return is_caip10(s) and s.split(":", 1)[0] in REGISTERED_NAMESPACES  # type: ignore[union-attr]


def is_registered_caip19(s: object) -> bool:
    """True iff ``s`` is a canonical CAIP-19 AND its chain namespace is registered."""
    return is_caip19(s) and s.split(":", 1)[0] in REGISTERED_NAMESPACES  # type: ignore[union-attr]


def require_registered_caip2(s: object) -> str:
    """Return ``s`` if it is a canonical CAIP-2 on a registered namespace, else raise."""
    if not is_registered_caip2(s):
        raise CaipError(f"not a canonical CAIP-2 on a registered namespace: {s!r}")
    return s  # type: ignore[return-value]


def require_registered_caip10(s: object) -> str:
    """Return ``s`` if it is a canonical CAIP-10 on a registered namespace, else raise."""
    if not is_registered_caip10(s):
        raise CaipError(f"not a canonical CAIP-10 on a registered namespace: {s!r}")
    return s  # type: ignore[return-value]


def require_registered_caip19(s: object) -> str:
    """Return ``s`` if it is a canonical CAIP-19 on a registered namespace, else raise."""
    if not is_registered_caip19(s):
        raise CaipError(f"not a canonical CAIP-19 on a registered namespace: {s!r}")
    return s  # type: ignore[return-value]


# Per-namespace CAIP-2 reference formats, verified against each namespace's caip2.md in
# ChainAgnostic/namespaces (2026-07-19). This is the third, strictest OPT-IN tier: it rejects
# a grammar-valid, registered identifier whose reference is not well-formed for its namespace
# (e.g. "eip155:abc" -- eip155 references are decimal chain ids). Only namespaces with a clear,
# spec-defined format are listed; a registered namespace without a rule here is accepted (the
# reference is not second-guessed), keeping the layer additive and chain-agnostic.
#   eip155   decimal chain id (EIP-155 unsigned integer)
#   bip122   first 16 bytes of the genesis hash, lowercase hex (32 chars)
#   polkadot first half of the genesis block hash, lowercase hex (spec regex [0-9a-f]{32})
#   solana   first 32 chars of the base58 genesis hash
#   starknet ASCII-decoded chain id, e.g. SN_MAIN / SN_GOERLI / SN_SEPOLIA
_REFERENCE_FORMATS = {
    "eip155": re.compile(r"\A[0-9]{1,32}\Z"),
    "bip122": re.compile(r"\A[0-9a-f]{32}\Z"),
    "polkadot": re.compile(r"\A[0-9a-f]{32}\Z"),
    "solana": re.compile(r"\A[1-9A-HJ-NP-Za-km-z]{32}\Z"),
    "starknet": re.compile(r"\ASN_[A-Z0-9]{1,29}\Z"),
}
REFERENCE_FORMAT_NAMESPACES = frozenset(_REFERENCE_FORMATS)


def _ns_ref(s: str) -> tuple:
    """(namespace, reference) of a CAIP-2/10/19 id. The reference ends at the next ':' or '/'
    (both excluded from the reference character class), so this is a faithful split."""
    ns, _sep, rest = s.partition(":")
    cut = len(rest)
    for delim in (":", "/"):
        i = rest.find(delim)
        if i >= 0:
            cut = min(cut, i)
    return ns, rest[:cut]


def _reference_format_ok(s: str) -> bool:
    ns, ref = _ns_ref(s)
    rule = _REFERENCE_FORMATS.get(ns)
    return rule is None or bool(rule.match(ref))


def is_valid_caip2(s: object) -> bool:
    """True iff ``s`` is a canonical CAIP-2 on a registered namespace whose reference is also
    well-formed for that namespace (strictest tier; e.g. rejects "eip155:abc")."""
    return is_registered_caip2(s) and _reference_format_ok(s)  # type: ignore[arg-type]


def is_valid_caip10(s: object) -> bool:
    """CAIP-10 whose chain is registered and whose chain reference matches its namespace format."""
    return is_registered_caip10(s) and _reference_format_ok(s)  # type: ignore[arg-type]


def is_valid_caip19(s: object) -> bool:
    """CAIP-19 whose chain is registered and whose chain reference matches its namespace format."""
    return is_registered_caip19(s) and _reference_format_ok(s)  # type: ignore[arg-type]


def require_valid_caip2(s: object) -> str:
    if not is_valid_caip2(s):
        raise CaipError(f"not a valid CAIP-2 (registered namespace + conformant reference): {s!r}")
    return s  # type: ignore[return-value]


def require_valid_caip10(s: object) -> str:
    if not is_valid_caip10(s):
        raise CaipError(f"not a valid CAIP-10 (registered namespace + conformant reference): {s!r}")
    return s  # type: ignore[return-value]


def require_valid_caip19(s: object) -> str:
    if not is_valid_caip19(s):
        raise CaipError(f"not a valid CAIP-19 (registered namespace + conformant reference): {s!r}")
    return s  # type: ignore[return-value]
