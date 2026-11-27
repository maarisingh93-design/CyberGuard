import glob
import pandas as pd

files = sorted(glob.glob("data/raw/*.parquet"))
print("Files found:", len(files))
print()

all_labels = []
for f in files:
    labels = pd.read_parquet(f, columns=["Label"])
    print(f, "->", len(labels), "rows")
    all_labels.append(labels)

combined = pd.concat(all_labels, ignore_index=True)

print()
print("Total rows:", len(combined))
print()
print(combined["Label"].value_counts())
print()
print((combined["Label"].value_counts(normalize=True) * 100).round(2))