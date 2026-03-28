# ELEVENELEVEN — Grants & Accelerator Scraper

Automated pipeline for a pre-revenue Black female founder in consumer/retail tech at HBS.

**What it does:**
1. Scrapes 20+ grant, accelerator, and fellowship sources daily
2. Auto-drafts application answers from your `founder_context.yaml`
3. Pushes every opportunity into Notion with a to-do checklist and draft answers

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium       # only needed for JS-heavy sites
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
NOTION_API_KEY=secret_xxxx       # ← Required
NOTION_DATABASE_ID=xxxx          # ← Required (see below)
OPENAI_API_KEY=sk-xxxx           # ← Optional (enables richer drafts)
```

**Getting your Notion API key:**
1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **New integration** → name it `ELEVENELEVEN Scraper`
3. Copy the **Internal Integration Secret** → this is your `NOTION_API_KEY`
4. In Notion, open the page/database you want to use → click `...` → **Add connections** → select your integration

**Setting up the Notion database:**
- Either create a database manually with the columns listed below, OR
- Run the setup script: `python -m notion.setup <your-notion-page-id>`
  - Your page ID is the 32-char hex string at the end of any Notion page URL

**Required Notion database columns:**

| Column | Type |
|---|---|
| Name | Title |
| Type | Select |
| Status | Select |
| Deadline | Date |
| Source | URL |
| Opportunity URL | URL |
| Tags | Multi-select |
| Relevance | Number |
| Scraped At | Date |

### 3. Fill in your founder context

Edit `founder_context.yaml` with your real details. The more specific you are, the better the auto-drafted answers will be.

### 4. Run

```bash
# One-time run (scrape → draft → push to Notion)
python main.py

# Dry run (scrape only, no Notion push — good for testing)
python main.py --dry-run

# Push only top 15 most relevant opportunities
python main.py --top 15

# Run on a daily schedule
python main.py --schedule
```

---

## Project Structure

```
1111-SCRAPER/
├── main.py                  # Entry point
├── founder_context.yaml     # YOUR info — fill this in
├── requirements.txt
├── .env.example
│
├── scraper/
│   ├── sources.py           # List of all sources to scrape
│   └── scraper.py           # Scraping logic + relevance scoring
│
├── drafts/
│   └── generator.py         # Template + OpenAI draft generation
│
├── notion/
│   ├── client.py            # Notion API push logic
│   └── setup.py             # One-time database creation helper
│
└── logs/                    # Daily log files
```

---

## Adding More Sources

Edit `scraper/sources.py` and add an entry:

```python
{
    "name": "Program Name",
    "url": "https://...",
    "type": "grant",           # grant | accelerator | fellowship | competition | investment
    "tags": ["Black founder", "consumer"],
    "scrape_method": "static",
}
```

---

## Relevance Scoring

Opportunities are scored 0–100 based on keyword matches:
- +10 per match: women, female, Black, minority, diverse, consumer, retail, tech, startup, etc.
- +15 bonus: "Black woman", "Black female", "Black founder", "HBCU"

Sort by **Relevance** in Notion to see the best matches first.
