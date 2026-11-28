import math
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL = joblib.load(BASE_DIR / "models" / "decision_tree.joblib")
FEATURE_COLUMNS = joblib.load(BASE_DIR / "models" / "feature_columns.joblib")

app = Flask(__name__)


@app.route("/")
def home():
    return "CyberGuard backend is running"


@app.route("/health")
def health():
    return {"status": "ok", "service": "CyberGuard"}


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("features"), dict):
        return jsonify({"error": "Send JSON with a 'features' object"}), 400

    features = data["features"]
    missing = [c for c in FEATURE_COLUMNS if c not in features]
    if missing:
        return jsonify(
            {
                "error": "Missing features",
                "missing_count": len(missing),
                "examples": missing[:3],
            }
        ), 400

    try:
        values = [float(features[c]) for c in FEATURE_COLUMNS]
    except (TypeError, ValueError):
        return jsonify({"error": "All feature values must be numbers"}), 400
    if not all(math.isfinite(v) for v in values):
        return jsonify({"error": "Feature values must be finite numbers"}), 400

    row = pd.DataFrame([values], columns=FEATURE_COLUMNS)
    prediction = int(MODEL.predict(row)[0])
    attack_probability = float(MODEL.predict_proba(row)[0][1])

    return jsonify(
        {
            "prediction": "Attack" if prediction == 1 else "Normal",
            "attack_probability": round(attack_probability, 4),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)