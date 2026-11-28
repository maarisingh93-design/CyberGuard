import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db

db.init_db()

conn = db.get_connection()
tables = [r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
conn.close()
print("Tables:", tables)

before = db.summary()
db.save_detections(
    [
        {"prediction": "Normal", "attack_probability": 0.0, "true_label": "Benign"},
        {"prediction": "Attack", "attack_probability": 1.0, "true_label": "DDoS"},
        {"prediction": "Attack", "attack_probability": 0.92, "true_label": "DoS Slowhttptest"},
    ],
    source="test",
)
after = db.summary()
print("Before:", before)
print("After :", after)
print()
for alert in db.recent_alerts(limit=5):
    print(alert)
    