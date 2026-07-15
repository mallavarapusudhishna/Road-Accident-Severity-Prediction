from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODEL_COMPARISON_PATH = ROOT / "models" / "model_comparison.csv"
MODEL_IMPROVEMENT_PATH = ROOT / "models" / "model_improvement_results.csv"
PROCESSED_DATA_PATH = ROOT / "data" / "processed" / "final_dataframe.pkl"

logger = logging.getLogger(__name__)

# Map numeric severity codes (from training) to human-readable labels.
_SEVERITY_LABEL_MAP = {0: "Minor", 1: "Serious", 2: "Fatal"}

# ---------------------------------------------------------------------------
# Cached statistics — populated once by build_statistics_payload() on first
# call.  All underlying data (training CSVs, processed DataFrame) are static
# artifacts that never change at runtime.
# ---------------------------------------------------------------------------
_CACHED_STATISTICS: dict | None = None


def _load_processed_dataframe() -> pd.DataFrame:
    import joblib

    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {PROCESSED_DATA_PATH}. "
            f"Please run the preprocessing notebook first."
        )
    return joblib.load(PROCESSED_DATA_PATH)


def _normalize_severity_distribution(raw_dist: dict) -> dict:
    """Ensure severity distribution uses string labels, not numeric codes.

    The processed dataframe may use numeric severity codes (0, 1, 2) or
    string labels ('Minor', 'Serious', 'Fatal') depending on the
    preprocessing pipeline.  The frontend expects string keys.
    """
    normalised: dict[str, int] = {}
    for key, count in raw_dist.items():
        if isinstance(key, (int, float)):
            label = _SEVERITY_LABEL_MAP.get(int(key), f"Unknown({key})")
        else:
            label = str(key)
        normalised[label] = int(count)
    return normalised


def build_statistics_payload() -> dict:
    """Return statistics about the training dataset and model comparison.

    Cached after first call to avoid re-reading three files from disk on
    every ``GET /statistics`` request.
    """
    global _CACHED_STATISTICS
    if _CACHED_STATISTICS is not None:
        return _CACHED_STATISTICS

    model_comparison = pd.read_csv(MODEL_COMPARISON_PATH)
    improvement_results = pd.read_csv(MODEL_IMPROVEMENT_PATH)
    processed_df = _load_processed_dataframe()

    # Determine the severity column name (handles both old and new schemas)
    if "severity" in processed_df.columns:
        sev_col = "severity"
    elif "target_severity" in processed_df.columns:
        sev_col = "target_severity"
    else:
        sev_col = processed_df.columns[-1]
        logger.warning("Could not find severity column, using last column: %s", sev_col)

    raw_distribution = processed_df[sev_col].value_counts().to_dict()

    _CACHED_STATISTICS = {
        "records": int(len(processed_df)),
        "severity_distribution": _normalize_severity_distribution(raw_distribution),
        "model_comparison": model_comparison.to_dict(orient="records"),
        "model_improvement_results": improvement_results.to_dict(orient="records"),
        "dataset_columns": list(processed_df.columns),
    }
    return _CACHED_STATISTICS
