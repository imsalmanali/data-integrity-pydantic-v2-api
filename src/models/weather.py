from datetime import datetime
from typing import Literal
from pydantic import Field, field_validator, model_validator
from .base import TimestampedModel


class WeatherForecastRequest(TimestampedModel):
    """Parameters for weather data requests."""
    city_name: str = Field(..., min_length=2, max_length=100, description="Name of the city")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude between -90 and 90")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude between -180 and 180")
    temperature_unit: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="Temperature scale"
    )


class WeatherObservation(TimestampedModel):
    """
    Validated weather entity parsed from Open-Meteo API.
    Guarantees strict type safety and physical plausibility for agent reasoning.
    """
    city: str = Field(..., min_length=2, description="Target city")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    temperature_c: float = Field(..., description="Observed temperature in Celsius")
    relative_humidity: int = Field(..., ge=0, le=100, description="Relative humidity percentage")
    wind_speed_kmh: float = Field(..., ge=0.0, description="Wind speed in km/h")
    wind_direction_deg: int = Field(..., ge=0, le=360, description="Wind direction azimuth 0-360")
    weather_code: int = Field(..., ge=0, description="WMO weather interpretation code")
    condition: str = Field(..., description="Human-readable condition translated from WMO code")
    is_day: bool = Field(..., description="True if observation occurred during daylight")
    observed_time: datetime = Field(..., description="ISO observation time from external sensor")

    @field_validator("temperature_c")
    @classmethod
    def validate_realistic_earth_temperature(cls, v: float) -> float:
        """Protect against corrupted sensor readings or rogue APIs."""
        if v < -90.0 or v > 65.0:
            raise ValueError(f"Unrealistic atmospheric temperature: {v}°C. Expected between -90°C and 65°C.")
        return round(v, 2)

    @model_validator(mode="after")
    def cross_validate_weather_state(self) -> "WeatherObservation":
        """Cross-field consistency check."""
        if self.wind_speed_kmh > 350.0:
            raise ValueError(f"Wind speed {self.wind_speed_kmh} km/h exceeds maximum recorded hurricane velocity.")
        return self
