"""
Notion API client — creates and updates opportunity pages in a Notion database.

Database schema expected (create this database in Notion first):
  - Name          (title)
  - Type          (select: grant | accelerator | fellowship | competition | investment)
  - Status        (select: New | Researching | Drafting | Submitted | Rejected | Won)
  - Deadline      (date)
  - Source        (url)
  - Opportunity URL (url)
  - Tags          (multi_select)
  - Relevance     (number)
  - Scraped At    (date)

Each page also gets:
  - A "To-Do List" section with standard application tasks
  - Auto-drafted answer blocks in the page body
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)


def get_client() -> Client:
    api_key = os.environ.get("NOTION_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "NOTION_API_KEY environment variable is not set. "
            "Please add it to your .env file."
        )
    return Client(auth=api_key)


def get_database_id() -> str:
    db_id = os.environ.get("NOTION_DATABASE_ID")
    if not db_id:
        raise EnvironmentError(
            "NOTION_DATABASE_ID environment variable is not set. "
            "Please add it to your .env file.\n\n"
            "To find your database ID: open the database in Notion, "
            "copy the URL — the ID is the 32-character string before the '?'."
        )
    return db_id


def _page_exists(client: Client, db_id: str, opportunity_url: str) -> Optional[str]:
    """Return page_id if an entry with this URL already exists, else None."""
    try:
        results = client.databases.query(
            database_id=db_id,
            filter={
                "property": "Opportunity URL",
                "url": {"equals": opportunity_url},
            },
        )
        pages = results.get("results", [])
        return pages[0]["id"] if pages else None
    except APIResponseError as e:
        logger.warning(f"Could not check for existing page: {e}")
        return None


def _build_todo_blocks(incomplete_fields: Optional[List[str]] = None) -> List[dict]:
    """
    Return a to-do checklist as Notion blocks.
    Includes dynamic items for any incomplete founder_context.yaml fields.
    """
    blocks = []

    # ── Context completion to-dos (dynamic) ───────────────────────────────────
    if incomplete_fields:
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {
                    "content": "Complete Your Founder Context (needed for better drafts)"
                }}]
            },
        })
        for field in incomplete_fields:
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {
                        "content": f"Fill in founder_context.yaml: {field}"
                    }}],
                    "checked": False,
                },
            })
        blocks.append({"object": "block", "type": "divider", "divider": {}})

    # ── Standard application to-dos ───────────────────────────────────────────
    blocks.append({
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": "Application Steps"}}]
        },
    })
    standard_todos = [
        "Review eligibility requirements",
        "Read about previous cohort / winners",
        "Customize 'Why This Program' answer with specific reasons",
        "Prepare pitch deck (if required)",
        "Gather references / letters of recommendation",
        "Proofread all application answers",
        "Submit application before deadline",
        "Follow up after submission",
    ]
    for todo in standard_todos:
        blocks.append({
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": todo}}],
                "checked": False,
            },
        })

    return blocks


def _build_draft_blocks(drafts: dict) -> List[dict]:
    """Convert draft answers dict into Notion paragraph blocks."""
    blocks = []

    # Section heading
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": "Auto-Drafted Application Answers"}}]
        },
    })
    blocks.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {
                "content": "These drafts are AI-generated from your founder_context.yaml. "
                           "Review and personalize each answer before submitting."
            }}],
            "icon": {"emoji": "✏️"},
        },
    })

    label_map = {
        "tell_us_about_yourself": "About Me",
        "describe_your_startup": "About the Startup",
        "what_problem_are_you_solving": "The Problem",
        "what_is_your_solution": "Our Solution",
        "describe_your_traction": "Traction",
        "what_is_your_business_model": "Business Model",
        "why_you": "Why Me",
        "why_now": "Why Now",
        "what_makes_you_unique": "Competitive Advantage & DEI",
        "how_will_you_use_funds": "Use of Funds",
        "what_are_your_goals": "Goals (6 & 12 months)",
        "what_mentorship_do_you_need": "Mentorship Needs",
        "market_size": "Market",
        "why_this_program": "Why This Program",
    }

    for key, text in drafts.items():
        label = label_map.get(key, key.replace("_", " ").title())

        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": label}}]
            },
        })

        # Notion API: paragraph text max 2000 chars per block
        chunk_size = 1900
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                },
            })

        blocks.append({"object": "block", "type": "divider", "divider": {}})

    return blocks


def _build_page_properties(opportunity: dict, completion_score: int = 0) -> dict:
    """Map opportunity fields to Notion database properties."""
    props = {
        "Name": {
            "title": [{"text": {"content": opportunity["title"][:200]}}]
        },
        "Type": {
            "select": {"name": opportunity["type"].replace("_aggregator", "").capitalize()}
        },
        "Status": {
            "select": {"name": opportunity.get("status", "New")}
        },
        "Source": {
            "url": opportunity["source_url"]
        },
        "Opportunity URL": {
            "url": opportunity["opportunity_url"]
        },
        "Relevance": {
            "number": opportunity.get("relevance_score", 0)
        },
        "Completion": {
            "number": round(completion_score / 100, 2)  # Notion percent format expects 0.0–1.0
        },
    }

    if opportunity.get("deadline"):
        props["Deadline"] = {"date": {"start": opportunity["deadline"]}}

    tags = opportunity.get("tags", [])
    if tags:
        props["Tags"] = {
            "multi_select": [{"name": tag[:100]} for tag in tags[:10]]
        }

    return props


def ensure_database_schema(client: Client, db_id: str) -> None:
    """
    Add any missing columns to the Notion database.
    Safe to call on every run — skips columns that already exist.
    """
    REQUIRED_PROPERTIES = {
        "Completion": {"number": {"format": "percent"}},
        "Tags": {"multi_select": {"options": []}},
        "Relevance": {"number": {"format": "number"}},
        "Deadline": {"date": {}},
        "Source": {"url": {}},
        "Opportunity URL": {"url": {}},
        "Type": {"select": {"options": [
            {"name": "Grant", "color": "green"},
            {"name": "Accelerator", "color": "blue"},
            {"name": "Fellowship", "color": "purple"},
            {"name": "Competition", "color": "orange"},
            {"name": "Investment", "color": "red"},
        ]}},
        "Status": {"select": {"options": [
            {"name": "New", "color": "gray"},
            {"name": "Researching", "color": "yellow"},
            {"name": "Drafting", "color": "orange"},
            {"name": "Submitted", "color": "blue"},
            {"name": "Rejected", "color": "red"},
            {"name": "Won", "color": "green"},
        ]}},
    }

    try:
        db = client.databases.retrieve(database_id=db_id)
        existing = set(db.get("properties", {}).keys())
        missing = {k: v for k, v in REQUIRED_PROPERTIES.items() if k not in existing}
        if missing:
            client.databases.update(database_id=db_id, properties=missing)
            logger.info(f"Added missing columns to Notion database: {list(missing.keys())}")
    except APIResponseError as e:
        logger.warning(f"Could not update database schema: {e}")


def archive_all_pages(client: Client, db_id: str) -> int:
    """Archive (soft-delete) all pages in the database. Returns count archived."""
    archived = 0
    cursor = None
    while True:
        kwargs = {"database_id": db_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        results = client.databases.query(**kwargs)
        for page in results.get("results", []):
            try:
                client.pages.update(page_id=page["id"], archived=True)
                archived += 1
            except APIResponseError as e:
                logger.warning(f"Could not archive page {page['id']}: {e}")
        if not results.get("has_more"):
            break
        cursor = results.get("next_cursor")
    return archived


def push_opportunity(
    opportunity: dict,
    drafts: Optional[dict] = None,
    completion_score: int = 0,
    incomplete_fields: Optional[List[str]] = None,
    update_existing: bool = False,
) -> Optional[str]:
    """
    Push a single opportunity to Notion.
    Returns the Notion page ID, or None on failure.
    """
    client = get_client()
    db_id = get_database_id()

    existing_id = _page_exists(client, db_id, opportunity["opportunity_url"])
    if existing_id and not update_existing:
        logger.info(f"  Skipping (already in Notion): {opportunity['title']}")
        return existing_id

    properties = _build_page_properties(opportunity, completion_score=completion_score)

    # Completion banner
    if incomplete_fields:
        remaining = len(incomplete_fields)
        banner_text = (
            f"Application {completion_score}% complete — "
            f"{remaining} context field{'s' if remaining != 1 else ''} still needed. "
            f"Fill them in founder_context.yaml to improve your drafts."
        )
    else:
        banner_text = "Application context 100% complete. Review and personalize your drafts before submitting."

    children = [
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": banner_text}}],
                "icon": {"emoji": "📊"},
                "color": "yellow_background" if incomplete_fields else "green_background",
            },
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "To-Do List"}}]
            },
        },
        *_build_todo_blocks(incomplete_fields=incomplete_fields),
        {"object": "block", "type": "divider", "divider": {}},
    ]

    if drafts:
        children.extend(_build_draft_blocks(drafts))

    try:
        if existing_id and update_existing:
            # Update properties only (children are append-only in Notion API)
            client.pages.update(page_id=existing_id, properties=properties)
            logger.info(f"  Updated: {opportunity['title']}")
            return existing_id
        else:
            page = client.pages.create(
                parent={"database_id": db_id},
                properties=properties,
                children=children[:100],  # Notion API limit: 100 blocks per request
            )
            page_id = page["id"]
            logger.info(f"  Created: {opportunity['title']} → {page_id}")

            # Append remaining blocks if over 100
            if len(children) > 100:
                for i in range(100, len(children), 100):
                    client.blocks.children.append(
                        block_id=page_id,
                        children=children[i : i + 100],
                    )

            return page_id

    except APIResponseError as e:
        logger.error(f"  Notion API error for '{opportunity['title']}': {e}")
        return None


def push_all(
    opportunities: List[dict],
    drafts_map: Optional[Dict[str, dict]] = None,
    completion_map: Optional[Dict[str, int]] = None,
    incomplete_map: Optional[Dict[str, List[str]]] = None,
    update_existing: bool = False,
) -> dict:
    """
    Push all opportunities to Notion.
    drafts_map:     { opportunity_url -> drafts_dict }
    completion_map: { opportunity_url -> completion_score }
    incomplete_map: { opportunity_url -> [incomplete_field_labels] }
    Returns { "created": int, "skipped": int, "errors": int }
    """
    stats = {"created": 0, "skipped": 0, "errors": 0}

    client = get_client()
    db_id = get_database_id()
    ensure_database_schema(client, db_id)

    for opp in opportunities:
        url = opp["opportunity_url"]
        drafts = (drafts_map or {}).get(url)
        score = (completion_map or {}).get(url, 0)
        incomplete = (incomplete_map or {}).get(url)
        result = push_opportunity(
            opp,
            drafts=drafts,
            completion_score=score,
            incomplete_fields=incomplete,
            update_existing=update_existing,
        )
        if result:
            stats["created"] += 1
        else:
            stats["errors"] += 1

    return stats
