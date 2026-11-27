import glob
import pandas as pd

files = sorted(glob.glob("data/raw/*.parquet"))
df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

dup_mask = df.duplicated()
print("Duplicate rows:", dup_mask.sum())
print("Duplicate %:", round(dup_mask.mean() * 100, 2))
print()

before = df["Label"].value_counts()
after = df.drop_duplicates()["Label"].value_counts()

summary = pd.DataFrame({"before": before, "after": after}).fillna(0).astype(int)
summary["removed"] = summary["before"] - summary["after"]
summary["removed_%"] = (summary["removed"] / summary["before"] * 100).round(1)

print(summary)