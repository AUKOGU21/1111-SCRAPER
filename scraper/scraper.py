"""
Core scraper — fetches each source, extracts opportunity metadata,
and returns structured dicts ready for Notion and draft generation.
"""

import logging
import re
import time
from datetime import datetime, timedelta
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
    "student", "early-stage", "pre-seed", "seed",
]

EXCLUDE_KEYWORDS = [
    "closed", "expired", "archived", "past", "no longer accepting",
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
    # Patterns: "March 31, 2025", "31 March 2025", "03/31/2025", "2025-03-31"
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
            for fmt in [
                "%B %d, %Y", "%B %d %Y",
                "%d %B %Y",
                "%m/%d/%Y",
                "%Y-%m-%d",
            ]:
                try:
                    dt = datetime.strptime(raw.replace(",", ""), fmt.replace(",", ""))
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return None


def _relevance_score(text: str) -> int:
    """Return a 0–100 relevance score based on keyword matches."""
    text_lower = text.lower()
    score = 0
    for kw in RELEVANCE_KEYWORDS:
        if kw in text_lower:
            score += 10
    # Bonus for explicit diversity language
    for bonus_kw in ["black woman", "black female", "black founder", "hbcu"]:
        if bonus_kw in text_lower:
            score += 15
    return min(score, 100)


def _is_excluded(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in EXCLUDE_KEYWORDS)


def _parse_opportunity_block(element, source: dict, base_url: str) -> Optional[dict]:
    """
    Given a BeautifulSoup element that likely represents one opportunity,
    extract a structured dict.
    """
    text = element.get_text(separator=" ", strip=True)
    if not text or len(text) < 30:
        return None
    if _is_excluded(text):
        return None

    # Find a link
    link_tag = element.find("a", href=True)
    link = None
    if link_tag:
        href = link_tag["href"]
        link = href if href.startswith("http") else urljoin(base_url, href)

    # Find a heading/title
    heading = element.find(re.compile(r"^h[1-6]$"))
    title = heading.get_text(strip=True) if heading else (
        link_tag.get_text(strip=True) if link_tag else text[:80]
    )

    deadline = _extract_deadline(text)
    score = _relevance_score(text)

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
    }


def scrape_source(source: dict) -> List[dict]:
    """Scrape a single source and return a list of opportunity dicts."""
    logger.info(f"Scraping: {source['name']} ({source['url']})")
    html = _fetch_html(source["url"])
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")

    # Remove nav, footer, scripts
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    opportunities = []
    base_url = f"{urlparse(source['url']).scheme}://{urlparse(source['url']).netloc}"

    # Strategy 1: look for article / card / list-item blocks with relevant keywords
    candidate_selectors = [
        "article", ".card", ".program", ".grant", ".opportunity",
        ".listing", "li", ".item", ".post",
    ]
    found_blocks = []
    for selector in candidate_selectors:
        blocks = soup.select(selector)
        if blocks:
            found_blocks = blocks
            break

    # Fallback: split on headings
    if not found_blocks:
        found_blocks = soup.find_all(re.compile(r"^h[2-4]$"))

    seen_titles = set()
    for block in found_blocks[:50]:  # cap per-source
        opp = _parse_opportunity_block(block, source, base_url)
        if opp and opp["title"] not in seen_titles:
            # Apply include-keyword filter: at least one keyword must appear
            combined = (opp["title"] + " " + opp["description"]).lower()
            if any(kw in combined for kw in INCLUDE_KEYWORDS):
                seen_titles.add(opp["title"])
                opportunities.append(opp)

    # If nothing found via blocks, create a single entry for the source itself
    if not opportunities:
        page_title = soup.title.string.strip() if soup.title else source["name"]
        opportunities.append({
            "title": page_title[:200],
            "source_name": source["name"],
            "source_url": source["url"],
            "opportunity_url": source["url"],
            "type": source["type"],
            "tags": source["tags"],
            "deadline": None,
            "description": soup.get_text(separator=" ", strip=True)[:1000],
            "relevance_score": _relevance_score(soup.get_text()),
            "scraped_at": datetime.utcnow().isoformat(),
            "status": "New",
        })

    logger.info(f"  → {len(opportunities)} opportunities found")
    return opportunities


def run_scraper(delay_between_sources: float = 2.0) -> List[dict]:
    """
    Scrape all sources and return a deduplicated list of opportunities,
    sorted by relevance score descending.
    """
    all_opportunities = []
    for source in SOURCES:
        try:
            results = scrape_source(source)
            all_opportunities.extend(results)
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")
        time.sleep(delay_between_sources)

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
