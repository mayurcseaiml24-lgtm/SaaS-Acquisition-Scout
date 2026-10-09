let allStartups = [];

document.addEventListener("DOMContentLoaded", () => {
  fetch("/api/startups")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Data file not found. Run scout.py first!");
      }
      return response.json();
    })
    .then((data) => {
      allStartups = data.startups || [];
      renderMeta(data);
      populateCategoryDropdown(allStartups);
      renderCards(allStartups);
      setupFilterListeners();
    })
    .catch((error) => {
      document.getElementById("meta-info").textContent = error.message;
    });
});

function renderMeta(data) {
  const metaEl = document.getElementById("meta-info");
  const date = data.fetched_at ? new Date(data.fetched_at).toLocaleString() : "N/A";
  metaEl.textContent = `Showing ${data.count || 0} listings • Last updated: ${date}`;
}

function populateCategoryDropdown(startups) {
  const select = document.getElementById("category-select");
  
  // Extract unique categories from listings
  const categories = Array.from(
    new Set(startups.map((s) => s.category).filter(Boolean))
  ).sort();

  categories.forEach((cat) => {
    const option = document.createElement("option");
    option.value = cat;
    option.textContent = cat;
    select.appendChild(option);
  });
}

function setupFilterListeners() {
  const searchInput = document.getElementById("search-input");
  const categorySelect = document.getElementById("category-select");
  const resetBtn = document.getElementById("reset-btn");

  const applyFilters = () => {
    const query = searchInput.value.toLowerCase().trim();
    const selectedCategory = categorySelect.value;

    const filtered = allStartups.filter((startup) => {
      const nameMatch = (startup.name || "").toLowerCase().includes(query);
      const descMatch = (startup.description || "").toLowerCase().includes(query);
      const catTextMatch = (startup.category || "").toLowerCase().includes(query);
      const buyerMatch = (startup.target_buyers || []).some((b) =>
        b.toLowerCase().includes(query)
      );

      const matchesSearch = nameMatch || descMatch || catTextMatch || buyerMatch;
      const matchesCategory =
        selectedCategory === "ALL" || startup.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });

    renderCards(filtered);
  };

  searchInput.addEventListener("input", applyFilters);
  categorySelect.addEventListener("change", applyFilters);

  resetBtn.addEventListener("click", () => {
    searchInput.value = "";
    categorySelect.value = "ALL";
    renderCards(allStartups);
  });
}

function renderCards(startups) {
  const container = document.getElementById("startup-grid");
  container.innerHTML = "";

  if (startups.length === 0) {
    container.innerHTML = `<div class="no-results">No startups match your current search criteria.</div>`;
    return;
  }

  startups.forEach((startup) => {
    const card = document.createElement("div");
    card.className = "card";

    const mrr = startup.mrr_usd !== null ? `$${startup.mrr_usd.toLocaleString()}` : "N/A";
    const price = startup.asking_price_usd !== null ? `$${startup.asking_price_usd.toLocaleString()}` : "N/A";
    const multiple = startup.multiple !== null ? `${Number(startup.multiple).toFixed(2)}x` : "N/A";

    const highlightsList = (startup.score_highlights || [])
      .map((h) => `<li>${h}</li>`)
      .join("");

    const buyersTags = (startup.target_buyers || [])
      .map((b) => `<span style="background:rgba(59,130,246,0.15); color:#60a5fa; font-size:0.75rem; padding:2px 6px; border-radius:4px; margin-right:4px;">${b}</span>`)
      .join("");

    card.innerHTML = `
      <div>
        <div class="card-header">
          <h2 class="card-title">${startup.name || "Unknown"}</h2>
          <span class="score-badge">Score: ${startup.opportunity_score || 0}</span>
        </div>
        <span class="category-tag">${startup.category || "General SaaS"}</span>
        
        <div class="metrics">
          <div class="metric-item">
            <span class="metric-label">MRR</span>
            <span class="metric-value">${mrr}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Asking Price</span>
            <span class="metric-value">${price}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Multiple</span>
            <span class="metric-value">${multiple}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">30d Growth</span>
            <span class="metric-value">${startup.growth_30d || 0}%</span>
          </div>
        </div>

        <ul class="highlights">
          ${highlightsList}
        </ul>

        <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid #334155;">
          <div style="font-size:0.75rem; color:#94a3b8; margin-bottom:0.4rem; font-weight:600;">TARGET BUYERS</div>
          <div style="margin-bottom:0.5rem;">${buyersTags}</div>
          <div style="font-size:0.8rem; color:#cbd5e1; font-style:italic;">
            "${startup.outreach_angle || 'Strategic fit based on category metrics.'}"
          </div>
        </div>
      </div>

      <div class="card-actions" style="margin-top:1rem;">
        ${
          startup.trustmrr_url
            ? `<a href="${startup.trustmrr_url}" target="_blank" rel="noopener" class="btn btn-primary">View Listing</a>`
            : ""
        }
      </div>
    `;

    container.appendChild(card);
  });
}