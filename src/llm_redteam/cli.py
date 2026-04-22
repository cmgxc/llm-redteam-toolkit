"""Command-line interface.

    python -m llm_redteam.cli run --target mock
    python -m llm_redteam.cli list
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .core import Judge, Runner, build_target, write_report
from .payloads import list_categories, load_payloads, PayloadError


console = Console()


@click.group(help="LLM Red Team Toolkit — adversarial testing for LLM apps.")
def cli() -> None:
    load_dotenv()  # load .env if present


@cli.command("list", help="List payload categories bundled with the toolkit.")
def list_cmd() -> None:
    cats = list_categories()
    try:
        payloads = load_payloads(cats)
    except PayloadError as e:
        console.print(f"[red]Payload error:[/red] {e}")
        sys.exit(2)

    table = Table(title="Payload catalog")
    table.add_column("Category")
    table.add_column("# payloads", justify="right")
    table.add_column("OWASP", justify="center")
    table.add_column("Default severity", justify="center")

    counts: dict[str, list] = {}
    for p in payloads:
        counts.setdefault(p["category"], []).append(p)

    for cat in cats:
        ps = counts.get(cat, [])
        if not ps:
            continue
        table.add_row(cat, str(len(ps)), ps[0]["owasp"], ps[0]["severity"])
    console.print(table)


@cli.command("run", help="Run payloads against a target.")
@click.option("--target", "target_kind", default="mock",
              type=click.Choice(["mock", "openai"]),
              help="Target adapter. `mock` needs no API keys.")
@click.option("--model", default=None, help="Override target model.")
@click.option("--categories", default=None,
              help="Comma-separated categories to run (default: all).")
@click.option("--out", "out_dir", default="reports/latest",
              type=click.Path(file_okay=False, path_type=Path),
              help="Directory to write report into.")
@click.option("--no-llm-judge", is_flag=True,
              help="Disable the LLM judge (regex only). Useful for offline CI.")
def run_cmd(target_kind: str, model: str | None, categories: str | None,
            out_dir: Path, no_llm_judge: bool) -> None:
    # --- pick payloads
    cats = [c.strip() for c in categories.split(",")] if categories else None
    try:
        payloads = load_payloads(cats)
    except PayloadError as e:
        console.print(f"[red]Payload error:[/red] {e}")
        sys.exit(2)
    if not payloads:
        console.print("[red]No payloads matched the given categories.[/red]")
        sys.exit(2)

    # --- target
    try:
        target = build_target(target_kind, model=model)
    except Exception as e:
        console.print(f"[red]Target error:[/red] {e}")
        sys.exit(2)

    # --- judge (LLM judge is optional — works regex-only without keys)
    judge_client = None
    if not no_llm_judge and os.environ.get("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            judge_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        except Exception as e:
            console.print(f"[yellow]LLM judge unavailable ({e}), falling back to regex-only.[/yellow]")
    judge = Judge(llm_client=judge_client)

    console.print(
        f"[bold]Target:[/bold] {target.name} ({target.model})   "
        f"[bold]Payloads:[/bold] {len(payloads)}   "
        f"[bold]Judge:[/bold] {'llm+regex' if judge_client else 'regex-only'}"
    )

    runner = Runner(target=target, judge=judge)

    def progress(i: int, total: int, p: dict):
        console.print(f"  [cyan][{i}/{total}][/cyan] {p['id']}", highlight=False)

    summary = runner.run(payloads, progress_cb=progress)

    md_path = write_report(summary, out_dir)

    # --- summary table
    console.print("")
    table = Table(title=f"Results — {summary.successes}/{summary.total} successful")
    table.add_column("Category")
    table.add_column("Success", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Rate", justify="right")
    for cat, (s, t) in sorted(summary.by_category().items()):
        pct = (s / t * 100) if t else 0
        table.add_row(cat, str(s), str(t), f"{pct:.0f}%")
    console.print(table)

    console.print(f"\n[green]Report written:[/green] {md_path}")


def main() -> None:  # entry point for `python -m llm_redteam.cli`
    cli()


if __name__ == "__main__":
    main()
