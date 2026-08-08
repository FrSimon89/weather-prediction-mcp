"""Open-Meteo adapter.

All external HTTP calls and API response parsing live here. MCP tool functions
should remain thin and call only the public functions in this module.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_SECONDS = 10

_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

class WeatherAPIError(RuntimeError):
    """Raised when Open-Meteo cannot provide a valid weather response."""


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise WeatherAPIError(f"Weather API request failed: {exc}") from exc


def resolve_location(location: str) -> dict[str, Any]:
    """Resolve a city/place name to latitude/longitude using Open-Meteo geocoding."""
    location = location.strip()
    if not location:
        raise ValueError("location must not be empty")

    # Accept "lat,lon" directly as a convenience.
    parts = [p.strip() for p in location.split(",")]
    if len(parts) == 2:
        try:
            lat, lon = float(parts[0]), float(parts[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return {"name": location, "latitude": lat, "longitude": lon, "country": None}
        except ValueError:
            pass

    data = _get_json(
        GEOCODING_URL,
        {"name": location, "count": 1, "language": "en", "format": "json"},
    )
    results = data.get("results") or []
    if not results:
        raise WeatherAPIError(f"Could not resolve location: {location!r}")
    result = results[0]
    return {
        "name": result.get("name", location),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
        "country": result.get("country"),
        "admin1": result.get("admin1"),
        "timezone": result.get("timezone"),
    }


def _forecast(location: str, days: int) -> tuple[dict[str, Any], dict[str, Any]]:
    if not 1 <= days <= 16:
        raise ValueError("days must be between 1 and 16")

    place = resolve_location(location)
    data = _get_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "weather_code",
                    "wind_speed_10m",
                    "precipitation",
                    "rain",
                    "showers",
                    "snowfall",
                ]
            ),
            "daily": ",".join(
                [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                    "precipitation_sum",
                    "rain_sum",
                    "showers_sum",
                    "snowfall_sum",
                    "wind_speed_10m_max",
                ]
            ),
            "forecast_days": days,
            "timezone": "auto",
        },
    )
    if "current" not in data or "daily" not in data:
        raise WeatherAPIError("Weather API returned an incomplete forecast")
    return place, data


def get_current_weather(location: str) -> dict[str, Any]:
    """Return normalized current conditions."""
    place, data = _forecast(location, 1)
    current = data["current"]
    units = data.get("current_units", {})
    return {
        "location": place,
        "observed_at": current.get("time"),
        "timezone": data.get("timezone"),
        "temperature": current.get("temperature_2m"),
        "temperature_unit": units.get("temperature_2m", "°C"),
        "apparent_temperature": current.get("apparent_temperature"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "wind_speed_unit": units.get("wind_speed_10m", "km/h"),
        "precipitation": current.get("precipitation"),
        "weather_code": current.get("weather_code"),
        "conditions": _WEATHER_CODES.get(current.get("weather_code"), "Unknown"),
    }


def get_forecast(location: str, days: int) -> dict[str, Any]:
    """Return normalized multi-day daily forecast."""
    place, data = _forecast(location, days)
    daily = data["daily"]
    units = data.get("daily_units", {})
    dates = daily["time"]
    forecasts = []
    for i, day in enumerate(dates):
        code = daily["weather_code"][i]
        forecasts.append(
            {
                "date": day,
                "conditions": _WEATHER_CODES.get(code, "Unknown"),
                "weather_code": code,
                "high": daily["temperature_2m_max"][i],
                "low": daily["temperature_2m_min"][i],
                "precipitation_probability_percent": daily["precipitation_probability_max"][i],
                "precipitation_sum": daily["precipitation_sum"][i],
                "rain_sum": daily["rain_sum"][i],
                "showers_sum": daily["showers_sum"][i],
                "snowfall_sum": daily["snowfall_sum"][i],
                "max_wind_speed": daily["wind_speed_10m_max"][i],
            }
        )
    return {
        "location": place,
        "timezone": data.get("timezone"),
        "temperature_unit": units.get("temperature_2m_max", "°C"),
        "wind_speed_unit": units.get("wind_speed_10m_max", "km/h"),
        "forecast": forecasts,
    }


def get_recommendation(location: str, target_date: str) -> dict[str, Any]:
    """Derive a practical recommendation from the forecast.

    Rules are intentionally simple and explainable:
    - umbrella: precipitation probability >= 40% OR measurable rain/showers
    - jacket: low < 12°C OR high < 16°C
    - caution: thunderstorm/snow/freezing precipitation
    """
    try:
        requested = date.fromisoformat(target_date)
    except ValueError as exc:
        raise ValueError("target_date must use YYYY-MM-DD format") from exc

    today = date.today()
    days = (requested - today).days + 1
    if days < 1:
        raise ValueError("target_date must be today or later")
    if days > 16:
        raise ValueError("Open-Meteo forecast supports recommendations up to 16 days ahead")

    result = get_forecast(location, days)
    matching = next((d for d in result["forecast"] if d["date"] == target_date), None)
    if matching is None:
        raise WeatherAPIError(f"No forecast returned for {target_date}")

    precip = matching["precipitation_probability_percent"] or 0
    conditions = matching["conditions"].lower()
    umbrella = precip >= 40 or (matching["rain_sum"] or 0) > 0 or (matching["showers_sum"] or 0) > 0
    jacket = (matching["low"] is not None and matching["low"] < 12) or (
        matching["high"] is not None and matching["high"] < 16
    )
    severe = any(word in conditions for word in ("thunderstorm", "heavy snow", "freezing rain", "hail"))

    actions = []
    if umbrella:
        actions.append("Bring an umbrella.")
    else:
        actions.append("An umbrella is probably not necessary.")
    if jacket:
        actions.append("Bring a jacket.")
    else:
        actions.append("A jacket is probably optional.")
    if severe:
        actions.append("Check local weather alerts before traveling.")

    return {
        "location": result["location"],
        "date": target_date,
        "forecast": matching,
        "recommendation": " ".join(actions),
        "rules_applied": {
            "umbrella_if_precipitation_probability_at_least_percent": 40,
            "jacket_if_low_below_celsius": 12,
            "jacket_if_high_below_celsius": 16,
            "alert_caution_for": ["thunderstorm", "heavy snow", "freezing rain", "hail"],
        },
    }
