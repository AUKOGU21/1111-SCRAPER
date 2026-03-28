"""
Auto-draft application answers from founder_context.yaml.
Supports two modes:
  1. OpenAI GPT-4 (if OPENAI_API_KEY is set) — richer, more tailored prose
  2. Rule-based template engine — works with zero API cost
"""

import logging
import os
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

CONTEXT_FILE = Path(__file__).parent.parent / "founder_context.yaml"


def load_context() -> dict:
    """Load founder_context.yaml and return as dict."""
    if not CONTEXT_FILE.exists():
        raise FileNotFoundError(f"founder_context.yaml not found at {CONTEXT_FILE}")
    with open(CONTEXT_FILE, "r") as f:
        return yaml.safe_load(f)


# ── Template-based drafts (no API needed) ─────────────────────────────────────

QUESTION_TEMPLATES = {
    "tell_us_about_yourself": (
        "My name is {founder[name]}, a {founder[program]} student at {founder[school]}. "
        "{founder[background]}"
    ),
    "describe_your_startup": (
        "{startup[name]} — {startup[tagline]}.\n\n"
        "{startup[description]}\n\n"
        "We are currently {startup[stage]} in the {startup[sector]} space."
    ),
    "what_problem_are_you_solving": (
        "{startup[problem]}"
    ),
    "what_is_your_solution": (
        "{startup[solution]}"
    ),
    "describe_your_traction": (
        "{startup[traction]}"
    ),
    "what_is_your_business_model": (
        "{startup[business_model]}"
    ),
    "why_you": (
        "{founder_story}"
    ),
    "why_now": (
        "{why_now}"
    ),
    "what_makes_you_unique": (
        "{startup[competitive_advantage]}\n\n{dei_statement}"
    ),
    "how_will_you_use_funds": (
        "{use_of_funds}"
    ),
    "what_are_your_goals": (
        "In the next 6 months: {goals_6_months}\n\nIn 12 months: {goals_12_months}"
    ),
    "what_mentorship_do_you_need": (
        "{mentorship_needs}"
    ),
    "market_size": (
        "Target customer: {startup[market][target_customer]}\n\n"
        "Market size: {startup[market][size]}"
    ),
}


def _render(template: str, ctx: dict) -> str:
    """Simple recursive format that handles nested dict keys like {startup[name]}."""
    import re

    def replacer(match):
        key_path = match.group(1)
        parts = re.split(r"\[|\]", key_path)
        parts = [p for p in parts if p]
        val = ctx
        try:
            for part in parts:
                val = val[part]
            return str(val).strip()
        except (KeyError, TypeError):
            return match.group(0)  # leave as-is if key missing

    pattern = r"\{([a-zA-Z_]+(?:\[[a-zA-Z_]+\])*)\}"
    result = re.sub(pattern, replacer, template)
    return result


def draft_with_templates(opportunity: dict, ctx: dict) -> dict:
    """
    Generate template-based draft answers for the most common application questions.
    Returns a dict of question_key -> draft_text.
    """
    drafts = {}
    for question_key, template in QUESTION_TEMPLATES.items():
        try:
            drafts[question_key] = _render(template, ctx)
        except Exception as e:
            logger.warning(f"Template render failed for {question_key}: {e}")
            drafts[question_key] = "[Draft unavailable — please fill in manually]"

    # Add a tailored "why this program" draft
    drafts["why_this_program"] = (
        f"{opportunity['source_name']} stood out to me because its focus on "
        f"{', '.join(opportunity.get('tags', [])[:3])} aligns directly with where "
        f"{ctx['startup']['name']} is today. "
        f"As a {ctx['founder']['program']} student at {ctx['founder']['school']}, "
        f"I am looking for the specific combination of capital, mentorship, and network "
        f"that {opportunity['source_name']} is known for. "
        f"[Customize with 2–3 specific reasons why THIS program, not just any program.]"
    )

    return drafts


def draft_with_openai(opportunity: dict, ctx: dict) -> dict:
    """
    Use OpenAI GPT-4 to generate polished, tailored application drafts.
    Falls back to templates if OpenAI is unavailable.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except (ImportError, KeyError):
        logger.info("OpenAI not configured — using template-based drafts.")
        return draft_with_templates(opportunity, ctx)

    system_prompt = (
        "You are a grant writing expert helping a pre-revenue Black female founder "
        "at Harvard Business School craft compelling, authentic application answers. "
        "Be specific, honest, and avoid corporate jargon. Write in first person. "
        "Highlight lived experience and competitive advantage without being performative."
    )

    context_summary = (
        f"Founder: {ctx['founder']['name']}, {ctx['founder']['program']} at "
        f"{ctx['founder']['school']}.\n"
        f"Startup: {ctx['startup']['name']} — {ctx['startup']['tagline']}.\n"
        f"Description: {ctx['startup']['description']}\n"
        f"Stage: {ctx['startup']['stage']}, Sector: {ctx['startup']['sector']}\n"
        f"Traction: {ctx['startup']['traction']}\n"
        f"Why now: {ctx['why_now']}\n"
        f"Founder story: {ctx['founder_story']}\n"
        f"DEI: {ctx['dei_statement']}\n"
        f"Use of funds: {ctx['use_of_funds']}"
    )

    questions = [
        ("tell_us_about_yourself", "Tell us about yourself."),
        ("describe_your_startup", "Describe your startup in 2–3 sentences."),
        ("what_problem_are_you_solving", "What problem are you solving?"),
        ("why_you", "Why are you the right person to build this?"),
        ("why_now", "Why is now the right time?"),
        ("how_will_you_use_funds", "How will you use the grant/investment?"),
        ("why_this_program", f"Why are you applying to {opportunity['source_name']}?"),
    ]

    drafts = {}
    for key, question in questions:
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Context about the founder and startup:\n{context_summary}\n\n"
                            f"Application question: {question}\n\n"
                            f"Write a 150–250 word answer."
                        ),
                    },
                ],
                max_tokens=400,
                temperature=0.7,
            )
            drafts[key] = response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI failed for question '{key}': {e}")
            drafts[key] = draft_with_templates(opportunity, ctx).get(key, "")

    # Fill remaining template-based questions
    template_drafts = draft_with_templates(opportunity, ctx)
    for key in QUESTION_TEMPLATES:
        if key not in drafts:
            drafts[key] = template_drafts[key]

    return drafts


def generate_drafts(opportunity: dict) -> dict:
    """
    Main entry point. Generates drafts for a given opportunity.
    Uses OpenAI if available, otherwise falls back to templates.
    """
    ctx = load_context()
    use_openai = bool(os.environ.get("OPENAI_API_KEY"))

    if use_openai:
        logger.info(f"Generating OpenAI drafts for: {opportunity['title']}")
        return draft_with_openai(opportunity, ctx)
    else:
        logger.info(f"Generating template drafts for: {opportunity['title']}")
        return draft_with_templates(opportunity, ctx)


def format_drafts_for_notion(drafts: dict) -> str:
    """
    Format draft answers as a single Notion-friendly markdown block.
    """
    labels = {
        "tell_us_about_yourself": "About Me",
        "describe_your_startup": "About the Startup",
        "what_problem_are_you_solving": "The Problem",
        "what_is_your_solution": "Our Solution",
        "describe_your_traction": "Traction",
        "what_is_your_business_model": "Business Model",
        "why_you": "Why Me",
        "why_now": "Why Now",
        "what_makes_you_unique": "Competitive Advantage / DEI",
        "how_will_you_use_funds": "Use of Funds",
        "what_are_your_goals": "Goals",
        "what_mentorship_do_you_need": "Mentorship Needs",
        "market_size": "Market",
        "why_this_program": "Why This Program",
    }

    lines = []
    for key, text in drafts.items():
        label = labels.get(key, key.replace("_", " ").title())
        lines.append(f"**{label}**\n{text}\n")

    return "\n---\n".join(lines)
