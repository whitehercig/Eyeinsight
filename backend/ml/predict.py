"""Run a trained research model against a session_features.json artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True, type=Path)
    parser.add_argument("--artifacts", default=Path("ml/artifacts"), type=Path)
    args = parser.parse_args()
    features = json.loads(args.features.read_text(encoding="utf-8"))
    columns = json.loads((args.artifacts / "feature_columns.json").read_text(encoding="utf-8"))
    model = joblib.load(args.artifacts / "model.pkl")
    input_frame = pd.DataFrame([{column: features.get(column) for column in columns}])
    missing = [column for column in columns if features.get(column) is None]
    probability = float(model.predict_proba(input_frame)[0, 1]) if hasattr(model, "predict_proba") else None
    prediction = model.predict(input_frame)[0]
    print(json.dumps({"prediction": str(prediction), "probability": probability, "feature_coverage": round(1 - len(missing) / len(columns), 4), "missing_features": missing, "disclaimer": "Research inference only; not a medical diagnosis."}, indent=2))


if __name__ == "__main__":
    main()
