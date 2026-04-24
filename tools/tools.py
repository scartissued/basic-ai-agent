"""Module for tools definition."""

import requests
from app.config import settings


def get_current_weather(location: str) -> dict[str, str]:
    """Get the current weather for a given location."""
    weather_api_key = settings.weather_api_key
    if not weather_api_key:
        raise ValueError("Missing WEATHER_API_KEY in environment")
    response = requests.get(
        "https://api.weatherapi.com/v1/current.json",
        params={"key": weather_api_key, "q": location, "aqi": "no"},
        timeout=10,
    )
    response.raise_for_status()
    raw = response.json()
    return {
        "location": raw["location"]["name"],
        "region": raw["location"]["region"],
        "country": raw["location"]["country"],
        "temp_c": raw["current"]["temp_c"],
        "temp_f": raw["current"]["temp_f"],
        "feels_like_c": raw["current"]["feelslike_c"],
        "feels_like_f": raw["current"]["feelslike_f"],
        "condition": raw["current"]["condition"]["text"],
        "humidity": raw["current"]["humidity"],
        "wind_kph": raw["current"]["wind_kph"],
        "last_updated": raw["current"]["last_updated"],
    }
