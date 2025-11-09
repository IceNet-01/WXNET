"""Radar data API client."""

import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from ..models import RadarData, StormCell
import random


class RadarClient:
    """Client for radar data."""

    # NEXRAD stations
    NEXRAD_STATIONS = {
        "KTLX": {"name": "Oklahoma City", "lat": 35.33, "lon": -97.28},
        "KOUN": {"name": "Norman", "lat": 35.24, "lon": -97.46},
        "KINX": {"name": "Tulsa", "lat": 36.18, "lon": -95.56},
        "KICT": {"name": "Wichita", "lat": 37.65, "lon": -97.44},
        "KDDC": {"name": "Dodge City", "lat": 37.76, "lon": -99.97},
        "KGLD": {"name": "Goodland", "lat": 39.37, "lon": -101.70},
        "KAMA": {"name": "Amarillo", "lat": 35.23, "lon": -101.71},
        "KLBB": {"name": "Lubbock", "lat": 33.65, "lon": -101.81},
        "KMAF": {"name": "Midland", "lat": 31.94, "lon": -102.19},
        "KDYX": {"name": "San Antonio", "lat": 32.54, "lon": -99.25},
    }

    def __init__(self):
        """Initialize radar client."""
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Enter async context."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self.session:
            await self.session.close()

    def find_nearest_station(self, latitude: float, longitude: float) -> str:
        """Find nearest NEXRAD station.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Station ID
        """
        min_dist = float('inf')
        nearest = "KTLX"

        for station_id, info in self.NEXRAD_STATIONS.items():
            dist = ((latitude - info["lat"]) ** 2 + (longitude - info["lon"]) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = station_id

        return nearest

    async def get_reflectivity_data(
        self,
        station: str,
        latitude: float,
        longitude: float
    ) -> Optional[RadarData]:
        """Get reflectivity radar data.

        Args:
            station: NEXRAD station ID
            latitude: Center latitude
            longitude: Center longitude

        Returns:
            Radar data or None
        """
        # For demo purposes, generate simulated radar data
        # In production, this would fetch actual NEXRAD Level 2 or Level 3 data
        return self._generate_simulated_radar(station, latitude, longitude, "reflectivity")

    async def get_velocity_data(
        self,
        station: str,
        latitude: float,
        longitude: float
    ) -> Optional[RadarData]:
        """Get velocity radar data.

        Args:
            station: NEXRAD station ID
            latitude: Center latitude
            longitude: Center longitude

        Returns:
            Radar data or None
        """
        return self._generate_simulated_radar(station, latitude, longitude, "velocity")

    def _generate_simulated_radar(
        self,
        station: str,
        latitude: float,
        longitude: float,
        product_type: str
    ) -> RadarData:
        """Generate simulated radar data for demonstration.

        Args:
            station: Station ID
            latitude: Latitude
            longitude: Longitude
            product_type: Type of radar product

        Returns:
            Simulated radar data
        """
        # Create a 100x100 grid
        size = 100
        data = [[None for _ in range(size)] for _ in range(size)]

        # Add some simulated weather features
        if product_type == "reflectivity":
            # Simulate some storm cells
            for _ in range(random.randint(2, 5)):
                cx, cy = random.randint(20, 80), random.randint(20, 80)
                max_intensity = random.randint(35, 70)

                for y in range(max(0, cy - 15), min(size, cy + 15)):
                    for x in range(max(0, cx - 15), min(size, cx + 15)):
                        dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                        if dist < 15:
                            intensity = int(max_intensity * (1 - dist / 15) + random.randint(-5, 5))
                            if intensity > 15:  # Threshold for display
                                data[y][x] = max(0, min(75, intensity))

        elif product_type == "velocity":
            # Simulate velocity data (positive = away, negative = toward)
            for _ in range(random.randint(1, 3)):
                cx, cy = random.randint(20, 80), random.randint(20, 80)

                for y in range(max(0, cy - 10), min(size, cy + 10)):
                    for x in range(max(0, cx - 10), min(size, cx + 10)):
                        dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                        if dist < 10:
                            # Create velocity couplet (rotation signature)
                            if x < cx:
                                velocity = int(-30 * (1 - dist / 10))
                            else:
                                velocity = int(30 * (1 - dist / 10))
                            data[y][x] = velocity

        return RadarData(
            station=station,
            product_type=product_type,
            timestamp=datetime.now(),
            latitude=latitude,
            longitude=longitude,
            range=124,  # nautical miles
            data=data
        )

    async def detect_storm_cells(
        self,
        radar_data: RadarData
    ) -> List[StormCell]:
        """Detect storm cells from radar data.

        Args:
            radar_data: Radar data

        Returns:
            List of detected storm cells
        """
        cells = []

        # Simple cell detection algorithm
        # In production, this would use more sophisticated algorithms
        size = len(radar_data.data)
        visited = [[False for _ in range(size)] for _ in range(size)]

        def flood_fill(y: int, x: int, threshold: int = 40) -> List[Tuple[int, int]]:
            """Flood fill to find connected regions."""
            if (y < 0 or y >= size or x < 0 or x >= size or
                visited[y][x] or radar_data.data[y][x] is None or
                radar_data.data[y][x] < threshold):
                return []

            visited[y][x] = True
            points = [(y, x)]

            # Check 8 neighbors
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    points.extend(flood_fill(y + dy, x + dx, threshold))

            return points

        # Find cells with reflectivity >= 40 dBZ
        for y in range(size):
            for x in range(size):
                if (not visited[y][x] and
                    radar_data.data[y][x] is not None and
                    radar_data.data[y][x] >= 40):

                    points = flood_fill(y, x)

                    if len(points) >= 10:  # Minimum cell size
                        # Calculate cell properties
                        max_intensity = max(radar_data.data[py][px] for py, px in points)
                        avg_y = sum(py for py, px in points) / len(points)
                        avg_x = sum(px for py, px in points) / len(points)

                        # Convert grid coords to lat/lon (simplified)
                        cell_lat = radar_data.latitude + (avg_y - size/2) * 0.01
                        cell_lon = radar_data.longitude + (avg_x - size/2) * 0.01

                        # Simulate movement and attributes
                        movement_speed = random.uniform(20, 45)
                        movement_direction = random.randint(0, 359)

                        has_rotation = random.random() < 0.2
                        tvs = has_rotation and random.random() < 0.3
                        meso = has_rotation and random.random() < 0.5

                        cell = StormCell(
                            id=f"CELL-{len(cells) + 1}",
                            latitude=cell_lat,
                            longitude=cell_lon,
                            intensity=max_intensity,
                            movement_speed=movement_speed,
                            movement_direction=movement_direction,
                            top_height=random.randint(35000, 55000) if max_intensity > 50 else None,
                            has_rotation=has_rotation,
                            rotation_strength=random.uniform(0.005, 0.015) if has_rotation else None,
                            hail_probability=min(100, int((max_intensity - 40) * 2.5)),
                            max_hail_size=round(random.uniform(0.5, 2.5), 1) if max_intensity > 55 else None,
                            tvs=tvs,
                            meso=meso,
                            timestamp=radar_data.timestamp
                        )
                        cells.append(cell)

        return cells
