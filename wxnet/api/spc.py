"""
Storm Prediction Center (SPC) products integration.

Provides:
- Convective outlooks (Day 1, 2, 3)
- Mesoscale discussions
- Tornado/Severe thunderstorm watches
- Storm reports (tornado, hail, wind)
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import re
from bs4 import BeautifulSoup
import csv
from io import StringIO

from ..models import ConvectiveOutlook, StormReport
from ..config import config


class SPCProductsClient:
    """Client for Storm Prediction Center products."""

    BASE_URL = "https://www.spc.noaa.gov"

    # Product URLs
    OUTLOOK_URL = f"{BASE_URL}/products/outlook"
    MD_URL = f"{BASE_URL}/products/md"
    WATCH_URL = f"{BASE_URL}/products/watch"
    REPORTS_URL = f"{BASE_URL}/climo/reports"

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
            Parsed outlook data or None
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        if day not in [1, 2, 3]:
            day = 1

        try:
            # Get the outlook text
            url = f"{self.OUTLOOK_URL}/day{day}otlk.html"
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Parse outlook text
                pre_text = soup.find('pre')
                if not pre_text:
                    return None

                outlook_text = pre_text.get_text()

                # Extract categorical risk
                categorical = self._extract_categorical_risk(outlook_text)

                # Extract probabilities
                tornado_prob = self._extract_probability(outlook_text, "tornado")
                wind_prob = self._extract_probability(outlook_text, "wind")
                hail_prob = self._extract_probability(outlook_text, "hail")

                # Extract valid times
                valid_time, expire_time = self._extract_times(outlook_text)

                # Extract discussion summary
                summary = self._extract_summary(outlook_text)

                return {
                    "day": day,
                    "valid_time": valid_time,
                    "expire_time": expire_time,
                    "categorical_risk": categorical,
                    "tornado_risk": tornado_prob,
                    "wind_risk": wind_prob,
                    "hail_risk": hail_prob,
                    "summary": summary,
                    "text": outlook_text
                }

        except Exception as e:
            print(f"Error fetching convective outlook: {e}")
            return None

    def _extract_categorical_risk(self, text: str) -> str:
        """Extract categorical risk level from outlook text."""
        risk_levels = ["HIGH", "MDT", "MODERATE", "ENH", "ENHANCED", "SLGT", "SLIGHT", "MRGL", "MARGINAL", "TSTM", "GENERAL THUNDER"]

        text_upper = text.upper()

        for risk in risk_levels:
            if risk in text_upper:
                # Normalize names
                if risk in ["MDT", "MODERATE"]:
                    return "MDT"
                elif risk in ["ENH", "ENHANCED"]:
                    return "ENH"
                elif risk in ["SLGT", "SLIGHT"]:
                    return "SLGT"
                elif risk in ["MRGL", "MARGINAL"]:
                    return "MRGL"
                elif risk in ["TSTM", "GENERAL THUNDER"]:
                    return "TSTM"
                elif risk == "HIGH":
                    return "HIGH"

        return "TSTM"

    def _extract_probability(self, text: str, hazard: str) -> Optional[str]:
        """Extract probability for specific hazard."""
        # Look for patterns like "10% tornado", "SIG 10 tornado", etc.
        patterns = [
            rf"(\d+)%\s+{hazard}",
            rf"{hazard}\s+(\d+)%",
            rf"SIG\s+(\d+)\s+{hazard}",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                prob = match.group(1)
                return f"{prob}%"

        return None

    def _extract_times(self, text: str) -> tuple:
        """Extract valid and expire times from outlook."""
        # Look for patterns like "VALID 151300Z - 160600Z"
        time_pattern = r"VALID\s+(\d{6})Z\s*-\s*(\d{6})Z"
        match = re.search(time_pattern, text)

        now = datetime.utcnow()

        if match:
            valid_str = match.group(1)
            expire_str = match.group(2)

            # Parse DDHHMM format
            valid_day = int(valid_str[:2])
            valid_hour = int(valid_str[2:4])
            valid_min = int(valid_str[4:6])

            expire_day = int(expire_str[:2])
            expire_hour = int(expire_str[2:4])
            expire_min = int(expire_str[4:6])

            # Construct datetimes
            valid_time = now.replace(day=valid_day, hour=valid_hour, minute=valid_min, second=0, microsecond=0)
            expire_time = now.replace(day=expire_day, hour=expire_hour, minute=expire_min, second=0, microsecond=0)

            # Handle month boundaries
            if expire_day < valid_day:
                if expire_time.month == 12:
                    expire_time = expire_time.replace(year=expire_time.year + 1, month=1)
                else:
                    expire_time = expire_time.replace(month=expire_time.month + 1)

            return valid_time, expire_time

        return now, now + timedelta(hours=24)

    def _extract_summary(self, text: str) -> str:
        """Extract summary from outlook text."""
        # Try to find the first paragraph after header
        lines = text.split('\n')
        summary_lines = []

        start_collecting = False
        for line in lines:
            line = line.strip()

            # Skip empty lines and headers
            if not line or 'CONVECTIVE OUTLOOK' in line or 'VALID' in line:
                continue

            # Start collecting after headers
            if line and not start_collecting:
                start_collecting = True

            if start_collecting:
                summary_lines.append(line)

                # Stop after 3-4 lines
                if len(summary_lines) >= 4:
                    break

        return ' '.join(summary_lines)[:300] + "..."

    async def get_mesoscale_discussions(self) -> List[Dict[str, Any]]:
        """Get active mesoscale discussions.

        Returns:
            List of mesoscale discussion summaries
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(self.MD_URL) as response:
                if response.status != 200:
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                discussions = []

                # Find MD links (format: mdYYMMDDnnnn.html)
                md_links = soup.find_all('a', href=re.compile(r'md\d{10}\.html'))

                for link in md_links[:5]:  # Get latest 5
                    md_num = re.search(r'md(\d{10})', link['href']).group(1)
                    md_url = f"{self.BASE_URL}/products/md/{link['href']}"

                    # Fetch MD text
                    async with self.session.get(md_url) as md_response:
                        if md_response.status == 200:
                            md_html = await md_response.text()
                            md_soup = BeautifulSoup(md_html, 'html.parser')
                            md_text = md_soup.find('pre')

                            if md_text:
                                discussions.append({
                                    "number": md_num,
                                    "url": md_url,
                                    "text": md_text.get_text(),
                                    "summary": self._extract_md_summary(md_text.get_text())
                                })

                return discussions

        except Exception as e:
            print(f"Error fetching mesoscale discussions: {e}")
            return []

    def _extract_md_summary(self, text: str) -> str:
        """Extract summary from MD text."""
        # Look for "SUMMARY" section
        summary_match = re.search(r'SUMMARY[.\s]+(.*?)(?=\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)

        if summary_match:
            return summary_match.group(1).strip()[:200]

        # Fallback to first few lines
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        return ' '.join(lines[2:5])[:200]

    async def get_active_watches(self) -> List[Dict[str, Any]]:
        """Get active tornado/severe thunderstorm watches.

        Returns:
            List of active watches
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(self.WATCH_URL) as response:
                if response.status != 200:
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                watches = []

                # Parse watch table or links
                watch_links = soup.find_all('a', href=re.compile(r'ww\d{4}\.html'))

                for link in watch_links:
                    watch_num = re.search(r'ww(\d{4})', link['href']).group(1)
                    watch_url = f"{self.BASE_URL}/products/watch/{link['href']}"

                    # Determine watch type from text
                    link_text = link.get_text().upper()
                    watch_type = "Tornado" if "TORNADO" in link_text else "Severe Thunderstorm"

                    watches.append({
                        "number": watch_num,
                        "type": watch_type,
                        "url": watch_url,
                        "issued": datetime.utcnow()  # Would parse from actual text
                    })

                return watches

        except Exception as e:
            print(f"Error fetching watches: {e}")
            return []

    async def get_todays_storm_reports(self) -> List[StormReport]:
        """Get today's storm reports (tornado, hail, wind).

        Returns:
            List of storm reports
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        today = datetime.utcnow()
        date_str = today.strftime("%y%m%d")

        # SPC reports are in CSV format
        reports_url = f"{self.REPORTS_URL}/{date_str}_rpts_filtered.csv"

        try:
            async with self.session.get(reports_url) as response:
                if response.status != 200:
                    return []

                csv_text = await response.text()
                return self._parse_storm_reports(csv_text)

        except Exception as e:
            print(f"Error fetching storm reports: {e}")
            return []

    def _parse_storm_reports(self, csv_text: str) -> List[StormReport]:
        """Parse CSV storm reports.

        Args:
            csv_text: CSV content

        Returns:
            List of StormReport objects
        """
        reports = []

        try:
            csv_file = StringIO(csv_text)
            reader = csv.DictReader(csv_file)

            for row in reader:
                # Determine report type
                report_type = "wind"
                if "torn" in str(row.get("type", "")).lower():
                    report_type = "tornado"
                elif "hail" in str(row.get("type", "")).lower():
                    report_type = "hail"

                # Parse location
                lat = float(row.get("lat", 0))
                lon = float(row.get("lon", 0))

                # Parse time
                time_str = row.get("time", "")
                try:
                    report_time = datetime.strptime(time_str, "%H%M")
                    report_time = datetime.utcnow().replace(
                        hour=report_time.hour,
                        minute=report_time.minute,
                        second=0,
                        microsecond=0
                    )
                except:
                    report_time = datetime.utcnow()

                # Create report
                report = StormReport(
                    id=f"RPT-{len(reports) + 1}",
                    type=report_type,
                    latitude=lat,
                    longitude=lon,
                    timestamp=report_time,
                    magnitude=row.get("mag", ""),
                    description=row.get("comments", ""),
                    source=row.get("source", "")
                )
                reports.append(report)

        except Exception as e:
            print(f"Error parsing storm reports: {e}")

        return reports

    async def get_severe_weather_summary(self) -> Dict[str, Any]:
        """Get comprehensive severe weather summary.

        Returns:
            Dictionary with all current products
        """
        # Fetch all products in parallel
        outlook1, outlook2, outlook3, mds, watches, reports = await asyncio.gather(
            self.get_convective_outlook(1),
            self.get_convective_outlook(2),
            self.get_convective_outlook(3),
            self.get_mesoscale_discussions(),
            self.get_active_watches(),
            self.get_todays_storm_reports(),
            return_exceptions=True
        )

        return {
            "outlooks": {
                "day1": outlook1 if not isinstance(outlook1, Exception) else None,
                "day2": outlook2 if not isinstance(outlook2, Exception) else None,
                "day3": outlook3 if not isinstance(outlook3, Exception) else None,
            },
            "mesoscale_discussions": mds if not isinstance(mds, Exception) else [],
            "watches": watches if not isinstance(watches, Exception) else [],
            "storm_reports": reports if not isinstance(reports, Exception) else [],
            "updated": datetime.utcnow()
        }
