"""Validate and stress the CAIP regexes themselves.

Three things a regex specifically needs proven:
  1. Correctness vs an INDEPENDENT non-regex oracle (caip_oracle) over a large differential
     fuzz corpus: any char-class or anchor bug shows up as a disagreement.
  2. No catastrophic backtracking (ReDoS): pathological inputs validate in bounded, linear
     time.
  3. Known-answer generative coverage across every grammar boundary and character class.
"""
from __future__ import annotations

import random
import string
import time

import pytest

from algovoi_substrate import caip
from caip_oracle import ORACLE

REGEX = {"caip2": caip.is_caip2, "caip10": caip.is_caip10, "caip19": caip.is_caip19}

# Alphabet mixes the grammar characters, the delimiters, and adversarial bytes.
_ALPHABET = (string.ascii_letters + string.digits + "-_.%:/@ "
             + "\n\r\t\x00" + "\u2028\u2029\uff11\u0435")
_VALID_SEED = [
    "eip155:1", "starknet:SN_GOERLI", "cosmos:Binance-Chain-Tigris", "abc:a",
    "eip155:1:0xab16a96D359eC26a11e2C2b3d8f8B8942d5Bfcdb", "hedera:mainnet:0.0.1-z",
    "eip155:1/slip44:60", "eip155:1/erc721:0xabc/771769", "abc:1:a", "abc:1/def:60/t",
]


def _fuzz_corpus(n: int, seed: int = 20260719) -> list[str]:
    rnd = random.Random(seed)
    out: list[str] = list(_VALID_SEED)
    # random strings of varied length
    for _ in range(n):
        L = rnd.randint(0, 40)
        out.append("".join(rnd.choice(_ALPHABET) for _ in range(L)))
    # single-point mutations of valid seeds (insert / delete / replace one char)
    for _ in range(n // 2):
        base = list(rnd.choice(_VALID_SEED))
        if base:
            i = rnd.randrange(len(base))
            op = rnd.randint(0, 2)
            if op == 0:
                base[i] = rnd.choice(_ALPHABET)
            elif op == 1:
                base.insert(i, rnd.choice(_ALPHABET))
            else:
                del base[i]
        out.append("".join(base))
    return out


FUZZ = _fuzz_corpus(60000)


@pytest.mark.parametrize("kind", ["caip2", "caip10", "caip19"])
def test_regex_matches_oracle_on_fuzz(kind):
    regex, oracle = REGEX[kind], ORACLE[kind]
    mismatches = []
    for s in FUZZ:
        if regex(s) != oracle(s):
            mismatches.append((kind, repr(s), regex(s), oracle(s)))
            if len(mismatches) >= 10:
                break
    assert not mismatches, f"regex vs oracle disagreements: {mismatches}"


def test_fuzz_corpus_exercises_both_verdicts():
    # guard: the corpus must actually contain accepts AND rejects for each kind, else the
    # differential test would pass vacuously.
    for kind in ("caip2", "caip10", "caip19"):
        acc = sum(1 for s in FUZZ if REGEX[kind](s))
        assert acc > 0, f"{kind}: no accepts in corpus"
        assert acc < len(FUZZ), f"{kind}: no rejects in corpus"


# ---------------------------------------------------------------- ReDoS / backtracking
def _t(fn, s: str) -> float:
    t0 = time.perf_counter()
    fn(s)
    return time.perf_counter() - t0


PATHOLOGICAL = [
    lambda n: "a" * n,
    lambda n: "eip155:" + "a" * n,                       # unterminated reference
    lambda n: "eip155:1:" + "a" * n,                     # long address, valid
    lambda n: "eip155:1:" + "%" * n,                     # long address, all percent
    lambda n: "eip155:1/slip44:" + "." * n,              # long asset reference
    lambda n: "eip155:1/slip44:60/" + "t" * n,           # long token
    lambda n: "eip155:1/" + "a" * n,                     # unterminated asset part
    lambda n: ("eip155:1" + "x") * n,                    # repeated near-valid
    lambda n: ":" * n,
    lambda n: "/" * n,
    lambda n: "eip155:1" + "\x00" * n,                   # trailing NUL run
]


@pytest.mark.parametrize("kind", ["caip2", "caip10", "caip19"])
def test_no_catastrophic_backtracking(kind):
    fn = REGEX[kind]
    for build in PATHOLOGICAL:
        big = _t(fn, build(200_000))
        # absolute bound: even 200k chars must validate well under a second
        assert big < 0.5, f"{kind}: {build(3)!r}-style 200k input took {big:.3f}s (possible ReDoS)"


@pytest.mark.parametrize("kind", ["caip2", "caip10", "caip19"])
def test_backtracking_scales_linearly(kind):
    fn = REGEX[kind]
    for build in PATHOLOGICAL:
        # 10x the input should cost roughly 10x, not 100x+ (catastrophic). Larger sizes keep
        # both timings well above the noise floor; a generous ceiling avoids timing flakiness
        # while still catching super-linear blowup (a ReDoS would be orders of magnitude worse).
        small = max(_t(fn, build(100_000)), 1e-4)
        big = _t(fn, build(1_000_000))
        assert big / small < 80, f"{kind}: {build(3)!r}-style scaled {big/small:.1f}x for 10x input"


# ---------------------------------------------------------------- known-answer generative
def test_generative_valid_caip2():
    for ns_len in (3, 8):
        ns = "a" * ns_len
        for ref in ("a", "A", "0", "-", "_", "aA0-_", "a" * 32, "SN_GOERLI", "Binance-Chain-Tigris"):
            s = f"{ns}:{ref}"
            assert caip.is_caip2(s) is True, s
            assert ORACLE["caip2"](s) is True, s


def test_generative_caip2_single_rule_violations():
    bad = [
        "aa:1",              # ns len 2
        "a" * 9 + ":1",      # ns len 9
        "aA:1",              # uppercase in ns
        "a_b:1",             # underscore in ns
        "abc:",              # ref len 0
        "abc:" + "a" * 33,   # ref len 33
        "abc:a.b",           # dot in ref
        "abc:a%b",           # percent in ref
        "abc:a b",           # space in ref
    ]
    for s in bad:
        assert caip.is_caip2(s) is False, s
        assert ORACLE["caip2"](s) is False, s


def test_generative_boundaries_all_levels():
    # every quantifier edge, accept at max and reject at max+1, agreeing with the oracle.
    cases = [
        ("caip2", "abc:" + "a" * 32, True), ("caip2", "abc:" + "a" * 33, False),
        ("caip10", "abc:1:" + "a" * 128, True), ("caip10", "abc:1:" + "a" * 129, False),
        ("caip19", "abc:1/def:" + "a" * 128, True), ("caip19", "abc:1/def:" + "a" * 129, False),
        ("caip19", "abc:1/def:60/" + "t" * 78, True), ("caip19", "abc:1/def:60/" + "t" * 79, False),
        ("caip19", "abc:1/ab:60", False),   # asset_ns len 2
        ("caip19", "abc:1/abcdefghi:60", False),  # asset_ns len 9
    ]
    for kind, s, want in cases:
        assert REGEX[kind](s) is want, (kind, s)
        assert ORACLE[kind](s) is want, (kind, s)
