"""Property-based tests for the CAIP validators (Hypothesis).

Where test_caip_regex.py runs a fixed differential corpus, these let Hypothesis explore the
input space structurally and SHRINK any failure to a minimal counterexample. The core
property is the differential one: the regex validator and the regex-free oracle must return
the same verdict for every input Hypothesis can find.
"""
from __future__ import annotations

from hypothesis import given, settings, strategies as st

from algovoi_substrate import caip
from caip_oracle import ORACLE

# an alphabet biased toward the grammar + its delimiters + adversarial bytes, so Hypothesis
# spends its budget near the accept/reject boundary rather than on obviously-invalid noise.
_ALPHABET = "abcxyzABCXYZ0159-_.%:/@ \n\r\t\x00\u2028\uffff\uff11\u0435"
_near = st.text(alphabet=_ALPHABET, max_size=45)
_any = st.text(max_size=60)


@given(s=_near)
@settings(max_examples=4000)
def test_caip2_regex_equals_oracle(s):
    assert caip.is_caip2(s) == ORACLE["caip2"](s)


@given(s=_near)
@settings(max_examples=4000)
def test_caip10_regex_equals_oracle(s):
    assert caip.is_caip10(s) == ORACLE["caip10"](s)


@given(s=_near)
@settings(max_examples=4000)
def test_caip19_regex_equals_oracle(s):
    assert caip.is_caip19(s) == ORACLE["caip19"](s)


@given(s=_any)
@settings(max_examples=2000)
def test_regex_equals_oracle_on_arbitrary_text(s):
    for kind, fn in (("caip2", caip.is_caip2), ("caip10", caip.is_caip10), ("caip19", caip.is_caip19)):
        assert fn(s) == ORACLE[kind](s), (kind, s)


# structured generators that BUILD grammar-valid identifiers: everything they produce must
# be accepted (round-trip: valid-by-construction implies validated).
_ns = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=3, max_size=8)
_ref = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_",
               min_size=1, max_size=32)
_addr = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.%",
                min_size=1, max_size=128)
_ans = _ns
_aref = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.%",
                min_size=1, max_size=128)
_tok = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.%",
               min_size=1, max_size=78)


@given(ns=_ns, ref=_ref)
def test_constructed_caip2_always_valid(ns, ref):
    s = f"{ns}:{ref}"
    assert caip.is_caip2(s)
    assert not caip.is_caip10(s) and not caip.is_caip19(s)  # level separation


@given(ns=_ns, ref=_ref, addr=_addr)
def test_constructed_caip10_always_valid(ns, ref, addr):
    assert caip.is_caip10(f"{ns}:{ref}:{addr}")


@given(ns=_ns, ref=_ref, ans=_ans, aref=_aref, tok=_tok, with_tok=st.booleans())
def test_constructed_caip19_always_valid(ns, ref, ans, aref, tok, with_tok):
    s = f"{ns}:{ref}/{ans}:{aref}"
    if with_tok:
        s += f"/{tok}"
    assert caip.is_caip19(s)


@given(s=_near)
def test_is_functions_never_raise(s):
    # robustness property: predicates always return a real bool, never raise.
    for fn in (caip.is_caip2, caip.is_caip10, caip.is_caip19):
        assert fn(s) in (True, False)
