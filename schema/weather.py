"""Schema validation via pydantic."""

from pydantic import BaseModel


class TemperatureData(BaseModel):
    """Schema for temperature data returned by the weather API"""

    location: str
    region: str
    country: str
    temp_c: float
    temp_f: float
    feels_like_c: float
    feels_like_f: float
    condition: str
    humidity: int
    wind_kph: float
    last_updated: str


class WeatherResponse(BaseModel):
    """Schema for the response returned by the weather API"""

    success: bool
    data: TemperatureData | None = None
    error: str | None = None


class RiskAlertData(BaseModel):
    """Schema for weather risk alert chain output."""

    location: str
    risk_level: str
    risks: list[str]
    actions: list[str]
    summary: str


class OutfitRecommendationData(BaseModel):
    """Schema for outfit recommendation chain output."""

    location: str
    activity: str
    primary_outfit: str
    backup_outfit: str
    tips: list[str]


class ToolExecutionResponse(BaseModel):
    """Generic schema for all tool execution responses."""

    success: bool
    data: dict | None = None
    error: str | None = None
