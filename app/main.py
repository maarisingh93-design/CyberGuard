import math
from pathlib import Path
from unittest import result

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request
from app import db

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL = joblib.load(BASE_DIR / "models" / "decision_tree.joblib")
FEATURE_COLUMNS = joblib.load(BASE_DIR / "models" / "feature_columns.joblib")
MAX_BATCH = 1000
DEMO_PATH = BASE_DIR / "data" / "processed" / "demo_flows.parquet"
DEMO = pd.read_parquet(DEMO_PATH) if DEMO_PATH.exists() else None


app = Flask(__name__)

db.init_db()

def features_to_values(features):
    """Return (values, error_message). Exactly one of them is None."""
    if not isinstance(features, dict):
        return None, "Each flow must be a JSON object"
    missing = [c for c in FEATURE_COLUMNS if c not in features]
    if missing:
        return None, f"Missing {len(missing)} features, e.g. {missing[:3]}"
    try:
        values = [float(features[c]) for c in FEATURE_COLUMNS]
    except (TypeError, ValueError):
        return None, "All feature values must be numbers"
    if not all(math.isfinite(v) for v in values):
        return None, "Feature values must be finite numbers"
    return values, None


def classify(rows):
    frame = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    predictions = MODEL.predict(frame)
    probabilities = MODEL.predict_proba(frame)[:, 1]
    return [
        {
            "prediction": "Attack" if int(p) == 1 else "Normal",
            "attack_probability": round(float(prob), 4),
        }
        for p, prob in zip(predictions, probabilities)
    ]


@app.route("/")
def home():
    return "CyberGuard backend is running"


@app.route("/health")
def health():
    return {"status": "ok", "service": "CyberGuard"}

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/simulate")
def simulate():
    if DEMO is None:
        return jsonify({"error": "Run src/12_make_demo_flows.py first"}), 503

    n = request.args.get("n", default=50, type=int)
    n = max(1, min(n, 200))
    batch = DEMO.sample(n)

    rows = batch[FEATURE_COLUMNS].astype(float).values.tolist()
    results = classify(rows)
    for result, label in zip(results, batch["Label"]):
        result["true_label"] = label
    db.save_detections(results, source="simulation")
    attacks = sum(r["prediction"] == "Attack" for r in results)
    return jsonify(
        {
            "count": n,
            "summary": {"normal": n - attacks, "attack": attacks},
            "results": results,
        }
    )

@app.route("/api/history")
def history():
    limit = request.args.get("limit", default=20, type=int)
    limit = max(1, min(limit, 100))
    return jsonify(
        {
            "summary": db.summary(),
            "attack_types": db.attack_types(),
            "alerts": db.recent_alerts(limit),
        }
    )

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "features" not in data:
        return jsonify({"error": "Send JSON with a 'features' object"}), 400
    values, error = features_to_values(data["features"])
    if error:
        return jsonify({"error": error}), 400
    result = classify([values])[0]
    db.save_detections([result], source="api")
    return jsonify(result)

@app.route("/predict_batch", methods=["POST"])
def predict_batch():
    data = request.get_json(silent=True)
    flows = data.get("flows") if isinstance(data, dict) else None
    if not isinstance(flows, list) or not flows:
        return jsonify({"error": "Send JSON with a non-empty 'flows' list"}), 400
    if len(flows) > MAX_BATCH:
        return jsonify({"error": f"Maximum {MAX_BATCH} flows per request"}), 400

    rows = []
    for i, features in enumerate(flows):
        values, error = features_to_values(features)
        if error:
            return jsonify({"error": f"Flow {i}: {error}"}), 400
        rows.append(values)

    results = classify(rows)
    db.save_detections(results, source="api")
    attacks = sum(r["prediction"] == "Attack" for r in results)
    return jsonify(
        {
            "count": len(results),
            "summary": {"normal": len(results) - attacks, "attack": attacks},
            "results": results,
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)