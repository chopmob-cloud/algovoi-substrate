"""The opt-in registered-namespace layer: is_registered_* / require_registered_*.

Grammar validity does not imply a real chain. is_caip2("abc:1") is True (well-formed) but
"abc" is not a registered namespace. This layer adds that check against the vendored
ChainAgnostic/namespaces registry, without changing the grammar validators (so the substrate
stays chain-agnostic for future/unregistered chains).
"""
import re

import pytest

from algovoi_substrate import caip

_NS_RE = re.compile(r"^[-a-z0-9]{3,8}$")


def test_registry_shape():
    reg = caip.registered_namespaces()
    assert reg is caip.REGISTERED_NAMESPACES
    assert len(reg) == 41
    # every registered namespace is itself a grammar-valid CAIP-2 namespace
    for ns in reg:
        assert _NS_RE.match(ns), ns
    # spot-check real namespaces incl the ones that differ from their directory name
    for ns in ("eip155", "bip122", "cosmos", "solana", "polkadot", "avax", "swift", "xrpl", "tvm"):
        assert ns in reg


def test_directory_name_is_not_the_namespace():
    # the "avalanche" directory registers the namespace "avax". Guard the exact trap that
    # would have shipped a wrong allowlist.
    assert caip.is_registered_namespace("avax")
    assert not caip.is_registered_namespace("avalanche")
    # "avalanche" is 9 chars so it is not even a grammar-valid namespace
    assert not caip.is_caip2("avalanche:1")


def test_is_registered_namespace():
    assert caip.is_registered_namespace("eip155")
    assert not caip.is_registered_namespace("abc")        # grammar-valid, not registered
    assert not caip.is_registered_namespace("fakechain")  # too long AND not registered
    assert not caip.is_registered_namespace("EIP155")     # uppercase, not registered
    assert not caip.is_registered_namespace("")
    assert not caip.is_registered_namespace(123)


def test_registered_caip2_layers_on_grammar():
    # the whole point: grammar accepts, registry rejects.
    assert caip.is_caip2("abc:1") is True
    assert caip.is_registered_caip2("abc:1") is False
    # real chains pass both
    for s in ("eip155:1", "bip122:000000000019d6689c085ae165831e93", "cosmos:cosmoshub-3",
              "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp", "avax:2q9e4r6mu"):
        assert caip.is_registered_caip2(s), s
    # malformed still rejected (grammar gate first)
    assert not caip.is_registered_caip2("eip155:1\n")
    assert not caip.is_registered_caip2("fakechain:1")


def test_registered_caip10_and_caip19():
    assert caip.is_registered_caip10("eip155:1:0xabc")
    assert not caip.is_registered_caip10("abc:1:0xabc")
    assert caip.is_registered_caip19("eip155:1/slip44:60")
    assert not caip.is_registered_caip19("abc:1/slip44:60")
    # swift as the fiat namespace, valid CAIP-19 asset
    assert caip.is_registered_caip19("swift:iso20022/iso4217:usd")


def test_require_registered_gates():
    assert caip.require_registered_caip2("eip155:1") == "eip155:1"
    assert caip.require_registered_caip10("eip155:1:0xabc") == "eip155:1:0xabc"
    assert caip.require_registered_caip19("eip155:1/slip44:60") == "eip155:1/slip44:60"
    for thunk in (
        lambda: caip.require_registered_caip2("abc:1"),
        lambda: caip.require_registered_caip2("eip155:1\n"),
        lambda: caip.require_registered_caip10("abc:1:0xabc"),
        lambda: caip.require_registered_caip19("abc:1/slip44:60"),
        lambda: caip.require_registered_caip2(123),
    ):
        with pytest.raises(caip.CaipError):
            thunk()
