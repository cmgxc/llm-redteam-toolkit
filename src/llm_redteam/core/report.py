"""Report generation — JSON + Markdown.

The Markdown report is the "hand to a security reviewer" artifact. It lists
severity-sorted findings, includes the raw prompt/response for each success,
and attaches a mitigation note per OWASP category.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .runner import RunSummary, RunResult


MITIGATIONS = {
    "direct_injection": (
        "Separate trusted instructions from untrusted input using clear delimiters "
        "or a structured format (e.g., JSON with schema validation). Consider a "
        "guardrail model or a deterministic pre-filter to detect injection cues."
    ),
    "jailbreaks": (
        "Harden the system prompt with explicit refusal policies and examples of "
        "what to refuse. Add a post-response classifier that blocks outputs matching "
        "high-risk categories regardless of how they were elicited."
    ),
    "encoding_attacks": (
        "Normalize inputs before passing them to the model: decode known encodings "
        "(base64, hex, ROT13), strip homoglyphs, and apply the same content policy "
        "to the normalized form as to the original."
    ),
    "data_leakage": (
        "Never put secrets or keys in the system prompt. Treat the system prompt as "
        "recoverable and design accordingly. Redact sensitive substrings from outputs."
    ),
    "indirect_injection": (
        "Tag retrieved documents as untrusted data, not instructions. Strip or escape "
        "HTML/Markdown that could carry instructions. Consider signing and validating "
        "trusted sources."
    ),
    "insecure_output": (
        "Never render model output as HTML/JS/Markdown without sanitization. Escape "
        "by default; allowlist tags if rich formatting is required."
    ),
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def write_report(summary: RunSummary, out_dir: Path) -> Path:
    """Write report.json and report.md into out_dir. Returns the markdown path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- JSON
    j = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": summary.target,
        "target_model": summary.target_model,
        "total": summary.total,
        "successes": summary.successes,
        "by_category": {
            k: {"successes": v[0], "total": v[1]}
            for k, v in summary.by_category().items()
        },
        "results": [r.to_dict() for r in summary.results],
    }
    (out_dir / "report.json").write_text(json.dumps(j, indent=2))

    # ---- Markdown
    md = _render_markdown(summary)
    md_path = out_dir / "report.md"
    md_path.write_text(md)
    return md_path


def _render_markdown(summary: RunSummary) -> str:
    lines: list[str] = []
    total = summary.total
    succ = summary.successes
    rate = (succ / total * 100) if total else 0.0

    lines += [
        f"# LLM Red Team Report",
        "",
        f"- **Generated:** {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- **Target:** `{summary.target}`",
        f"- **Model:** `{summary.target_model}`",
        f"- **Payloads run:** {total}",
        f"- **Successful attacks:** {succ} ({rate:.1f}%)",
        "",
        "## Results by category",
        "",
        "| Category | Successes | Total | Rate |",
        "|---|---:|---:|---:|",
    ]
    for cat, (s, t) in sorted(summary.by_category().items()):
        pct = (s / t * 100) if t else 0
        lines.append(f"| `{cat}` | {s} | {t} | {pct:.0f}% |")
    lines += ["", "## Findings", ""]

    # severity-sorted successes first, then failures grouped by category
    successes = [r for r in summary.results if r.verdict.success]
    successes.sort(key=lambda r: (SEVERITY_ORDER.get(r.severity, 9), r.category, r.payload_id))

    if not successes:
        lines += ["_No successful attacks detected in this run._", ""]
    else:
        for r in successes:
            lines += _finding_block(r)

    # Mitigations section
    cats_with_success = {r.category for r in successes}
    if cats_with_success:
        lines += ["## Suggested mitigations", ""]
        for cat in sorted(cats_with_success):
            if cat in MITIGATIONS:
                lines += [f"### `{cat}`", "", MITIGATIONS[cat], ""]

    # Appendix: all payloads (collapsed-feeling)
    lines += ["## Appendix — all payloads", ""]
    for r in summary.results:
        mark = "✅" if r.verdict.success else "❌"
        lines.append(f"- {mark} `{r.payload_id}` ({r.category}, {r.severity}) — {r.verdict.mode}: {r.verdict.rationale}")
    lines.append("")

    return "\n".join(lines)


def _finding_block(r: RunResult) -> list[str]:
    return [
        f"### [{r.severity.upper()}] `{r.payload_id}` — {r.category} ({r.owasp})",
        "",
        f"**Verdict:** SUCCESS via {r.verdict.mode} judge "
        f"(confidence {r.verdict.confidence:.2f}). {r.verdict.rationale}",
        "",
        "<details><summary>Prompt</summary>",
        "",
        "```",
        r.prompt,
        "```",
        "</details>",
        "",
        "<details><summary>Response</summary>",
        "",
        "```",
        (r.response or "").strip()[:1200],
        "```",
        "</details>",
        "",
    ]
