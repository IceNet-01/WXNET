"""Utility functions for WXNET."""

from typing import List, Optional, Tuple
from datetime import datetime
from rich.text import Text
from rich.style import Style


def format_temperature(temp: float) -> str:
    """Format temperature with color.

    Args:
        temp: Temperature in Fahrenheit

    Returns:
        Formatted temperature string
    """
    return f"{temp:.0f}°F"


def format_wind(speed: float, direction: int, gust: Optional[float] = None) -> str:
    """Format wind information.

    Args:
        speed: Wind speed in mph
        direction: Wind direction in degrees
        gust: Wind gust in mph (optional)

    Returns:
        Formatted wind string
    """
    # Convert degrees to cardinal direction
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((direction + 11.25) / 22.5) % 16
    cardinal = directions[idx]

    wind_str = f"{cardinal} {speed:.0f} mph"
    if gust and gust > speed + 5:
        wind_str += f" G{gust:.0f}"

    return wind_str


def format_pressure(pressure: float, trend: Optional[str] = None) -> str:
    """Format barometric pressure.

    Args:
        pressure: Pressure in inHg
        trend: Pressure trend (rising/falling/steady)

    Returns:
        Formatted pressure string
    """
    pressure_str = f"{pressure:.2f} inHg"
    if trend:
        if trend == "rising":
            pressure_str += " ↑"
        elif trend == "falling":
            pressure_str += " ↓"
        else:
            pressure_str += " →"
    return pressure_str


def get_alert_color(severity: str) -> str:
    """Get color for alert severity.

    Args:
        severity: Alert severity level

    Returns:
        Color name
    """
    colors = {
        "Extreme": "bright_red",
        "Severe": "red",
        "Moderate": "yellow",
        "Minor": "blue",
        "Unknown": "white"
    }
    return colors.get(severity, "white")


def get_alert_symbol(event: str) -> str:
    """Get symbol for alert type.

    Args:
        event: Alert event type

    Returns:
        Symbol character
    """
    if "Tornado" in event:
        return "🌪"
    elif "Thunderstorm" in event:
        return "⛈"
    elif "Flood" in event or "Flash Flood" in event:
        return "🌊"
    elif "Wind" in event:
        return "💨"
    elif "Snow" in event or "Winter" in event:
        return "❄"
    elif "Heat" in event:
        return "🔥"
    else:
        return "⚠"


def format_distance(miles: float) -> str:
    """Format distance.

    Args:
        miles: Distance in miles

    Returns:
        Formatted distance string
    """
    if miles < 1:
        return f"{miles * 5280:.0f} ft"
    else:
        return f"{miles:.1f} mi"


def format_bearing(degrees: int) -> str:
    """Format bearing to cardinal direction.

    Args:
        degrees: Bearing in degrees

    Returns:
        Cardinal direction
    """
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((degrees + 11.25) / 22.5) % 16
    return directions[idx]


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula.

    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        Distance in miles
    """
    from math import radians, sin, cos, sqrt, atan2

    R = 3959.0  # Earth radius in miles

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Calculate bearing from point 1 to point 2.

    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        Bearing in degrees
    """
    from math import radians, degrees, atan2, sin, cos

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    dlon = radians(lon2 - lon1)

    y = sin(dlon) * cos(lat2_rad)
    x = cos(lat1_rad) * sin(lat2_rad) - sin(lat1_rad) * cos(lat2_rad) * cos(dlon)

    bearing = degrees(atan2(y, x))
    return int((bearing + 360) % 360)


def render_radar_ascii(
    data: List[List[Optional[int]]],
    width: int,
    height: int,
    color: bool = True
) -> List[str]:
    """Render radar data as ASCII art.

    Args:
        data: 2D array of radar values
        width: Target width
        height: Target height
        color: Use color coding

    Returns:
        List of ASCII art lines
    """
    if not data or not data[0]:
        return ["No radar data available"]

    # Scale data to fit display
    data_height = len(data)
    data_width = len(data[0])

    y_scale = data_height / height
    x_scale = data_width / width

    lines = []

    for y in range(height):
        line = ""
        for x in range(width):
            # Sample from data
            data_y = int(y * y_scale)
            data_x = int(x * x_scale)

            value = data[data_y][data_x]

            if value is None or value < 15:
                line += " "
            elif value < 25:
                line += "."
            elif value < 35:
                line += "+"
            elif value < 45:
                line += "#"
            elif value < 55:
                line += "@"
            else:
                line += "█"

        lines.append(line)

    return lines


def get_reflectivity_color(dbz: Optional[int]) -> str:
    """Get color for reflectivity value.

    Args:
        dbz: Reflectivity in dBZ

    Returns:
        Color name
    """
    if dbz is None or dbz < 15:
        return "black"
    elif dbz < 25:
        return "blue"
    elif dbz < 35:
        return "green"
    elif dbz < 45:
        return "yellow"
    elif dbz < 55:
        return "bright_yellow"
    elif dbz < 65:
        return "red"
    else:
        return "bright_red"


def format_time_ago(dt: datetime) -> str:
    """Format datetime as relative time.

    Args:
        dt: Datetime to format

    Returns:
        Formatted relative time string
    """
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    else:
        days = int(seconds / 86400)
        return f"{days}d ago"


def format_cape(cape: Optional[float]) -> Tuple[str, str]:
    """Format CAPE value with interpretation.

    Args:
        cape: CAPE in J/kg

    Returns:
        Tuple of (formatted value, interpretation)
    """
    if cape is None:
        return ("N/A", "Unknown")

    value_str = f"{cape:.0f} J/kg"

    if cape < 1000:
        return (value_str, "Weak")
    elif cape < 2500:
        return (value_str, "Moderate")
    elif cape < 4000:
        return (value_str, "Strong")
    else:
        return (value_str, "Extreme")


def format_helicity(helicity: Optional[float]) -> Tuple[str, str]:
    """Format helicity value with interpretation.

    Args:
        helicity: Helicity in m²/s²

    Returns:
        Tuple of (formatted value, interpretation)
    """
    if helicity is None:
        return ("N/A", "Unknown")

    value_str = f"{helicity:.0f} m²/s²"

    if helicity < 150:
        return (value_str, "Weak")
    elif helicity < 300:
        return (value_str, "Moderate")
    elif helicity < 450:
        return (value_str, "Strong")
    else:
        return (value_str, "Extreme")
