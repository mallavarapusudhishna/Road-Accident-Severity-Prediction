from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "backend" / "ml_artifacts" / "severity_model.joblib"
PREPROCESSOR_PATH = ROOT / "models" / "preprocessor.pkl"
FEATURE_NAMES_PATH = ROOT / "models" / "feature_names.pkl"
MODEL_COMPARISON_PATH = ROOT / "models" / "model_comparison.csv"
MODEL_IMPROVEMENT_PATH = ROOT / "models" / "model_improvement_results.csv"

# ---------------------------------------------------------------------------
# Cached metadata — populated once by load_model_metadata() on first call.
# ---------------------------------------------------------------------------
_CACHED_METADATA: dict | None = None


def load_model() -> object:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model artifact missing at {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


def load_feature_names() -> list[str]:
    if not FEATURE_NAMES_PATH.exists():
        raise FileNotFoundError(f"Feature names artifact missing at {FEATURE_NAMES_PATH}")
    return joblib.load(FEATURE_NAMES_PATH)


def load_model_metadata() -> dict:
    """Return model metadata.

    The metadata is cached after the first call because all underlying
    artifacts (model file, CSVs, feature names) are static training outputs
    that never change at runtime.
    """
    global _CACHED_METADATA
    if _CACHED_METADATA is not None:
        return _CACHED_METADATA

    model = load_model()
    feature_names = load_feature_names()
    model_comparison = pd.read_csv(MODEL_COMPARISON_PATH)
    model_improvement = pd.read_csv(MODEL_IMPROVEMENT_PATH)

    _CACHED_METADATA = {
        "model_path": str(MODEL_PATH.relative_to(ROOT)),
        "preprocessor_path": str(PREPROCESSOR_PATH.relative_to(ROOT)),
        "feature_names_count": len(feature_names),
        "feature_names": feature_names,
        "model_type": type(model).__name__,
        "pipeline_steps": list(model.named_steps.keys()) if hasattr(model, "named_steps") else [],
        "model_comparison": model_comparison.to_dict(orient="records"),
        "model_improvement_results": model_improvement.to_dict(orient="records"),
        "severity_label_map": {
            0: "Minor",
            1: "Serious",
            2: "Fatal",
        },
    }
    return _CACHED_METADATA
