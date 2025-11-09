"""Data models for WXNET."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    EXTREME = "Extreme"
    SEVERE = "Severe"
    MODERATE = "Moderate"
    MINOR = "Minor"
    UNKNOWN = "Unknown"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTUAL = "Actual"
    EXERCISE = "Exercise"
    SYSTEM = "System"
    TEST = "Test"
    DRAFT = "Draft"


class AlertType(str, Enum):
    """Types of weather alerts."""
    TORNADO_WARNING = "Tornado Warning"
    TORNADO_WATCH = "Tornado Watch"
    SEVERE_THUNDERSTORM_WARNING = "Severe Thunderstorm Warning"
    SEVERE_THUNDERSTORM_WATCH = "Severe Thunderstorm Watch"
    FLASH_FLOOD_WARNING = "Flash Flood Warning"
    FLASH_FLOOD_WATCH = "Flash Flood Watch"
    FLOOD_WARNING = "Flood Warning"
    SPECIAL_WEATHER_STATEMENT = "Special Weather Statement"
    OTHER = "Other"


class WeatherAlert(BaseModel):
    """Weather alert from NWS."""
    id: str
    event: str
    headline: Optional[str] = None
    description: Optional[str] = None
    instruction: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.UNKNOWN
    certainty: Optional[str] = None
    urgency: Optional[str] = None
    status: AlertStatus = AlertStatus.ACTUAL
    onset: Optional[datetime] = None
    expires: Optional[datetime] = None
    sender_name: Optional[str] = None
    areas: List[str] = Field(default_factory=list)


class CurrentWeather(BaseModel):
    """Current weather conditions."""
    temperature: float
    feels_like: float
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: int
    wind_gust: Optional[float] = None
    visibility: Optional[float] = None
    clouds: int
    dewpoint: Optional[float] = None
    conditions: str
    timestamp: datetime


class StormCell(BaseModel):
    """Individual storm cell data."""
    id: str
    latitude: float
    longitude: float
    intensity: int  # dBZ
    movement_speed: float  # mph
    movement_direction: int  # degrees
    top_height: Optional[int] = None  # feet
    has_rotation: bool = False
    rotation_strength: Optional[float] = None
    hail_probability: int = 0
    max_hail_size: Optional[float] = None  # inches
    tvs: bool = False  # Tornado Vortex Signature
    meso: bool = False  # Mesocyclone
    timestamp: datetime


class LightningStrike(BaseModel):
    """Lightning strike data."""
    latitude: float
    longitude: float
    timestamp: datetime
    strength: Optional[float] = None
    type: Optional[str] = None  # CG, IC, etc.


class AtmosphericData(BaseModel):
    """Atmospheric parameters for severe weather."""
    cape: Optional[float] = None  # J/kg
    cin: Optional[float] = None  # J/kg
    helicity: Optional[float] = None  # m²/s²
    shear: Optional[float] = None  # knots
    lifted_index: Optional[float] = None
    k_index: Optional[float] = None
    total_totals: Optional[float] = None
    timestamp: datetime


class ForecastPeriod(BaseModel):
    """Forecast for a specific period."""
    name: str
    temperature: int
    temperature_trend: Optional[str] = None
    wind_speed: str
    wind_direction: str
    short_forecast: str
    detailed_forecast: str
    precipitation_probability: Optional[int] = None
    dewpoint: Optional[float] = None


class Forecast(BaseModel):
    """Weather forecast."""
    periods: List[ForecastPeriod]
    updated: datetime


class ConvectiveOutlook(BaseModel):
    """SPC Convective Outlook."""
    day: int  # 1, 2, or 3
    valid_time: datetime
    expire_time: datetime
    categorical_risk: str  # TSTM, MRGL, SLGT, ENH, MDT, HIGH
    tornado_risk: Optional[str] = None
    wind_risk: Optional[str] = None
    hail_risk: Optional[str] = None
    areas: List[str] = Field(default_factory=list)


class Location(BaseModel):
    """Geographic location."""
    latitude: float
    longitude: float
    name: Optional[str] = None
    elevation: Optional[float] = None


class RadarData(BaseModel):
    """Radar data snapshot."""
    station: str
    product_type: str  # reflectivity, velocity, etc.
    timestamp: datetime
    latitude: float
    longitude: float
    range: int  # nautical miles
    data: List[List[Optional[int]]]  # 2D array of values


class StormReport(BaseModel):
    """Storm report (tornado, hail, wind)."""
    id: str
    type: str  # tornado, hail, wind
    latitude: float
    longitude: float
    timestamp: datetime
    magnitude: Optional[str] = None
    description: str
    source: str
