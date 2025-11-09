"""Configuration management for WXNET."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Application configuration."""

    # Location settings
    default_latitude: float = Field(default=35.0)
    default_longitude: float = Field(default=-97.5)
    default_location: str = Field(default="Oklahoma City, OK")

    # API settings
    openweather_api_key: Optional[str] = Field(default=None)
    nws_user_agent: str = Field(
        default="WXNET Weather Terminal (github.com/wxnet/wxnet)"
    )

    # Update intervals (seconds)
    weather_update_interval: int = Field(default=300)
    alert_update_interval: int = Field(default=60)
    radar_update_interval: int = Field(default=120)
    lightning_update_interval: int = Field(default=30)

    # Display settings
    use_color: bool = Field(default=True)
    alert_sound: bool = Field(default=False)
    animation_speed: str = Field(default="medium")

    # Data cache directory
    cache_dir: Path = Field(default=Path.home() / ".wxnet" / "cache")

    class Config:
        """Pydantic configuration."""
        env_prefix = ""
        case_sensitive = False

    def __init__(self, **data):
        """Initialize configuration from environment variables."""
        # Override defaults with environment variables
        env_data = {
            "default_latitude": float(os.getenv("DEFAULT_LATITUDE", "35.0")),
            "default_longitude": float(os.getenv("DEFAULT_LONGITUDE", "-97.5")),
            "default_location": os.getenv("DEFAULT_LOCATION", "Oklahoma City, OK"),
            "openweather_api_key": os.getenv("OPENWEATHER_API_KEY"),
            "nws_user_agent": os.getenv(
                "NWS_USER_AGENT",
                "WXNET Weather Terminal (github.com/wxnet/wxnet)"
            ),
            "weather_update_interval": int(os.getenv("WEATHER_UPDATE_INTERVAL", "300")),
            "alert_update_interval": int(os.getenv("ALERT_UPDATE_INTERVAL", "60")),
            "radar_update_interval": int(os.getenv("RADAR_UPDATE_INTERVAL", "120")),
            "use_color": os.getenv("USE_COLOR", "true").lower() == "true",
            "alert_sound": os.getenv("ALERT_SOUND", "false").lower() == "true",
            "animation_speed": os.getenv("ANIMATION_SPEED", "medium"),
        }
        env_data.update(data)
        super().__init__(**env_data)

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config()
