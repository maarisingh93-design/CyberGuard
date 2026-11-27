import time
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import f1_score, recall_score

train_df = pd.read_parquet("data/processed/train.parquet")
test_df = pd.read_parquet("data/processed/test.parquet")

drop_cols = ["Label", "is_attack"]
X_train = train_df.drop(columns=drop_cols)
y_train = train_df["is_attack"]
X_test = test_df.drop(columns=drop_cols)
y_test = test_df["is_attack"]

for depth in [3, 10, 20, None]:
    start = time.time()
    model = DecisionTreeClassifier(max_depth=depth, random_state=42)
    model.fit(X_train, y_train)
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    print(
        "depth", depth,
        "| train F1", round(f1_score(y_train, train_pred), 4),
        "| test F1", round(f1_score(y_test, test_pred), 4),
        "| train recall", round(recall_score(y_train, train_pred), 4),
        "| test recall", round(recall_score(y_test, test_pred), 4),
        "| time", round(time.time() - start, 1),
        flush=True,
    )