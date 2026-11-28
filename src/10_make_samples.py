import json

import pandas as pd

test_df = pd.read_parquet("data/processed/test.parquet")
features_df = test_df.drop(columns=["Label", "is_attack"])

samples = {"benign": "Benign", "ddos": "DDoS", "portscan": "PortScan"}

for name, label in samples.items():
    row = features_df[test_df["Label"] == label].iloc[0]
    payload = {"features": row.to_dict()}
    with open(f"tests/sample_{name}.json", "w") as f:
        json.dump(payload, f, indent=2)
    print(name, "| true label:", label, "| features:", len(payload["features"]))