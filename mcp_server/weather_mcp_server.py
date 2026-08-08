"""FastMCP weather server backed by Open-Meteo.

The MCP surface is intentionally thin: HTTP and parsing live in weather_broker.py.
Run with:
    python weather_mcp_server.py
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

import weather_broker

mcp = FastMCP("open-meteo-weather")


@mcp.tool
def get_current_weather(location: str) -> dict:
    """Get current temperature, conditions, humidity, precipitation, and wind."""
    return weather_broker.get_current_weather(location)


@mcp.tool
def get_forecast(location: str, days: int = 5) -> dict:
    """Get the next 1-16 days of daily highs/lows, precipitation chance, and conditions."""
    return weather_broker.get_forecast(location, days)


@mcp.tool
def get_weather_recommendation(location: str, date: str) -> dict:
    """Give an explainable umbrella/jacket/travel recommendation for YYYY-MM-DD."""
    return weather_broker.get_recommendation(location, date)


if __name__ == "__main__":
    port = int(os.getenv("DATABRICKS_APP_PORT", os.getenv("PORT", "8000")))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
