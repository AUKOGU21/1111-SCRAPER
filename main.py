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
from typing import List

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
    table.add_column("Title", style="bold white", max_width=45)
    table.add_column("Type", style="green", width=14)
    table.add_column("Deadline", style="yellow", width=12)
    table.add_column("Source", style="dim", max_width=25)

    for opp in opportunities[:limit]:
        table.add_row(
            str(opp.get("relevance_score", 0)),
            opp["title"],
            opp["type"],
            opp.get("deadline") or "TBD",
            opp["source_name"],
        )

    console.print(table)


def run(dry_run: bool = False, top: int = 0) -> None:
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

    # 2. Generate drafts
    console.print("[bold]Step 2/3: Generating application drafts...[/bold]")
    from drafts.generator import generate_drafts
    drafts_map = {}
    for opp in opportunities:
        try:
            drafts_map[opp["opportunity_url"]] = generate_drafts(opp)
            console.print(f"  Drafted: [dim]{opp['title'][:60]}[/dim]")
        except Exception as e:
            logger.error(f"Draft generation failed for {opp['title']}: {e}")
    console.print(f"\n  [green]Drafts generated for {len(drafts_map)} opportunities.[/green]\n")

    # 3. Push to Notion
    console.print("[bold]Step 3/3: Pushing to Notion...[/bold]")
    from notion.client import push_all
    stats = push_all(opportunities, drafts_map=drafts_map)

    console.print(f"\n  [green]Done![/green]")
    console.print(f"  Created: [bold]{stats['created']}[/bold]  "
                  f"Skipped: {stats['skipped']}  "
                  f"Errors: [red]{stats['errors']}[/red]")
    console.rule()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ELEVENELEVEN Grants & Accelerator Scraper"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape only; do not generate drafts or push to Notion.",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on a daily schedule (interval set by SCRAPE_INTERVAL_HOURS).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="Only push the top N opportunities by relevance score.",
    )
    args = parser.parse_args()

    Path("logs").mkdir(exist_ok=True)

    if args.schedule:
        interval = int(os.environ.get("SCRAPE_INTERVAL_HOURS", 24))
        console.print(
            f"[bold blue]Scheduling scraper every {interval} hours.[/bold blue] "
            f"Press Ctrl+C to stop."
        )
        # Run immediately, then on schedule
        run(dry_run=args.dry_run, top=args.top)
        schedule.every(interval).hours.do(run, dry_run=args.dry_run, top=args.top)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run(dry_run=args.dry_run, top=args.top)


if __name__ == "__main__":
    main()
