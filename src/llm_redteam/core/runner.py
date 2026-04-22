"""Runner — orchestrates payloads → target → judge → results."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Iterable, Optional

from .target import Target, TargetResponse
from .judge import Judge, Verdict


@dataclass
class RunResult:
    payload_id: str
    category: str
    severity: str
    owasp: str
    prompt: str
    response: str
    verdict: Verdict
    target: str
    target_model: str
    latency_ms: int
    error: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = asdict(self.verdict)
        return d


@dataclass
class RunSummary:
    target: str
    target_model: str
    results: list[RunResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def successes(self) -> int:
        return sum(1 for r in self.results if r.verdict.success)

    def by_category(self) -> dict[str, tuple[int, int]]:
        out: dict[str, tuple[int, int]] = {}
        for r in self.results:
            s, t = out.get(r.category, (0, 0))
            out[r.category] = (s + int(r.verdict.success), t + 1)
        return out


class Runner:
    def __init__(self, target: Target, judge: Judge):
        self.target = target
        self.judge = judge

    def run(self, payloads: Iterable[dict], progress_cb=None) -> RunSummary:
        """Execute every payload once. `progress_cb(i, total, payload)` optional."""
        summary = RunSummary(target=self.target.name, target_model=self.target.model)
        payloads = list(payloads)

        for i, p in enumerate(payloads, start=1):
            if progress_cb:
                progress_cb(i, len(payloads), p)

            prompt = p["prompt"]
            system_prompt = p.get("system_prompt")  # usually None

            resp: TargetResponse = self.target.send(prompt, system_prompt=system_prompt)
            verdict = self.judge.evaluate(p, resp.text)

            summary.results.append(RunResult(
                payload_id=p["id"],
                category=p["category"],
                severity=p.get("severity", "medium"),
                owasp=p.get("owasp", "LLM01"),
                prompt=prompt,
                response=resp.text,
                verdict=verdict,
                target=self.target.name,
                target_model=resp.model,
                latency_ms=resp.latency_ms,
                error=resp.error,
            ))
        return summary
