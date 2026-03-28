"""
Grant and accelerator sources tailored for:
- Pre-revenue solo Black female founder
- Consumer / retail tech
- HBS student
"""

SOURCES = [
    # ── Black / Women founder-focused ─────────────────────────────────────────
    {
        "name": "digitalundivided ProjectDiane",
        "url": "https://www.digitalundivided.com/programs",
        "type": "grant",
        "tags": ["Black founder", "women founder", "tech"],
        "scrape_method": "static",
    },
    {
        "name": "Fearless Fund",
        "url": "https://fearlessfund.com/grants/",
        "type": "grant",
        "tags": ["Black women founder", "consumer", "retail"],
        "scrape_method": "static",
    },
    {
        "name": "Hello Alice Business Grants",
        "url": "https://helloalice.com/grants/",
        "type": "grant",
        "tags": ["women founder", "diverse founder", "small business"],
        "scrape_method": "static",
    },
    {
        "name": "Tory Burch Foundation Fellows",
        "url": "https://www.toryburchfoundation.org/resources/fellows-program/",
        "type": "accelerator",
        "tags": ["women founder", "consumer", "retail", "fellowship"],
        "scrape_method": "static",
    },
    {
        "name": "NMSDC / Minority Business Programs",
        "url": "https://nmsdc.org/programs/",
        "type": "grant",
        "tags": ["minority founder", "business development"],
        "scrape_method": "static",
    },
    {
        "name": "SBA Office of Women's Business Ownership",
        "url": "https://www.sba.gov/business-guide/grow-your-business/women-owned-businesses",
        "type": "grant",
        "tags": ["women founder", "SBA", "government"],
        "scrape_method": "static",
    },
    {
        "name": "Backstage Capital",
        "url": "https://backstagecapital.com/",
        "type": "investment",
        "tags": ["underrepresented founder", "Black founder", "women founder"],
        "scrape_method": "static",
    },

    # ── HBS / University-affiliated ───────────────────────────────────────────
    {
        "name": "HBS Rock Center for Entrepreneurship",
        "url": "https://www.hbs.edu/entrepreneurship/programs/Pages/default.aspx",
        "type": "accelerator",
        "tags": ["HBS", "university", "student founder"],
        "scrape_method": "static",
    },
    {
        "name": "HBS New Venture Competition",
        "url": "https://www.hbs.edu/newventurecompetition",
        "type": "competition",
        "tags": ["HBS", "competition", "prize"],
        "scrape_method": "static",
    },
    {
        "name": "Harvard i-lab",
        "url": "https://ilab.harvard.edu/programs",
        "type": "accelerator",
        "tags": ["Harvard", "student founder", "incubator"],
        "scrape_method": "static",
    },

    # ── Top accelerators (consumer/retail friendly) ───────────────────────────
    {
        "name": "Y Combinator",
        "url": "https://www.ycombinator.com/apply",
        "type": "accelerator",
        "tags": ["top-tier", "consumer", "tech"],
        "scrape_method": "static",
    },
    {
        "name": "Techstars",
        "url": "https://www.techstars.com/accelerators",
        "type": "accelerator",
        "tags": ["consumer", "retail tech", "top-tier"],
        "scrape_method": "static",
    },
    {
        "name": "500 Global",
        "url": "https://500.co/accelerators",
        "type": "accelerator",
        "tags": ["diverse founder", "consumer", "global"],
        "scrape_method": "static",
    },
    {
        "name": "MassChallenge",
        "url": "https://masschallenge.org/programs-apply/",
        "type": "accelerator",
        "tags": ["Boston", "HBS adjacent", "no equity"],
        "scrape_method": "static",
    },
    {
        "name": "Founders Factory",
        "url": "https://foundersfactory.com/apply/",
        "type": "accelerator",
        "tags": ["consumer", "retail", "UK/global"],
        "scrape_method": "static",
    },

    # ── Consumer / Retail tech specific ───────────────────────────────────────
    {
        "name": "Retail Technology Innovation Hub (RTECH)",
        "url": "https://retailtechinnovationhub.com/",
        "type": "accelerator",
        "tags": ["retail tech", "consumer tech"],
        "scrape_method": "static",
    },
    {
        "name": "LVMH La Maison des Startups",
        "url": "https://lamaisondesstartups.lvmh.com/",
        "type": "accelerator",
        "tags": ["consumer", "retail", "luxury", "fashion"],
        "scrape_method": "static",
    },
    {
        "name": "Comcast NBCUniversal LIFT Labs",
        "url": "https://liftlabs.comcast.com/",
        "type": "accelerator",
        "tags": ["consumer tech", "diverse founder"],
        "scrape_method": "static",
    },

    # ── Aggregator pages to scrape for new listings ───────────────────────────
    {
        "name": "GrantWatch (tech / women)",
        "url": "https://www.grantwatch.com/cat/56/women-grants.html",
        "type": "grant_aggregator",
        "tags": ["women", "aggregator"],
        "scrape_method": "static",
    },
    {
        "name": "Instrumentl (consumer / retail)",
        "url": "https://www.instrumentl.com/browse-grants",
        "type": "grant_aggregator",
        "tags": ["aggregator", "consumer", "retail"],
        "scrape_method": "static",
    },
    {
        "name": "F6S Accelerator Programs",
        "url": "https://www.f6s.com/programs",
        "type": "accelerator_aggregator",
        "tags": ["aggregator", "accelerator"],
        "scrape_method": "static",
    },
    {
        "name": "Crunchbase Funding Opportunities",
        "url": "https://about.crunchbase.com/resources/grants-for-black-founders/",
        "type": "grant_aggregator",
        "tags": ["Black founder", "aggregator"],
        "scrape_method": "static",
    },
]
