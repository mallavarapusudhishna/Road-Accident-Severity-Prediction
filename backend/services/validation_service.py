"""Real-world validation for prediction requests.

Runs **before** the ML model to reject logically impossible or
physically absurd accident scenarios with human-readable messages.
"""

from __future__ import annotations

from backend.models.schemas import PredictionRequest

# India legal minimum driving age
_MIN_DRIVING_AGE = 18
# Minimum age to hold a commercial heavy-vehicle licence (Bus / Truck)
_MIN_HEAVY_VEHICLE_AGE = 20

_HEAVY_VEHICLES = {"Bus", "Truck"}

_VALID_MONTHS = {
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
}

_VALID_DAYS = {
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
}


def validate_prediction_request(payload: PredictionRequest) -> list[str]:
    """Return a list of human-readable validation errors.

    An empty list means the request is valid and may proceed to prediction.
    """
    errors: list[str] = []

    age = payload.driver_age
    license_status = payload.driver_license_status
    vehicle = payload.vehicle_type
    alcohol = payload.alcohol_involved
    speed = payload.speed_limit_kmh
    num_vehicles = payload.num_vehicles

    # ── Age validations ─────────────────────────────────────────────
    if age <= 0:
        errors.append("Driver age must be a positive number.")
    elif age < _MIN_DRIVING_AGE:
        errors.append(
            f"A {age}-year-old cannot legally drive in India. "
            f"The minimum driving age is {_MIN_DRIVING_AGE}."
        )

    if age < _MIN_DRIVING_AGE and license_status in ("Valid", "Expired"):
        errors.append(
            f"A {age}-year-old driver cannot possess a "
            f"{'valid' if license_status == 'Valid' else 'previously valid (expired)'} "
            f"driving license."
        )

    if age < _MIN_HEAVY_VEHICLE_AGE and vehicle in _HEAVY_VEHICLES:
        errors.append(
            f"A {age}-year-old cannot legally operate a {vehicle.lower()}. "
            f"The minimum age for heavy vehicle operation is {_MIN_HEAVY_VEHICLE_AGE}."
        )

    if age > 100:
        errors.append(
            f"Driver age of {age} is unrealistic. Please enter a value between "
            f"{_MIN_DRIVING_AGE} and 100."
        )

    # ── Speed validations ───────────────────────────────────────────
    if speed < 0:
        errors.append("Speed limit cannot be negative.")
    elif speed == 0:
        errors.append(
            "Speed limit cannot be zero. Please enter a realistic speed limit "
            "for the accident location."
        )
    elif speed > 200:
        errors.append(
            f"A speed limit of {speed} km/h is unrealistic. "
            f"Maximum highway speed limit in India is around 120 km/h."
        )

    # ── Vehicle count validations ───────────────────────────────────
    if num_vehicles < 1:
        errors.append("Number of vehicles involved must be at least 1.")
    elif num_vehicles > 20:
        errors.append(
            f"Number of vehicles ({num_vehicles}) is unrealistically high. "
            f"Please enter a value between 1 and 20."
        )

    # ── Alcohol + minor combination ─────────────────────────────────
    if age < _MIN_DRIVING_AGE and alcohol == "Yes":
        errors.append(
            f"An underage person ({age} years old) with alcohol involvement "
            f"is an invalid accident scenario for prediction."
        )

    # ── Month / Day of week validation ──────────────────────────────
    if payload.month and payload.month not in _VALID_MONTHS:
        errors.append(
            f"'{payload.month}' is not a valid month name. "
            f"Please use the full English name (e.g. January, February)."
        )

    if payload.day_of_week and payload.day_of_week not in _VALID_DAYS:
        errors.append(
            f"'{payload.day_of_week}' is not a valid day of the week. "
            f"Please use the full English name (e.g. Monday, Tuesday)."
        )

    # ── Year range validation ───────────────────────────────────────
    if payload.year < 2018 or payload.year > 2030:
        errors.append(
            f"Year {payload.year} is outside the supported range (2018–2030)."
        )

    return errors
