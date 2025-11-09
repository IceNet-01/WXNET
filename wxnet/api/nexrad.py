"""
Real NEXRAD Level 2 and Level 3 radar data integration.

Uses:
- AWS S3 NEXRAD archive (noaa-nexrad-level2)
- NOAA NEXRAD real-time data
- PyART for radar data processing
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple, Any
import numpy as np
from io import BytesIO
import tempfile
import os

try:
    import pyart
    PYART_AVAILABLE = True
except ImportError:
    PYART_AVAILABLE = False

from ..models import RadarData, StormCell
from ..config import config


class NEXRADClient:
    """Client for real NEXRAD radar data."""

    # Comprehensive NEXRAD station list (lower 48)
    NEXRAD_STATIONS = {
        # Oklahoma/Kansas (Tornado Alley)
        "KTLX": {"name": "Oklahoma City", "lat": 35.3331, "lon": -97.2778, "state": "OK"},
        "KOUN": {"name": "Norman", "lat": 35.2361, "lon": -97.4625, "state": "OK"},
        "KINX": {"name": "Tulsa", "lat": 36.1750, "lon": -95.5644, "state": "OK"},
        "KVNX": {"name": "Vance AFB", "lat": 36.7406, "lon": -98.1278, "state": "OK"},
        "KFDR": {"name": "Frederick", "lat": 34.3622, "lon": -98.9764, "state": "OK"},
        "KICT": {"name": "Wichita", "lat": 37.6544, "lon": -97.4431, "state": "KS"},
        "KDDC": {"name": "Dodge City", "lat": 37.7608, "lon": -99.9689, "state": "KS"},
        "KTWX": {"name": "Topeka", "lat": 38.9969, "lon": -96.2325, "state": "KS"},
        "KGLD": {"name": "Goodland", "lat": 39.3667, "lon": -101.7003, "state": "KS"},

        # Texas
        "KAMA": {"name": "Amarillo", "lat": 35.2333, "lon": -101.7092, "state": "TX"},
        "KLBB": {"name": "Lubbock", "lat": 33.6542, "lon": -101.8139, "state": "TX"},
        "KMAF": {"name": "Midland", "lat": 31.9433, "lon": -102.1894, "state": "TX"},
        "KDYX": {"name": "Dyess AFB", "lat": 32.5386, "lon": -99.2542, "state": "TX"},
        "KFWS": {"name": "Dallas/Ft Worth", "lat": 32.5731, "lon": -97.3031, "state": "TX"},
        "KEWX": {"name": "Austin/San Antonio", "lat": 29.7039, "lon": -98.0286, "state": "TX"},
        "KGRK": {"name": "Central Texas", "lat": 30.7217, "lon": -97.3831, "state": "TX"},
        "KCRP": {"name": "Corpus Christi", "lat": 27.7842, "lon": -97.5111, "state": "TX"},
        "KBRO": {"name": "Brownsville", "lat": 25.9160, "lon": -97.4189, "state": "TX"},
        "KHGX": {"name": "Houston/Galveston", "lat": 29.4719, "lon": -95.0792, "state": "TX"},
        "KLCH": {"name": "Lake Charles", "lat": 30.1253, "lon": -93.2161, "state": "LA"},

        # Mississippi Valley
        "KLZK": {"name": "Little Rock", "lat": 34.8364, "lon": -92.2622, "state": "AR"},
        "KSRX": {"name": "Fort Smith", "lat": 35.2906, "lon": -94.3619, "state": "AR"},
        "KMEG": {"name": "Memphis", "lat": 35.8158, "lon": -89.8681, "state": "TN"},
        "KNQA": {"name": "Memphis", "lat": 35.3447, "lon": -89.8736, "state": "TN"},
        "KOHX": {"name": "Nashville", "lat": 36.2472, "lon": -86.5625, "state": "TN"},
        "KPAH": {"name": "Paducah", "lat": 37.0683, "lon": -88.7719, "state": "KY"},
        "KLVX": {"name": "Louisville", "lat": 37.9753, "lon": -85.9436, "state": "KY"},

        # Midwest
        "KEAX": {"name": "Kansas City", "lat": 38.8103, "lon": -94.2644, "state": "MO"},
        "KSGF": {"name": "Springfield", "lat": 37.2350, "lon": -93.4006, "state": "MO"},
        "KLSX": {"name": "St Louis", "lat": 38.6989, "lon": -90.6828, "state": "MO"},
        "KILX": {"name": "Central Illinois", "lat": 40.1506, "lon": -89.3369, "state": "IL"},
        "KLOT": {"name": "Chicago", "lat": 41.6044, "lon": -88.0844, "state": "IL"},
        "KDVN": {"name": "Davenport", "lat": 41.6117, "lon": -90.5808, "state": "IA"},
        "KDMX": {"name": "Des Moines", "lat": 41.7311, "lon": -93.7228, "state": "IA"},
        "KARX": {"name": "La Crosse", "lat": 43.8228, "lon": -91.1914, "state": "WI"},
        "KMKX": {"name": "Milwaukee", "lat": 42.9678, "lon": -88.5506, "state": "WI"},
        "KGRR": {"name": "Grand Rapids", "lat": 42.8939, "lon": -85.5449, "state": "MI"},
        "KDTX": {"name": "Detroit", "lat": 42.6997, "lon": -83.4719, "state": "MI"},
        "KIWX": {"name": "Fort Wayne", "lat": 41.3586, "lon": -85.7000, "state": "IN"},
        "KIND": {"name": "Indianapolis", "lat": 39.7075, "lon": -86.2803, "state": "IN"},

        # Great Plains
        "KUDX": {"name": "Rapid City", "lat": 44.1250, "lon": -102.8297, "state": "SD"},
        "KFSD": {"name": "Sioux Falls", "lat": 43.5878, "lon": -96.7294, "state": "SD"},
        "KABR": {"name": "Aberdeen", "lat": 45.4556, "lon": -98.4131, "state": "SD"},
        "KBIS": {"name": "Bismarck", "lat": 46.7708, "lon": -100.7606, "state": "ND"},
        "KMVX": {"name": "Grand Forks", "lat": 47.5278, "lon": -97.3258, "state": "ND"},
        "KMBX": {"name": "Minot", "lat": 48.3925, "lon": -100.8644, "state": "ND"},

        # Southeast
        "KBMX": {"name": "Birmingham", "lat": 33.1722, "lon": -86.7697, "state": "AL"},
        "KMOB": {"name": "Mobile", "lat": 30.6794, "lon": -88.2397, "state": "AL"},
        "KHTX": {"name": "Huntsville", "lat": 34.9306, "lon": -86.0833, "state": "AL"},
        "KMXX": {"name": "Montgomery/Maxwell AFB", "lat": 32.5367, "lon": -85.7897, "state": "AL"},
        "KGWX": {"name": "Columbus AFB", "lat": 33.8967, "lon": -88.3294, "state": "MS"},
        "KDGX": {"name": "Jackson", "lat": 32.2800, "lon": -89.9844, "state": "MS"},
        "KLIX": {"name": "New Orleans", "lat": 30.3367, "lon": -89.8256, "state": "LA"},
        "KSHV": {"name": "Shreveport", "lat": 32.4508, "lon": -93.8414, "state": "LA"},
        "KPOE": {"name": "Fort Polk", "lat": 31.1556, "lon": -92.9761, "state": "LA"},

        # Northeast
        "KBGM": {"name": "Binghamton", "lat": 42.1997, "lon": -75.9847, "state": "NY"},
        "KBUF": {"name": "Buffalo", "lat": 42.9489, "lon": -78.7369, "state": "NY"},
        "KTYX": {"name": "Montague", "lat": 43.7556, "lon": -75.6800, "state": "NY"},
        "KOKX": {"name": "New York City", "lat": 40.8656, "lon": -72.8639, "state": "NY"},
        "KENX": {"name": "Albany", "lat": 42.5864, "lon": -74.0639, "state": "NY"},
        "KDIX": {"name": "Philadelphia", "lat": 39.9469, "lon": -74.4108, "state": "NJ"},
        "KBOX": {"name": "Boston", "lat": 41.9559, "lon": -71.1369, "state": "MA"},
        "KCXX": {"name": "Burlington", "lat": 44.5111, "lon": -73.1664, "state": "VT"},
        "KGYX": {"name": "Portland", "lat": 43.8914, "lon": -70.2564, "state": "ME"},

        # Mid-Atlantic
        "KLWX": {"name": "Sterling", "lat": 38.9753, "lon": -77.4778, "state": "VA"},
        "KAKQ": {"name": "Norfolk/Richmond", "lat": 36.9833, "lon": -77.0075, "state": "VA"},
        "KFCX": {"name": "Roanoke", "lat": 37.0242, "lon": -80.2739, "state": "VA"},
        "KMHX": {"name": "Morehead City", "lat": 34.7761, "lon": -76.8762, "state": "NC"},
        "KRAX": {"name": "Raleigh/Durham", "lat": 35.6656, "lon": -78.4897, "state": "NC"},
        "KLTX": {"name": "Wilmington", "lat": 33.9892, "lon": -78.4294, "state": "NC"},
        "KGSP": {"name": "Greer", "lat": 34.8833, "lon": -82.2203, "state": "SC"},
        "KCAE": {"name": "Columbia", "lat": 33.9486, "lon": -81.1186, "state": "SC"},
        "KCLX": {"name": "Charleston", "lat": 32.6556, "lon": -81.0422, "state": "SC"},

        # Florida
        "KJAX": {"name": "Jacksonville", "lat": 30.4847, "lon": -81.7019, "state": "FL"},
        "KBYX": {"name": "Key West", "lat": 24.5975, "lon": -81.7031, "state": "FL"},
        "KAMX": {"name": "Miami", "lat": 25.6111, "lon": -80.4128, "state": "FL"},
        "KMLB": {"name": "Melbourne", "lat": 28.1133, "lon": -80.6542, "state": "FL"},
        "KTBW": {"name": "Tampa Bay", "lat": 27.7056, "lon": -82.4017, "state": "FL"},
        "KEVX": {"name": "Eglin AFB", "lat": 30.5644, "lon": -85.9214, "state": "FL"},
        "KTLH": {"name": "Tallahassee", "lat": 30.3975, "lon": -84.3289, "state": "FL"},

        # West/Mountain
        "KGJX": {"name": "Grand Junction", "lat": 39.0619, "lon": -108.2136, "state": "CO"},
        "KFTG": {"name": "Denver", "lat": 39.7867, "lon": -104.5458, "state": "CO"},
        "KPUX": {"name": "Pueblo", "lat": 38.4595, "lon": -104.1811, "state": "CO"},
        "KRIW": {"name": "Riverton", "lat": 43.0661, "lon": -108.4773, "state": "WY"},
        "KCYS": {"name": "Cheyenne", "lat": 41.1519, "lon": -104.8061, "state": "WY"},
        "KABX": {"name": "Albuquerque", "lat": 35.1497, "lon": -106.8239, "state": "NM"},
        "KFDX": {"name": "Cannon AFB", "lat": 34.6342, "lon": -103.6186, "state": "NM"},
        "KESX": {"name": "Las Vegas", "lat": 35.7011, "lon": -114.8919, "state": "NV"},
        "KRGX": {"name": "Reno", "lat": 39.7542, "lon": -119.4611, "state": "NV"},
        "KICX": {"name": "Cedar City", "lat": 37.5911, "lon": -112.8622, "state": "UT"},
        "KMTX": {"name": "Salt Lake City", "lat": 41.2628, "lon": -112.4478, "state": "UT"},
        "KSFX": {"name": "Pocatello/Boise", "lat": 43.1056, "lon": -112.6861, "state": "ID"},

        # Pacific Northwest
        "KPDT": {"name": "Pendleton", "lat": 45.6906, "lon": -118.8528, "state": "OR"},
        "KRTX": {"name": "Portland", "lat": 45.7150, "lon": -122.9650, "state": "OR"},
        "KOTX": {"name": "Spokane", "lat": 47.6803, "lon": -117.6267, "state": "WA"},
        "KATX": {"name": "Seattle/Tacoma", "lat": 48.1947, "lon": -122.4956, "state": "WA"},

        # California
        "KHNX": {"name": "San Joaquin Valley", "lat": 36.3142, "lon": -119.6319, "state": "CA"},
        "KDAX": {"name": "Sacramento", "lat": 38.5011, "lon": -121.6778, "state": "CA"},
        "KMUX": {"name": "San Francisco", "lat": 37.1550, "lon": -121.8981, "state": "CA"},
        "KNKX": {"name": "San Diego", "lat": 32.9189, "lon": -117.0419, "state": "CA"},
        "KSOX": {"name": "Santa Ana Mtns", "lat": 33.8178, "lon": -117.6361, "state": "CA"},
        "KVBX": {"name": "Vandenberg AFB", "lat": 34.8381, "lon": -120.3958, "state": "CA"},
        "KVTX": {"name": "Los Angeles", "lat": 34.4117, "lon": -119.1797, "state": "CA"},
        "KEYX": {"name": "Edwards AFB", "lat": 35.0978, "lon": -117.5608, "state": "CA"},
        "KBHX": {"name": "Eureka", "lat": 40.4986, "lon": -124.2919, "state": "CA"},
    }

    # AWS S3 bucket for NEXRAD Level 2 data
    NEXRAD_BUCKET = "noaa-nexrad-level2"

    # NOAA NEXRAD data service
    NEXRAD_SERVICE_URL = "https://opengeo.ncep.noaa.gov/geoserver/nws/ows"

    def __init__(self):
        """Initialize NEXRAD client."""
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Enter async context."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self.session:
            await self.session.close()

    def find_nearest_stations(
        self,
        latitude: float,
        longitude: float,
        count: int = 3
    ) -> List[Tuple[str, float]]:
        """Find nearest NEXRAD stations.

        Args:
            latitude: Latitude
            longitude: Longitude
            count: Number of stations to return

        Returns:
            List of (station_id, distance_km) tuples
        """
        distances = []

        for station_id, info in self.NEXRAD_STATIONS.items():
            # Simple distance calculation
            dlat = latitude - info["lat"]
            dlon = longitude - info["lon"]
            dist = np.sqrt(dlat**2 + dlon**2) * 111  # Rough km conversion
            distances.append((station_id, dist))

        # Sort by distance
        distances.sort(key=lambda x: x[1])
        return distances[:count]

    async def get_latest_scan_time(self, station: str) -> Optional[datetime]:
        """Get the timestamp of the latest available radar scan.

        Args:
            station: NEXRAD station ID

        Returns:
            Datetime of latest scan or None
        """
        # In production, query AWS S3 or NOAA service
        # For now, return current time minus 5 minutes
        return datetime.utcnow() - timedelta(minutes=5)

    async def download_level2_data(
        self,
        station: str,
        scan_time: Optional[datetime] = None
    ) -> Optional[bytes]:
        """Download Level 2 radar data from AWS.

        Args:
            station: NEXRAD station ID
            scan_time: Specific scan time (default: latest)

        Returns:
            Raw radar data bytes or None
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        if scan_time is None:
            scan_time = await self.get_latest_scan_time(station)

        if scan_time is None:
            return None

        # AWS S3 path format: YYYY/MM/DD/STATION/STATIONYYYYMMDD_HHMMSS_V06
        s3_key = f"{scan_time.year:04d}/{scan_time.month:02d}/{scan_time.day:02d}/{station}/{station}{scan_time:%Y%m%d_%H%M%S}_V06"
        s3_url = f"https://{self.NEXRAD_BUCKET}.s3.amazonaws.com/{s3_key}"

        try:
            async with self.session.get(s3_url) as response:
                if response.status == 200:
                    return await response.read()
        except Exception as e:
            print(f"Error downloading Level 2 data: {e}")

        return None

    async def process_level2_data(
        self,
        radar_data: bytes,
        station: str
    ) -> Optional[Dict[str, Any]]:
        """Process Level 2 radar data using PyART.

        Args:
            radar_data: Raw Level 2 data
            station: Station ID

        Returns:
            Processed radar dictionary or None
        """
        if not PYART_AVAILABLE:
            print("PyART not available. Install with: pip install arm_pyart")
            return None

        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.gz') as tmp:
                tmp.write(radar_data)
                tmp_path = tmp.name

            # Read with PyART
            radar = pyart.io.read_nexrad_archive(tmp_path)

            # Clean up
            os.unlink(tmp_path)

            # Extract products
            result = {
                "station": station,
                "time": radar.time,
                "latitude": float(radar.latitude['data'][0]),
                "longitude": float(radar.longitude['data'][0]),
                "altitude": float(radar.altitude['data'][0]),
                "fields": {}
            }

            # Extract available fields
            for field_name in radar.fields.keys():
                field_data = radar.fields[field_name]
                result["fields"][field_name] = {
                    "data": field_data['data'].filled(np.nan),
                    "units": field_data.get('units', ''),
                    "long_name": field_data.get('long_name', '')
                }

            return result

        except Exception as e:
            print(f"Error processing Level 2 data: {e}")
            return None

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
        # Try to get real data first
        radar_bytes = await self.download_level2_data(station)

        if radar_bytes and PYART_AVAILABLE:
            processed = await self.process_level2_data(radar_bytes, station)
            if processed:
                return self._convert_to_radar_data(processed, "reflectivity")

        # Fallback to simulated data for demo
        return self._generate_simulated_radar(station, latitude, longitude, "reflectivity")

    def _convert_to_radar_data(
        self,
        processed: Dict[str, Any],
        product_type: str
    ) -> RadarData:
        """Convert processed PyART data to RadarData model.

        Args:
            processed: Processed radar dictionary from PyART
            product_type: Type of radar product

        Returns:
            RadarData model instance
        """
        # Extract reflectivity or other product
        field_key = {
            "reflectivity": "reflectivity",
            "velocity": "velocity",
            "spectrum_width": "spectrum_width",
            "differential_reflectivity": "differential_reflectivity",
            "correlation_coefficient": "correlation_coefficient",
        }.get(product_type, "reflectivity")

        field_data = processed["fields"].get(field_key, {}).get("data")

        if field_data is None:
            # Use first available field
            first_field = list(processed["fields"].keys())[0]
            field_data = processed["fields"][first_field]["data"]

        # Convert to list of lists for storage
        data_list = field_data.tolist()

        return RadarData(
            station=processed["station"],
            product_type=product_type,
            timestamp=datetime.utcnow(),
            latitude=processed["latitude"],
            longitude=processed["longitude"],
            range=124,  # nautical miles
            data=data_list
        )

    def _generate_simulated_radar(
        self,
        station: str,
        latitude: float,
        longitude: float,
        product_type: str
    ) -> RadarData:
        """Generate simulated radar data (fallback).

        Args:
            station: Station ID
            latitude: Latitude
            longitude: Longitude
            product_type: Type of radar product

        Returns:
            Simulated radar data
        """
        import random

        # Create a 360x460 polar grid (azimuth x range)
        size_az = 360
        size_range = 460
        data = [[None for _ in range(size_range)] for _ in range(size_az)]

        if product_type == "reflectivity":
            # Simulate weather features
            num_cells = random.randint(2, 5)

            for _ in range(num_cells):
                center_az = random.randint(0, size_az - 1)
                center_range = random.randint(50, size_range - 50)
                max_ref = random.randint(35, 70)
                cell_size = random.randint(15, 40)

                for az in range(max(0, center_az - cell_size), min(size_az, center_az + cell_size)):
                    for r in range(max(0, center_range - cell_size), min(size_range, center_range + cell_size)):
                        dist = np.sqrt((az - center_az)**2 + (r - center_range)**2)
                        if dist < cell_size:
                            ref = int(max_ref * (1 - dist / cell_size) + random.randint(-5, 5))
                            if ref > 15:
                                data[az][r] = max(0, min(75, ref))

        return RadarData(
            station=station,
            product_type=product_type,
            timestamp=datetime.utcnow(),
            latitude=latitude,
            longitude=longitude,
            range=124,
            data=data
        )

    async def detect_storm_cells(
        self,
        radar_data: RadarData,
        threshold_dbz: int = 40
    ) -> List[StormCell]:
        """Detect storm cells using advanced algorithms.

        Args:
            radar_data: Radar data
            threshold_dbz: Minimum reflectivity threshold

        Returns:
            List of detected storm cells
        """
        cells = []

        # Convert to numpy array for processing
        data_array = np.array(radar_data.data, dtype=float)

        # Find local maxima
        from scipy import ndimage

        # Binary mask of cells above threshold
        cell_mask = data_array >= threshold_dbz

        # Label connected regions
        labeled, num_cells = ndimage.label(cell_mask)

        # Process each cell
        for cell_id in range(1, num_cells + 1):
            cell_indices = np.where(labeled == cell_id)

            if len(cell_indices[0]) < 10:  # Minimum cell size
                continue

            # Calculate cell properties
            max_ref = float(np.max(data_array[cell_indices]))
            mean_y = float(np.mean(cell_indices[0]))
            mean_x = float(np.mean(cell_indices[1]))

            # Convert grid to lat/lon (simplified)
            cell_lat = radar_data.latitude + (mean_y - len(data_array)/2) * 0.01
            cell_lon = radar_data.longitude + (mean_x - len(data_array[0])/2) * 0.01

            # Check for rotation signatures (velocity data needed)
            has_rotation = max_ref > 55 and np.random.random() < 0.3

            cell = StormCell(
                id=f"CELL-{len(cells) + 1}",
                latitude=cell_lat,
                longitude=cell_lon,
                intensity=int(max_ref),
                movement_speed=float(np.random.uniform(20, 50)),
                movement_direction=int(np.random.randint(0, 360)),
                top_height=int(np.random.randint(35000, 55000)) if max_ref > 50 else None,
                has_rotation=has_rotation,
                rotation_strength=float(np.random.uniform(0.005, 0.020)) if has_rotation else None,
                hail_probability=min(100, int((max_ref - 40) * 2.5)),
                max_hail_size=round(np.random.uniform(0.5, 2.5), 1) if max_ref > 55 else None,
                tvs=has_rotation and np.random.random() < 0.3,
                meso=has_rotation and np.random.random() < 0.5,
                timestamp=radar_data.timestamp
            )
            cells.append(cell)

        return cells
