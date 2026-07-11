# EyeInsight ML Training Seam

The running MVP uses deterministic, explainable screening rules because no validated labeled dataset is bundled with this repository. `backend/ml/` prepares a conventional supervised-learning handoff once appropriate, consented, representative data exists.

## Train

Provide one labeled row per session, containing numeric columns from `session_features.csv` and a label column such as `risk_label`.

```bash
cd backend
python ml/train_model.py --dataset /path/to/labeled_sessions.csv --label risk_label --model logistic_regression
```

Supported models are `logistic_regression`, `random_forest`, `xgboost` (optional dependency), and `lightgbm` (optional dependency). The script produces `model.pkl`, `scaler.pkl`, `feature_columns.json`, and `metrics.json`; it reports accuracy, precision, recall, F1, and ROC AUC for binary labels.

## Predict

```bash
python ml/predict.py --features features/SESSION_ID/session_features.json --artifacts ml/artifacts
```

The predictor aligns required columns and reports missing feature coverage. A trained model must not be connected to user-facing screening until it has undergone ethics review, calibration, external validation, subgroup analysis, and clinical/regulatory review appropriate to its use.
