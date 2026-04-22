"""Payload loader — reads the bundled YAML files and validates them.

Each file in this directory defines one category. Every payload gets a stable
`id`, a free-form `prompt`, and *at least one* of `regex_success` or
`judge_prompt`. Category-level fields (owasp, severity) are inherited onto
each payload so downstream code can treat them as flat records.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml


class PayloadError(Exception):
    """Raised when a payload YAML file is malformed."""


REQUIRED_FILE_KEYS = {"category", "payloads"}
REQUIRED_PAYLOAD_KEYS = {"id", "prompt"}


def _payload_dir() -> Path:
    return Path(__file__).resolve().parent


def list_categories() -> list[str]:
    return sorted(p.stem for p in _payload_dir().glob("*.yaml"))


def load_payloads(categories: Iterable[str] | None = None) -> list[dict]:
    """Load (and validate) payloads for the given categories.

    If `categories` is None, load everything.
    Returns a flat list of payload dicts annotated with category/owasp/severity.
    """
    selected = set(categories) if categories else None
    out: list[dict] = []

    for path in sorted(_payload_dir().glob("*.yaml")):
        if selected is not None and path.stem not in selected:
            continue
        with path.open() as fh:
            data = yaml.safe_load(fh) or {}

        missing = REQUIRED_FILE_KEYS - data.keys()
        if missing:
            raise PayloadError(f"{path.name}: missing file-level key(s) {missing}")

        category = data["category"]
        default_owasp = data.get("owasp", "LLM01")
        default_severity = data.get("severity", "medium")

        for p in data["payloads"]:
            pm = REQUIRED_PAYLOAD_KEYS - p.keys()
            if pm:
                raise PayloadError(f"{path.name}:{p.get('id','<no id>')}: missing {pm}")
            if not (p.get("regex_success") or p.get("judge_prompt")):
                raise PayloadError(
                    f"{path.name}:{p['id']}: must define regex_success or judge_prompt"
                )
            out.append({
                "id": p["id"],
                "category": category,
                "owasp": p.get("owasp", default_owasp),
                "severity": p.get("severity", default_severity),
                "prompt": p["prompt"].rstrip(),
                "regex_success": p.get("regex_success"),
                "regex_mode": p.get("regex_mode", "any"),
                "judge_prompt": p.get("judge_prompt"),
                "system_prompt": p.get("system_prompt"),
            })
    return out
