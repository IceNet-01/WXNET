"""National Weather Service API client."""

import aiohttp
from datetime import datetime
from typing import List, Optional, Dict, Any
from ..models import WeatherAlert, AlertSeverity, AlertStatus, Forecast, ForecastPeriod, CurrentWeather
from ..config import config


class NWSClient:
    """Client for National Weather Service API."""

    BASE_URL = "https://api.weather.gov"

    def __init__(self):
        """Initialize NWS client."""
        self.headers = {
            "User-Agent": config.nws_user_agent,
            "Accept": "application/geo+json"
        }
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Enter async context."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self.session:
            await self.session.close()

    async def get_alerts(self, latitude: float, longitude: float) -> List[WeatherAlert]:
        """Get active weather alerts for a location.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            List of active weather alerts
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        url = f"{self.BASE_URL}/alerts/active"
        params = {
            "point": f"{latitude},{longitude}",
            "status": "actual",
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                alerts = []

                for feature in data.get("features", []):
                    props = feature.get("properties", {})

                    # Parse severity
                    severity_str = props.get("severity", "Unknown")
                    try:
                        severity = AlertSeverity(severity_str)
                    except ValueError:
                        severity = AlertSeverity.UNKNOWN

                    # Parse status
                    status_str = props.get("status", "Actual")
                    try:
                        status = AlertStatus(status_str)
                    except ValueError:
                        status = AlertStatus.ACTUAL

                    # Parse timestamps
                    onset = None
                    if props.get("onset"):
                        try:
                            onset = datetime.fromisoformat(props["onset"].replace("Z", "+00:00"))
                        except:
                            pass

                    expires = None
                    if props.get("expires"):
                        try:
                            expires = datetime.fromisoformat(props["expires"].replace("Z", "+00:00"))
                        except:
                            pass

                    alert = WeatherAlert(
                        id=props.get("id", ""),
                        event=props.get("event", "Unknown"),
                        headline=props.get("headline"),
                        description=props.get("description"),
                        instruction=props.get("instruction"),
                        severity=severity,
                        certainty=props.get("certainty"),
                        urgency=props.get("urgency"),
                        status=status,
                        onset=onset,
                        expires=expires,
                        sender_name=props.get("senderName"),
                        areas=props.get("areaDesc", "").split("; ") if props.get("areaDesc") else []
                    )
                    alerts.append(alert)

                return alerts

        except Exception as e:
            print(f"Error fetching alerts: {e}")
            return []

    async def get_forecast(self, latitude: float, longitude: float) -> Optional[Forecast]:
        """Get forecast for a location.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Forecast data or None
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            # First get the grid point
            point_url = f"{self.BASE_URL}/points/{latitude},{longitude}"
            async with self.session.get(point_url) as response:
                if response.status != 200:
                    return None

                point_data = await response.json()
                forecast_url = point_data.get("properties", {}).get("forecast")

                if not forecast_url:
                    return None

            # Get the forecast
            async with self.session.get(forecast_url) as response:
                if response.status != 200:
                    return None

                forecast_data = await response.json()
                properties = forecast_data.get("properties", {})

                periods = []
                for period_data in properties.get("periods", []):
                    period = ForecastPeriod(
                        name=period_data.get("name", ""),
                        temperature=period_data.get("temperature", 0),
                        temperature_trend=period_data.get("temperatureTrend"),
                        wind_speed=period_data.get("windSpeed", ""),
                        wind_direction=period_data.get("windDirection", ""),
                        short_forecast=period_data.get("shortForecast", ""),
                        detailed_forecast=period_data.get("detailedForecast", ""),
                        precipitation_probability=period_data.get("probabilityOfPrecipitation", {}).get("value"),
                        dewpoint=period_data.get("dewpoint", {}).get("value")
                    )
                    periods.append(period)

                updated_str = properties.get("updated", "")
                try:
                    updated = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                except:
                    updated = datetime.now()

                return Forecast(periods=periods, updated=updated)

        except Exception as e:
            print(f"Error fetching forecast: {e}")
            return None

    async def get_observation(self, latitude: float, longitude: float) -> Optional[CurrentWeather]:
        """Get current weather observation.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Current weather data or None
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            # First get the grid point
            point_url = f"{self.BASE_URL}/points/{latitude},{longitude}"
            async with self.session.get(point_url) as response:
                if response.status != 200:
                    return None

                point_data = await response.json()
                stations_url = point_data.get("properties", {}).get("observationStations")

                if not stations_url:
                    return None

            # Get the nearest station
            async with self.session.get(stations_url) as response:
                if response.status != 200:
                    return None

                stations_data = await response.json()
                stations = stations_data.get("features", [])

                if not stations:
                    return None

                station_id = stations[0].get("properties", {}).get("stationIdentifier")

            # Get latest observation
            obs_url = f"{self.BASE_URL}/stations/{station_id}/observations/latest"
            async with self.session.get(obs_url) as response:
                if response.status != 200:
                    return None

                obs_data = await response.json()
                props = obs_data.get("properties", {})

                # Helper to get value from unit dict
                def get_value(data: Optional[Dict], default=0):
                    if data is None:
                        return default
                    return data.get("value", default) if isinstance(data, dict) else default

                # Convert Celsius to Fahrenheit
                temp_c = get_value(props.get("temperature"))
                temp_f = temp_c * 9/5 + 32 if temp_c else 0

                feels_c = get_value(props.get("heatIndex")) or get_value(props.get("windChill")) or temp_c
                feels_f = feels_c * 9/5 + 32 if feels_c else temp_f

                dewpoint_c = get_value(props.get("dewpoint"))
                dewpoint_f = dewpoint_c * 9/5 + 32 if dewpoint_c else None

                # Convert m/s to mph for wind
                wind_ms = get_value(props.get("windSpeed"))
                wind_mph = wind_ms * 2.237 if wind_ms else 0

                gust_ms = get_value(props.get("windGust"))
                gust_mph = gust_ms * 2.237 if gust_ms else None

                # Convert Pa to inHg for pressure
                pressure_pa = get_value(props.get("barometricPressure"))
                pressure_inhg = pressure_pa * 0.0002953 if pressure_pa else 0

                # Convert meters to miles for visibility
                vis_m = get_value(props.get("visibility"))
                vis_mi = vis_m * 0.000621371 if vis_m else None

                timestamp_str = props.get("timestamp", "")
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.now()

                return CurrentWeather(
                    temperature=round(temp_f, 1),
                    feels_like=round(feels_f, 1),
                    humidity=int(get_value(props.get("relativeHumidity"))),
                    pressure=round(pressure_inhg, 2),
                    wind_speed=round(wind_mph, 1),
                    wind_direction=int(get_value(props.get("windDirection"))),
                    wind_gust=round(gust_mph, 1) if gust_mph else None,
                    visibility=round(vis_mi, 1) if vis_mi else None,
                    clouds=int(get_value(props.get("cloudLayers", [{}])[0].get("amount") if props.get("cloudLayers") else 0)),
                    dewpoint=round(dewpoint_f, 1) if dewpoint_f else None,
                    conditions=props.get("textDescription", "Unknown"),
                    timestamp=timestamp
                )

        except Exception as e:
            print(f"Error fetching observation: {e}")
            return None
