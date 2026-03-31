"""
Core scraper — fetches each source, extracts opportunity metadata,
and returns structured dicts ready for Notion and draft generation.
"""

import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from scraper.sources import SOURCES

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Keyword filters ────────────────────────────────────────────────────────────

INCLUDE_KEYWORDS = [
    "grant", "accelerator", "fellowship", "award", "prize",
    "fund", "cohort", "program", "competition", "apply",
    "deadline", "open", "applications",
]

RELEVANCE_KEYWORDS = [
    "women", "female", "black", "minority", "diverse", "underrepresented",
    "consumer", "retail", "tech", "startup", "entrepreneur", "founder",
    "student", "early-stage", "pre-seed", "seed", "pre-revenue",
]

# Signals that a program is CLOSED — used to flag entries, not hard-remove
CLOSED_SIGNALS = [
    "applications are closed", "applications closed", "closed for applications",
    "no longer accepting", "deadline has passed", "this cycle is closed",
    "not currently accepting", "check back", "coming soon",
    "applications open in", "waitlist",
]

# Signals that a program is OPEN — boosts confidence
OPEN_SIGNALS = [
    "apply now", "applications open", "now accepting", "apply today",
    "rolling admissions", "open applications", "currently accepting",
    "submit your application", "deadline:", "applications due",
]

# Disqualifiers for pre-revenue founders
REVENUE_REQUIRED_SIGNALS = [
    "minimum revenue", "must have revenue", "$1m arr", "$500k arr",
    "series a", "series b", "post-revenue only", "revenue requirement",
    "at least 6 months of revenue", "proven revenue",
]


def _fetch_html(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch raw HTML from a URL, returning None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def _extract_deadline(text: str) -> Optional[str]:
    """
    Attempt to parse a deadline date from freeform text.
    Returns ISO 8601 date string or None.
    """
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
                    # Ignore dates clearly in the past by more than 30 days
                    if (datetime.now() - dt).days > 30:
                        continue
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return None


def _detect_open_status(text: str) -> str:
    """
    Return 'Open', 'Closed', or 'Unknown' based on page text signals.
    """
    text_lower = text.lower()
    closed_hits = sum(1 for s in CLOSED_SIGNALS if s in text_lower)
    open_hits = sum(1 for s in OPEN_SIGNALS if s in text_lower)

    if closed_hits > open_hits:
        return "Closed"
    elif open_hits > 0:
        return "Open"
    return "Unknown"


def _requires_revenue(text: str) -> bool:
    """Return True if the page text suggests revenue is required."""
    text_lower = text.lower()
    return any(sig in text_lower for sig in REVENUE_REQUIRED_SIGNALS)


def _relevance_score(text: str, source: dict) -> int:
    """Return a 0–100 relevance score based on keyword matches and source tags."""
    text_lower = text.lower()
    score = 0

    for kw in RELEVANCE_KEYWORDS:
        if kw in text_lower:
            score += 8

    # Bonus for explicit identity/profile language
    for bonus_kw in ["black woman", "black female", "black founder", "hbcu",
                     "pre-revenue", "idea stage", "early stage"]:
        if bonus_kw in text_lower:
            score += 15

    # Source tag bonus — if the source is tagged as highly relevant, reward it
    high_value_tags = {"Black women founder", "Black founder", "pre-revenue ok",
                       "HBS", "consumer", "retail"}
    tag_matches = len(high_value_tags & set(source.get("tags", [])))
    score += tag_matches * 8

    return min(score, 100)


def _parse_opportunity_block(element, source: dict, base_url: str) -> Optional[dict]:
    """Extract a structured opportunity dict from a BeautifulSoup element."""
    text = element.get_text(separator=" ", strip=True)
    if not text or len(text) < 30:
        return None

    # Find a link
    link_tag = element.find("a", href=True)
    link = None
    if link_tag:
        href = link_tag["href"]
        link = href if href.startswith("http") else urljoin(base_url, href)

    # Find title
    heading = element.find(re.compile(r"^h[1-6]$"))
    title = heading.get_text(strip=True) if heading else (
        link_tag.get_text(strip=True) if link_tag else text[:80]
    )

    deadline = _extract_deadline(text)
    score = _relevance_score(text, source)

    return {
        "title": title[:200],
        "source_name": source["name"],
        "source_url": source["url"],
        "opportunity_url": link or source["url"],
        "type": source["type"],
        "tags": source["tags"],
        "deadline": deadline,
        "description": text[:1000],
        "relevance_score": score,
        "scraped_at": datetime.utcnow().isoformat(),
        "status": "New",
        "pre_revenue_ok": source.get("pre_revenue_ok", False),
        "open_status": "Unknown",
    }


def scrape_source(source: dict) -> List[dict]:
    """Scrape a single source and return a list of opportunity dicts."""
    logger.info(f"Scraping: {source['name']} ({source['url']})")
    html = _fetch_html(source["url"])
    if not html:
        # Return the source as a stub so it still appears in Notion for manual review
        return [{
            "title": source["name"],
            "source_name": source["name"],
            "source_url": source["url"],
            "opportunity_url": source["url"],
            "type": source["type"],
            "tags": source["tags"],
            "deadline": None,
            "description": source.get("focus", ""),
            "relevance_score": _relevance_score(source.get("focus", ""), source),
            "scraped_at": datetime.utcnow().isoformat(),
            "status": "New",
            "pre_revenue_ok": source.get("pre_revenue_ok", False),
            "open_status": "Unknown",
        }]

    soup = BeautifulSoup(html, "lxml")
    full_text = soup.get_text(separator=" ", strip=True)

    # Page-level open/closed and revenue detection
    page_open_status = _detect_open_status(full_text)
    page_requires_revenue = _requires_revenue(full_text)

    # If page is clearly closed, log and skip
    if page_open_status == "Closed":
        logger.info(f"  → CLOSED (skipping): {source['name']}")
        return []

    # If page clearly requires revenue and source isn't flagged pre-revenue-ok, skip
    if page_requires_revenue and not source.get("pre_revenue_ok", False):
        logger.info(f"  → Revenue required (skipping): {source['name']}")
        return []

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    base_url = f"{urlparse(source['url']).scheme}://{urlparse(source['url']).netloc}"

    # Find content blocks
    candidate_selectors = [
        "article", ".card", ".program", ".grant", ".opportunity",
        ".listing", "li", ".item", ".post", "section",
    ]
    found_blocks = []
    for selector in candidate_selectors:
        blocks = soup.select(selector)
        if len(blocks) >= 2:  # need at least 2 to be a real list
            found_blocks = blocks
            break

    if not found_blocks:
        found_blocks = soup.find_all(re.compile(r"^h[2-4]$"))

    opportunities = []
    seen_titles = set()

    for block in found_blocks[:60]:
        opp = _parse_opportunity_block(block, source, base_url)
        if not opp or opp["title"] in seen_titles:
            continue

        combined = (opp["title"] + " " + opp["description"]).lower()

        # Must match at least one include keyword
        if not any(kw in combined for kw in INCLUDE_KEYWORDS):
            continue

        opp["open_status"] = page_open_status
        seen_titles.add(opp["title"])
        opportunities.append(opp)

    # Fallback: one entry for the whole source page
    if not opportunities:
        page_title = soup.title.string.strip() if soup.title else source["name"]
        opportunities.append({
            "title": page_title[:200],
            "source_name": source["name"],
            "source_url": source["url"],
            "opportunity_url": source["url"],
            "type": source["type"],
            "tags": source["tags"],
            "deadline": _extract_deadline(full_text),
            "description": source.get("focus", full_text[:500]),
            "relevance_score": _relevance_score(full_text, source),
            "scraped_at": datetime.utcnow().isoformat(),
            "status": "New",
            "pre_revenue_ok": source.get("pre_revenue_ok", False),
            "open_status": page_open_status,
        })

    logger.info(f"  → {len(opportunities)} opportunities found (status: {page_open_status})")
    return opportunities


def add_manual_opportunity(
    name: str,
    url: str,
    opp_type: str = "accelerator",
    deadline: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: str = "",
) -> dict:
    """
    Manually add an opportunity you found (e.g. on Instagram).
    Call this directly or via: python -c "from scraper.scraper import add_manual_opportunity; ..."
    """
    return {
        "title": name,
        "source_name": "Manual Entry",
        "source_url": url,
        "opportunity_url": url,
        "type": opp_type,
        "tags": tags or ["manual"],
        "deadline": deadline,
        "description": notes,
        "relevance_score": 90,  # manual entries get high priority
        "scraped_at": datetime.utcnow().isoformat(),
        "status": "New",
        "pre_revenue_ok": True,
        "open_status": "Open",
    }


def run_scraper(
    delay_between_sources: float = 2.0,
    pre_revenue_only: bool = True,
    skip_closed: bool = True,
) -> List[dict]:
    """
    Scrape all sources and return a deduplicated list of opportunities,
    sorted by relevance score descending.

    pre_revenue_only: skip sources not tagged pre_revenue_ok
    skip_closed:      skip entries where open_status == 'Closed'
    """
    sources_to_use = SOURCES
    if pre_revenue_only:
        sources_to_use = [s for s in SOURCES if s.get("pre_revenue_ok", False)]
        logger.info(f"Pre-revenue filter ON: {len(sources_to_use)}/{len(SOURCES)} sources")

    all_opportunities = []
    for source in sources_to_use:
        try:
            results = scrape_source(source)
            all_opportunities.extend(results)
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")
        time.sleep(delay_between_sources)

    # Filter closed
    if skip_closed:
        before = len(all_opportunities)
        all_opportunities = [
            o for o in all_opportunities if o.get("open_status") != "Closed"
        ]
        logger.info(f"Closed filter removed {before - len(all_opportunities)} entries")

    # Deduplicate by opportunity_url
    seen_urls = set()
    deduped = []
    for opp in all_opportunities:
        url = opp["opportunity_url"]
        if url not in seen_urls:
            seen_urls.add(url)
            deduped.append(opp)

    deduped.sort(key=lambda x: x["relevance_score"], reverse=True)
    logger.info(f"Total unique opportunities: {len(deduped)}")
    return deduped
