const API = "/api";

const els = {
  region: document.getElementById("region-select"),
  product: document.getElementById("product-select"),
  start: document.getElementById("start-date"),
  end: document.getElementById("end-date"),
  granularity: document.getElementById("granularity-select"),
  apply: document.getElementById("apply-filters"),
  reset: document.getElementById("reset-filters"),
  uploadForm: document.getElementById("upload-form"),
  fileInput: document.getElementById("file-input"),
  uploadStatus: document.getElementById("upload-status"),
};

function currentFilters() {
  return {
    region: els.region.value || null,
    product: els.product.value || null,
    start_date: els.start.value || null,
    end_date: els.end.value || null,
    granularity: els.granularity.value || "month",
  };
}

function buildQuery(params) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v) usp.append(k, v);
  });
  const qs = usp.toString();
  return qs ? `?${qs}` : "";
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${url}`);
  return res.json();
}

function formatCurrency(n) {
  return "$" + Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

async function loadFilters() {
  const data = await fetchJSON(`${API}/filters`);
  els.region.innerHTML = '<option value="">All Regions</option>' +
    data.regions.map((r) => `<option value="${r}">${r}</option>`).join("");
  els.product.innerHTML = '<option value="">All Products</option>' +
    data.products.map((p) => `<option value="${p}">${p}</option>`).join("");

  if (data.date_range) {
    els.start.min = data.date_range[0];
    els.start.max = data.date_range[1];
    els.end.min = data.date_range[0];
    els.end.max = data.date_range[1];
  }
}

async function loadKPIs(filters) {
  const q = buildQuery(filters);
  const data = await fetchJSON(`${API}/kpis${q}`);
  document.getElementById("kpi-revenue").textContent = formatCurrency(data.total_revenue);
  document.getElementById("kpi-units").textContent = data.total_units.toLocaleString();
  document.getElementById("kpi-aov").textContent = formatCurrency(data.avg_order_value);
  document.getElementById("kpi-transactions").textContent = data.num_transactions.toLocaleString();
  document.getElementById("kpi-growth").textContent =
    data.mom_growth_pct === null || data.mom_growth_pct === undefined
      ? "—"
      : `${data.mom_growth_pct > 0 ? "+" : ""}${data.mom_growth_pct}%`;
}

async function loadTrend(filters) {
  const q = buildQuery({
    granularity: filters.granularity,
    region: filters.region,
    product: filters.product,
    start_date: filters.start_date,
    end_date: filters.end_date,
  });
  const data = await fetchJSON(`${API}/revenue-trend${q}`);
  const x = data.map((d) => d.period);
  const y = data.map((d) => d.revenue);

  Plotly.newPlot(
    "chart-trend",
    [{ x, y, type: "scatter", mode: "lines+markers", line: { color: "#1a8a6b", width: 2.5 }, marker: { size: 5 } }],
    {
      margin: { t: 10, r: 20, l: 55, b: 40 },
      xaxis: { title: "" },
      yaxis: { title: "Revenue", tickprefix: "$" },
      font: { family: "Inter, sans-serif", size: 12 },
    },
    { displayModeBar: false, responsive: true }
  );
}

async function loadRegional(filters) {
  const q = buildQuery({
    product: filters.product,
    start_date: filters.start_date,
    end_date: filters.end_date,
  });
  const data = await fetchJSON(`${API}/regional-performance${q}`);
  const x = data.map((d) => d.region);
  const y = data.map((d) => d.revenue);

  Plotly.newPlot(
    "chart-regional",
    [{ x, y, type: "bar", marker: { color: "#223447" } }],
    {
      margin: { t: 10, r: 10, l: 55, b: 40 },
      yaxis: { title: "Revenue", tickprefix: "$" },
      font: { family: "Inter, sans-serif", size: 12 },
    },
    { displayModeBar: false, responsive: true }
  );
}

async function loadProducts(filters) {
  const q = buildQuery({
    region: filters.region,
    start_date: filters.start_date,
    end_date: filters.end_date,
    top_n: 10,
  });
  const data = await fetchJSON(`${API}/product-performance${q}`);
  const y = data.map((d) => d.product);
  const x = data.map((d) => d.revenue);

  Plotly.newPlot(
    "chart-products",
    [{ x, y, type: "bar", orientation: "h", marker: { color: "#1a8a6b" } }],
    {
      margin: { t: 10, r: 10, l: 90, b: 40 },
      xaxis: { title: "Revenue", tickprefix: "$" },
      font: { family: "Inter, sans-serif", size: 12 },
    },
    { displayModeBar: false, responsive: true }
  );
}

async function refreshDashboard() {
  const filters = currentFilters();
  await Promise.all([
    loadKPIs(filters),
    loadTrend(filters),
    loadRegional(filters),
    loadProducts(filters),
  ]);
}

els.apply.addEventListener("click", refreshDashboard);
els.reset.addEventListener("click", () => {
  els.region.value = "";
  els.product.value = "";
  els.start.value = "";
  els.end.value = "";
  els.granularity.value = "month";
  refreshDashboard();
});

els.uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = els.fileInput.files[0];
  if (!file) {
    els.uploadStatus.textContent = "Choose a file first.";
    return;
  }
  const formData = new FormData();
  formData.append("file", file);

  els.uploadStatus.textContent = "Uploading...";
  try {
    const res = await fetch(`${API}/upload`, { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    els.uploadStatus.textContent = `Ingested ${data.rows_ingested.toLocaleString()} rows (${data.date_range[0]} to ${data.date_range[1]})`;
    await loadFilters();
    await refreshDashboard();
  } catch (err) {
    els.uploadStatus.textContent = `Error: ${err.message}`;
  }
});

(async function init() {
  await loadFilters();
  await refreshDashboard();
})();
