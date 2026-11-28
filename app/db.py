import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "cyberguard.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    source TEXT NOT NULL,
    model TEXT NOT NULL,
    prediction TEXT NOT NULL CHECK (prediction IN ('Normal', 'Attack')),
    attack_probability REAL NOT NULL,
    true_label TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_id INTEGER NOT NULL REFERENCES detections(id),
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged'))
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'analyst' CHECK (role IN ('admin', 'analyst')),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_detections_created ON detections(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);
"""


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def save_detections(results, source, model="decision_tree"):
    """Store classification results. Every Attack result also creates an alert."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn = get_connection()
    try:
        for r in results:
            cursor = conn.execute(
                """
                INSERT INTO detections
                    (created_at, source, model, prediction, attack_probability, true_label)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, source, model, r["prediction"], r["attack_probability"], r.get("true_label")),
            )
            if r["prediction"] == "Attack":
                conn.execute(
                    "INSERT INTO alerts (detection_id, created_at) VALUES (?, ?)",
                    (cursor.lastrowid, now),
                )
        conn.commit()
    finally:
        conn.close()


def recent_alerts(limit=20):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT alerts.id, alerts.created_at, alerts.status,
                   detections.attack_probability, detections.true_label
            FROM alerts
            JOIN detections ON detections.id = alerts.detection_id
            ORDER BY alerts.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def summary():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT prediction, COUNT(*) AS n FROM detections GROUP BY prediction"
        ).fetchall()
        result = {"Normal": 0, "Attack": 0}
        for row in rows:
            result[row["prediction"]] = row["n"]
        return result
    finally:
        conn.close()

def attack_types():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT COALESCE(detections.true_label, 'Unknown') AS label, COUNT(*) AS n
            FROM alerts
            JOIN detections ON detections.id = alerts.detection_id
            GROUP BY label
            ORDER BY n DESC
            """
        ).fetchall()
        return [{"label": row["label"], "count": row["n"]} for row in rows]
    finally:
        conn.close()   

# A fake hash used when the username does not exist, so a wrong username and
# a wrong password take about the same time to answer.
DUMMY_HASH = generate_password_hash("this-is-not-a-real-password")


def create_user(username, password, role="analyst"):
    if not 3 <= len(username) <= 32:
        raise ValueError("Username must be 3 to 32 characters")
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters")
    if role not in ("admin", "analyst"):
        raise ValueError("Role must be admin or analyst")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(password), role, now),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Username already exists") from None
    finally:
        conn.close()


def verify_user(username, password):
    """Return the user dict if the credentials are right, otherwise None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        check_password_hash(DUMMY_HASH, password)
        return None
    if not check_password_hash(row["password_hash"], password):
        return None
    return {"id": row["id"], "username": row["username"], "role": row["role"]}