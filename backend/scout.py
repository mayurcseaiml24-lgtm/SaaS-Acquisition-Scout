import os
import json
from pathlib import Path
from datetime import datetime, timezone
import requests

API_URL = "https://trustmrr.com/api/v1/startups"

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "startups.json"
)

def to_usd(cents):
    if cents is None:
        return None
    return round(cents / 100, 2)

def generate_buyer_persona(startup):
    """
    Generates targeted buyer profiles and strategic angles based on startup characteristics.
    """
    category = (startup.get("category") or "General SaaS").lower()
    mrr = startup.get("mrr_usd") or 0
    price = startup.get("asking_price_usd") or 0

    buyer_types = []
    strategic_angles = []

    # Categorization Rules
    if any(k in category for k in ["ai", "prompt", "content", "automation"]):
        buyer_types.extend(["AI Agency Owners", "SaaS Portfolio Operators", "Solo Micro-Acquirers"])
        strategic_angles.append("Plug-and-play workflow integration into existing AI agency toolstacks.")
    elif any(k in category for k in ["dev", "notion", "developer", "tool"]):
        buyer_types.extend(["Developer Content Creators", "Indie Hackers", "DevTool Studios"])
        strategic_angles.append("Low-maintenance product with immediate cross-promotion to dev audiences.")
    else:
        buyer_types.extend(["Niche Aggregators", "First-time SaaS Buyers", "Digital Asset Investors"])
        strategic_angles.append("Turnkey digital asset with pre-existing user traction.")

    # MRR / Price tiering strategy
    if mrr < 100:
        strategic_angles.append("Ideal starter project for an indie builder seeking immediate product-market fit without building from scratch.")
    elif mrr >= 1000:
        strategic_angles.append("Cash-flowing asset ready for SEO and outbound marketing scaling.")

    return {
        "target_buyers": buyer_types,
        "outreach_angle": " ".join(strategic_angles)
    }

def calculate_opportunity_score(startup_data):
    score = 0
    reasons = []

    mrr = startup_data.get("mrr_usd") or 0
    asking_price = startup_data.get("asking_price_usd") or 0
    multiple = startup_data.get("multiple")
    growth_30d = startup_data.get("growth_30d") or 0

    # 1. Valuation Multiple Score (Max 35 points)
    if multiple is not None and multiple > 0:
        if multiple <= 2.5:
            score += 35
            reasons.append("Highly attractive multiple (<= 2.5x)")
        elif multiple <= 4.0:
            score += 25
            reasons.append("Fair valuation multiple (2.5x - 4.0x)")
        elif multiple <= 6.0:
            score += 10
            reasons.append("Standard growth multiple (4.0x - 6.0x)")
        else:
            reasons.append("High valuation multiple (> 6.0x)")

    # 2. Growth Score (Max 30 points)
    if growth_30d >= 20:
        score += 30
        reasons.append("High 30-day growth (>= 20%)")
    elif growth_30d >= 5:
        score += 20
        reasons.append("Solid 30-day growth (5% - 20%)")
    elif growth_30d >= 0:
        score += 10
        reasons.append("Stable revenue (0% - 5%)")
    else:
        reasons.append("Declining 30-day growth")

    # 3. MRR Health (Max 20 points)
    if mrr >= 5000:
        score += 20
        reasons.append("Established MRR ($5k+)")
    elif mrr >= 1000:
        score += 15
        reasons.append("Proven traction ($1k - $5k MRR)")
    elif mrr > 0:
        score += 8
        reasons.append("Early revenue (> $0 MRR)")
    else:
        reasons.append("Pre-revenue / $0 MRR")

    # 4. Listing Completeness (Max 15 points)
    if asking_price > 0:
        score += 10
    if startup_data.get("website"):
        score += 5

    return {
        "score": min(score, 100),
        "highlights": reasons
    }

def get_startups():
    api_key = os.getenv("TMRR_API_KEY")

    if not api_key:
        print("API key not found. Set TMRR_API_KEY in terminal first.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    params = {
        "onSale": "true",
        "sort": "best-deal",
        "limit": 10
    }

    try:
        response = requests.get(
            API_URL,
            headers=headers,
            params=params,
            timeout=20
        )
        response.raise_for_status()
        result = response.json()

    except requests.RequestException as error:
        print("API request failed:", error)
        return

    raw_startups = result.get("data", [])
    processed_startups = []

    for startup in raw_startups:
        revenue = startup.get("revenue") or {}
        slug = startup.get("slug")

        item = {
            "name": startup.get("name"),
            "slug": slug,
            "website": startup.get("website"),
            "category": startup.get("category"),
            "description": startup.get("description"),
            "mrr_usd": to_usd(revenue.get("mrr")),
            "revenue_30d_usd": to_usd(revenue.get("last30Days")),
            "asking_price_usd": to_usd(startup.get("askingPrice")),
            "multiple": startup.get("multiple"),
            "growth_30d": startup.get("growth30d"),
            "on_sale": startup.get("onSale"),
            "trustmrr_url": f"https://trustmrr.com/startup/{slug}" if slug else None
        }

        # Calculate opportunity score
        scoring_res = calculate_opportunity_score(item)
        item["opportunity_score"] = scoring_res["score"]
        item["score_highlights"] = scoring_res["highlights"]

        # Generate buyer research profile
        buyer_research = generate_buyer_persona(item)
        item["target_buyers"] = buyer_research["target_buyers"]
        item["outreach_angle"] = buyer_research["outreach_angle"]

        processed_startups.append(item)

    processed_startups.sort(key=lambda x: x["opportunity_score"], reverse=True)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_matching": result.get("meta", {}).get("total"),
        "count": len(processed_startups),
        "startups": processed_startups
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    print(f"\n🎯 Successfully re-processed {len(processed_startups)} startups with Buyer Profiling!")
    print(f"Data saved to: {DATA_FILE}\n")

if __name__ == "__main__":
    get_startups()