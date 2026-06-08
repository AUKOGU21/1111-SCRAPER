"""
Scraper — builds opportunity list from the verified program registry.

Strategy:
  1. Start from the curated PROGRAMS list (known-good, pre-verified)
  2. For programs with a scrape_url, attempt to fetch a fresher deadline
  3. Return structured dicts sorted by urgency (open + soonest deadline first)
"""

import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from scraper.sources import PROGRAMS

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

STATUS_PRIORITY = {
    "open": 0,
    "always_open": 1,
    "opens_soon": 2,
    "closed_check_site": 3,
}

RELEVANCE_BONUSES = {
    "Black women founder": 20,
    "Black founder": 15,
    "women founder": 10,
    "HBS": 15,
    "pre-revenue ok": 10,
    "consumer": 8,
    "retail": 8,
    "no-equity": 5,
    "top-tier": 8,
}


def _fetch_html(url: str, timeout: int = 12) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.debug(f"Could not fetch {url}: {e}")
        return None


def _extract_deadline(text: str) -> Optional[str]:
    """Parse a deadline date from freeform text. Returns ISO 8601 or None."""
    patterns = [
        r"\b(January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{4}\b",
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(0)
            for fmt in ["%B %d, %Y", "%B %d %Y", "%d %B %Y", "%m/%d/%Y", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(raw.replace(",", ""), fmt.replace(",", ""))
                    # Skip dates more than 30 days in the past
                    if (datetime.now() - dt).days > 30:
                        continue
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return None


def _try_refresh_deadline(program: dict) -> Optional[str]:
    """
    Try to scrape a fresher deadline from the program's page.
    Returns ISO date string if found, else None.
    """
    scrape_url = program.get("scrape_url")
    if not scrape_url:
        return None

    html = _fetch_html(scrape_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    return _extract_deadline(text)


def _relevance_score(program: dict) -> int:
    """Score 0–100 based on tags and program characteristics."""
    score = 40  # base score — everything in the registry is pre-vetted
    for tag in program.get("tags", []):
        score += RELEVANCE_BONUSES.get(tag, 0)
    if program.get("pre_revenue_ok"):
        score += 5
    return min(score, 100)


def build_opportunity(program: dict, refreshed_deadline: Optional[str] = None) -> dict:
    """Convert a program registry entry into a push-ready opportunity dict."""
    deadline = refreshed_deadline or program.get("deadline")

    return {
        "title": program["name"],
        "source_name": program["name"],
        "source_url": program["url"],
        "opportunity_url": program["url"],
        "type": program["type"],
        "tags": program.get("tags", []),
        "deadline": deadline,
        "description": program.get("notes", ""),
        "amount": program.get("amount", ""),
        "cycle": program.get("cycle", ""),
        "status": program.get("status", "open"),
        "relevance_score": _relevance_score(program),
        "scraped_at": datetime.utcnow().isoformat(),
        "pre_revenue_ok": program.get("pre_revenue_ok", True),
        "open_status": "Open" if program["status"] in ("open", "always_open") else "Unknown",
        "notion_status": "New",
    }


def add_manual_opportunity(
    name: str,
    url: str,
    opp_type: str = "accelerator",
    deadline: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: str = "",
) -> dict:
    """Manually add an opportunity found on Instagram, email, etc."""
    return {
        "title": name,
        "source_name": "Manual Entry",
        "source_url": url,
        "opportunity_url": url,
        "type": opp_type,
        "tags": tags or ["manual"],
        "deadline": deadline,
        "description": notes,
        "amount": "",
        "cycle": "unknown",
        "status": "open",
        "relevance_score": 95,
        "scraped_at": datetime.utcnow().isoformat(),
        "pre_revenue_ok": True,
        "open_status": "Open",
        "notion_status": "New",
    }


def run_scraper(
    open_only: bool = True,
    delay_between_scrapes: float = 1.5,
) -> List[dict]:
    """
    Build the opportunity list from the verified registry.
    Attempts to refresh deadlines from live pages where possible.

    open_only: if True, excludes programs with status 'closed_check_site'
    """
    programs_to_use = PROGRAMS
    if open_only:
        programs_to_use = [
            p for p in PROGRAMS
            if p["status"] != "closed_check_site"
        ]

    opportunities = []
    for program in programs_to_use:
        logger.info(f"Processing: {program['name']} [{program['status']}]")

        refreshed_deadline = None
        if program.get("scrape_url"):
            refreshed_deadline = _try_refresh_deadline(program)
            if refreshed_deadline and refreshed_deadline != program.get("deadline"):
                logger.info(f"  Refreshed deadline: {refreshed_deadline}")
            time.sleep(delay_between_scrapes)

        opp = build_opportunity(program, refreshed_deadline=refreshed_deadline)
        opportunities.append(opp)

    # Sort: open/always_open first, then by deadline (soonest first), then relevance
    def sort_key(o):
        status_rank = STATUS_PRIORITY.get(o["status"], 9)
        deadline_rank = o["deadline"] or "9999-12-31"
        relevance_rank = -o["relevance_score"]
        return (status_rank, deadline_rank, relevance_rank)

    opportunities.sort(key=sort_key)
    logger.info(f"Total opportunities: {len(opportunities)}")
    return opportunities
