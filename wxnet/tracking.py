"""
GPS tracking and chase utilities for storm chasers.

Provides:
- GPS location tracking
- Distance/bearing to storms
- Intercept calculations
- Chase logging
- Sound alerts
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from pathlib import Path
import json

try:
    from gpsd import connect, get_current
    GPS_AVAILABLE = True
except ImportError:
    GPS_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from .models import StormCell, WeatherAlert, Location
from .config import config


class GPSTracker:
    """GPS tracking for storm chasers."""

    def __init__(self):
        """Initialize GPS tracker."""
        self.current_location: Optional[Location] = None
        self.track_history: List[Tuple[datetime, Location]] = []
        self.is_tracking = False

    def start_tracking(self):
        """Start GPS tracking."""
        if not GPS_AVAILABLE:
            print("GPS not available. Install gpsd-py3 and configure gpsd daemon.")
            return False

        try:
            connect()
            self.is_tracking = True
            return True
        except Exception as e:
            print(f"Error starting GPS tracking: {e}")
            return False

    def stop_tracking(self):
        """Stop GPS tracking."""
        self.is_tracking = False

    def get_current_location(self) -> Optional[Location]:
        """Get current GPS location.

        Returns:
            Current location or None
        """
        if not self.is_tracking or not GPS_AVAILABLE:
            return self.current_location

        try:
            packet = get_current()

            if packet.mode >= 2:  # 2D or 3D fix
                location = Location(
                    latitude=packet.lat,
                    longitude=packet.lon,
                    elevation=packet.alt if packet.mode == 3 else None
                )

                self.current_location = location
                self.track_history.append((datetime.utcnow(), location))

                # Trim history to last 1000 points
                if len(self.track_history) > 1000:
                    self.track_history = self.track_history[-1000:]

                return location

        except Exception as e:
            print(f"Error getting GPS location: {e}")

        return None

    def calculate_intercept(
        self,
        storm: StormCell,
        chase_speed_mph: float = 60,
        update_interval_minutes: float = 5
    ) -> Optional[Dict[str, Any]]:
        """Calculate intercept point and time for a storm cell.

        Args:
            storm: Storm cell to intercept
            chase_speed_mph: Chase vehicle speed
            update_interval_minutes: Storm update frequency

        Returns:
            Intercept calculation or None
        """
        if not self.current_location:
            return None

        # Current positions
        chase_lat = self.current_location.latitude
        chase_lon = self.current_location.longitude
        storm_lat = storm.latitude
        storm_lon = storm.longitude

        # Storm motion vector
        storm_speed = storm.movement_speed  # mph
        storm_dir = storm.movement_direction  # degrees

        # Convert storm direction to radians
        storm_dir_rad = np.radians(storm_dir)

        # Storm velocity components (degrees per hour, rough approximation)
        storm_v_lat = (storm_speed * np.cos(storm_dir_rad)) / 69  # 69 miles per degree latitude
        storm_v_lon = (storm_speed * np.sin(storm_dir_rad)) / (69 * np.cos(np.radians(storm_lat)))

        # Try different intercept times (0 to 120 minutes)
        best_intercept = None
        min_chase_time = float('inf')

        for t_minutes in range(0, 121, 5):
            t_hours = t_minutes / 60.0

            # Storm position at time t
            future_storm_lat = storm_lat + storm_v_lat * t_hours
            future_storm_lon = storm_lon + storm_v_lon * t_hours

            # Distance from current chase position to future storm position
            dist_miles = self._haversine_distance(
                chase_lat, chase_lon,
                future_storm_lat, future_storm_lon
            )

            # Time to reach that point
            chase_time_hours = dist_miles / chase_speed_mph

            # If we can reach it in time
            if chase_time_hours <= t_hours and chase_time_hours < min_chase_time:
                min_chase_time = chase_time_hours

                bearing = self._calculate_bearing(
                    chase_lat, chase_lon,
                    future_storm_lat, future_storm_lon
                )

                best_intercept = {
                    "intercept_latitude": future_storm_lat,
                    "intercept_longitude": future_storm_lon,
                    "intercept_time_minutes": t_minutes,
                    "chase_time_minutes": chase_time_hours * 60,
                    "distance_miles": dist_miles,
                    "bearing": bearing,
                    "estimated_arrival": datetime.utcnow() + timedelta(hours=chase_time_hours)
                }

        return best_intercept

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance using Haversine formula.

        Args:
            lat1, lon1: First point
            lat2, lon2: Second point

        Returns:
            Distance in miles
        """
        R = 3959.0  # Earth radius in miles

        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return R * c

    def _calculate_bearing(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> int:
        """Calculate bearing from point 1 to point 2.

        Args:
            lat1, lon1: Starting point
            lat2, lon2: Ending point

        Returns:
            Bearing in degrees
        """
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        dlon = np.radians(lon2 - lon1)

        y = np.sin(dlon) * np.cos(lat2_rad)
        x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon)

        bearing = np.degrees(np.arctan2(y, x))
        return int((bearing + 360) % 360)

    def save_track(self, filename: str):
        """Save GPS track to file.

        Args:
            filename: Output filename
        """
        track_data = {
            "start_time": self.track_history[0][0].isoformat() if self.track_history else None,
            "end_time": self.track_history[-1][0].isoformat() if self.track_history else None,
            "points": [
                {
                    "time": time.isoformat(),
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "elevation": loc.elevation
                }
                for time, loc in self.track_history
            ]
        }

        filepath = Path(config.cache_dir) / filename
        with open(filepath, 'w') as f:
            json.dump(track_data, f, indent=2)


class SoundAlerts:
    """Sound alert system for critical warnings."""

    def __init__(self):
        """Initialize sound alert system."""
        self.enabled = config.alert_sound
        self.pygame_initialized = False

        if self.enabled and PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.pygame_initialized = True
            except Exception as e:
                print(f"Error initializing pygame: {e}")

    def play_alert(self, severity: str = "severe"):
        """Play alert sound based on severity.

        Args:
            severity: Alert severity (extreme, severe, moderate, minor)
        """
        if not self.enabled or not self.pygame_initialized:
            return

        # Alert frequencies and patterns
        alert_patterns = {
            "extreme": [(800, 200), (600, 200), (800, 200), (600, 200)],  # Alternating high/low
            "severe": [(700, 300), (500, 200)],  # Two-tone
            "moderate": [(600, 400)],  # Single tone
            "minor": [(500, 200)]  # Short beep
        }

        pattern = alert_patterns.get(severity.lower(), alert_patterns["moderate"])

        try:
            for freq, duration_ms in pattern:
                # Generate tone
                sample_rate = 22050
                duration_s = duration_ms / 1000.0
                samples = int(sample_rate * duration_s)

                # Create sine wave
                t = np.linspace(0, duration_s, samples, False)
                wave = np.sin(2 * np.pi * freq * t)

                # Add envelope to prevent clicks
                envelope = np.linspace(0, 1, int(samples * 0.1))
                wave[:len(envelope)] *= envelope
                wave[-len(envelope):] *= envelope[::-1]

                # Scale to 16-bit integer
                wave = (wave * 32767).astype(np.int16)

                # Convert to stereo
                stereo_wave = np.column_stack((wave, wave))

                # Play sound
                sound = pygame.sndarray.make_sound(stereo_wave)
                sound.play()

                # Wait for sound to finish
                while pygame.mixer.get_busy():
                    pygame.time.wait(10)

                # Short gap between tones
                pygame.time.wait(100)

        except Exception as e:
            print(f"Error playing alert sound: {e}")

    def play_tornado_warning(self):
        """Play urgent tornado warning alert."""
        self.play_alert("extreme")

    def play_severe_warning(self):
        """Play severe thunderstorm warning alert."""
        self.play_alert("severe")


class ChaseLogger:
    """Log chase activities and events."""

    def __init__(self):
        """Initialize chase logger."""
        self.log_dir = Path(config.cache_dir) / "chase_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log_file: Optional[Path] = None
        self.chase_start_time: Optional[datetime] = None

    def start_chase(self, chase_name: Optional[str] = None):
        """Start a new chase log.

        Args:
            chase_name: Optional name for this chase
        """
        self.chase_start_time = datetime.utcnow()

        if chase_name is None:
            chase_name = self.chase_start_time.strftime("%Y%m%d_%H%M")

        self.current_log_file = self.log_dir / f"chase_{chase_name}.log"

        self.log_event("CHASE_START", "Chase session started")

    def log_event(self, event_type: str, description: str, data: Optional[Dict] = None):
        """Log a chase event.

        Args:
            event_type: Type of event
            description: Event description
            data: Optional additional data
        """
        if not self.current_log_file:
            return

        timestamp = datetime.utcnow().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "description": description,
            "data": data
        }

        with open(self.current_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def log_alert(self, alert: WeatherAlert):
        """Log a weather alert.

        Args:
            alert: Weather alert
        """
        self.log_event(
            "ALERT",
            f"{alert.severity.value}: {alert.event}",
            {
                "event": alert.event,
                "severity": alert.severity.value,
                "areas": alert.areas
            }
        )

    def log_storm_cell(self, cell: StormCell):
        """Log a storm cell observation.

        Args:
            cell: Storm cell
        """
        self.log_event(
            "STORM_CELL",
            f"Cell {cell.id}: {cell.intensity} dBZ",
            {
                "id": cell.id,
                "intensity": cell.intensity,
                "latitude": cell.latitude,
                "longitude": cell.longitude,
                "has_rotation": cell.has_rotation,
                "tvs": cell.tvs,
                "meso": cell.meso
            }
        )

    def end_chase(self):
        """End the current chase log."""
        if self.chase_start_time:
            duration = datetime.utcnow() - self.chase_start_time
            self.log_event("CHASE_END", f"Chase ended. Duration: {duration}")

        self.current_log_file = None
        self.chase_start_time = None
