"""Python <-> TypeScript constant parity for the CAIP module.

The two implementations hand-maintain the same regex grammar and the same 41-namespace
registry in separate files. If they drift, Python and JavaScript silently disagree on what is
valid or registered. This test parses the TypeScript source and asserts its constants are
byte-identical to Python's, so any copy drift fails CI rather than shipping.
"""
import re
from pathlib import Path

import pytest

from algovoi_substrate import caip

_TS = Path(__file__).resolve().parents[2] / "typescript" / "src" / "caip.ts"


def _ts_source() -> str:
    if not _TS.is_file():
        pytest.skip(f"TypeScript source not present at {_TS}")
    return _TS.read_text(encoding="utf-8")


def test_registry_parity_py_vs_ts():
    src = _ts_source()
    m = re.search(r"REGISTERED_NAMESPACES:\s*ReadonlySet<string>\s*=\s*new Set\(\[(.*?)\]\)", src, re.S)
    assert m, "could not locate REGISTERED_NAMESPACES Set literal in caip.ts"
    ts_ns = set(re.findall(r"'([^']+)'", m.group(1)))
    py_ns = set(caip.REGISTERED_NAMESPACES)
    assert ts_ns == py_ns, (
        f"registry drift: only in py={sorted(py_ns - ts_ns)} only in ts={sorted(ts_ns - py_ns)}"
    )
    assert len(ts_ns) == 41


def test_grammar_constants_parity_py_vs_ts():
    src = _ts_source()
    # the shared CHAIN fragment
    m = re.search(r"const CHAIN = '([^']+)'", src)
    assert m, "CHAIN constant not found in caip.ts"
    ts_chain = m.group(1)
    py_chain = caip._CHAIN  # noqa: SLF001 - deliberately checking the private constant matches
    assert ts_chain == py_chain, f"CHAIN grammar drift: py={py_chain!r} ts={ts_chain!r}"

    # the three character-class bodies must match between the Python and TS regexes
    for name, ts_pat in {
        "caip10_tail": r":\[-\.%a-zA-Z0-9\]\{1,128\}",
        "caip19_tail": r"/\[-a-z0-9\]\{3,8\}:\[-\.%a-zA-Z0-9\]\{1,128\}\(/\[-\.%a-zA-Z0-9\]\{1,78\}\)\?",
    }.items():
        assert re.search(ts_pat, src), f"{name}: expected class body not found in caip.ts"

    # and Python's compiled patterns use the same class bodies (anchors differ by language)
    assert caip._CAIP10_RE.pattern.count("[-.%a-zA-Z0-9]{1,128}") == 1  # noqa: SLF001
    assert caip._CAIP19_RE.pattern.count("[-.%a-zA-Z0-9]{1,78}") == 1   # noqa: SLF001


def test_public_api_parity_py_vs_ts():
    """Every CAIP function exported from Python has a camelCase counterpart in caip.ts."""
    src = _ts_source()
    mapping = {
        "is_caip2": "isCaip2", "is_caip10": "isCaip10", "is_caip19": "isCaip19",
        "require_caip2": "requireCaip2", "require_caip10": "requireCaip10",
        "require_caip19": "requireCaip19", "caip19_slip44": "caip19Slip44",
        "caip10_of": "caip10Of", "is_registered_namespace": "isRegisteredNamespace",
        "is_registered_caip2": "isRegisteredCaip2", "is_registered_caip10": "isRegisteredCaip10",
        "is_registered_caip19": "isRegisteredCaip19", "require_registered_caip2": "requireRegisteredCaip2",
        "require_registered_caip10": "requireRegisteredCaip10",
        "require_registered_caip19": "requireRegisteredCaip19",
        "registered_namespaces": "registeredNamespaces",
        "is_valid_caip2": "isValidCaip2", "is_valid_caip10": "isValidCaip10",
        "is_valid_caip19": "isValidCaip19", "require_valid_caip2": "requireValidCaip2",
        "require_valid_caip10": "requireValidCaip10", "require_valid_caip19": "requireValidCaip19",
    }
    for py_name, ts_name in mapping.items():
        assert hasattr(caip, py_name), f"python missing {py_name}"
        assert re.search(rf"\bexport function {ts_name}\b", src), f"caip.ts missing export {ts_name}"


def test_reference_format_parity_py_vs_ts():
    """The per-namespace reference-format rules must be identical between Python and TS."""
    src = _ts_source()
    # extract the TS REFERENCE_FORMATS object body
    m = re.search(r"const REFERENCE_FORMATS: Record<string, RegExp> = \{(.*?)\};", src, re.S)
    assert m, "REFERENCE_FORMATS not found in caip.ts"
    body = m.group(1)
    # ns: /pattern/,  -> {ns: pattern}
    ts_rules = dict(re.findall(r"(\w+):\s*/(.+?)/,", body))
    py_rules = {ns: rx.pattern.replace(r"\A", "^").replace(r"\Z", "$")
                for ns, rx in caip._REFERENCE_FORMATS.items()}  # noqa: SLF001
    assert set(ts_rules) == set(py_rules) == set(caip.REFERENCE_FORMAT_NAMESPACES)
    for ns in py_rules:
        assert ts_rules[ns] == py_rules[ns], f"{ns}: py={py_rules[ns]!r} ts={ts_rules[ns]!r}"
