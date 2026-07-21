"""Tier 3: per-namespace reference format (is_valid_* / require_valid_*).

Grammar + a registered namespace still is not a real chain: "eip155:abc" is well-formed and
"eip155" is registered, but eip155 references are decimal chain ids. This tier enforces the
reference format for the namespaces with a clear spec-defined rule, while accepting any
registered namespace that has no rule (so the layer stays additive and chain-agnostic).
"""
import pytest

from algovoi_substrate import caip


def test_rule_set():
    assert caip.REFERENCE_FORMAT_NAMESPACES == frozenset(
        {"eip155", "bip122", "polkadot", "solana", "starknet"})


def test_the_goal_eip155_abc_is_rejected_only_at_valid_tier():
    s = "eip155:abc"
    assert caip.is_caip2(s) is True            # grammar accepts
    assert caip.is_registered_caip2(s) is True  # registered namespace
    assert caip.is_valid_caip2(s) is False      # reference is not decimal -> rejected here


@pytest.mark.parametrize("s", [
    "eip155:1", "eip155:9", "eip155:295", "eip155:15000",
    "bip122:000000000019d6689c085ae165831e93", "bip122:000000000933ea01ad0ee984209779ba",
    "polkadot:91b171bb158e2d3848fa23a9f1c25182",
    "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp", "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1",
    "starknet:SN_GOERLI", "starknet:SN_MAIN", "starknet:SN_SEPOLIA",
])
def test_real_references_pass_valid(s):
    assert caip.is_valid_caip2(s), s


@pytest.mark.parametrize("s", [
    "eip155:abc",          # not decimal
    "eip155:0x1",          # hex prefix, not decimal
    "eip155:-1",           # sign
    "bip122:ZZZZ",         # not hex
    "bip122:000000000019d6689c085ae165831e9",   # 31 hex, not 32
    "polkadot:91B171BB158E2D3848FA23A9F1C25182",  # uppercase hex (spec is lowercase)
    "solana:abc",          # too short for a 32-char base58 genesis
    "solana:0OIl1111111111111111111111111111",   # base58 excludes 0 O I l
    "starknet:sn_goerli",  # lowercase
    "starknet:MAINNET",    # no SN_ prefix
])
def test_malformed_references_rejected_at_valid_tier(s):
    assert caip.is_caip2(s), f"{s} should still be grammar-valid"
    assert not caip.is_valid_caip2(s), f"{s} should fail the reference-format tier"


def test_rule_less_namespace_still_valid_cover_all():
    # a registered namespace without a format rule is accepted: the reference is not
    # second-guessed, so future/unruled chains keep working.
    for s in ("cosmos:cosmoshub-3", "cosmos:Binance-Chain-Tigris", "tezos:NetXdQprcVkpaWU",
              "hedera:mainnet", "sui:mainnet", "avax:2q9e4r"):
        assert caip.is_valid_caip2(s), s
    # but an unregistered namespace is still rejected (registered gate comes first)
    assert not caip.is_valid_caip2("abc:1")
    assert not caip.is_valid_caip2("fakechain:1")


def test_valid_caip10_and_caip19_apply_the_chain_reference_rule():
    # the reference rule applies to the embedded chain reference of a CAIP-10 / CAIP-19.
    assert caip.is_valid_caip10("eip155:1:0xab16a96D359eC26a11e2C2b3d8f8B8942d5Bfcdb")
    assert not caip.is_valid_caip10("eip155:abc:0xdeadbeef")   # chain ref not decimal
    assert caip.is_valid_caip19("eip155:1/slip44:60")
    assert not caip.is_valid_caip19("eip155:abc/slip44:60")


def test_require_valid_gates():
    assert caip.require_valid_caip2("eip155:1") == "eip155:1"
    assert caip.require_valid_caip10("eip155:1:0xabc") == "eip155:1:0xabc"
    assert caip.require_valid_caip19("eip155:1/slip44:60") == "eip155:1/slip44:60"
    for thunk in (
        lambda: caip.require_valid_caip2("eip155:abc"),
        lambda: caip.require_valid_caip2("abc:1"),
        lambda: caip.require_valid_caip10("eip155:abc:0xdeadbeef"),
        lambda: caip.require_valid_caip19("eip155:abc/slip44:60"),
        lambda: caip.require_valid_caip2(123),
    ):
        with pytest.raises(caip.CaipError):
            thunk()
