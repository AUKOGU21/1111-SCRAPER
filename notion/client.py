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


def _build_todo_blocks() -> List[dict]:
    """Return a standard to-do checklist as Notion blocks."""
    todos = [
        "Review eligibility requirements",
        "Read previous cohort / winners for research",
        "Customize 'Why This Program' answer",
        "Prepare pitch deck (if required)",
        "Gather references / letters of recommendation",
        "Proofread all application answers",
        "Submit application",
        "Follow up after submission",
    ]
    return [
        {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": todo}}],
                "checked": False,
            },
        }
        for todo in todos
    ]


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


def _build_page_properties(opportunity: dict) -> dict:
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
    }

    # Deadline (optional)
    if opportunity.get("deadline"):
        props["Deadline"] = {"date": {"start": opportunity["deadline"]}}

    # Tags (multi_select — must be plain strings)
    tags = opportunity.get("tags", [])
    if tags:
        props["Tags"] = {
            "multi_select": [{"name": tag[:100]} for tag in tags[:10]]
        }

    return props


def push_opportunity(
    opportunity: dict,
    drafts: Optional[dict] = None,
    update_existing: bool = False,
) -> Optional[str]:
    """
    Push a single opportunity to Notion.
    Returns the Notion page ID, or None on failure.
    """
    client = get_client()
    db_id = get_database_id()

    # Check for duplicates
    existing_id = _page_exists(client, db_id, opportunity["opportunity_url"])
    if existing_id and not update_existing:
        logger.info(f"  Skipping (already in Notion): {opportunity['title']}")
        return existing_id

    properties = _build_page_properties(opportunity)

    # Build page body
    children = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Application To-Do List"}}]
            },
        },
        *_build_todo_blocks(),
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
    update_existing: bool = False,
) -> dict:
    """
    Push all opportunities to Notion.
    drafts_map: { opportunity_url -> drafts_dict }
    Returns { "created": int, "skipped": int, "errors": int }
    """
    stats = {"created": 0, "skipped": 0, "errors": 0}

    for opp in opportunities:
        drafts = (drafts_map or {}).get(opp["opportunity_url"])
        result = push_opportunity(opp, drafts=drafts, update_existing=update_existing)
        if result:
            stats["created"] += 1
        else:
            # Distinguish skip vs error by checking if it already existed
            stats["errors"] += 1

    return stats
