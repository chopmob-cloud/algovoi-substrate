"""Independent, regex-free reference parser for CAIP-2/10/19.

This is the ORACLE the regex validators are differentially tested against. It implements the
same grammar by explicit character-class membership, length bounds, and delimiter splitting,
using no regular expressions at all. Because the delimiter characters ``:`` and ``/`` are
excluded from every component character class, splitting on them is a faithful parse. If the
regex and this oracle ever disagree on any input, one of them has a bug.
"""
from __future__ import annotations

import string

_LOWER = set(string.ascii_lowercase)
_DIGIT = set(string.digits)
_NS = _LOWER | _DIGIT | {"-"}                       # namespace / asset_namespace [-a-z0-9]
_REF = _LOWER | set(string.ascii_uppercase) | _DIGIT | {"-", "_"}   # reference [-_a-zA-Z0-9]
_ADDR = _LOWER | set(string.ascii_uppercase) | _DIGIT | {"-", ".", "%"}  # [-.%a-zA-Z0-9]


def _cls(s: str, allowed: set, lo: int, hi: int) -> bool:
    return lo <= len(s) <= hi and all(c in allowed for c in s)


def _namespace(s: str) -> bool:
    return _cls(s, _NS, 3, 8)


def _reference(s: str) -> bool:
    return _cls(s, _REF, 1, 32)


def _address(s: str) -> bool:
    return _cls(s, _ADDR, 1, 128)


def _asset_reference(s: str) -> bool:
    return _cls(s, _ADDR, 1, 128)


def _token_id(s: str) -> bool:
    return _cls(s, _ADDR, 1, 78)


def ref_is_caip2(s: object) -> bool:
    if not isinstance(s, str):
        return False
    parts = s.split(":")
    return len(parts) == 2 and _namespace(parts[0]) and _reference(parts[1])


def ref_is_caip10(s: object) -> bool:
    if not isinstance(s, str):
        return False
    parts = s.split(":")   # exactly ns : ref : address (address excludes ':')
    if len(parts) != 3:
        return False
    ns, ref, addr = parts
    return _namespace(ns) and _reference(ref) and _address(addr)


def ref_is_caip19(s: object) -> bool:
    if not isinstance(s, str):
        return False
    slash = s.split("/")   # chain / asset_ns:asset_ref [ / token ]  ('/' excluded elsewhere)
    if len(slash) == 2:
        chain, assetpart, token = slash[0], slash[1], None
    elif len(slash) == 3:
        chain, assetpart, token = slash
    else:
        return False
    if not ref_is_caip2(chain):
        return False
    ap = assetpart.split(":")
    if len(ap) != 2:
        return False
    asset_ns, asset_ref = ap
    if not (_namespace(asset_ns) and _asset_reference(asset_ref)):
        return False
    return token is None or _token_id(token)


ORACLE = {"caip2": ref_is_caip2, "caip10": ref_is_caip10, "caip19": ref_is_caip19}
