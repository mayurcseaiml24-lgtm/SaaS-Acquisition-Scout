import json
from pathlib import Path

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "startups.json"
)

def generate_pitch(startup):
    name = startup.get("name", "Unknown Startup")
    mrr = startup.get("mrr_usd")
    price = startup.get("asking_price_usd")
    multiple = startup.get("multiple")
    category = startup.get("category") or "SaaS"
    url = startup.get("trustmrr_url") or "#"
    buyers = ", ".join(startup.get("target_buyers", ["Digital Asset Investors"]))
    angle = startup.get("outreach_angle", "")

    mrr_formatted = f"${mrr:,.2f}" if mrr is not None else "N/A"
    price_formatted = f"${price:,.2f}" if price is not None else "N/A"
    mult_formatted = f"{multiple:.2f}x" if multiple is not None else "N/A"

    memo = f"""
================================================================================
🎯 ACQUISITION PITCH MEMO: {name}
================================================================================
Category: {category}
Score: {startup.get('opportunity_score', 0)} / 100
MRR: {mrr_formatted} | Asking Price: {price_formatted} | Multiple: {mult_formatted}
Listing Link: {url}

--------------------------------------------------------------------------------
1. IDEAL BUYER PROFILE
--------------------------------------------------------------------------------
Primary Targets: {buyers}

--------------------------------------------------------------------------------
2. STRATEGIC THESIS & OUTREACH ANGLE
--------------------------------------------------------------------------------
{angle}

--------------------------------------------------------------------------------
3. OUTREACH EMAIL TEMPLATE
--------------------------------------------------------------------------------
Subject: Strategic Acquisition Opportunity: {name} ({category})

Hi [Buyer Name],

I came across {name}, an active SaaS in the {category} space, and thought of your portfolio.

Key Highlights:
• Current MRR: {mrr_formatted}
• Valuation Multiple: {mult_formatted} ({price_formatted} asking price)
• Key Advantage: {angle}

Given your focus in this market, this could be a high-upside bolt-on or starter acquisition.

You can review the full listing details here: {url}

Let me know if you'd like an introduction or further details!

Best regards,
[Your Name]
================================================================================
"""
    return memo

def generate_all_memos():
    if not DATA_FILE.exists():
        print("Data file not found. Please run scout.py first!")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    startups = data.get("startups", [])
    if not startups:
        print("No startups found in data file.")
        return

    # Focus on the top 3 highest-ranked opportunities
    top_startups = startups[:3]

    print(f"\n🔥 Generating Pitch Memos for Top {len(top_startups)} Opportunities...\n")

    output_dir = DATA_FILE.parent / "pitches"
    output_dir.mkdir(exist_ok=True)

    for idx, startup in enumerate(top_startups, start=1):
        memo_content = generate_pitch(startup)
        
        # Save pitch text file
        file_slug = startup.get("slug") or f"startup_{idx}"
        pitch_file = output_dir / f"{file_slug}_pitch.txt"
        
        with open(pitch_file, "w", encoding="utf-8") as pf:
            pf.write(memo_content)

        print(memo_content)
        print(f"Saved to: {pitch_file}\n")

if __name__ == "__main__":
    generate_all_memos()