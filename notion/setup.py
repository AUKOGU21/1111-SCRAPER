"""
One-time Notion database setup helper.
Run this once to create the required database in your Notion workspace.

Usage:
    python -m notion.setup
"""

import logging
import os

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)

DATABASE_TITLE = "ELEVENELEVEN — Grants & Accelerators"

SCHEMA = {
    "Name": {"title": {}},
    "Type": {
        "select": {
            "options": [
                {"name": "Grant", "color": "green"},
                {"name": "Accelerator", "color": "blue"},
                {"name": "Fellowship", "color": "purple"},
                {"name": "Competition", "color": "orange"},
                {"name": "Investment", "color": "red"},
            ]
        }
    },
    "Status": {
        "select": {
            "options": [
                {"name": "New", "color": "gray"},
                {"name": "Researching", "color": "yellow"},
                {"name": "Drafting", "color": "orange"},
                {"name": "Submitted", "color": "blue"},
                {"name": "Rejected", "color": "red"},
                {"name": "Won", "color": "green"},
            ]
        }
    },
    "Deadline": {"date": {}},
    "Source": {"url": {}},
    "Opportunity URL": {"url": {}},
    "Tags": {"multi_select": {"options": []}},
    "Relevance": {"number": {"format": "number"}},
    "Completion": {"number": {"format": "percent"}},
    "Scraped At": {"date": {}},
}


def create_database(parent_page_id: str) -> str:
    """
    Create the grants tracker database under the given Notion page.
    Returns the new database ID.
    """
    api_key = os.environ.get("NOTION_API_KEY")
    if not api_key:
        raise EnvironmentError("NOTION_API_KEY not set.")

    client = Client(auth=api_key)

    try:
        db = client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": DATABASE_TITLE}}],
            properties=SCHEMA,
        )
        db_id = db["id"]
        print(f"\n✅ Database created successfully!")
        print(f"   Title: {DATABASE_TITLE}")
        print(f"   Database ID: {db_id}")
        print(f"\nAdd this to your .env file:")
        print(f"   NOTION_DATABASE_ID={db_id}\n")
        return db_id
    except APIResponseError as e:
        print(f"\n❌ Failed to create database: {e}")
        raise


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python -m notion.setup <parent_page_id>")
        print()
        print("To find your parent page ID:")
        print("  1. Open the Notion page where you want the database")
        print("  2. Click '...' menu → 'Copy link'")
        print("  3. The ID is the last 32-character hex string in the URL")
        sys.exit(1)

    parent_page_id = sys.argv[1].strip()
    create_database(parent_page_id)
