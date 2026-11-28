import sys
import textwrap
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db

OUTPUT = Path("reports/cyberguard_security_report.pdf")
PAGE = (8.27, 11.69)

MODEL_COLUMNS = ["Model", "Accuracy", "Precision", "Recall", "F1", "FP", "FN"]
MODEL_ROWS = [
    ["Decision Tree (depth 20)", "0.9991", "0.9974", "0.9968", "0.9971", "178", "215"],
    ["Random Forest", "0.9988", "0.9983", "0.9935", "0.9959", "114", "439"],
    ["Isolation Forest", "0.8548", "0.6180", "0.0968", "0.1674", "4,027", "60,784"],
]
NOTES = [
    "Scores come from one random split of CICIDS2017 (laboratory data). They do not guarantee real-network performance.",
    "Bot attacks are missed in about a third of cases and SQL Injection is not detected.",
    "Dashboard figures come from simulated traffic with about 53% attacks, not from live capture.",
    "The system does not detect all cyberattacks.",
]

summary = db.summary()
total = summary["Normal"] + summary["Attack"]
if total == 0:
    sys.exit("No detections yet. Click 'Run simulated traffic' on the dashboard first.")

types = db.attack_types()
alerts = db.recent_alerts(limit=10)

OUTPUT.parent.mkdir(exist_ok=True)
with PdfPages(OUTPUT) as pdf:
    fig = plt.figure(figsize=PAGE)
    fig.text(0.5, 0.95, "CyberGuard Security Report", ha="center", fontsize=20, weight="bold")
    fig.text(0.5, 0.925, "Generated " + datetime.now().strftime("%Y-%m-%d %H:%M"), ha="center", fontsize=10)
    fig.text(0.08, 0.88, f"Total flows analysed: {total}", fontsize=12)
    fig.text(0.08, 0.855, f"Normal: {summary['Normal']}    Suspicious: {summary['Attack']}", fontsize=12)

    pie_ax = fig.add_axes([0.08, 0.60, 0.3, 0.2])
    pie_ax.pie(
        [summary["Normal"], summary["Attack"]],
        labels=["Normal", "Suspicious"],
        colors=["#3fb950", "#f85149"],
        autopct="%1.1f%%",
    )
    pie_ax.set_title("Normal vs suspicious")

    bar_ax = fig.add_axes([0.32, 0.33, 0.6, 0.2])
    names = [t["label"] for t in types][::-1]
    counts = [t["count"] for t in types][::-1]
    bar_ax.barh(names, counts, color="#f85149")
    bar_ax.set_title("Flagged flows by attack type (simulated truth)", fontsize=10)
    bar_ax.tick_params(labelsize=7)

    table_ax = fig.add_axes([0.05, 0.05, 0.9, 0.22])
    table_ax.axis("off")
    table_ax.set_title("Latest alerts", fontsize=10)
    rows = [
        [
            a["created_at"].replace("T", " ")[:19],
            a["status"],
            f"{a['attack_probability']:.2f}",
            a["true_label"] or "unknown",
        ]
        for a in alerts
    ]
    if rows:
        tbl = table_ax.table(
            cellText=rows,
            colLabels=["Time (UTC)", "Status", "Probability", "Simulated truth"],
            loc="upper center",
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(7)
    pdf.savefig(fig)
    plt.close(fig)

    fig2 = plt.figure(figsize=PAGE)
    fig2.text(0.5, 0.95, "Model comparison (test set, 446,362 flows)", ha="center", fontsize=16, weight="bold")
    model_ax = fig2.add_axes([0.05, 0.72, 0.9, 0.18])
    model_ax.axis("off")
    model_tbl = model_ax.table(
        cellText=MODEL_ROWS,
        colLabels=MODEL_COLUMNS,
        colWidths=[0.28, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12],
        loc="center",
    )
    model_tbl.auto_set_font_size(False)
    model_tbl.set_fontsize(9)
    model_tbl.scale(1, 1.6)
    fig2.text(0.07, 0.62, "Limitations", fontsize=12, weight="bold")
    notes = "\n\n".join(textwrap.fill("- " + n, 95) for n in NOTES)
    fig2.text(0.07, 0.60, notes, fontsize=9, va="top")
    pdf.savefig(fig2)
    plt.close(fig2)

print("Saved", OUTPUT)