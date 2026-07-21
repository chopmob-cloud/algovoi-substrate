"""Error-path completeness and robustness for algovoi_substrate.caip.

Goal: prove CAIP validation "hits all errors" cleanly. The is_* predicates must return a
bool for ANY input and never raise; the require_* gates and the builders must reject every
non-canonical input by raising CaipError and NEVER leak a different exception type
(TypeError, ValueError, re.error, UnicodeError). A large deterministic fuzz corpus of
hostile strings and non-string types exercises this, alongside an explicit catalogue that
names each distinct error condition.
"""
from __future__ import annotations
import unicodedata

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

_IS = (is_caip2, is_caip10, is_caip19)
_REQUIRE = (require_caip2, require_caip10, require_caip19)

VALID = {"caip2": "eip155:1", "caip10": "eip155:1:0xabc", "caip19": "eip155:1/slip44:60"}


def _fuzz_strings() -> list[str]:
    out: list[str] = []
    base = "eip155:1"
    # every C0 control + DEL, standalone and appended/prepended/embedded in a valid id
    for cp in list(range(0x00, 0x20)) + [0x7F]:
        ch = chr(cp)
        out += [ch, base + ch, ch + base, "eip155" + ch + ":1", base + ch + "x"]
    # every ASCII punctuation, in each structural position
    for ch in "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
        out += [ch, base + ch, ch + base, "eip155" + ch + "1", "eip" + ch + "155:1",
                "eip155:1:0xab" + ch, "eip155:1/slip44:60" + ch, "eip155:1/slip44:60/" + ch]
    # unicode whitespace / line terminators / bidi / zero-width / confusables
    for cp in [0x85, 0xA0, 0x1680, 0x2000, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000,
               0x200B, 0x200E, 0x202E, 0xFEFF, 0xFF11, 0xFF45, 0x0435, 0x0301, 0x00B2,
               0x1F600, 0xD800, 0xDFFF]:
        ch = chr(cp)
        out += [ch, base + ch, ch + base, "eip155:" + ch, "eip155:1:0x" + ch,
                "eip155:1/slip44:" + ch]
    # lengths and repeats
    out += ["", " ", "\n", "a" * 10000, "eip155:" + "a" * 10000, ":", "::", "/", "//",
            "eip155:1:" + "a" * 10000, "eip155:1/slip44:60/" + "t" * 10000]
    # a few normalization pairs (NFC vs NFD of an accented char, both non-ASCII -> reject)
    out += [unicodedata.normalize("NFC", "café:1"), unicodedata.normalize("NFD", "café:1")]
    return out


FUZZ_STRINGS = _fuzz_strings()
NON_STR = [123, -1, 0, 1.5, float("nan"), True, False, None, b"eip155:1",
           bytearray(b"eip155:1"), ["eip155:1"], ("eip155:1",), {"x": 1}, {1, 2},
           object(), 2 ** 128]


@pytest.mark.parametrize("fn", _IS)
def test_is_never_raises_on_strings(fn):
    for s in FUZZ_STRINGS:
        r = fn(s)
        assert r is True or r is False  # always a real bool, never an exception


@pytest.mark.parametrize("fn", _IS)
def test_is_never_raises_on_non_strings(fn):
    for x in NON_STR:
        assert fn(x) is False


@pytest.mark.parametrize("fn", _REQUIRE)
def test_require_raises_only_caiperror(fn):
    for x in FUZZ_STRINGS + NON_STR:
        try:
            fn(x)
        except CaipError:
            pass
        except BaseException as e:  # noqa: BLE001 - the whole point: nothing else may escape
            raise AssertionError(f"{fn.__name__}({x!r}) leaked {type(e).__name__}: {e}")


def test_builders_raise_only_caiperror():
    hostile_chains = FUZZ_STRINGS + NON_STR
    for c in hostile_chains:
        for coin in [60, -1, 1.5, True, None, "60"]:
            try:
                caip19_slip44(c, coin)
            except CaipError:
                pass
            except BaseException as e:  # noqa: BLE001
                raise AssertionError(f"caip19_slip44({c!r},{coin!r}) leaked {type(e).__name__}: {e}")
        for addr in ["0xabc", "", "0x ab", 123, None]:
            try:
                caip10_of(c, addr)
            except CaipError:
                pass
            except BaseException as e:  # noqa: BLE001
                raise AssertionError(f"caip10_of({c!r},{addr!r}) leaked {type(e).__name__}: {e}")


def test_is_and_require_agree_on_every_fuzz_input():
    # require_* must accept exactly what is_* accepts and reject exactly what is_* rejects.
    for s in FUZZ_STRINGS:
        for is_fn, req_fn, kind in zip(_IS, _REQUIRE, ("caip2", "caip10", "caip19")):
            if is_fn(s):
                assert req_fn(s) == s
            else:
                with pytest.raises(CaipError):
                    req_fn(s)


def test_error_catalogue():
    """Every distinct error condition raises CaipError. Names the full error surface."""
    conditions = {
        "require_caip2 rejects non-string": lambda: require_caip2(123),
        "require_caip2 rejects malformed": lambda: require_caip2("EIP155:1"),
        "require_caip2 rejects trailing newline": lambda: require_caip2("eip155:1\n"),
        "require_caip10 rejects a bare caip2": lambda: require_caip10("eip155:1"),
        "require_caip10 rejects bad address char": lambda: require_caip10("eip155:1:0x_a"),
        "require_caip19 rejects a bare caip2": lambda: require_caip19("eip155:1"),
        "require_caip19 rejects missing token colon": lambda: require_caip19("eip155:1/slip4460"),
        "caip19_slip44 rejects bad chain": lambda: caip19_slip44("not a chain", 60),
        "caip19_slip44 rejects negative coin": lambda: caip19_slip44("eip155:1", -1),
        "caip19_slip44 rejects float coin": lambda: caip19_slip44("eip155:1", 1.5),
        "caip19_slip44 rejects bool coin": lambda: caip19_slip44("eip155:1", True),
        "caip19_slip44 rejects non-int coin": lambda: caip19_slip44("eip155:1", "60"),
        "caip10_of rejects bad chain": lambda: caip10_of("not a chain", "0xabc"),
        "caip10_of rejects bad address": lambda: caip10_of("eip155:1", "0x ab"),
        "caip10_of rejects non-string address": lambda: caip10_of("eip155:1", 123),
        "caip10_of does not silently coerce int address": lambda: caip10_of("eip155:1", 0),
    }
    for name, thunk in conditions.items():
        with pytest.raises(CaipError):
            thunk()


def test_caiperror_is_a_valueerror():
    # callers that catch ValueError (the common contract) still catch CaipError.
    assert issubclass(CaipError, ValueError)
