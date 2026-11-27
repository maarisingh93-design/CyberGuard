import pandas as pd

file_path = "data/raw/Benign-Monday-no-metadata.parquet"
df = pd.read_parquet(file_path)

print("Shape (rows, columns):", df.shape)
print()
print(df.head())