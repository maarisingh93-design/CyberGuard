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

let total = 0;
let normal = 0;
let attack = 0;
const typeCounts = {};

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

function updateCharts() {
  ratioChart.data.datasets[0].data = [normal, attack];
  ratioChart.update();

  const entries = Object.entries(typeCounts).sort((a, b) => b[1] - a[1]);
  typesChart.data.labels = entries.map((entry) => entry[0]);
  typesChart.data.datasets[0].data = entries.map((entry) => entry[1]);
  typesChart.update();
}

function addAlertRow(result) {
  const row = document.createElement("tr");
  const cells = [
    new Date().toLocaleTimeString(),
    result.prediction,
    result.attack_probability.toFixed(2),
    result.true_label,
  ];
  for (const text of cells) {
    const td = document.createElement("td");
    td.textContent = text;
    row.appendChild(td);
  }
  tbody.prepend(row);
  while (tbody.rows.length > 20) {
    tbody.deleteRow(tbody.rows.length - 1);
  }
}

async function runSimulation() {
  runBtn.disabled = true;
  statusEl.textContent = "Analysing...";
  try {
    const response = await fetch("/api/simulate?n=50");
    const data = await response.json();
    if (!response.ok) {
      statusEl.textContent = "Error: " + data.error;
      return;
    }

    total += data.count;
    normal += data.summary.normal;
    attack += data.summary.attack;
    totalEl.textContent = total;
    normalEl.textContent = normal;
    attackEl.textContent = attack;

    for (const result of data.results) {
      if (result.prediction === "Attack") {
        addAlertRow(result);
        typeCounts[result.true_label] = (typeCounts[result.true_label] || 0) + 1;
      }
    }
    updateCharts();

    if (tbody.rows.length > 0) {
      emptyMsg.hidden = true;
      table.hidden = false;
    }
    statusEl.textContent = "Done: " + data.summary.attack + " suspicious out of " + data.count;
  } catch (error) {
    statusEl.textContent = "Could not reach the server";
  } finally {
    runBtn.disabled = false;
  }
}

runBtn.addEventListener("click", runSimulation);