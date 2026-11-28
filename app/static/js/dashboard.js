Chart.defaults.color = "#8b949e";
Chart.defaults.borderColor = "#30363d";

const runBtn = document.getElementById("run-btn");
const statusEl = document.getElementById("status");
const totalEl = document.getElementById("total-count");
const normalEl = document.getElementById("normal-count");
const attackEl = document.getElementById("attack-count");
const emptyMsg = document.getElementById("empty-msg");
const table = document.getElementById("alerts-table");
const tbody = document.getElementById("alerts-body");

const ratioChart = new Chart(document.getElementById("ratio-chart"), {
  type: "doughnut",
  data: {
    labels: ["Normal", "Suspicious"],
    datasets: [{ data: [0, 0], backgroundColor: ["#3fb950", "#f85149"], borderWidth: 0 }],
  },
  options: { responsive: true, maintainAspectRatio: false },
});

const typesChart = new Chart(document.getElementById("types-chart"), {
  type: "bar",
  data: {
    labels: [],
    datasets: [{ label: "Flagged flows", data: [], backgroundColor: "#f85149" }],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
  },
});

function renderHistory(data) {
  const normal = data.summary.Normal;
  const attack = data.summary.Attack;
  totalEl.textContent = normal + attack;
  normalEl.textContent = normal;
  attackEl.textContent = attack;

  ratioChart.data.datasets[0].data = [normal, attack];
  ratioChart.update();

  typesChart.data.labels = data.attack_types.map((item) => item.label);
  typesChart.data.datasets[0].data = data.attack_types.map((item) => item.count);
  typesChart.update();

  tbody.replaceChildren();
  for (const alert of data.alerts) {
    const row = document.createElement("tr");
    const cells = [
      new Date(alert.created_at).toLocaleString(),
      "Attack",
      alert.status,
      alert.attack_probability.toFixed(2),
      alert.true_label || "unknown (live traffic)",
    ];
    for (const text of cells) {
      const td = document.createElement("td");
      td.textContent = text;
      row.appendChild(td);
    }
    tbody.appendChild(row);
  }

  const hasAlerts = data.alerts.length > 0;
  emptyMsg.hidden = hasAlerts;
  table.hidden = !hasAlerts;
}

async function loadHistory() {
  const response = await fetch("/api/history?limit=20");
  if (response.status === 401) {
    window.location.href = "/login";
    return;
  }
  renderHistory(await response.json());
}

async function runSimulation() {
  runBtn.disabled = true;
  statusEl.textContent = "Analysing...";
  try {
    const response = await fetch("/api/simulate?n=50");
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    const data = await response.json();
    if (!response.ok) {
      statusEl.textContent = "Error: " + data.error;
      return;
    }
    await loadHistory();
    statusEl.textContent = "Done: " + data.summary.attack + " suspicious out of " + data.count;
  } catch (error) {
    statusEl.textContent = "Could not reach the server";
  } finally {
    runBtn.disabled = false;
  }
}

runBtn.addEventListener("click", runSimulation);
loadHistory().catch(() => {
  statusEl.textContent = "Could not load history";
});