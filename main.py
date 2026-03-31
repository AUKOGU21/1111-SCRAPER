"""
ELEVENELEVEN Grants & Accelerator Scraper
Main entry point.

Usage:
    python main.py              # Run once immediately
    python main.py --schedule   # Run daily on a schedule
    python main.py --dry-run    # Scrape only, no Notion push
    python main.py --top 10     # Push only top 10 by relevance
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import schedule
import time

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

# ── Bootstrap ──────────────────────────────────────────────────────────────────

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(
            Path("logs") / f"scraper_{datetime.now().strftime('%Y%m%d')}.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)
console = Console()


def check_env() -> bool:
    """Validate required environment variables are present."""
    missing = []
    if not os.environ.get("NOTION_API_KEY"):
        missing.append("NOTION_API_KEY")
    if not os.environ.get("NOTION_DATABASE_ID"):
        missing.append("NOTION_DATABASE_ID")

    if missing:
        console.print(
            f"\n[bold red]Missing required environment variables:[/bold red] "
            f"{', '.join(missing)}\n"
            f"Copy [bold].env.example[/bold] to [bold].env[/bold] and fill in your values.\n"
        )
        return False
    return True


def print_opportunities_table(opportunities: List[dict], limit: int = 20) -> None:
    table = Table(title=f"Top {min(limit, len(opportunities))} Opportunities by Relevance")
    table.add_column("Score", style="cyan", width=6)
    table.add_column("Title", style="bold white", max_width=40)
    table.add_column("Type", style="green", width=12)
    table.add_column("Deadline", style="yellow", width=12)
    table.add_column("Status", style="magenta", width=9)
    table.add_column("Source", style="dim", max_width=22)

    for opp in opportunities[:limit]:
        open_status = opp.get("open_status", "Unknown")
        status_style = {
            "Open": "[green]Open[/green]",
            "Closed": "[red]Closed[/red]",
            "Unknown": "[yellow]?[/yellow]",
        }.get(open_status, open_status)

        table.add_row(
            str(opp.get("relevance_score", 0)),
            opp["title"],
            opp["type"],
            opp.get("deadline") or "TBD",
            status_style,
            opp["source_name"],
        )

    console.print(table)


def run(dry_run: bool = False, top: int = 0, refresh: bool = False) -> None:
    """Core pipeline: scrape → draft → push to Notion."""
    console.rule("[bold blue]ELEVENELEVEN Grants Scraper[/bold blue]")
    console.print(f"  Run started at [bold]{datetime.now().strftime('%Y-%m-%d %H:%M')}[/bold]\n")

    # 1. Scrape
    console.print("[bold]Step 1/3: Scraping sources...[/bold]")
    from scraper.scraper import run_scraper
    opportunities = run_scraper()

    if top:
        opportunities = opportunities[:top]
        console.print(f"  Filtered to top {top} by relevance score.\n")

    print_opportunities_table(opportunities)
    console.print(f"\n  [green]Found {len(opportunities)} unique opportunities.[/green]\n")

    if dry_run:
        console.print("[yellow]Dry run — skipping draft generation and Notion push.[/yellow]")
        return

    if not check_env():
        sys.exit(1)

    # Optional: wipe existing pages before re-creating
    if refresh:
        from notion.client import get_client, get_database_id, archive_all_pages
        console.print("[bold yellow]Refreshing: archiving all existing Notion pages...[/bold yellow]")
        n = archive_all_pages(get_client(), get_database_id())
        console.print(f"  Archived {n} pages. Recreating now...\n")

    # 2. Generate drafts + completion scores
    console.print("[bold]Step 2/3: Generating application drafts...[/bold]")
    from drafts.generator import generate_drafts
    drafts_map = {}
    completion_map = {}
    incomplete_map = {}
    for opp in opportunities:
        try:
            drafts, score, incomplete = generate_drafts(opp)
            url = opp["opportunity_url"]
            drafts_map[url] = drafts
            completion_map[url] = score
            incomplete_map[url] = incomplete
            console.print(
                f"  [{('green' if score >= 80 else 'yellow' if score >= 50 else 'red')}]"
                f"{score}%[/] complete  [dim]{opp['title'][:55]}[/dim]"
            )
        except Exception as e:
            logger.error(f"Draft generation failed for {opp['title']}: {e}")

    if completion_map:
        avg = int(sum(completion_map.values()) / len(completion_map))
        console.print(f"\n  Average completion: [bold]{avg}%[/bold]")
        if avg < 80:
            console.print(
                f"  [yellow]Tip: fill in more of founder_context.yaml "
                f"to improve draft quality.[/yellow]"
            )
    console.print()

    # 3. Push to Notion
    console.print("[bold]Step 3/3: Pushing to Notion...[/bold]")
    from notion.client import push_all
    stats = push_all(
        opportunities,
        drafts_map=drafts_map,
        completion_map=completion_map,
        incomplete_map=incomplete_map,
    )

    console.print(f"\n  [green]Done![/green]")
    console.print(f"  Created: [bold]{stats['created']}[/bold]  "
                  f"Skipped: {stats['skipped']}  "
                  f"Errors: [red]{stats['errors']}[/red]")
    console.rule()


def add_manual(name: str, url: str, opp_type: str, deadline: Optional[str], tags: str, notes: str) -> None:
    """Add a manually found opportunity directly to Notion."""
    if not check_env():
        sys.exit(1)

    from scraper.scraper import add_manual_opportunity
    from drafts.generator import generate_drafts
    from notion.client import push_opportunity

    tag_list = [t.strip() for t in tags.split(",")] if tags else ["manual"]
    opp = add_manual_opportunity(name, url, opp_type, deadline, tag_list, notes)

    console.print(f"\n[bold]Generating drafts for:[/bold] {name}")
    drafts, score, incomplete = generate_drafts(opp)
    console.print(f"  Context completion: [bold]{score}%[/bold]")

    console.print("[bold]Pushing to Notion...[/bold]")
    page_id = push_opportunity(opp, drafts=drafts, completion_score=score, incomplete_fields=incomplete)
    if page_id:
        console.print(f"[green]Done![/green] Added to Notion: {name}")
    else:
        console.print(f"[red]Failed to push to Notion.[/red]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ELEVENELEVEN Grants & Accelerator Scraper"
    )
    subparsers = parser.add_subparsers(dest="command")

    # ── run (default) ──────────────────────────────────────────────────────────
    run_parser = subparsers.add_parser("run", help="Scrape and push to Notion (default)")
    run_parser.add_argument("--dry-run", action="store_true",
                            help="Scrape only; no Notion push.")
    run_parser.add_argument("--schedule", action="store_true",
                            help="Run on a daily schedule.")
    run_parser.add_argument("--top", type=int, default=0,
                            help="Only push the top N by relevance.")
    run_parser.add_argument("--all-sources", action="store_true",
                            help="Include sources not flagged as pre-revenue-ok.")
    run_parser.add_argument("--refresh", action="store_true",
                            help="Archive all existing Notion pages and recreate from scratch.")

    # ── add (manual entry) ─────────────────────────────────────────────────────
    add_parser = subparsers.add_parser("add", help="Manually add an opportunity to Notion")
    add_parser.add_argument("name", help="Program name, e.g. 'Canopy by f.inc'")
    add_parser.add_argument("url", help="Application URL")
    add_parser.add_argument("--type", default="accelerator",
                            choices=["grant", "accelerator", "fellowship", "competition", "investment"],
                            help="Opportunity type")
    add_parser.add_argument("--deadline", default=None,
                            help="Deadline in YYYY-MM-DD format, e.g. 2025-04-06")
    add_parser.add_argument("--tags", default="manual",
                            help="Comma-separated tags, e.g. 'consumer,pre-revenue ok'")
    add_parser.add_argument("--notes", default="",
                            help="Any notes about this opportunity")

    args = parser.parse_args()
    Path("logs").mkdir(exist_ok=True)

    # Default to 'run' if no subcommand given
    if args.command == "add":
        add_manual(args.name, args.url, args.type, args.deadline, args.tags, args.notes)
        return

    # run command (or no subcommand)
    dry_run = getattr(args, "dry_run", False)
    top = getattr(args, "top", 0)
    refresh = getattr(args, "refresh", False)
    schedule_mode = getattr(args, "schedule", False)

    if schedule_mode:
        interval = int(os.environ.get("SCRAPE_INTERVAL_HOURS", 24))
        console.print(
            f"[bold blue]Scheduling scraper every {interval} hours.[/bold blue] "
            f"Press Ctrl+C to stop."
        )
        run(dry_run=dry_run, top=top, refresh=refresh)
        schedule.every(interval).hours.do(run, dry_run=dry_run, top=top)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run(dry_run=dry_run, top=top, refresh=refresh)


if __name__ == "__main__":
    main()
