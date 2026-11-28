import pandas as pd

test_df = pd.read_parquet("data/processed/test.parquet")

parts = [test_df[test_df["Label"] == "Benign"].sample(1000, random_state=11)]
for label, group in test_df[test_df["Label"] != "Benign"].groupby("Label"):
    parts.append(group.sample(min(100, len(group)), random_state=11))

demo = pd.concat(parts).sample(frac=1, random_state=11).reset_index(drop=True)
demo.to_parquet("data/processed/demo_flows.parquet", index=False)

print(demo.shape)
print(demo["Label"].value_counts())