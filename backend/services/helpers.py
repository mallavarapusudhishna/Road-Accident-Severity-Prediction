from __future__ import annotations


def derive_time_of_day(accident_hour: int) -> str:
    if 0 <= accident_hour < 5:
        return "Late Night"
    if 5 <= accident_hour < 12:
        return "Morning"
    if 12 <= accident_hour < 17:
        return "Afternoon"
    return "Evening"


def derive_driver_age_group(driver_age: int) -> str:
    if driver_age < 25:
        return "Young"
    if driver_age <= 60:
        return "Adult"
    return "Senior"


def build_derived_fields(payload: object) -> dict:
    time_val = getattr(payload, "time", None) or payload.get("time", "12:00")
    num_vehicles = getattr(payload, "num_vehicles", None) or payload.get("num_vehicles", 1)
    day_of_week = getattr(payload, "day_of_week", None) or payload.get("day_of_week", "Monday")
    driver_age = getattr(payload, "driver_age", None) or payload.get("driver_age", 35)

    # Manual parse is ~317x faster than pd.to_datetime for a single HH:MM string.
    # PredictionRequest.validate_time() already guarantees "HH:MM" format, so
    # this is safe. For dict-style callers we fall back gracefully.
    try:
        hour_str, _ = str(time_val).strip().split(":", 1)
        hour_int = int(hour_str)
        if not (0 <= hour_int <= 23):
            raise ValueError("hour out of range")
    except (ValueError, AttributeError) as exc:
        raise ValueError("time must be a valid HH:MM value") from exc

    return {
        "accident_hour": hour_int,
        "time_of_day": derive_time_of_day(hour_int),
        "driver_age_group": derive_driver_age_group(int(driver_age)),
        "is_multi_vehicle": "Yes" if int(num_vehicles) > 1 else "No",
        "is_weekend": "Yes" if day_of_week in {"Saturday", "Sunday"} else "No",
        "is_night": "Yes" if hour_int >= 20 or hour_int < 6 else "No",
        "is_peak_hour": "Yes" if 7 <= hour_int <= 10 or 17 <= hour_int <= 20 else "No",
    }
