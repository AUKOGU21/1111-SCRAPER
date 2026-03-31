"""
Grant and accelerator sources for ELEVENELEVEN.

Profile: Pre-revenue, solo, Black female founder, consumer/retail tech, HBS.

Each source has:
  pre_revenue_ok  — True if program explicitly accepts pre-revenue / idea-stage
  requires_revenue — True if program requires revenue/traction (will be skipped)
  focus           — brief note on why this source is relevant
"""

SOURCES = [

    # ══════════════════════════════════════════════════════════════════════════
    # BLACK WOMEN FOUNDERS — most relevant, highest relevance score
    # ══════════════════════════════════════════════════════════════════════════

    {
        "name": "Black Girl Ventures",
        "url": "https://www.blackgirlventures.org/programs",
        "type": "grant",
        "tags": ["Black women founder", "consumer", "pitch competition", "grant"],
        "pre_revenue_ok": True,
        "focus": "Pitch competitions and grants specifically for Black & Brown women founders",
    },
    {
        "name": "digitalundivided (DID) Accelerator",
        "url": "https://www.digitalundivided.com/programs",
        "type": "accelerator",
        "tags": ["Black founder", "women founder", "tech", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "DID's programs explicitly serve pre-revenue Black women in tech",
    },
    {
        "name": "New Voices Foundation",
        "url": "https://www.newvoicesfoundation.org/programs",
        "type": "grant",
        "tags": ["Black women founder", "consumer", "retail", "CPG"],
        "pre_revenue_ok": True,
        "focus": "Grants for Black women in consumer/CPG/retail space",
    },
    {
        "name": "Camelback Ventures",
        "url": "https://www.camelbackventures.org/fellowship",
        "type": "fellowship",
        "tags": ["Black founder", "women founder", "fellowship", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "Fellowship for underrepresented founders, pre-revenue friendly",
    },
    {
        "name": "The Doonie Fund",
        "url": "https://www.thedooniefund.org",
        "type": "grant",
        "tags": ["Black women founder", "grant", "no-equity"],
        "pre_revenue_ok": True,
        "focus": "Grants specifically for Black women entrepreneurs",
    },
    {
        "name": "IFundWomen",
        "url": "https://ifundwomen.com/grants",
        "type": "grant",
        "tags": ["women founder", "grant", "consumer", "no-equity"],
        "pre_revenue_ok": True,
        "focus": "Rolling grants for women founders, actively lists open opportunities",
    },
    {
        "name": "Hello Alice Grants",
        "url": "https://helloalice.com/grants/",
        "type": "grant",
        "tags": ["women founder", "diverse founder", "small business"],
        "pre_revenue_ok": True,
        "focus": "Aggregates many open grants for diverse founders",
    },
    {
        "name": "Amber Grant Foundation",
        "url": "https://ambergrant.com",
        "type": "grant",
        "tags": ["women founder", "monthly grant", "no-equity"],
        "pre_revenue_ok": True,
        "focus": "$10K monthly grant for women founders, no revenue requirement",
    },
    {
        "name": "SoGal Foundation Black Founder Startup Grant",
        "url": "https://sogalfoundation.com",
        "type": "grant",
        "tags": ["Black founder", "women founder", "grant"],
        "pre_revenue_ok": True,
        "focus": "Grant for Black women founders",
    },
    {
        "name": "Tory Burch Foundation Fellows",
        "url": "https://www.toryburchfoundation.org/resources/fellows-program/",
        "type": "fellowship",
        "tags": ["women founder", "consumer", "retail", "fellowship"],
        "pre_revenue_ok": True,
        "focus": "Prestigious fellowship for women entrepreneurs in consumer/retail",
    },
    {
        "name": "Fearless Fund Grants",
        "url": "https://fearlessfund.com/grants/",
        "type": "grant",
        "tags": ["Black women founder", "consumer", "retail", "grant"],
        "pre_revenue_ok": True,
        "focus": "Grants and investment for Black women founders",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # F.INC ECOSYSTEM — newer, high-quality, pre-revenue friendly
    # ══════════════════════════════════════════════════════════════════════════

    {
        "name": "f.inc Programs (incl. Canopy)",
        "url": "https://f.inc",
        "type": "accelerator",
        "tags": ["pre-revenue ok", "consumer", "tech", "early-stage"],
        "pre_revenue_ok": True,
        "focus": "f.inc runs cohort programs like Canopy — check for open applications",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # HBS & HARVARD — high relevance, you have insider access
    # ══════════════════════════════════════════════════════════════════════════

    {
        "name": "HBS Rock Center — Entrepreneurship Programs",
        "url": "https://www.hbs.edu/entrepreneurship/programs/Pages/default.aspx",
        "type": "accelerator",
        "tags": ["HBS", "university", "student founder", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "HBS-specific programs — you have priority access as a student",
    },
    {
        "name": "HBS New Venture Competition",
        "url": "https://www.hbs.edu/newventurecompetition",
        "type": "competition",
        "tags": ["HBS", "competition", "prize", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "Annual competition open to HBS students, prizes up to $75K",
    },
    {
        "name": "Harvard i-lab Programs",
        "url": "https://ilab.harvard.edu/programs",
        "type": "accelerator",
        "tags": ["Harvard", "student founder", "incubator", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "Venture incubation programs for Harvard students",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # PRE-REVENUE FRIENDLY ACCELERATORS
    # ══════════════════════════════════════════════════════════════════════════

    {
        "name": "Y Combinator",
        "url": "https://www.ycombinator.com/apply",
        "type": "accelerator",
        "tags": ["top-tier", "consumer", "tech", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "YC explicitly accepts pre-revenue; 2 cohorts/year",
    },
    {
        "name": "Antler",
        "url": "https://www.antler.co/apply",
        "type": "accelerator",
        "tags": ["pre-revenue ok", "idea stage", "early-stage"],
        "pre_revenue_ok": True,
        "focus": "Accepts founders at idea stage, provides stipend",
    },
    {
        "name": "On Deck Founders",
        "url": "https://www.beondeck.com/founders",
        "type": "accelerator",
        "tags": ["pre-revenue ok", "community", "early-stage"],
        "pre_revenue_ok": True,
        "focus": "Fellowship for early-stage founders, pre-revenue ok",
    },
    {
        "name": "MassChallenge",
        "url": "https://masschallenge.org/programs-apply/",
        "type": "accelerator",
        "tags": ["Boston", "no equity", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "No-equity accelerator in Boston, accepts pre-revenue",
    },
    {
        "name": "Techstars",
        "url": "https://www.techstars.com/accelerators",
        "type": "accelerator",
        "tags": ["consumer", "retail tech", "top-tier"],
        "pre_revenue_ok": True,
        "focus": "Many Techstars programs accept pre-revenue — filter by program focus",
    },
    {
        "name": "Backstage Capital",
        "url": "https://backstagecapital.com",
        "type": "investment",
        "tags": ["underrepresented founder", "Black founder", "women founder"],
        "pre_revenue_ok": True,
        "focus": "Invests in underrepresented founders, pre-revenue ok",
    },
    {
        "name": "Precursor Ventures",
        "url": "https://precursorvc.com",
        "type": "investment",
        "tags": ["pre-revenue ok", "pre-seed", "diverse founder"],
        "pre_revenue_ok": True,
        "focus": "Pre-seed fund, invests at idea/pre-revenue stage",
    },
    {
        "name": "Overlooked Ventures",
        "url": "https://www.overlooked.vc",
        "type": "investment",
        "tags": ["Black founder", "women founder", "pre-seed", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "Pre-seed fund focused on overlooked founders",
    },
    {
        "name": "Harlem Capital",
        "url": "https://harlemcapital.co/apply",
        "type": "investment",
        "tags": ["Black founder", "diverse founder", "consumer"],
        "pre_revenue_ok": True,
        "focus": "Invests in diverse founders including pre-revenue",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # CONSUMER / RETAIL TECH SPECIFIC
    # ══════════════════════════════════════════════════════════════════════════

    {
        "name": "LVMH La Maison des Startups",
        "url": "https://lamaisondesstartups.lvmh.com",
        "type": "accelerator",
        "tags": ["consumer", "retail", "luxury", "fashion", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "LVMH accelerator for consumer/retail/luxury tech startups",
    },
    {
        "name": "Comcast NBCUniversal LIFT Labs",
        "url": "https://liftlabs.comcast.com",
        "type": "accelerator",
        "tags": ["consumer tech", "diverse founder", "media"],
        "pre_revenue_ok": True,
        "focus": "Diverse-founder-focused accelerator, consumer tech",
    },
    {
        "name": "Women's Startup Lab",
        "url": "https://womenstartupslab.com/programs",
        "type": "accelerator",
        "tags": ["women founder", "consumer", "tech", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "Accelerator for women founders in tech/consumer",
    },
    {
        "name": "Astia",
        "url": "https://astia.org/programs",
        "type": "accelerator",
        "tags": ["women founder", "tech", "pre-revenue ok"],
        "pre_revenue_ok": True,
        "focus": "Accelerator and funding for women-led tech startups",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # GOVERNMENT & INSTITUTIONAL GRANTS
    # ══════════════════════════════════════════════════════════════════════════

    {
        "name": "Minority Business Development Agency (MBDA) Grants",
        "url": "https://www.mbda.gov/page/grants",
        "type": "grant",
        "tags": ["minority founder", "government", "grant"],
        "pre_revenue_ok": True,
        "focus": "Federal grants for minority-owned businesses",
    },
    {
        "name": "SBA Grants for Women",
        "url": "https://www.sba.gov/funding-programs/grants",
        "type": "grant",
        "tags": ["women founder", "SBA", "government"],
        "pre_revenue_ok": True,
        "focus": "SBA grant programs for women and minority entrepreneurs",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # AGGREGATORS — cast a wide net for new listings
    # ══════════════════════════════════════════════════════════════════════════

    {
        "name": "IFundWomen Grant Database",
        "url": "https://ifundwomen.com/grants",
        "type": "grant_aggregator",
        "tags": ["women founder", "aggregator", "open grants"],
        "pre_revenue_ok": True,
        "focus": "Live database of open grants for women founders",
    },
    {
        "name": "Hello Alice Grant Feed",
        "url": "https://helloalice.com/grants/",
        "type": "grant_aggregator",
        "tags": ["diverse founder", "aggregator", "open grants"],
        "pre_revenue_ok": True,
        "focus": "Aggregates currently open grants with deadlines",
    },
    {
        "name": "F6S Accelerator Programs",
        "url": "https://www.f6s.com/programs",
        "type": "accelerator_aggregator",
        "tags": ["aggregator", "accelerator", "open applications"],
        "pre_revenue_ok": True,
        "focus": "Large aggregator of accelerator programs globally",
    },
    {
        "name": "Visible.vc Funding Opportunities",
        "url": "https://visible.vc/blog/funding-for-black-founders/",
        "type": "grant_aggregator",
        "tags": ["Black founder", "aggregator", "funding"],
        "pre_revenue_ok": True,
        "focus": "Curated list of funding for Black founders",
    },
    {
        "name": "Crunchbase — Grants for Black Founders",
        "url": "https://about.crunchbase.com/resources/grants-for-black-founders/",
        "type": "grant_aggregator",
        "tags": ["Black founder", "aggregator"],
        "pre_revenue_ok": True,
        "focus": "Crunchbase curated list of grants for Black founders",
    },
    {
        "name": "Founders of Color Opportunities",
        "url": "https://www.foundersofcolor.com",
        "type": "grant_aggregator",
        "tags": ["diverse founder", "aggregator", "BIPOC"],
        "pre_revenue_ok": True,
        "focus": "Opportunities database for founders of color",
    },
]

# Quick lookup: only pre-revenue-ok sources
PRE_REVENUE_SOURCES = [s for s in SOURCES if s.get("pre_revenue_ok", False)]
