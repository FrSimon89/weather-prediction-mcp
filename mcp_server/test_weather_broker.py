from unittest.mock import patch

import weather_broker


def test_current_weather():
    payload = {
        "current": {
            "time": "2026-08-08T12:00",
            "temperature_2m": 20,
            "relative_humidity_2m": 70,
            "apparent_temperature": 20,
            "weather_code": 61,
            "wind_speed_10m": 12,
            "precipitation": 1.2,
        },
        "current_units": {"temperature_2m": "°C", "wind_speed_10m": "km/h"},
        "daily": {
            "time": ["2026-08-08"],
            "weather_code": [61],
            "temperature_2m_max": [21],
            "temperature_2m_min": [15],
            "precipitation_probability_max": [70],
            "precipitation_sum": [3],
            "rain_sum": [3],
            "showers_sum": [0],
            "snowfall_sum": [0],
            "wind_speed_10m_max": [20],
        },
        "daily_units": {"temperature_2m_max": "°C", "wind_speed_10m_max": "km/h"},
        "timezone": "UTC",
    }
    with patch("weather_broker.resolve_location", return_value={"name": "Test", "latitude": 1, "longitude": 2}):
        with patch("weather_broker._get_json", return_value=payload):
            result = weather_broker.get_current_weather("Test")
    assert result["temperature"] == 20
    assert result["conditions"] == "Slight rain"


def test_recommendation_rules():
    daily = {
        "time": ["2026-08-08"],
        "weather_code": [61],
        "temperature_2m_max": [15],
        "temperature_2m_min": [8],
        "precipitation_probability_max": [80],
        "precipitation_sum": [4],
        "rain_sum": [4],
        "showers_sum": [0],
        "snowfall_sum": [0],
        "wind_speed_10m_max": [15],
    }
    result = {
        "location": {"name": "Test"},
        "timezone": "UTC",
        "temperature_unit": "°C",
        "wind_speed_unit": "km/h",
        "forecast": [{
            "date": "2026-08-08", "conditions": "Slight rain", "weather_code": 61,
            "high": 15, "low": 8, "precipitation_probability_percent": 80,
            "precipitation_sum": 4, "rain_sum": 4, "showers_sum": 0,
            "snowfall_sum": 0, "max_wind_speed": 15,
        }],
    }
    with patch("weather_broker.get_forecast", return_value=result):
        with patch("weather_broker.date") as mock_date:
            mock_date.today.return_value = __import__("datetime").date(2026, 8, 8)
            mock_date.fromisoformat.return_value = __import__("datetime").date(2026, 8, 8)
            out = weather_broker.get_recommendation("Test", "2026-08-08")
    assert "umbrella" in out["recommendation"].lower()
    assert "jacket" in out["recommendation"].lower()
