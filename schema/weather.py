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
