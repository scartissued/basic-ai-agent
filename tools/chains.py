"""Higher-level tool chains for side-project trip assistant use cases."""

from schema.weather import (
    OutfitRecommendationData,
    RiskAlertData,
    TemperatureData,
)
from tools.tools import get_current_weather


def weather_risk_alert_chain(location: str) -> dict:
    """Classify current weather risks and return simple actions."""
    weather = TemperatureData(**get_current_weather(location))

    risks: list[str] = []
    actions: list[str] = []
    severity_score = 0

    if weather.temp_c >= 36:
        risks.append("High heat stress risk")
        actions.append("Avoid direct sun in the afternoon and hydrate frequently.")
        severity_score += 2
    elif weather.temp_c >= 32:
        risks.append("Warm to hot conditions")
        actions.append("Carry water and prefer shaded routes.")
        severity_score += 1

    if weather.humidity >= 80:
        risks.append("High humidity discomfort")
        actions.append("Wear breathable fabrics and take cooling breaks.")
        severity_score += 1

    if weather.wind_kph >= 30:
        risks.append("Strong wind conditions")
        actions.append("Secure loose items and avoid lightweight umbrellas.")
        severity_score += 1

    condition_lower = weather.condition.lower()
    if "rain" in condition_lower or "storm" in condition_lower:
        risks.append("Wet weather expected")
        actions.append("Carry rain protection and waterproof footwear.")
        severity_score += 2

    if not risks:
        risks.append("No major weather risk right now")
        actions.append("Proceed with normal plans and light preparedness.")

    if severity_score >= 4:
        risk_level = "high"
    elif severity_score >= 2:
        risk_level = "medium"
    else:
        risk_level = "low"

    response = RiskAlertData(
        location=f"{weather.location}, {weather.country}",
        risk_level=risk_level,
        risks=risks,
        actions=actions,
        summary=(
            f"Current conditions: {weather.temp_c}C, {weather.condition}, "
            f"humidity {weather.humidity}%."
        ),
    )
    return response.model_dump()


def outfit_recommendation_chain(location: str, activity: str = "general") -> dict:
    """Generate a weather-aware outfit recommendation with fallback option."""
    weather = TemperatureData(**get_current_weather(location))

    base_top = "a light breathable t-shirt"
    base_bottom = "comfortable trousers"
    outer_layer = "a light layer"
    footwear = "comfortable shoes"

    if weather.temp_c >= 32:
        base_top = "a moisture-wicking short-sleeve top"
        base_bottom = "lightweight pants or shorts"
        outer_layer = "no outer layer needed"
    elif weather.temp_c <= 18:
        base_top = "a full-sleeve base layer"
        base_bottom = "full-length pants"
        outer_layer = "a warm jacket"

    condition_lower = weather.condition.lower()
    if "rain" in condition_lower or "storm" in condition_lower:
        outer_layer = "a waterproof rain jacket"
        footwear = "water-resistant shoes"

    if weather.wind_kph >= 25:
        outer_layer = f"{outer_layer} with a wind-resistant shell"

    activity_lower = activity.lower().strip() or "general"
    if activity_lower in {"walk", "walking", "sightseeing"}:
        footwear = "cushioned walking shoes"
    elif activity_lower in {"dinner", "office", "meeting"}:
        base_bottom = "smart-casual trousers"

    primary_outfit = f"{base_top}, {base_bottom}, {outer_layer}, and {footwear}."
    backup_outfit = (
        "Keep a compact umbrella and an extra dry t-shirt in your bag in case "
        "conditions shift."
    )

    response = OutfitRecommendationData(
        location=f"{weather.location}, {weather.country}",
        activity=activity_lower,
        primary_outfit=primary_outfit,
        backup_outfit=backup_outfit,
        tips=[
            f"Feels like {weather.feels_like_c}C currently.",
            f"Condition reported as {weather.condition}.",
        ],
    )
    return response.model_dump()
