import math
import secrets
import time
from datetime import timedelta
from functools import wraps
from pathlib import Path

import joblib
import pandas as pd
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app import db

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL = joblib.load(BASE_DIR / "models" / "decision_tree.joblib")
FEATURE_COLUMNS = joblib.load(BASE_DIR / "models" / "feature_columns.joblib")
MAX_BATCH = 1000
DEMO_PATH = BASE_DIR / "data" / "processed" / "demo_flows.parquet"
DEMO = pd.read_parquet(DEMO_PATH) if DEMO_PATH.exists() else None

SECRET_KEY_PATH = BASE_DIR / "database" / "secret_key.txt"
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 300
failed_logins = {}


def load_secret_key():
    """Create a random secret key on first run and reuse it afterwards."""
    SECRET_KEY_PATH.parent.mkdir(exist_ok=True)
    if not SECRET_KEY_PATH.exists():
        SECRET_KEY_PATH.write_text(secrets.token_hex(32))
        SECRET_KEY_PATH.chmod(0o600)
    return SECRET_KEY_PATH.read_text().strip()


app = Flask(__name__)
app.config.update(
    SECRET_KEY=load_secret_key(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)
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


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith(("/api/", "/predict")):
                return jsonify({"error": "Login required"}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def is_locked_out(key):
    now = time.time()
    recent = [t for t in failed_logins.get(key, []) if now - t < LOCKOUT_SECONDS]
    if recent:
        failed_logins[key] = recent
    else:
        failed_logins.pop(key, None)
    return len(recent) >= MAX_FAILED_LOGINS


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.route("/")
def home():
    return "CyberGuard backend is running"


@app.route("/health")
def health():
    return {"status": "ok", "service": "CyberGuard"}


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()[:64]
        password = request.form.get("password", "")[:256]
        key = (request.remote_addr, username.lower())

        if is_locked_out(key):
            message = "Too many failed attempts. Try again in a few minutes."
            return render_template("login.html", error=message), 429

        user = db.verify_user(username, password)
        if user:
            failed_logins.pop(key, None)
            session.clear()
            session.permanent = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

        failed_logins.setdefault(key, []).append(time.time())
        error = "Invalid username or password"
    return render_template("login.html", error=error), (401 if error else 200)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username"))


@app.route("/api/simulate")
@login_required
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
@login_required
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
@login_required
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
@login_required
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