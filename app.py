import os
from flask import Flask, jsonify, send_from_directory
import requests

app = Flask(__name__, static_folder="frontend", static_url_path="")

API_URL = "https://trustmrr.com/api/v1/startups"

def to_usd(cents):
    if cents is None:
        return None
    return round(cents / 100, 2)

def generate_buyer_persona(startup):
    category = (startup.get("category") or "General SaaS").lower()
    mrr = startup.get("mrr_usd") or 0

    buyer_types = []
    strategic_angles = []

    if any(k in category for k in ["ai", "prompt", "content", "automation"]):
        buyer_types.extend(["AI Agency Owners", "SaaS Portfolio Operators", "Solo Micro-Acquirers"])
        strategic_angles.append("Plug-and-play workflow integration into existing AI agency toolstacks.")
    elif any(k in category for k in ["dev", "notion", "developer", "tool"]):
        buyer_types.extend(["Developer Content Creators", "Indie Hackers", "DevTool Studios"])
        strategic_angles.append("Low-maintenance product with immediate cross-promotion to dev audiences.")
    else:
        buyer_types.extend(["Niche Aggregators", "First-time SaaS Buyers", "Digital Asset Investors"])
        strategic_angles.append("Turnkey digital asset with pre-existing user traction.")

    if mrr < 100:
        strategic_angles.append("Ideal starter project for an indie builder seeking immediate product-market fit.")
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
    lifetime_revenue = startup_data.get("lifetime_revenue_usd") or 0

    # Lifetime Revenue Scaling
    if lifetime_revenue >= 1000000:
        score += 30
        reasons.append("Massive lifetime revenue ($1M+)")
    elif lifetime_revenue >= 100000:
        score += 20
        reasons.append("Strong lifetime revenue ($100k+)")
    elif lifetime_revenue >= 10000:
        score += 10
        reasons.append("Proven lifetime revenue ($10k+)")

    # Multiple
    if multiple is not None and multiple > 0:
        if multiple <= 2.5:
            score += 25
            reasons.append("Highly attractive multiple (<= 2.5x)")
        elif multiple <= 4.0:
            score += 18
            reasons.append("Fair valuation multiple (2.5x - 4.0x)")
        elif multiple <= 6.0:
            score += 8
            reasons.append("Standard growth multiple (4.0x - 6.0x)")
        else:
            reasons.append("High valuation multiple (> 6.0x)")

    # 30-Day Growth
    if growth_30d >= 20:
        score += 20
        reasons.append("High 30-day growth (>= 20%)")
    elif growth_30d >= 5:
        score += 12
        reasons.append("Solid 30-day growth (5% - 20%)")
    elif growth_30d >= 0:
        score += 5
        reasons.append("Stable revenue (0% - 5%)")

    # MRR
    if mrr >= 5000:
        score += 15
        reasons.append("Established MRR ($5k+)")
    elif mrr >= 1000:
        score += 10
        reasons.append("Proven traction ($1k - $5k MRR)")
    elif mrr > 0:
        score += 5
        reasons.append("Early revenue (> $0 MRR)")

    if asking_price > 0:
        score += 5
    if startup_data.get("website"):
        score += 5

    return {"score": min(score, 100), "highlights": reasons}

@app.route("/favicon.ico")
def favicon():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, "favicon.ico", mimetype="image/vnd.microsoft.icon")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/startups")
def fetch_startups_api():
    api_key = os.getenv("TMRR_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not configured"}), 500

    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"onSale": "true", "sort": "best-deal", "limit": 20}

    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as error:
        return jsonify({"error": str(error)}), 500

    raw_startups = result.get("data", [])
    all_processed = []

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
            "lifetime_revenue_usd": to_usd(revenue.get("total") or revenue.get("lifetime")),
            "asking_price_usd": to_usd(startup.get("askingPrice")),
            "multiple": startup.get("multiple"),
            "growth_30d": startup.get("growth30d") or 0,
            "on_sale": startup.get("onSale"),
            "trustmrr_url": f"https://trustmrr.com/startup/{slug}" if slug else None,
        }

        scoring_res = calculate_opportunity_score(item)
        item["opportunity_score"] = scoring_res["score"]
        item["score_highlights"] = scoring_res["highlights"]

        buyer_research = generate_buyer_persona(item)
        item["target_buyers"] = buyer_research["target_buyers"]
        item["outreach_angle"] = buyer_research["outreach_angle"]

        all_processed.append(item)

    # List 1: Rapid Short-Term Growth (Sorted by 30d growth)
    rapid_growth_list = sorted(all_processed, key=lambda x: x["growth_30d"], reverse=True)

    # List 2: All-Time Peak / Lifetime Revenue Giants (Sorted by lifetime revenue)
    all_time_peak_list = sorted(all_processed, key=lambda x: (x.get("lifetime_revenue_usd") or 0), reverse=True)

    return jsonify({
        "rapid_growth": rapid_growth_list[:10],
        "all_time_peak": all_time_peak_list[:10]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)