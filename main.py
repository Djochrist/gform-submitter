#!/usr/bin/env python3
"""
Google Forms Bulk Submitter
============================
Reads config.toml and submits each configured form the specified number of times.
Includes random delays and user-agent rotation to avoid blocks.

Usage:
    uv run main.py
"""

import random
import sys
import time
import tomllib
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
]


def parse_prefilled_url(url: str) -> tuple[str, dict[str, str]]:
    """
    Extract the form submission endpoint and field values from a pre-filled URL.

    Args:
        url: A Google Forms pre-filled URL (viewform?usp=pp_url&entry.xxx=yyy...)

    Returns:
        Tuple of (action_url, {field: value}) ready to POST.
    """
    parsed = urlparse(url)

    # Extract the form ID from the URL path
    # Path looks like: /forms/d/e/<FORM_ID>/viewform
    path_parts = [p for p in parsed.path.split("/") if p]
    try:
        e_index = path_parts.index("e")
        form_id = path_parts[e_index + 1]
    except (ValueError, IndexError):
        console.print(f"[bold red]ERROR:[/bold red] Could not extract form ID from:\n  {url}")
        console.print("Make sure the URL contains '/forms/d/e/<FORM_ID>/viewform'")
        sys.exit(1)

    action_url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
    referer_url = f"https://docs.google.com/forms/d/e/{form_id}/viewform"

    # Extract all entry.* query parameters
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    fields = {k: v[0] for k, v in query_params.items() if k.startswith("entry.")}

    if not fields:
        console.print(f"[bold yellow]WARNING:[/bold yellow] No entry.* fields found in URL for form {form_id}.")
        console.print("Make sure you used a pre-filled link, not a plain form link.")

    return action_url, fields, referer_url


def submit_once(
    client: httpx.Client,
    action_url: str,
    fields: dict[str, str],
    referer_url: str,
    index: int,
    total: int,
    label: str,
) -> bool:
    """
    Submit the form a single time.

    Returns True on success, False on failure.
    """
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": referer_url,
        "Origin": "https://docs.google.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
    }

    try:
        response = client.post(
            action_url,
            data=fields,
            headers=headers,
            follow_redirects=True,
            timeout=20.0,
        )
        if response.status_code == 200:
            console.print(f"  [green]✓[/green] [{index}/{total}] {label}")
            return True
        else:
            console.print(f"  [yellow]✗[/yellow] [{index}/{total}] {label} — HTTP {response.status_code}")
            return False

    except httpx.TimeoutException:
        console.print(f"  [red]✗[/red] [{index}/{total}] {label} — Timeout (will retry next round)")
        return False
    except Exception as exc:
        console.print(f"  [red]✗[/red] [{index}/{total}] {label} — {exc}")
        return False


def run_form(
    action_url: str,
    fields: dict[str, str],
    referer_url: str,
    count: int,
    label: str,
    settings: dict,
) -> tuple[int, int]:
    """
    Submit a form `count` times, respecting timing settings.

    Returns (successes, failures).
    """
    min_pause      = float(settings.get("min_pause", 2.0))
    max_pause      = float(settings.get("max_pause", 5.0))
    long_every     = int(settings.get("long_pause_every", 15))
    long_min       = float(settings.get("long_pause_min", 10.0))
    long_max       = float(settings.get("long_pause_max", 20.0))

    ok = 0
    fail = 0

    with httpx.Client() as client:
        for i in range(1, count + 1):
            success = submit_once(client, action_url, fields, referer_url, i, count, label)
            if success:
                ok += 1
            else:
                fail += 1

            if i < count:
                if i % long_every == 0:
                    pause = round(random.uniform(long_min, long_max), 1)
                    console.print(f"  [dim]  ⏸  Long pause {pause}s after {i} submissions...[/dim]")
                    time.sleep(pause)
                else:
                    pause = round(random.uniform(min_pause, max_pause), 1)
                    time.sleep(pause)

    return ok, fail


def validate_config(forms: list[dict]) -> None:
    """Check that at least one form is properly configured."""
    for i, form in enumerate(forms):
        url = form.get("url", "")
        if "PASTE_YOUR_PREFILLED_LINK_HERE" in url or not url:
            console.print(
                Panel(
                    f"[yellow]Form #{i + 1} has a placeholder URL.[/yellow]\n\n"
                    "Edit [bold]config.toml[/bold] and replace the example URLs with your "
                    "actual pre-filled Google Form links.\n\n"
                    "To get a pre-filled link:\n"
                    "  1. Open your Google Form\n"
                    "  2. Click ⋮ (top right) → 'Get pre-filled link'\n"
                    "  3. Fill in your desired answers\n"
                    "  4. Click 'Get link' and copy the URL",
                    title="Configuration needed",
                    border_style="yellow",
                )
            )
            sys.exit(1)


def main() -> None:
    config_path = Path(__file__).parent / "config.toml"

    if not config_path.exists():
        console.print(
            Panel(
                "config.toml not found.\n"
                "Make sure config.toml is in the same directory as main.py.",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        sys.exit(1)

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    forms: list[dict] = config.get("forms", [])
    settings: dict = config.get("settings", {})

    if not forms:
        console.print("[bold red]No [[forms]] blocks found in config.toml[/bold red]")
        sys.exit(1)

    validate_config(forms)

    # ── Banner ──────────────────────────────────────────────
    console.print()
    console.rule("[bold blue]Google Forms Bulk Submitter[/bold blue]")
    console.print()
    console.print(f"  [dim]Forms to process : {len(forms)}[/dim]")
    for f in forms:
        console.print(f"  [dim]• {f.get('label', '?')} — {f.get('count', '?')} submissions[/dim]")
    console.print()

    total_ok = 0
    total_fail = 0
    start_time = time.time()

    for idx, form in enumerate(forms):
        url   = form["url"]
        count = int(form.get("count", 1))
        label = form.get("label", f"Form {idx + 1}")

        action_url, fields, referer_url = parse_prefilled_url(url)
        form_id = action_url.split("/e/")[1].split("/")[0]

        console.rule(f"[bold cyan]{label}[/bold cyan]")
        console.print(f"  [dim]Form ID : {form_id}[/dim]")
        console.print(f"  [dim]Fields  : {len(fields)} detected[/dim]")
        console.print(f"  [dim]Goal    : {count} submissions[/dim]")
        console.print()

        ok, fail = run_form(action_url, fields, referer_url, count, label, settings)
        total_ok   += ok
        total_fail += fail

        console.print()
        result_text = Text()
        result_text.append(f"  Result: ")
        result_text.append(f"{ok} OK", style="bold green")
        result_text.append("  ")
        result_text.append(f"{fail} failed" if fail else "0 failed", style="bold red" if fail else "dim")
        console.print(result_text)
        console.print()

        if idx < len(forms) - 1:
            between = float(settings.get("pause_between_forms", 15.0))
            console.print(f"  [dim]Pausing {between}s before next form...[/dim]")
            time.sleep(between)

    # ── Summary ──────────────────────────────────────────────
    elapsed = round(time.time() - start_time)
    minutes, seconds = divmod(elapsed, 60)

    console.rule("[bold blue]Final Summary[/bold blue]")
    console.print()

    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Metric", style="dim", width=22)
    table.add_column("Value",  style="bold")

    table.add_row("Total submissions",  str(total_ok + total_fail))
    table.add_row("Successful",         f"[green]{total_ok}[/green]")
    table.add_row("Failed",             f"[red]{total_fail}[/red]" if total_fail else "[dim]0[/dim]")
    table.add_row("Total time",         f"{minutes}m {seconds}s")

    console.print(table)
    console.print()


if __name__ == "__main__":
    main()
