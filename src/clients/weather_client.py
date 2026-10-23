from datetime import datetime, timezone
from typing import Dict
from .http_client import ResilientHTTPClient
from ..models.weather import WeatherObservation

WMO_CODE_MAP: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherClient:
    """Fetches real-time meteorological data and parses it into strict Pydantic entities."""

    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, http_client: ResilientHTTPClient = None):
        self.http = http_client or ResilientHTTPClient()

    async def get_current_weather(
        self, city: str, latitude: float, longitude: float
    ) -> WeatherObservation:
        """Queries Open-Meteo and validates returned values with Pydantic V2."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code,is_day",
            "timezone": "auto",
        }

        raw = await self.http.get_json(self.OPEN_METEO_URL, params=params)
        current = raw.get("current", {})

        wmo_code = current.get("weather_code", 0)
        condition_str = WMO_CODE_MAP.get(wmo_code, "Unknown / Variable")

        # Parse observation timestamp safely
        time_str = current.get("time")
        if time_str:
            observed_dt = datetime.fromisoformat(time_str)
        else:
            observed_dt = datetime.now(timezone.utc)

        # Ingest into Pydantic model (validates all fields & bounds)
        observation = WeatherObservation(
            city=city,
            latitude=raw.get("latitude", latitude),
            longitude=raw.get("longitude", longitude),
            temperature_c=current.get("temperature_2m"),
            relative_humidity=current.get("relative_humidity_2m"),
            wind_speed_kmh=current.get("wind_speed_10m"),
            wind_direction_deg=current.get("wind_direction_10m"),
            weather_code=wmo_code,
            condition=condition_str,
            is_day=bool(current.get("is_day", 1)),
            observed_time=observed_dt,
        )
        return observation
