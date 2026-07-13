from __future__ import annotations

import json

from backend.database import session
from backend.database.models import AccidentRecord, PredictionRecord
from backend.models.schemas import PredictionRequest


def _derive_time_of_day(accident_hour: int) -> str:
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


def _build_derived_fields(payload: PredictionRequest) -> dict:
    import pandas as pd

    accident_hour = pd.to_datetime(payload.time, format="%H:%M", errors="coerce").hour
    if pd.isna(accident_hour):
        raise ValueError("time must be a valid HH:MM value")

    return {
        "accident_hour": int(accident_hour),
        "time_of_day": _derive_time_of_day(int(accident_hour)),
        "driver_age_group": _driver_age_group(int(payload.driver_age)),
        "is_multi_vehicle": "Yes" if int(payload.num_vehicles) > 1 else "No",
        "is_weekend": "Yes" if payload.day_of_week in {"Saturday", "Sunday"} else "No",
        "is_night": "Yes" if int(accident_hour) >= 20 or int(accident_hour) < 6 else "No",
        "is_peak_hour": "Yes" if 7 <= int(accident_hour) <= 10 or 17 <= int(accident_hour) <= 20 else "No",
    }


def save_prediction_records(payload: PredictionRequest, predicted_severity: str, confidence: float) -> None:
    session.init_db()
    db = session.SessionLocal()
    try:
        derived_fields = _build_derived_fields(payload)
        accident_record = AccidentRecord(
            state=payload.state,
            city=payload.city,
            year=payload.year,
            month=payload.month,
            day_of_week=payload.day_of_week,
            time=payload.time,
            severity=predicted_severity,
            num_vehicles=payload.num_vehicles,
            vehicle_type=payload.vehicle_type,
            driver_age=payload.driver_age,
            driver_gender=payload.driver_gender,
            license_status=payload.driver_license_status,
            weather=payload.weather,
            lighting=payload.lighting_conditions,
            road_type=payload.road_type,
            road_condition=payload.road_condition,
            traffic_control_presence=payload.traffic_control_presence,
            accident_location_details=payload.accident_location_details,
            speed_limit=payload.speed_limit_kmh,
            alcohol_involved=payload.alcohol_involved,
            accident_hour=derived_fields["accident_hour"],
            time_of_day=derived_fields["time_of_day"],
            driver_age_group=derived_fields["driver_age_group"],
            is_multi_vehicle=derived_fields["is_multi_vehicle"],
            is_weekend=derived_fields["is_weekend"],
            is_night=derived_fields["is_night"],
            is_peak_hour=derived_fields["is_peak_hour"],
            confidence=float(confidence),
        )
        prediction_record = PredictionRecord(
            state=payload.state,
            prediction=predicted_severity,
            confidence=float(confidence),
            input_payload=json.dumps(payload.model_dump(), default=str),
        )

        db.add(accident_record)
        db.add(prediction_record)
        db.commit()
    finally:
        db.close()
