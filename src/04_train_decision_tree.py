import time
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

train_df = pd.read_parquet("data/processed/train.parquet")
test_df = pd.read_parquet("data/processed/test.parquet")

drop_cols = ["Label", "is_attack"]
X_train = train_df.drop(columns=drop_cols)
y_train = train_df["is_attack"]
X_test = test_df.drop(columns=drop_cols)
y_test = test_df["is_attack"]

print("Number of features:", X_train.shape[1])

model = DecisionTreeClassifier(max_depth=10, random_state=42)

start = time.time()
model.fit(X_train, y_train)
print("Training time (sec):", round(time.time() - start, 1))

y_pred = model.predict(X_test)

print()
print("Accuracy :", round(accuracy_score(y_test, y_pred), 4))
print("Precision:", round(precision_score(y_test, y_pred), 4))
print("Recall   :", round(recall_score(y_test, y_pred), 4))
print("F1-score :", round(f1_score(y_test, y_pred), 4))
print()
print("Confusion matrix [[TN, FP], [FN, TP]]:")
print(confusion_matrix(y_test, y_pred))