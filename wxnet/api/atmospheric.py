"""Atmospheric data API client."""

import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any
from ..models import AtmosphericData
import random


class AtmosphericClient:
    """Client for atmospheric parameters."""

    def __init__(self):
        """Initialize atmospheric client."""
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Enter async context."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self.session:
            await self.session.close()

    async def get_atmospheric_data(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[AtmosphericData]:
        """Get atmospheric parameters for severe weather analysis.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Atmospheric data or None
        """
        # In production, this would fetch from sources like:
        # - RAP/RUC model data
        # - SPC mesoanalysis
        # - Upper air soundings
        # For now, generate realistic simulated data

        return self._generate_simulated_atmospheric_data()

    def _generate_simulated_atmospheric_data(self) -> AtmosphericData:
        """Generate simulated atmospheric data.

        Returns:
            Simulated atmospheric parameters
        """
        # Generate realistic values for severe weather environment
        cape = random.uniform(500, 4000)  # J/kg
        cin = random.uniform(-100, -10)  # J/kg
        helicity = random.uniform(100, 500)  # m²/s²
        shear = random.uniform(20, 60)  # knots
        lifted_index = random.uniform(-8, 2)
        k_index = random.uniform(20, 40)
        total_totals = random.uniform(45, 60)

        return AtmosphericData(
            cape=round(cape, 1),
            cin=round(cin, 1),
            helicity=round(helicity, 1),
            shear=round(shear, 1),
            lifted_index=round(lifted_index, 1),
            k_index=round(k_index, 1),
            total_totals=round(total_totals, 1),
            timestamp=datetime.now()
        )


class SPCClient:
    """Client for Storm Prediction Center data."""

    BASE_URL = "https://www.spc.noaa.gov"

    def __init__(self):
        """Initialize SPC client."""
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Enter async context."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self.session:
            await self.session.close()

    async def get_convective_outlook(self, day: int = 1) -> Optional[Dict[str, Any]]:
        """Get SPC convective outlook.

        Args:
            day: Outlook day (1, 2, or 3)

        Returns:
            Convective outlook data or None
        """
        # In production, this would parse actual SPC outlook products
        # For now, return simulated data
        return {
            "day": day,
            "categorical_risk": random.choice(["TSTM", "MRGL", "SLGT", "ENH", "MDT"]),
            "tornado_risk": random.choice(["2%", "5%", "10%", "15%"]),
            "wind_risk": random.choice(["5%", "15%", "30%", "45%"]),
            "hail_risk": random.choice(["5%", "15%", "30%", "45%"]),
        }

    async def get_mesoscale_discussions(self) -> list:
        """Get active mesoscale discussions.

        Returns:
            List of mesoscale discussions
        """
        # In production, would fetch actual MD products
        return []

    async def get_watches(self) -> list:
        """Get active severe weather watches.

        Returns:
            List of watches
        """
        # In production, would fetch actual watch products
        return []
