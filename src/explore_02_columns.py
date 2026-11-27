import pandas as pd

file_path = "data/raw/DDoS-Friday-no-metadata.parquet"
df = pd.read_parquet(file_path)

print("Total columns:", len(df.columns))
print()

for i, col in enumerate(df.columns):
    print(i, col)

print()
print("Label counts:")
print(df["Label"].value_counts())