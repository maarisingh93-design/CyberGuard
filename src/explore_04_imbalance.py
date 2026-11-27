import glob
import pandas as pd

files = sorted(glob.glob("data/raw/*.parquet"))
labels = pd.concat(
    [pd.read_parquet(f, columns=["Label"]) for f in files],
    ignore_index=True,
)

total = len(labels)
benign = (labels["Label"] == "Benign").sum()
attack = total - benign

print("Total rows:", total)
print("Benign:", benign)
print("Attack:", attack)
print("Attack %:", round(attack / total * 100, 2))
print()
print("Accuracy of an 'always say Benign' model:", round(benign / total * 100, 2), "%")