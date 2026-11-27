import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_parquet("data/processed/cyberguard_clean.parquet")

train_df, test_df = train_test_split(
    df,
    test_size=0.2,
    stratify=df["Label"],
    random_state=42,
)

print("Train:", train_df.shape)
print("Test :", test_df.shape)
print()
print("Attack % in train:", round(train_df["is_attack"].mean() * 100, 2))
print("Attack % in test :", round(test_df["is_attack"].mean() * 100, 2))
print()
print("Rarest labels in test set:")
print(test_df["Label"].value_counts().tail(4))

train_df.to_parquet("data/processed/train.parquet", index=False)
test_df.to_parquet("data/processed/test.parquet", index=False)
print()
print("Saved train.parquet and test.parquet")