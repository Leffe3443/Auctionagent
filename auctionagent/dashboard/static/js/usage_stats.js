let runsChart, soonChart, currencyChart;

async function loadAuctionStats() {
  const res = await fetch("/api/auction-agent/stats");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const stats = await res.json();

  // ----- 1) Items per run (last 10) -----
  const runsLabels = stats.runs.labels;         // e.g. ["12:15#42", ...]
  const runsCounts = stats.runs.counts;         // items found
  const runsDurMs  = stats.runs.durations;      // duration in ms

  const ctxRuns = document.getElementById("runsChart");
  if (runsChart) runsChart.destroy();
  runsChart = new Chart(ctxRuns, {
    type: "line",
    data: {
      labels: runsLabels,
      datasets: [
        { label: "Miliseconds", data: runsDurMs, tension: 0.25, spanGaps: true },
        // { label: "Duration (ms)", data: runsDurMs, yAxisID: "y1", tension: 0.25 }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      plugins: {
        tooltip: {
          callbacks: {
            title: (items) => {
              // Show time + run id nicely (labels are "HH:MM#RUNID")
              const raw = items[0].label || "";
              const [t, id] = raw.split("#");
              return id ? `Run #${id} at ${t}` : raw;
            }
          }
        },
        legend: { position: "bottom" }
      },
      scales: {
        y:  { title: { display: true, text: "Items" }, beginAtZero: true },
        y1: { title: { display: true, text: "ms" }, position: "right", grid: { drawOnChartArea: false } }
      }
    }
  });

  // ----- 2) Ending soon buckets -----
  const ctxSoon = document.getElementById("soonChart");
  if (soonChart) soonChart.destroy();
  soonChart = new Chart(ctxSoon, {
    type: "bar",
    data: {
      labels: stats.endingSoon.labels,   // ["<=24h","<=48h","<=72h"]
      datasets: [{ label: "Count", data: stats.endingSoon.counts }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, title: { display: true, text: "Items" } } },
      plugins: { legend: { display: false } }
    }
  });

  // ----- 3) Currency mix -----
  const ctxCurr = document.getElementById("currencyChart");
  if (currencyChart) currencyChart.destroy();
  currencyChart = new Chart(ctxCurr, {
    type: "doughnut",
    data: {
      labels: stats.currency.labels,     // e.g. ["SEK","EUR","—"]
      datasets: [{ data: stats.currency.counts }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom" } }
    }
  });
}

// initial render
document.addEventListener("DOMContentLoaded", loadAuctionStats);

// optional: call loadAuctionStats() again after each scrape/AI run to refresh charts
// e.g. after handling items:
// await ...; loadAuctionStats();
