"""CAIP identifier grammar conformance for algovoi_substrate.caip.

Runs every normative test vector from the CAIP-2/10/19 specs (ChainAgnostic/CAIPs)
through the validators and asserts each is accepted; asserts malformed forms are
rejected; pins the boundary lengths and the trailing-newline anchor discipline; and
exercises the strict require_* pre-hash gates and the pure builders.
"""
import pytest

from algovoi_substrate.caip import (
    CaipError,
    caip10_of,
    caip19_slip44,
    is_caip2,
    is_caip10,
    is_caip19,
    require_caip2,
    require_caip10,
    require_caip19,
)

# ---- verbatim normative vectors from the specs ----
CAIP2_SPEC = [
    "eip155:1", "bip122:000000000019d6689c085ae165831e93",
    "bip122:12a765e31ffd4059bada1e25190f6e98", "bip122:fdbe99b90c90bae7505796461471d89a",
    "cosmos:cosmoshub-2", "cosmos:cosmoshub-3", "cosmos:Binance-Chain-Tigris",
    "cosmos:iov-mainnet", "starknet:SN_GOERLI", "lip9:9ee11e9df416b18b",
    "chainstd:8c3444cf8970a9e41a706fab93e7a6c4",
]
CAIP10_SPEC = [
    "eip155:1:0xab16a96D359eC26a11e2C2b3d8f8B8942d5Bfcdb",
    "bip122:000000000019d6689c085ae165831e93:128Lkh3S7CkDTBZ8W7BbpsN3YYizJMp8p6",
    "cosmos:cosmoshub-3:cosmos1t2uflqwqe0fsj0shcfkrvpukewcw40yjj6hdc0",
    "polkadot:b0a8d493285c2df73290dfb7e61f870f:5hmuyxw9xdgbpptgypokw4thfyoe3ryenebr381z9iaegmfy",
    "starknet:SN_GOERLI:0x02dd1b492765c064eac4039e3841aa5f382773b598097a40073bd8b48170ab57",
    "chainstd:8c3444cf8970a9e41a706fab93e7a6c4:6d9b0b4b9994e8a6afbd3dc3ed983cd51c755afb27cd1dc7825ef59c134a39f7",
    "hedera:mainnet:0.0.1234567890-zbhlt",
]
CAIP19_SPEC = [
    "eip155:1/slip44:60", "bip122:000000000019d6689c085ae165831e93/slip44:0",
    "cosmos:cosmoshub-3/slip44:118", "bip122:12a765e31ffd4059bada1e25190f6e98/slip44:2",
    "cosmos:Binance-Chain-Tigris/slip44:714", "cosmos:iov-mainnet/slip44:234",
    "lip9:9ee11e9df416b18b/slip44:134",
    "eip155:1/erc20:0x6b175474e89094c44da98b954eedeac495271d0f",
    "eip155:1/erc721:0x06012c8cf97BEaD5deAe237070F9587f8E7A266d",
    "eip155:1/erc721:0x06012c8cf97BEaD5deAe237070F9587f8E7A266d/771769",
    "hedera:mainnet/nft:0.0.55492/12",
]


@pytest.mark.parametrize("v", CAIP2_SPEC)
def test_caip2_spec_vectors_accepted(v):
    assert is_caip2(v)


@pytest.mark.parametrize("v", CAIP10_SPEC)
def test_caip10_spec_vectors_accepted(v):
    assert is_caip10(v)


@pytest.mark.parametrize("v", CAIP19_SPEC)
def test_caip19_spec_vectors_accepted(v):
    assert is_caip19(v)


def test_cross_level_no_confusion():
    assert not is_caip10("eip155:1")
    assert not is_caip19("eip155:1")
    assert not is_caip2("eip155:1:0xabc")
    assert not is_caip2("eip155:1/slip44:60")
    assert not is_caip19("eip155:1:0xabc")


@pytest.mark.parametrize("s", [
    "", "ab:1", "123456789:1", "EIP155:1", "eip_155:1", "eip155:", "eip155",
    "eip155:" + "a" * 33, "eip155:na@me", " eip155:1", "eip155:1 ",
    "eip155:1\n", "eip155:1\r\n", "eip155:1\t", "eip155:1\x00",
    123, None, {"x": 1}, b"eip155:1",
])
def test_caip2_malformed_rejected(s):
    assert not is_caip2(s)


@pytest.mark.parametrize("s", [
    "eip155:1", "eip155:1:", "eip155:1:0x_ab", "eip155:1:" + "a" * 129,
    "eip155:1:0xab\n", "eip155:1:0x ab", "eip155:1:0x/ab", "eip155:1:0x:ab",
])
def test_caip10_malformed_rejected(s):
    assert not is_caip10(s)


@pytest.mark.parametrize("s", [
    "eip155:1", "eip155:1/", "eip155:1/SLIP44:60", "eip155:1/sl:60",
    "eip155:1/slip44:", "eip155:1/slip44:60\n", "eip155:1/slip44:60/" + "t" * 79,
    "eip155:1/slip_44:60",
])
def test_caip19_malformed_rejected(s):
    assert not is_caip19(s)


def test_trailing_newline_anchor_closed():
    # the \A..\Z discipline: $ would let these through and break byte-canonicity.
    assert not is_caip2("eip155:1\n")
    assert not is_caip2("eip155:1\r\n")
    assert not is_caip10("eip155:1:0xabc\n")
    assert not is_caip19("eip155:1/slip44:60\n")


def test_boundary_lengths():
    assert is_caip2("abc:" + "a" * 32)
    assert not is_caip2("abc:" + "a" * 33)
    assert is_caip2("abc:a") and is_caip2("abcdefgh:a")
    assert not is_caip2("ab:a") and not is_caip2("abcdefghi:a")
    assert is_caip10("abc:1:" + "a" * 128)
    assert not is_caip10("abc:1:" + "a" * 129)
    assert is_caip19("abc:1/def:60/" + "t" * 78)
    assert not is_caip19("abc:1/def:60/" + "t" * 79)


def test_require_gates_pass_through_valid():
    assert require_caip2("eip155:1") == "eip155:1"
    assert require_caip10("eip155:1:0xabc") == "eip155:1:0xabc"
    assert require_caip19("eip155:1/slip44:60") == "eip155:1/slip44:60"


def test_require_gates_raise_on_noncanonical():
    with pytest.raises(CaipError):
        require_caip2("eip155:1\n")
    with pytest.raises(CaipError):
        require_caip10("eip155:1")          # a bare CAIP-2 is not a CAIP-10
    with pytest.raises(CaipError):
        require_caip19("not/an:asset:x")


def test_caip19_slip44_builder():
    assert caip19_slip44("eip155:1", 60) == "eip155:1/slip44:60"
    assert caip19_slip44("cosmos:cosmoshub-3", 118) == "cosmos:cosmoshub-3/slip44:118"
    with pytest.raises(CaipError):
        caip19_slip44("not a chain", 60)     # bad chain
    with pytest.raises(CaipError):
        caip19_slip44("eip155:1", -1)        # bad coin_type
    with pytest.raises(CaipError):
        caip19_slip44("eip155:1", True)      # bool is not a coin_type


def test_caip10_of_builder():
    assert caip10_of("eip155:1", "0xab16a96D359eC26a11e2C2b3d8f8B8942d5Bfcdb").startswith("eip155:1:0x")
    with pytest.raises(CaipError):
        caip10_of("eip155:1", "0x ab")       # space is outside the address class
    with pytest.raises(CaipError):
        caip10_of("not a chain", "0xabc")    # bad chain
