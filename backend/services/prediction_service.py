from __future__ import annotations

import time
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from backend.models.schemas import PredictionRequest, PredictionResponse
from backend.services.model_service import load_feature_names, load_model
from backend.services.helpers import build_derived_fields

ROOT = Path(__file__).resolve().parents[2]
SEVERITY_LABELS = {0: "Minor", 1: "Serious", 2: "Fatal"}
logger = logging.getLogger(__name__)


def _build_feature_frame(payload: PredictionRequest, feature_names_in: list) -> tuple[pd.DataFrame, dict]:
    input_payload = payload.model_dump()
    derived = build_derived_fields(payload)

    # Set exact feature column name expected by the preprocessor
    input_payload["speed_limit_(km/h)"] = input_payload.pop("speed_limit_kmh")
    input_payload.update(derived)

    # Apply defaults for columns excluded from simplified form
    input_payload["city"] = input_payload.get("city") or "Unknown"
    input_payload["road_condition"] = input_payload.get("road_condition") or "Under Construction"
    input_payload["lighting_conditions"] = input_payload.get("lighting_conditions") or "Dark"
    input_payload["accident_location_details"] = input_payload.get("accident_location_details") or "Intersection"
    input_payload["driver_gender"] = input_payload.get("driver_gender") or "Male"

    # Map None / "Unknown" to np.nan for fields trained with NaN as a category.
    # The OneHotEncoder was fit on data where driver_license_status and
    # traffic_control_presence contained NaN values as a distinct category.
    # Sending the string "Unknown" would hit handle_unknown="ignore" (all
    # zeros), losing the signal.  Mapping to NaN matches the trained category.
    dls = input_payload.get("driver_license_status")
    if dls is None or dls == "Unknown":
        input_payload["driver_license_status"] = np.nan

    tcp = input_payload.get("traffic_control_presence")
    if tcp is None or tcp == "Unknown":
        input_payload["traffic_control_presence"] = np.nan

    # Build DataFrame already in the correct column order — avoids a separate
    # reindex() pass (saves ~1 ms per request on a 25-column frame).
    ordered = {k: input_payload.get(k, 0) for k in feature_names_in}
    frame = pd.DataFrame([ordered])
    return frame, derived


def _build_friendly_feature_explanation(fname: str, sval: float, payload: PredictionRequest) -> str:
    direction = "increased" if sval >= 0 else "decreased"
    
    # Identify the base feature and map it
    if fname.startswith("state_"):
        state_name = fname.replace("state_", "")
        phrase = f"the accident occurring in {state_name}"
    elif fname.startswith("city_"):
        city_name = fname.replace("city_", "")
        phrase = f"the accident occurring in {city_name}"
    elif fname.startswith("vehicle_type_"):
        vtype = fname.replace("vehicle_type_", "")
        phrase = f"the involvement of a {vtype}"
    elif fname.startswith("weather_"):
        weather = fname.replace("weather_", "")
        phrase = f"weather conditions being {weather.lower()}"
    elif fname.startswith("road_type_"):
        rtype = fname.replace("road_type_", "")
        phrase = f"driving on a {rtype}"
    elif fname.startswith("road_condition_"):
        rcond = fname.replace("road_condition_", "")
        phrase = f"road conditions being {rcond.lower()}"
    elif fname.startswith("lighting_conditions_"):
        light = fname.replace("lighting_conditions_", "")
        phrase = f"lighting conditions being {light.lower()}"
    elif fname.startswith("traffic_control_presence_"):
        traffic = fname.replace("traffic_control_presence_", "")
        if traffic == "nan":
            traffic = "unknown"
        phrase = f"traffic control presence ({traffic.lower()})"
    elif fname.startswith("driver_license_status_"):
        lic = fname.replace("driver_license_status_", "")
        phrase = f"the driver having a/an {lic.lower()} license"
    elif fname.startswith("alcohol_involved_"):
        alc = fname.replace("alcohol_involved_", "")
        phrase = f"alcohol involvement being '{alc}'"
    elif fname.startswith("accident_location_details_"):
        loc = fname.replace("accident_location_details_", "")
        phrase = f"the accident location details ({loc.lower()})"
    elif fname.startswith("time_of_day_"):
        tod = fname.replace("time_of_day_", "")
        phrase = f"occurring during the {tod.lower()}"
    elif fname.startswith("driver_age_group_"):
        grp = fname.replace("driver_age_group_", "")
        phrase = f"the driver being a/an {grp.lower()}"
    elif fname.startswith("is_multi_vehicle_"):
        mv = fname.replace("is_multi_vehicle_", "")
        phrase = "multiple vehicles being involved" if mv == "Yes" else "a single vehicle being involved"
    elif fname.startswith("is_weekend_"):
        wk = fname.replace("is_weekend_", "")
        phrase = "occurring on the weekend" if wk == "Yes" else "occurring on a weekday"
    elif fname.startswith("is_night_"):
        nt = fname.replace("is_night_", "")
        phrase = "occurring at night-time" if nt == "Yes" else "occurring during daylight hours"
    elif fname.startswith("is_peak_hour_"):
        ph = fname.replace("is_peak_hour_", "")
        phrase = "occurring during peak traffic hours" if ph == "Yes" else "occurring during off-peak hours"
    elif fname.startswith("day_of_week_"):
        dow = fname.replace("day_of_week_", "")
        phrase = f"occurring on a {dow}"
    elif fname.startswith("month_"):
        mth = fname.replace("month_", "")
        phrase = f"occurring in {mth}"
    elif fname == "speed_limit_(km/h)" or fname == "speed_limit_kmh":
        phrase = f"the speed limit of {payload.speed_limit_kmh} km/h"
    elif fname == "driver_age":
        phrase = f"the driver's age of {payload.driver_age} years"
    elif fname == "num_vehicles":
        phrase = f"{payload.num_vehicles} vehicle(s) being involved"
    elif fname == "year":
        phrase = f"the accident year {payload.year}"
    else:
        phrase = fname.replace("_", " ")

    return f"factors related to {phrase} {direction}"


# ---------------------------------------------------------------------------
# Global cache — populated once at startup by init_prediction_service().
# ---------------------------------------------------------------------------
_MODEL = None
_FEATURE_NAMES = None           # list[str] – 137 post-OHE feature names (matches preprocessor output)
_FEATURE_NAMES_IN = None        # list[str] – 25 raw input feature names (pipeline order)
_FEATURE_NAME_TO_IDX = None     # dict[str, int] – O(1) lookup for _is_active_feature
_EXPLAINER = None
_INIT_FAILED = False            # Flag to prevent repeated init attempts after a fatal failure


def init_prediction_service() -> None:
    """Load all heavy artifacts exactly once at application startup."""
    global _MODEL, _FEATURE_NAMES, _FEATURE_NAMES_IN, _FEATURE_NAME_TO_IDX, _EXPLAINER, _INIT_FAILED

    t_start = time.perf_counter()

    try:
        if _MODEL is None:
            _MODEL = load_model()

        if _FEATURE_NAMES is None:
            _FEATURE_NAMES = load_feature_names()

        # Cache the ordered input-feature list used for DataFrame construction.
        if _FEATURE_NAMES_IN is None:
            if hasattr(_MODEL, "feature_names_in_"):
                _FEATURE_NAMES_IN = list(_MODEL.feature_names_in_)
            else:
                _FEATURE_NAMES_IN = _FEATURE_NAMES

        # Pre-build a dict for O(1) index lookups inside _is_active_feature.
        if _FEATURE_NAME_TO_IDX is None:
            _FEATURE_NAME_TO_IDX = {name: idx for idx, name in enumerate(_FEATURE_NAMES)}

        if _EXPLAINER is None:
            import shap

            if not hasattr(_MODEL, "named_steps") or "model" not in _MODEL.named_steps:
                raise RuntimeError(
                    "Model pipeline does not have a 'model' step. "
                    "Cannot create SHAP explainer."
                )
            clf = _MODEL.named_steps["model"]
            _EXPLAINER = shap.TreeExplainer(clf)

        _INIT_FAILED = False
        logger.info(
            "init_prediction_service completed in %.0f ms",
            (time.perf_counter() - t_start) * 1000.0,
        )
    except Exception:
        _INIT_FAILED = True
        logger.exception("init_prediction_service FAILED — predictions will be unavailable")
        raise


def predict_from_request(
    payload: PredictionRequest,
) -> tuple[PredictionResponse, dict[str, float], dict]:
    """Run the full prediction pipeline.

    Returns
    -------
    prediction : PredictionResponse
    timings    : dict[str, float]  – per-stage millisecond timings
    derived    : dict              – fields computed from payload (reused by DB layer
                                    to avoid a duplicate build_derived_fields call)
    """
    global _MODEL, _FEATURE_NAMES, _FEATURE_NAMES_IN, _FEATURE_NAME_TO_IDX, _EXPLAINER

    # Lazy-init guard (should not be hit after startup, kept as a safety net)
    if _MODEL is None or _FEATURE_NAMES is None or _EXPLAINER is None:
        if _INIT_FAILED:
            raise RuntimeError(
                "Prediction service failed to initialise. "
                "Check logs for details."
            )
        init_prediction_service()

    timings: dict[str, float] = {}

    # ------------------------------------------------------------------
    # 1. Payload → feature frame
    # ------------------------------------------------------------------
    t_frame_start = time.perf_counter()

    # _build_feature_frame now returns the derived dict so we can reuse it
    # in the DB layer without a second call to build_derived_fields().
    frame, derived = _build_feature_frame(payload, _FEATURE_NAMES_IN)

    timings["frame_build"] = (time.perf_counter() - t_frame_start) * 1000.0

    # ------------------------------------------------------------------
    # 2. Preprocessing  (ColumnTransformer — sklearn internal)
    # ------------------------------------------------------------------
    t_preprocess_start = time.perf_counter()

    preprocessor = _MODEL.named_steps["preprocess"]
    X_proc = preprocessor.transform(frame)
    if hasattr(X_proc, "toarray"):
        X_proc = X_proc.toarray()

    timings["preprocessing"] = (time.perf_counter() - t_preprocess_start) * 1000.0

    # ------------------------------------------------------------------
    # 3. Prediction
    # ------------------------------------------------------------------
    t_pred_start = time.perf_counter()

    clf = _MODEL.named_steps["model"]
    confidence_scores = clf.predict_proba(X_proc)[0]
    prediction = int(np.argmax(confidence_scores))
    predicted_severity = SEVERITY_LABELS[prediction]
    confidence = float(np.max(confidence_scores))

    probabilities = {
        "Minor": float(confidence_scores[0]),
        "Serious": float(confidence_scores[1]),
        "Fatal": float(confidence_scores[2]),
    }

    timings["prediction"] = (time.perf_counter() - t_pred_start) * 1000.0

    # ------------------------------------------------------------------
    # 4. SHAP explanation
    # ------------------------------------------------------------------
    t_shap_start = time.perf_counter()
    top_features: list[str] = []
    shap_values_map: dict[str, float] = {}
    human_explanation = ""

    try:
        sv = _EXPLAINER.shap_values(X_proc, approximate=True)
        t_shap_values_done = time.perf_counter()

        # sv shape is (n_samples, n_features, n_classes)
        raw_shap = sv[0, :, prediction]
        abs_vals = np.abs(raw_shap)
        X_row = X_proc[0]

        def _is_active_feature(feature_name: str) -> bool:
            """Return True for numerical features and for active (==1) one-hot categories."""
            if "_" not in feature_name:
                return True
            idx = _FEATURE_NAME_TO_IDX.get(feature_name, -1)
            if idx == -1:
                return True
            val = X_row[idx]
            return float(val) == 1.0 or abs(float(val)) > 0.9999

        # --- Input-specific categorical prefixes (things the user actually selected) ---
        _CATEGORICAL_PREFIXES = (
            "state_", "vehicle_type_", "weather_", "road_type_",
            "road_condition_", "lighting_conditions_", "traffic_control_presence_",
            "accident_location_details_", "driver_license_status_", "alcohol_involved_",
        )
        # Derived/contextual prefixes (computed, not directly user-chosen)
        _DERIVED_PREFIXES = (
            "is_weekend_", "is_night_", "is_peak_hour_", "is_multi_vehicle_",
            "time_of_day_", "driver_age_group_", "day_of_week_", "month_",
        )

        # 1. Collect ALL active features (not just top-12) for accurate pool
        all_active_idx = [
            i for i in range(len(_FEATURE_NAMES))
            if _is_active_feature(_FEATURE_NAMES[i])
        ]

        # 2. Sort by absolute SHAP within each pool
        all_active_idx.sort(key=lambda i: abs_vals[i], reverse=True)

        # Separate into three pools
        categorical_idx = [
            i for i in all_active_idx
            if any(_FEATURE_NAMES[i].startswith(p) for p in _CATEGORICAL_PREFIXES)
        ]
        derived_idx = [
            i for i in all_active_idx
            if any(_FEATURE_NAMES[i].startswith(p) for p in _DERIVED_PREFIXES)
        ]
        numerical_idx = [
            i for i in all_active_idx
            if not any(_FEATURE_NAMES[i].startswith(p)
                       for p in _CATEGORICAL_PREFIXES + _DERIVED_PREFIXES)
        ]

        # 3. Build a balanced top-5 selection:
        #    - up to 2 top user-specific categorical features
        #    - up to 2 top numerical features (speed, age, num_vehicles, year)
        #    - up to 1 derived feature (weekend/night/peak)
        selected: list[int] = []
        seen: set[int] = set()

        def _add(pool: list[int], limit: int) -> None:
            added = 0
            for i in pool:
                if i not in seen and added < limit:
                    # Skip features with essentially zero SHAP (adds no info)
                    if abs_vals[i] < 1e-6 and added > 0:
                        continue
                    selected.append(i)
                    seen.add(i)
                    added += 1

        _add(categorical_idx, 2)
        _add(numerical_idx, 2)
        _add(derived_idx, 1)

        # Fill remaining slots (up to 5 total) from the overall active pool
        for i in all_active_idx:
            if len(selected) >= 5:
                break
            if i not in seen:
                selected.append(i)
                seen.add(i)

        # Sort final selection by absolute SHAP for display
        selected.sort(key=lambda i: abs_vals[i], reverse=True)

        top_features = [_FEATURE_NAMES[i] for i in selected]
        shap_values_map = {_FEATURE_NAMES[i]: float(raw_shap[i]) for i in selected}

        # Generate custom natural-language explanation
        pieces = [
            _build_friendly_feature_explanation(_FEATURE_NAMES[i], float(raw_shap[i]), payload)
            for i in selected
        ]

        if len(pieces) == 1:
            human_explanation = (
                f"The model predicted a {predicted_severity.lower()} severity risk level. "
                f"The key factor influencing this prediction was {pieces[0]}."
            )
        elif len(pieces) == 2:
            human_explanation = (
                f"The model predicted a {predicted_severity.lower()} severity risk level. "
                f"The key factors were: {pieces[0]} and {pieces[1]}."
            )
        elif pieces:
            human_explanation = (
                f"The model predicted a {predicted_severity.lower()} severity risk level. "
                f"The key factors were: {', '.join(pieces[:-1])}, and {pieces[-1]}."
            )
        else:
            human_explanation = (
                f"The model predicted a {predicted_severity.lower()} severity risk level "
                f"based on the inputted accident factors."
            )

        timings["shap_values"] = (t_shap_values_done - t_shap_start) * 1000.0
        timings["shap_postprocess"] = (time.perf_counter() - t_shap_values_done) * 1000.0

    except Exception:
        logger.exception("SHAP explanation failed for this prediction request")
        human_explanation = (
            f"The model predicted a {predicted_severity.lower()} severity risk level based on the "
            f"inputted accident factors. SHAP explanation was unavailable for this request."
        )
        timings["shap_values"] = (time.perf_counter() - t_shap_start) * 1000.0
        timings["shap_postprocess"] = 0.0

    timings["shap"] = timings["shap_values"] + timings["shap_postprocess"]

    resp = PredictionResponse(
        predicted_severity=predicted_severity,
        confidence=confidence,
        probabilities=probabilities,
        top_contributing_features=top_features,
        shap_values=shap_values_map,
        human_readable_explanation=human_explanation,
    )

    # Return derived so the DB layer can reuse it without a second computation.
    return resp, timings, derived
