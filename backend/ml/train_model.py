"""Train an optional calibrated risk model from labeled session-level features.

Usage: python ml/train_model.py --dataset /path/to/labeled_sessions.csv --label risk_label
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_model(name: str) -> object:
    if name == "logistic_regression":
        return LogisticRegression(max_iter=2000, class_weight="balanced")
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=400, min_samples_leaf=3, class_weight="balanced", random_state=42, n_jobs=-1)
    if name == "xgboost":
        try:
            from xgboost import XGBClassifier
        except ImportError as error:
            raise RuntimeError("Install xgboost to use --model xgboost") from error
        return XGBClassifier(n_estimators=300, max_depth=4, learning_rate=.05, subsample=.8, colsample_bytree=.8, random_state=42)
    if name == "lightgbm":
        try:
            from lightgbm import LGBMClassifier
        except ImportError as error:
            raise RuntimeError("Install lightgbm to use --model lightgbm") from error
        return LGBMClassifier(n_estimators=300, learning_rate=.05, random_state=42)
    raise ValueError(f"Unsupported model: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a non-clinical EyeInsight research model from a labeled CSV.")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--label", default="risk_label")
    parser.add_argument("--model", choices=("logistic_regression", "random_forest", "xgboost", "lightgbm"), default="logistic_regression")
    parser.add_argument("--output-dir", type=Path, default=Path("ml/artifacts"))
    args = parser.parse_args()
    data = pd.read_csv(args.dataset)
    if args.label not in data:
        raise ValueError(f"Label column '{args.label}' is absent from {args.dataset}")
    target = data[args.label]
    if target.nunique() < 2:
        raise ValueError("Training requires at least two label classes")
    features = data.drop(columns=[args.label]).select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan)
    if features.empty:
        raise ValueError("No numeric session features were found")
    x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=.2, random_state=42, stratify=target)
    pipeline = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", build_model(args.model))])
    pipeline.fit(x_train, y_train)
    prediction = pipeline.predict(x_test)
    metrics = {"accuracy": round(accuracy_score(y_test, prediction), 4), "precision": round(precision_score(y_test, prediction, average="weighted", zero_division=0), 4), "recall": round(recall_score(y_test, prediction, average="weighted", zero_division=0), 4), "f1": round(f1_score(y_test, prediction, average="weighted", zero_division=0), 4), "training_rows": len(x_train), "test_rows": len(x_test), "model": args.model}
    if target.nunique() == 2 and hasattr(pipeline, "predict_proba"):
        metrics["roc_auc"] = round(roc_auc_score(y_test, pipeline.predict_proba(x_test)[:, 1]), 4)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, args.output_dir / "model.pkl")
    joblib.dump(pipeline.named_steps["scaler"], args.output_dir / "scaler.pkl")
    (args.output_dir / "feature_columns.json").write_text(json.dumps(list(features.columns), indent=2), encoding="utf-8")
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
