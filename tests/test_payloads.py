"""Validate every bundled payload loads and has a usable success signal."""

import re

import pytest

from llm_redteam.payloads import list_categories, load_payloads


def test_categories_nonempty():
    cats = list_categories()
    assert len(cats) >= 4, f"expected at least 4 payload categories, got {cats}"


def test_all_payloads_load():
    payloads = load_payloads()
    assert len(payloads) >= 30, "catalog should have at least 30 payloads"
    ids = [p["id"] for p in payloads]
    assert len(ids) == len(set(ids)), "payload IDs must be unique"


def test_every_payload_has_success_signal():
    for p in load_payloads():
        assert p.get("regex_success") or p.get("judge_prompt"), (
            f"{p['id']}: must define regex_success or judge_prompt"
        )


def test_regex_success_patterns_compile():
    for p in load_payloads():
        for pat in (p.get("regex_success") or []):
            try:
                re.compile(pat)
            except re.error as e:
                pytest.fail(f"{p['id']}: bad regex {pat!r}: {e}")


def test_owasp_ids_look_valid():
    valid = {"LLM01", "LLM02", "LLM03", "LLM04", "LLM05", "LLM06",
             "LLM07", "LLM08", "LLM09", "LLM10"}
    for p in load_payloads():
        assert p["owasp"] in valid, f"{p['id']}: unknown OWASP id {p['owasp']}"
