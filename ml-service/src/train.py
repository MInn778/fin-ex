"""Train and evaluate the XGBoost stage-1 classifier from a labelled CSV."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from .features import FEATURE_NAMES, feature_vector


def train(csv_path: Path, output_path: Path) -> None:
    data = pd.read_csv(csv_path)
    if not {"url", "label"}.issubset(data.columns):
        raise ValueError("CSV must contain url and label columns")
    labels = data["label"].astype(int).to_numpy()
    if set(np.unique(labels)) != {0, 1}:
        raise ValueError("label must contain both 0 (normal) and 1 (phishing)")

    features = np.asarray([feature_vector(url) for url in data["url"].astype(str)], dtype=float)
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, random_state=42, stratify=labels
    )
    model = XGBClassifier(
        n_estimators=350, max_depth=6, learning_rate=0.05, subsample=0.85,
        colsample_bytree=0.85, eval_metric="logloss", random_state=42, n_jobs=-1,
    )
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    print(classification_report(y_test, probabilities >= 0.5, digits=4))
    print(f"ROC-AUC: {roc_auc_score(y_test, probabilities):.4f}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "feature_names": FEATURE_NAMES,
            "version": datetime.now(timezone.utc).strftime("xgb-%Y%m%d-%H%M%S"),
        },
        output_path,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True, help="CSV with url,label columns")
    parser.add_argument("--output", type=Path, default=Path("artifacts/url_xgb.joblib"))
    arguments = parser.parse_args()
    train(arguments.data, arguments.output)

