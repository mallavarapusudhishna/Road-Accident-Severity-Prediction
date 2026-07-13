from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from backend.models.schemas import PredictionRequest, PredictionResponse
from backend.services.model_service import load_feature_names, load_model

ROOT = Path(__file__).resolve().parents[2]
SEVERITY_LABELS = {0: "Minor", 1: "Serious", 2: "Fatal"}


def _derived_time_of_day(accident_hour: int) -> str:
    if 0 <= accident_hour < 5:
        return "Late Night"
    if 5 <= accident_hour < 12:
        return "Morning"
    if 12 <= accident_hour < 17:
        return "Afternoon"
    return "Evening"


def _driver_age_group(driver_age: int) -> str:
    if driver_age < 25:
        return "Young"
    if driver_age <= 60:
        return "Adult"
    return "Senior"


def _build_feature_frame(payload: PredictionRequest) -> pd.DataFrame:
    input_payload = payload.model_dump()
    accident_hour = pd.to_datetime(input_payload["time"], format="%H:%M", errors="coerce").hour
    if pd.isna(accident_hour):
        raise ValueError("time must be a valid HH:MM value")

    input_payload["speed_limit_(km/h)"] = input_payload.pop("speed_limit_kmh")
    input_payload["accident_hour"] = int(accident_hour)
    input_payload["time_of_day"] = _derived_time_of_day(int(accident_hour))
    input_payload["driver_age_group"] = _driver_age_group(int(input_payload["driver_age"]))
    input_payload["is_multi_vehicle"] = "Yes" if int(input_payload["num_vehicles"]) > 1 else "No"
    input_payload["is_weekend"] = "Yes" if input_payload["day_of_week"] in {"Saturday", "Sunday"} else "No"
    input_payload["is_night"] = "Yes" if int(accident_hour) >= 20 or int(accident_hour) < 6 else "No"
    input_payload["is_peak_hour"] = "Yes" if 7 <= int(accident_hour) <= 10 or 17 <= int(accident_hour) <= 20 else "No"

    input_payload["driver_license_status"] = input_payload.get("driver_license_status") or "Valid"
    input_payload["city"] = input_payload.get("city") or "Unknown"
    input_payload["road_condition"] = input_payload.get("road_condition") or "Under Construction"
    input_payload["lighting_conditions"] = input_payload.get("lighting_conditions") or "Dark"
    input_payload["traffic_control_presence"] = input_payload.get("traffic_control_presence") or "Signs"
    input_payload["accident_location_details"] = input_payload.get("accident_location_details") or "Intersection"

    frame = pd.DataFrame([input_payload])
    return frame


def predict_from_request(payload: PredictionRequest) -> PredictionResponse:
    model = load_model()
    feature_names = load_feature_names()
    frame = _build_feature_frame(payload)

    if "feature_names_in_" in dir(model):
        feature_names_in = list(model.feature_names_in_)
    else:
        feature_names_in = feature_names

    frame = frame.reindex(columns=feature_names_in, fill_value=np.nan)

    prediction = int(model.predict(frame)[0])
    predicted_severity = SEVERITY_LABELS[prediction]
    confidence_scores = model.predict_proba(frame)[0]
    confidence = float(np.max(confidence_scores))

    return PredictionResponse(
        predicted_severity=predicted_severity,
        confidence=confidence,
    )
