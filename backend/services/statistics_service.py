from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODEL_COMPARISON_PATH = ROOT / "models" / "model_comparison.csv"
MODEL_IMPROVEMENT_PATH = ROOT / "models" / "model_improvement_results.csv"
PROCESSED_DATA_PATH = ROOT / "data" / "processed" / "final_dataframe.pkl"


def _load_processed_dataframe() -> pd.DataFrame:
    import joblib

    return joblib.load(PROCESSED_DATA_PATH)


def build_statistics_payload() -> dict:
    model_comparison = pd.read_csv(MODEL_COMPARISON_PATH)
    improvement_results = pd.read_csv(MODEL_IMPROVEMENT_PATH)
    processed_df = _load_processed_dataframe()

    return {
        "records": int(len(processed_df)),
        "severity_distribution": processed_df["severity"].value_counts().to_dict(),
        "model_comparison": model_comparison.to_dict(orient="records"),
        "model_improvement_results": improvement_results.to_dict(orient="records"),
        "dataset_columns": list(processed_df.columns),
    }
