"""Real-world corpus: identifiers pulled from the ChainAgnostic/namespaces registry docs.

Synthetic vectors prove the grammar; this proves the validator accepts the CAIP identifiers
that actually appear in the registry across many namespaces (CAIP-2, CAIP-10 and CAIP-19
forms), and that the registered layer correctly rejects real doc shorthands that use an
unregistered namespace (e.g. "eip" instead of "eip155").
"""
import json
from pathlib import Path

import pytest

from algovoi_substrate import caip

DATA = json.loads((Path(__file__).parent / "caip_realworld.json").read_text(encoding="utf-8"))


def _grammar_ok(s: str) -> bool:
    return caip.is_caip2(s) or caip.is_caip10(s) or caip.is_caip19(s)


def _registered_ok(s: str) -> bool:
    return (caip.is_registered_caip2(s) or caip.is_registered_caip10(s)
            or caip.is_registered_caip19(s))


def test_corpus_is_substantial():
    assert len(DATA["registered_real"]) >= 30


@pytest.mark.parametrize("s", DATA["registered_real"] + DATA["conflux_verified"])
def test_real_registry_identifiers_accepted(s):
    assert _grammar_ok(s), f"real registry identifier rejected by grammar: {s!r}"
    assert _registered_ok(s), f"real registry identifier not on a registered namespace: {s!r}"


@pytest.mark.parametrize("s", DATA["unregistered_shorthand"])
def test_doc_shorthand_is_grammar_valid_but_unregistered(s):
    # e.g. "eip:297": well-formed CAIP-2 but "eip" is not a registered namespace, so the
    # registered layer catches the shorthand while the grammar layer does not.
    assert _grammar_ok(s)
    assert not _registered_ok(s)


def test_spans_all_three_caip_levels():
    real = DATA["registered_real"] + DATA["conflux_verified"]
    assert any(caip.is_caip2(s) for s in real), "no CAIP-2 in corpus"
    assert any(caip.is_caip10(s) for s in real), "no CAIP-10 in corpus"
    assert any(caip.is_caip19(s) for s in real), "no CAIP-19 in corpus"
