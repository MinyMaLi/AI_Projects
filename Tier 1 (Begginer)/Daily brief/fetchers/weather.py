"""
Fetches today's weather forecast via Open-Meteo (free, no API key required).
Geocodes the LOCATION name from .env to lat/lon, then pulls the daily forecast.
"""

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Light snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Moderate rain showers", 82: "Heavy rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm with hail",
}


def fetch_weather(location: str) -> dict:
    geo = requests.get(GEOCODING_URL, params={"name": location, "count": 1}, timeout=10)
    geo.raise_for_status()
    results = geo.json().get("results")
    if not results:
        raise ValueError(f"Could not geocode location: {location!r}")

    place = results[0]
    lat, lon = place["latitude"], place["longitude"]
    city = place.get("name", location)
    country = place.get("country", "")

    forecast = requests.get(FORECAST_URL, params={
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
        "timezone": "auto",
        "forecast_days": 1,
    }, timeout=10)
    forecast.raise_for_status()
    daily = forecast.json()["daily"]

    code = daily["weathercode"][0]
    return {
        "location": f"{city}, {country}".strip(", "),
        "temp_high": round(daily["temperature_2m_max"][0]),
        "temp_low": round(daily["temperature_2m_min"][0]),
        "condition": WMO_CODES.get(code, "Unknown"),
        "rain_chance": daily["precipitation_probability_max"][0],
    }
