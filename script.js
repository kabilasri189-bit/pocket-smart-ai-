const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

let currentPlanner = "home";

function formatINR(value) {
  return new Intl.NumberFormat("en-IN", {style:"currency", currency:"INR", maximumFractionDigits:0}).format(Number(value || 0));
}

function setPlanner(planner) {
  currentPlanner = planner;
  $("#planner").value = planner;
  $$(".tab").forEach(t => t.classList.toggle("active", t.dataset.planner === planner));
  $("#homeFields").classList.toggle("hidden", planner !== "home");
  $("#partyFields").classList.toggle("hidden", planner !== "party");
  $("#jewelryFields").classList.toggle("hidden", planner !== "jewelry");
}

$$(".tab").forEach(tab => tab.addEventListener("click", () => setPlanner(tab.dataset.planner)));

$("#budget").addEventListener("input", e => {
  const v = Math.max(1000, Number(e.target.value || 0));
  $("#budgetPreview").textContent = formatINR(v);
  $("#heroTotal").textContent = formatINR(v);
  $("#budgetRange").value = Math.min(200000, v);
});
$("#budgetRange").addEventListener("input", e => {
  $("#budget").value = e.target.value;
  $("#budgetPreview").textContent = formatINR(e.target.value);
  $("#heroTotal").textContent = formatINR(e.target.value);
});

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;" }[c]));
}

function renderResults(data) {
  const allocations = (data.budget_categories || []).map(x => `
    <div class="alloc-item">
      <b>${escapeHTML(x.category)}</b>
      <span>${formatINR(x.allocation)}</span>
      <small>${escapeHTML(x.reason)}</small>
    </div>`).join("");

  const recs = (data.recommendations || []).map(x => `
    <article class="rec">
      <div>
        <h4>${escapeHTML(x.name)}</h4>
        <p>${escapeHTML(x.reason)}</p>
        <span class="platform">${escapeHTML(x.platform)}</span>
      </div>
      <div class="rec-price">${formatINR(x.estimated_price)}</div>
      <a class="view-link" href="${escapeHTML(x.search_url)}" target="_blank" rel="noopener">Search this recommendation →</a>
    </article>`).join("");

  $("#results").innerHTML = `
    <div class="summary">
      <div class="summary-top">
        <div><h3>${escapeHTML(data.title)}</h3><p>${escapeHTML(data.summary)}</p></div>
        <div class="summary-total"><strong>${formatINR(data.estimated_total)}</strong><small>estimated plan</small></div>
      </div>
      <div class="alloc">${allocations}</div>
    </div>
    <div class="rec-list">${recs}</div>
    <p class="source">${escapeHTML(data.source || "AI generated")} • ${escapeHTML(data.disclaimer || "")}</p>`;
}

$("#plannerForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const btn = $("#generateBtn");
  btn.disabled = true;
  btn.innerHTML = "Creating your plan… <span>✦</span>";
  $("#results").innerHTML = `<div class="empty-state"><div class="empty-icon">✦</div><h3>Thinking through your budget...</h3><p>Building category allocations and recommendations.</p></div>`;

  try {
    const response = await fetch("/api/recommend", {method:"POST", body:new FormData(event.target)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Request failed");
    renderResults(data);
  } catch (error) {
    $("#results").innerHTML = `<div class="error"><b>Could not create the plan.</b><br>${escapeHTML(error.message)}<br><br>Check that the Flask server is running and try again.</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Generate my plan <span>→</span>';
  }
});

$("#resetBtn").addEventListener("click", () => {
  $("#plannerForm").reset();
  $("#budget").value = 10000;
  $("#budgetRange").value = 10000;
  $("#budgetPreview").textContent = formatINR(10000);
  $("#heroTotal").textContent = formatINR(10000);
  setPlanner("home");
  $("#results").innerHTML = `<div class="empty-state"><div class="empty-icon">✦</div><h3>Your recommendations will appear here</h3><p>Choose a planner, enter your budget, and click <b>Generate my plan</b>.</p><div class="example"><span>Example</span> ₹10,000 • Modern living room</div></div>`;
});

fetch("/api/health").then(r => r.json()).then(data => {
  if (!data.ai_configured) $("#status").innerHTML = "<span></span> Demo mode • add Gemini key for AI";
}).catch(() => {
  $("#status").innerHTML = "<span></span> Server connection unavailable";
});
