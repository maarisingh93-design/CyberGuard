import pandas as pd
import requests

URL = "http://127.0.0.1:5000/predict_batch"

test_df = pd.read_parquet("data/processed/test.parquet")
benign = test_df[test_df["is_attack"] == 0].sample(300, random_state=7)
attack = test_df[test_df["is_attack"] == 1].sample(200, random_state=7)
sample = pd.concat([benign, attack]).sample(frac=1, random_state=7)

features = sample.drop(columns=["Label", "is_attack"])
payload = {"flows": features.to_dict(orient="records")}

response = requests.post(URL, json=payload, timeout=30)
print("HTTP", response.status_code)
body = response.json()
print("Summary from API:", body["summary"])

sample = sample.copy()
sample["pred"] = [r["prediction"] for r in body["results"]]
sample["prob"] = [r["attack_probability"] for r in body["results"]]
sample["truth"] = sample["is_attack"].map({0: "Normal", 1: "Attack"})

print()
print(pd.crosstab(sample["truth"], sample["pred"]))

print()
sure = ((sample["prob"] == 0.0) | (sample["prob"] == 1.0)).mean() * 100
print("Probability exactly 0 or 1:", round(sure, 1), "%")
print("Flows with probability in between:", int(((sample["prob"] > 0) & (sample["prob"] < 1)).sum()))