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
      }
    }
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