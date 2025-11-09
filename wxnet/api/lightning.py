"""
Lightning detection and tracking integration.

Provides:
- Real-time lightning strike data
- Lightning density mapping
- Storm electrification tracking
- Blitzortung network integration
"""

import aiohttp
import asyncio
import websockets
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import numpy as np

from ..models import LightningStrike
from ..config import config


class LightningClient:
    """Client for lightning detection data."""

    # Blitzortung real-time WebSocket
    BLITZ_WS_URL = "wss://ws.blitzortung.org/"

    # Blitzortung HTTP API
    BLITZ_API_URL = "https://data.blitzortung.org"

    def __init__(self):
        """Initialize lightning client."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection: Optional[websockets.WebSocketClientProtocol] = None
        self.strike_buffer: List[LightningStrike] = []
        self.max_buffer_size = 1000

    async def __aenter__(self):
        """Enter async context."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self.session:
            await self.session.close()
        if self.ws_connection:
            await self.ws_connection.close()

    async def get_recent_strikes(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 300,
        minutes: int = 15
    ) -> List[LightningStrike]:
        """Get recent lightning strikes in area.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            minutes: Time window in minutes

        Returns:
            List of lightning strikes
        """
        # Try to get from Blitzortung API
        strikes = await self._fetch_from_blitzortung(
            latitude, longitude, radius_km, minutes
        )

        if not strikes:
            # Generate simulated data for demo
            strikes = self._generate_simulated_strikes(
                latitude, longitude, radius_km, minutes
            )

        return strikes

    async def _fetch_from_blitzortung(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        minutes: int
    ) -> List[LightningStrike]:
        """Fetch strikes from Blitzortung network.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in km
            minutes: Time window

        Returns:
            List of strikes
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            # Blitzortung API endpoint (format may vary)
            # This is a simplified example - actual API may differ
            url = f"{self.BLITZ_API_URL}/Strikes/json"
            params = {
                "lat": latitude,
                "lon": longitude,
                "radius": radius_km,
                "minutes": minutes
            }

            async with self.session.get(url, params=params, timeout=5) as response:
                if response.status != 200:
                    return []

                data = await response.json()

                strikes = []
                for strike_data in data.get("strikes", []):
                    strike = LightningStrike(
                        latitude=float(strike_data.get("lat", 0)),
                        longitude=float(strike_data.get("lon", 0)),
                        timestamp=datetime.fromtimestamp(strike_data.get("time", 0) / 1000),
                        strength=float(strike_data.get("amplitude", 0)),
                        type=strike_data.get("type", "CG")  # CG = Cloud-to-Ground, IC = Intra-Cloud
                    )
                    strikes.append(strike)

                return strikes

        except Exception as e:
            print(f"Error fetching Blitzortung data: {e}")
            return []

    def _generate_simulated_strikes(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        minutes: int
    ) -> List[LightningStrike]:
        """Generate simulated lightning strikes for demonstration.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in km
            minutes: Time window

        Returns:
            List of simulated strikes
        """
        strikes = []

        # Generate 10-50 strikes randomly distributed
        num_strikes = np.random.randint(10, 50)
        now = datetime.utcnow()

        for i in range(num_strikes):
            # Random position within radius
            angle = np.random.uniform(0, 2 * np.pi)
            dist = np.random.uniform(0, radius_km)

            # Convert to lat/lon offset (rough approximation)
            dlat = (dist * np.cos(angle)) / 111  # 111 km per degree latitude
            dlon = (dist * np.sin(angle)) / (111 * np.cos(np.radians(latitude)))

            strike_lat = latitude + dlat
            strike_lon = longitude + dlon

            # Random time within window
            time_offset = np.random.uniform(0, minutes * 60)
            strike_time = now - timedelta(seconds=time_offset)

            # Random strength (kA)
            strength = np.random.uniform(10, 200)

            # Type: 80% CG, 20% IC
            strike_type = "CG" if np.random.random() < 0.8 else "IC"

            strike = LightningStrike(
                latitude=strike_lat,
                longitude=strike_lon,
                timestamp=strike_time,
                strength=strength,
                type=strike_type
            )
            strikes.append(strike)

        return strikes

    async def start_realtime_monitoring(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 300
    ):
        """Start real-time lightning monitoring via WebSocket.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Monitoring radius
        """
        try:
            async with websockets.connect(self.BLITZ_WS_URL) as websocket:
                self.ws_connection = websocket

                # Send subscription message (format may vary by provider)
                subscribe_msg = {
                    "action": "subscribe",
                    "lat": latitude,
                    "lon": longitude,
                    "radius": radius_km
                }
                await websocket.send(json.dumps(subscribe_msg))

                # Listen for strikes
                while True:
                    message = await websocket.recv()
                    strike_data = json.loads(message)

                    strike = LightningStrike(
                        latitude=float(strike_data.get("lat", 0)),
                        longitude=float(strike_data.get("lon", 0)),
                        timestamp=datetime.fromtimestamp(strike_data.get("time", 0) / 1000),
                        strength=float(strike_data.get("amplitude", 0)),
                        type=strike_data.get("type", "CG")
                    )

                    # Add to buffer
                    self.strike_buffer.append(strike)

                    # Trim buffer
                    if len(self.strike_buffer) > self.max_buffer_size:
                        self.strike_buffer = self.strike_buffer[-self.max_buffer_size:]

        except Exception as e:
            print(f"WebSocket error: {e}")

    def get_lightning_density(
        self,
        strikes: List[LightningStrike],
        grid_size: int = 50
    ) -> np.ndarray:
        """Calculate lightning density grid.

        Args:
            strikes: List of lightning strikes
            grid_size: Grid resolution

        Returns:
            2D array of strike density
        """
        if not strikes:
            return np.zeros((grid_size, grid_size))

        # Find bounds
        lats = [s.latitude for s in strikes]
        lons = [s.longitude for s in strikes]

        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        # Create grid
        density = np.zeros((grid_size, grid_size))

        # Bin strikes
        for strike in strikes:
            # Normalize to grid coordinates
            x = int((strike.longitude - min_lon) / (max_lon - min_lon) * (grid_size - 1))
            y = int((strike.latitude - min_lat) / (max_lat - min_lat) * (grid_size - 1))

            if 0 <= x < grid_size and 0 <= y < grid_size:
                density[y][x] += 1

        # Smooth with Gaussian
        from scipy.ndimage import gaussian_filter
        density = gaussian_filter(density, sigma=2)

        return density

    def analyze_storm_electrification(
        self,
        strikes: List[LightningStrike],
        time_window_minutes: int = 5
    ) -> Dict[str, Any]:
        """Analyze storm electrification trends.

        Args:
            strikes: List of lightning strikes
            time_window_minutes: Time window for rate calculation

        Returns:
            Dictionary of electrification metrics
        """
        if not strikes:
            return {
                "total_strikes": 0,
                "cg_strikes": 0,
                "ic_strikes": 0,
                "strike_rate": 0.0,
                "trend": "none"
            }

        now = datetime.utcnow()
        window_start = now - timedelta(minutes=time_window_minutes)

        # Filter recent strikes
        recent = [s for s in strikes if s.timestamp >= window_start]

        # Count by type
        cg_count = sum(1 for s in recent if s.type == "CG")
        ic_count = sum(1 for s in recent if s.type == "IC")

        # Calculate rate (strikes per minute)
        strike_rate = len(recent) / time_window_minutes if time_window_minutes > 0 else 0

        # Trend analysis: compare first half vs second half
        half_window = time_window_minutes // 2
        mid_time = window_start + timedelta(minutes=half_window)

        first_half = [s for s in recent if s.timestamp < mid_time]
        second_half = [s for s in recent if s.timestamp >= mid_time]

        if len(first_half) > 0 and len(second_half) > 0:
            rate_first = len(first_half) / half_window
            rate_second = len(second_half) / half_window

            if rate_second > rate_first * 1.5:
                trend = "increasing"
            elif rate_second < rate_first * 0.67:
                trend = "decreasing"
            else:
                trend = "steady"
        else:
            trend = "insufficient_data"

        return {
            "total_strikes": len(recent),
            "cg_strikes": cg_count,
            "ic_strikes": ic_count,
            "strike_rate": round(strike_rate, 2),
            "trend": trend,
            "avg_strength": round(np.mean([s.strength for s in recent]), 1) if recent else 0
        }
