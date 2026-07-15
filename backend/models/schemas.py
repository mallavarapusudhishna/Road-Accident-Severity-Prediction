from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

_VALID_MONTHS = {
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
}

_VALID_DAYS = {
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
}


class PredictionRequest(BaseModel):
    state: str = Field(..., description="State of accident occurrence")
    city: str = Field(default="Unknown", description="City of accident occurrence")
    year: int = Field(..., ge=2018, le=2030)
    month: str = Field(..., description="Month name")
    day_of_week: str = Field(..., description="Day of week")
    time: str = Field(..., description="Time string in HH:MM format")
    num_vehicles: int = Field(..., ge=1, le=20)
    vehicle_type: str = Field(..., description="Vehicle type")
    weather: str = Field(..., description="Weather condition")
    road_type: str = Field(..., description="Road type")
    road_condition: str = Field(default="Under Construction", description="Road condition")
    lighting_conditions: str = Field(default="Dark", description="Lighting condition")
    traffic_control_presence: str = Field(default="Signs", description="Traffic control presence")
    speed_limit_kmh: int = Field(..., ge=0, le=300)
    driver_age: int = Field(..., ge=1, le=120)
    driver_gender: str = Field(..., description="Driver gender")
    driver_license_status: Optional[str] = Field(default=None, description="Driver license status")
    alcohol_involved: str = Field(..., description="Alcohol involvement")
    accident_location_details: str = Field(default="Intersection", description="Accident location details")

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        parts = value.strip().split(":")
        if len(parts) != 2:
            raise ValueError("time must be in HH:MM format")
        hour, minute = parts
        if not hour.isdigit() or not minute.isdigit():
            raise ValueError("time must be in HH:MM format")
        if int(hour) < 0 or int(hour) > 23 or int(minute) < 0 or int(minute) > 59:
            raise ValueError("time must be in HH:MM format with valid hours (0-23) and minutes (0-59)")
        return value

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        
        if value not in _VALID_MONTHS:
            raise ValueError(
                f"'{value}' is not a valid month name. "
                f"Use full English names: January, February, ... December."
            )
        return value

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, value: str) -> str:
        if value not in _VALID_DAYS:
            raise ValueError(
                f"'{value}' is not a valid day. "
                f"Use full English names: Monday, Tuesday, ... Sunday."
            )
        return value

    @field_validator("driver_license_status", mode="before")
    @classmethod
    def clean_driver_license_status(cls, value):
        if value is None:
            return None
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, float) and value != value:
            return None
        return value


class PredictionResponse(BaseModel):
    predicted_severity: Literal["Minor", "Serious", "Fatal"]
    confidence: float = Field(..., ge=0, le=1)

    probabilities: dict[str, float] = Field(
        default_factory=dict,
        description="Map of severity class -> probability.",
    )
    # SHAP-based explainability
    top_contributing_features: list[str] = Field(
        default_factory=list,
        description="Top feature names that contributed to the prediction (by absolute SHAP value).",
    )
    shap_values: dict[str, float] = Field(
        default_factory=dict,
        description="Map of feature -> SHAP value for the predicted class (approximate).",
    )
    human_readable_explanation: str = Field(
        default="",
        description="Natural-language explanation derived from SHAP values.",
    )


class ValidationErrorResponse(BaseModel):
    """Returned when real-world validation fails (HTTP 422)."""

    detail: str = Field(..., description="Summary error message.")
    validation_errors: list[str] = Field(
        ..., description="List of individual human-readable validation errors."
    )
