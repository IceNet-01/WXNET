"""
WXNET Advanced Application - Professional Severe Weather Monitoring Terminal
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, VerticalScroll
from textual.widgets import Header, Footer, Static, Label, DataTable, TabbedContent, TabPane, Button
from textual.reactive import reactive
from textual.binding import Binding
from rich.text import Text
from rich.table import Table as RichTable
from rich.panel import Panel
from rich.layout import Layout

from .config import config
from .models import WeatherAlert, CurrentWeather, StormCell, AtmosphericData, LightningStrike, Location

# Import new advanced APIs
from .api.nws import NWSClient
from .api.nexrad import NEXRADClient
from .api.spc import SPCProductsClient
from .api.lightning import LightningClient
from .api.mesoanalysis import MesoanalysisClient
from .tracking import GPSTracker, SoundAlerts, ChaseLogger

from .utils import (
    format_temperature, format_wind, format_pressure,
    get_alert_color, get_alert_symbol, format_distance,
    calculate_distance, calculate_bearing, format_bearing,
    render_radar_ascii, format_time_ago,
    format_cape, format_helicity
)


class AlertsPanel(Static):
    """Scrollable panel for weather alerts."""

    alerts: reactive[List[WeatherAlert]] = reactive(list, recompose=True)

    def compose(self) -> ComposeResult:
        """Compose alerts display."""
        with VerticalScroll():
            if not self.alerts:
                yield Label("[dim]No active alerts[/dim]")
            else:
                for alert in self.alerts:
                    severity_color = get_alert_color(alert.severity.value)
                    symbol = get_alert_symbol(alert.event)

                    # Create alert panel
                    alert_text = Text()
                    alert_text.append(f"{symbol} ", style="bold")
                    alert_text.append(alert.event, style=f"bold {severity_color}")
                    alert_text.append(f"\n{', '.join(alert.areas[:3])}", style="dim")

                    if alert.expires:
                        alert_text.append(f"\nExpires: {format_time_ago(alert.expires)}", style="yellow")

                    if alert.description:
                        desc = alert.description[:200] + "..." if len(alert.description) > 200 else alert.description
                        alert_text.append(f"\n{desc}", style="white")

                    yield Static(alert_text)
                    yield Static("─" * 60)


class CurrentConditionsPanel(Static):
    """Panel for current weather conditions."""

    weather: reactive[Optional[CurrentWeather]] = reactive(None, recompose=True)

    def compose(self) -> ComposeResult:
        """Compose current conditions."""
        if not self.weather:
            yield Label("[dim]Loading weather data...[/dim]")
            return

        w = self.weather
        table = RichTable.grid(padding=(0, 2))
        table.add_column(style="bold cyan", width=18)
        table.add_column()

        table.add_row("🌡️  Temperature:", format_temperature(w.temperature))
        table.add_row("🌡️  Feels Like:", format_temperature(w.feels_like))
        if w.dewpoint:
            table.add_row("💧 Dewpoint:", format_temperature(w.dewpoint))
        table.add_row("💦 Humidity:", f"{w.humidity}%")
        table.add_row("🔽 Pressure:", format_pressure(w.pressure))
        table.add_row("💨 Wind:", format_wind(w.wind_speed, w.wind_direction, w.wind_gust))
        if w.visibility:
            table.add_row("👁️  Visibility:", f"{w.visibility:.1f} mi")
        table.add_row("☁️  Conditions:", w.conditions)
        table.add_row("🕐 Updated:", format_time_ago(w.timestamp))

        yield Static(table)


class RadarPanel(Static):
    """Scrollable radar display panel."""

    radar_data: reactive[Optional[Any]] = reactive(None, recompose=True)
    station: reactive[str] = reactive("KTLX")

    def compose(self) -> ComposeResult:
        """Compose radar display."""
        with VerticalScroll():
            if not self.radar_data:
                yield Label("[dim]Loading radar data...[/dim]")
            else:
                # Header
                header = Text()
                header.append(f"📡 NEXRAD RADAR: {self.station}\n", style="bold green")
                header.append(f"Time: {self.radar_data.timestamp.strftime('%H:%M:%S UTC')}\n", style="dim")
                header.append(f"Product: {self.radar_data.product_type.upper()}", style="cyan")
                yield Static(header)

                # Render radar
                ascii_lines = render_radar_ascii(self.radar_data.data, width=100, height=40)
                radar_text = "\n".join(ascii_lines)
                yield Static(radar_text)

                # Legend
                legend = Text("\nREFLECTIVITY SCALE (dBZ):\n", style="bold")
                legend.append("  15-25: Light precip   ", style="blue")
                legend.append("  25-35: Moderate   ", style="green")
                legend.append("  35-45: Heavy   ", style="yellow")
                legend.append("  45-55: Very Heavy   ", style="bright_yellow")
                legend.append("  55-65: Extreme   ", style="red")
                legend.append("  65+: Giant Hail", style="bright_red")
                yield Static(legend)


class StormCellsPanel(Static):
    """Scrollable storm cells panel."""

    cells: reactive[List[StormCell]] = reactive(list, recompose=True)
    location: reactive[tuple] = reactive((35.0, -97.5))
    gps_tracker: Optional[GPSTracker] = None

    def compose(self) -> ComposeResult:
        """Compose storm cells display."""
        with VerticalScroll():
            if not self.cells:
                yield Label("[dim]No storm cells detected[/dim]")
            else:
                lat, lon = self.location

                for i, cell in enumerate(self.cells, 1):
                    # Calculate distance and bearing
                    dist = calculate_distance(lat, lon, cell.latitude, cell.longitude)
                    bearing = calculate_bearing(lat, lon, cell.latitude, cell.longitude)
                    bearing_str = format_bearing(bearing)

                    # Create cell info
                    cell_info = Text()
                    cell_info.append(f"CELL {i}: ", style="bold yellow")

                    # Color code intensity
                    intensity_color = "red" if cell.intensity > 60 else "yellow" if cell.intensity > 50 else "green"
                    cell_info.append(f"{cell.intensity} dBZ  ", style=f"bold {intensity_color}")

                    # Severe indicators
                    if cell.tvs:
                        cell_info.append("[TVS] ", style="bold bright_red blink")
                    if cell.meso:
                        cell_info.append("[MESO] ", style="bold red")
                    if cell.max_hail_size and cell.max_hail_size > 1.0:
                        cell_info.append(f"[HAIL {cell.max_hail_size}\"] ", style="bold magenta")

                    # Location and movement
                    cell_info.append(f"\n   📍 Location: {format_distance(dist)} {bearing_str} ({bearing}°)")
                    cell_info.append(f"\n   🎯 Coordinates: {cell.latitude:.3f}°N, {cell.longitude:.3f}°W")
                    cell_info.append(f"\n   ➡️  Movement: {format_bearing(cell.movement_direction)} @ {cell.movement_speed:.0f} mph")

                    # Severe attributes
                    if cell.has_rotation:
                        cell_info.append(f"\n   🌪️  Rotation: {cell.rotation_strength:.4f}", style="red")
                    if cell.top_height:
                        cell_info.append(f"\n   ⬆️  Top: {cell.top_height:,} ft", style="cyan")
                    if cell.hail_probability > 50:
                        cell_info.append(f"\n   🧊 Hail Prob: {cell.hail_probability}%", style="magenta")

                    # Intercept calculation
                    if self.gps_tracker and self.gps_tracker.current_location:
                        intercept = self.gps_tracker.calculate_intercept(cell)
                        if intercept:
                            cell_info.append(f"\n   🚗 Intercept: {intercept['chase_time_minutes']:.0f} min, {intercept['distance_miles']:.1f} mi @ {format_bearing(intercept['bearing'])}", style="bright_green")

                    yield Static(cell_info)
                    yield Static("─" * 80)


class AtmosphericPanel(Static):
    """Panel for atmospheric parameters."""

    atmos_data: reactive[Optional[AtmosphericData]] = reactive(None, recompose=True)
    sounding: reactive[Optional[Dict]] = reactive(None)

    def compose(self) -> ComposeResult:
        """Compose atmospheric display."""
        with VerticalScroll():
            if not self.atmos_data:
                yield Label("[dim]Loading atmospheric data...[/dim]")
            else:
                data = self.atmos_data

                # Create parameters table
                table = RichTable.grid(padding=(0, 2))
                table.add_column(style="bold cyan", width=25)
                table.add_column(width=15)
                table.add_column(style="dim")

                if data.cape is not None:
                    cape_val, cape_interp = format_cape(data.cape)
                    cape_color = "red" if data.cape > 2500 else "yellow" if data.cape > 1000 else "green"
                    table.add_row("⚡ CAPE:", f"[{cape_color}]{cape_val}[/{cape_color}]", cape_interp)

                if data.cin is not None:
                    table.add_row("🔒 CIN:", f"{data.cin:.0f} J/kg", "")

                if data.helicity is not None:
                    hel_val, hel_interp = format_helicity(data.helicity)
                    hel_color = "red" if data.helicity > 300 else "yellow" if data.helicity > 150 else "green"
                    table.add_row("🌀 0-3km Helicity:", f"[{hel_color}]{hel_val}[/{hel_color}]", hel_interp)

                if data.shear is not None:
                    shear_color = "red" if data.shear > 40 else "yellow" if data.shear > 20 else "green"
                    table.add_row("💨 0-6km Shear:", f"[{shear_color}]{data.shear:.0f} kts[/{shear_color}]", "")

                if data.lifted_index is not None:
                    li_color = "red" if data.lifted_index < -4 else "yellow" if data.lifted_index < 0 else "green"
                    table.add_row("📊 Lifted Index:", f"[{li_color}]{data.lifted_index:.1f}[/{li_color}]", "")

                if data.k_index is not None:
                    table.add_row("📈 K-Index:", f"{data.k_index:.0f}", "")

                if data.total_totals is not None:
                    table.add_row("📉 Total Totals:", f"{data.total_totals:.0f}", "")

                table.add_row("🕐 Updated:", format_time_ago(data.timestamp), "")

                yield Static(table)

                # Show hodograph if available
                if self.sounding:
                    yield Static("\n")
                    yield Static(Text("📊 HODOGRAPH (0-10km)", style="bold magenta"))
                    # Would render hodograph ASCII art here
                    yield Static("[dim]Hodograph visualization (coming soon)[/dim]")


class SPCProductsPanel(Static):
    """Panel for SPC products."""

    outlook: reactive[Optional[Dict]] = reactive(None)
    mds: reactive[List[Dict]] = reactive(list)
    watches: reactive[List[Dict]] = reactive(list)

    def compose(self) -> ComposeResult:
        """Compose SPC products display."""
        with VerticalScroll():
            # Convective Outlook
            yield Static(Text("⚠️  CONVECTIVE OUTLOOK - DAY 1", style="bold yellow"))

            if self.outlook:
                outlook_text = Text()
                risk = self.outlook.get("categorical_risk", "TSTM")
                risk_colors = {
                    "HIGH": "bright_red",
                    "MDT": "red",
                    "ENH": "bright_yellow",
                    "SLGT": "yellow",
                    "MRGL": "blue",
                    "TSTM": "green"
                }
                risk_color = risk_colors.get(risk, "white")

                outlook_text.append(f"Risk Level: ", style="bold")
                outlook_text.append(f"{risk}", style=f"bold {risk_color}")

                if self.outlook.get("tornado_risk"):
                    outlook_text.append(f"\n🌪️  Tornado: {self.outlook['tornado_risk']}", style="red")
                if self.outlook.get("wind_risk"):
                    outlook_text.append(f"\n💨 Wind: {self.outlook['wind_risk']}", style="yellow")
                if self.outlook.get("hail_risk"):
                    outlook_text.append(f"\n🧊 Hail: {self.outlook['hail_risk']}", style="cyan")

                if self.outlook.get("summary"):
                    outlook_text.append(f"\n\n{self.outlook['summary']}", style="white")

                yield Static(outlook_text)
            else:
                yield Label("[dim]Loading outlook...[/dim]")

            yield Static("\n")

            # Mesoscale Discussions
            yield Static(Text("📋 MESOSCALE DISCUSSIONS", style="bold cyan"))
            if self.mds:
                for md in self.mds[:3]:
                    md_text = Text()
                    md_text.append(f"MD #{md.get('number', 'N/A')}\n", style="bold yellow")
                    md_text.append(md.get('summary', 'No summary available'), style="white")
                    yield Static(md_text)
                    yield Static("─" * 60)
            else:
                yield Label("[dim]No active mesoscale discussions[/dim]")

            yield Static("\n")

            # Watches
            yield Static(Text("⚠️  ACTIVE WATCHES", style="bold red"))
            if self.watches:
                for watch in self.watches:
                    watch_text = Text()
                    watch_type_color = "bright_red" if "Tornado" in watch['type'] else "yellow"
                    watch_text.append(f"WATCH #{watch['number']} - ", style="bold")
                    watch_text.append(f"{watch['type']}", style=f"bold {watch_type_color}")
                    yield Static(watch_text)
                    yield Static("─" * 60)
            else:
                yield Label("[dim]No active watches[/dim]")


class LightningPanel(Static):
    """Panel for lightning data."""

    strikes: reactive[List[LightningStrike]] = reactive(list)
    analysis: reactive[Optional[Dict]] = reactive(None)

    def compose(self) -> ComposeResult:
        """Compose lightning display."""
        with VerticalScroll():
            if self.analysis:
                # Summary
                summary = Text()
                summary.append("⚡ LIGHTNING ANALYSIS (15 min)\n\n", style="bold yellow")

                total = self.analysis.get('total_strikes', 0)
                cg = self.analysis.get('cg_strikes', 0)
                ic = self.analysis.get('ic_strikes', 0)
                rate = self.analysis.get('strike_rate', 0)
                trend = self.analysis.get('trend', 'none')

                summary.append(f"Total Strikes: {total}\n", style="white")
                summary.append(f"Cloud-to-Ground: {cg}\n", style="red")
                summary.append(f"Intra-Cloud: {ic}\n", style="yellow")
                summary.append(f"Strike Rate: {rate:.1f}/min\n", style="cyan")

                trend_color = "red" if trend == "increasing" else "green" if trend == "decreasing" else "yellow"
                trend_arrow = "↑" if trend == "increasing" else "↓" if trend == "decreasing" else "→"
                summary.append(f"Trend: {trend_arrow} {trend.upper()}", style=f"bold {trend_color}")

                yield Static(summary)
                yield Static("─" * 60)

            # Recent strikes
            if self.strikes:
                yield Static(Text("\n📍 RECENT STRIKES", style="bold"))
                for i, strike in enumerate(self.strikes[:20], 1):
                    strike_text = Text()
                    strike_type_color = "red" if strike.type == "CG" else "yellow"
                    age = format_time_ago(strike.timestamp)

                    strike_text.append(f"{i}. ", style="dim")
                    strike_text.append(f"[{strike.type}] ", style=f"bold {strike_type_color}")
                    strike_text.append(f"{strike.latitude:.3f}°N, {strike.longitude:.3f}°W  ", style="white")
                    strike_text.append(f"{age}  ", style="dim")
                    strike_text.append(f"{strike.strength:.0f}kA", style="bright_yellow")

                    yield Static(strike_text)
            else:
                yield Label("[dim]No recent lightning detected[/dim]")


class GPSPanel(Static):
    """Panel for GPS and chase info."""

    location: reactive[Optional[Location]] = reactive(None)
    gps_enabled: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        """Compose GPS display."""
        if not self.gps_enabled:
            yield Label("[dim]GPS tracking disabled. Enable in config.[/dim]")
        elif not self.location:
            yield Label("[yellow]GPS: Acquiring satellite fix...[/yellow]")
        else:
            gps_text = Text()
            gps_text.append("📍 GPS LOCATION\n\n", style="bold green")
            gps_text.append(f"Latitude: {self.location.latitude:.6f}°N\n", style="cyan")
            gps_text.append(f"Longitude: {self.location.longitude:.6f}°W\n", style="cyan")
            if self.location.elevation:
                gps_text.append(f"Elevation: {self.location.elevation:.0f} ft\n", style="cyan")
            gps_text.append(f"\nTracking active ✓", style="green")

            yield Static(gps_text)


class WXNETApp(App):
    """WXNET Advanced Application."""

    CSS = """
    Screen {
        background: $panel;
    }

    Header {
        background: $primary;
        color: $text;
    }

    Footer {
        background: $primary;
    }

    VerticalScroll {
        height: 100%;
        border: solid $primary;
        background: $surface;
    }

    ScrollableContainer {
        height: 100%;
        border: solid $primary;
        background: $surface;
    }

    .panel {
        border: solid $primary;
        height: 100%;
        background: $surface;
        padding: 1;
    }

    #left-column {
        width: 50%;
        height: 100%;
    }

    #right-column {
        width: 50%;
        height: 100%;
    }

    TabbedContent {
        height: 100%;
    }

    TabPane {
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_all", "Refresh All"),
        Binding("1", "show_overview", "Overview"),
        Binding("2", "show_spc", "SPC Products"),
        Binding("3", "show_lightning", "Lightning"),
        Binding("4", "show_gps", "GPS/Chase"),
        Binding("s", "toggle_sound", "Sound Alerts"),
    ]

    TITLE = "WXNET - Professional Severe Weather Monitoring"
    SUB_TITLE = "Real-time Storm Tracking & Analysis"

    def __init__(self):
        """Initialize application."""
        super().__init__()
        self.location = Location(
            latitude=config.default_latitude,
            longitude=config.default_longitude,
            name=config.default_location
        )

        # Data stores
        self.alerts: List[WeatherAlert] = []
        self.current_weather: Optional[CurrentWeather] = None
        self.radar_data = None
        self.storm_cells: List[StormCell] = []
        self.atmospheric_data: Optional[AtmosphericData] = None
        self.lightning_strikes: List[LightningStrike] = []
        self.spc_outlook: Optional[Dict] = None
        self.spc_mds: List[Dict] = []
        self.spc_watches: List[Dict] = []

        # Clients
        self.nws_client: Optional[NWSClient] = None
        self.nexrad_client: Optional[NEXRADClient] = None
        self.spc_client: Optional[SPCProductsClient] = None
        self.lightning_client: Optional[LightningClient] = None
        self.meso_client: Optional[MesoanalysisClient] = None

        # Chase utilities
        self.gps_tracker = GPSTracker()
        self.sound_alerts = SoundAlerts()
        self.chase_logger = ChaseLogger()

        # Try to start GPS
        if self.gps_tracker.start_tracking():
            self.log("GPS tracking started")

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()

        with TabbedContent(initial="overview"):
            # Overview Tab
            with TabPane("Overview", id="overview"):
                with Horizontal():
                    with Vertical(id="left-column"):
                        with Container(classes="panel"):
                            yield Static("[bold red]⚠️  ACTIVE ALERTS[/bold red]")
                            yield AlertsPanel(id="alerts")

                        with Container(classes="panel"):
                            yield Static("[bold cyan]🌡️  CURRENT CONDITIONS[/bold cyan]")
                            yield Static(f"[dim]{self.location.name}[/dim]")
                            yield CurrentConditionsPanel(id="current")

                        with Container(classes="panel"):
                            yield Static("[bold magenta]📊 ATMOSPHERIC DATA[/bold magenta]")
                            yield AtmosphericPanel(id="atmospheric")

                    with Vertical(id="right-column"):
                        with Container(classes="panel"):
                            yield Static("[bold green]📡 NEXRAD RADAR[/bold green]")
                            yield RadarPanel(id="radar")

                        with Container(classes="panel"):
                            yield Static("[bold yellow]⛈️  STORM CELLS[/bold yellow]")
                            yield StormCellsPanel(id="cells")

            # SPC Products Tab
            with TabPane("SPC Products", id="spc"):
                with Container(classes="panel"):
                    yield SPCProductsPanel(id="spc-products")

            # Lightning Tab
            with TabPane("Lightning", id="lightning"):
                with Container(classes="panel"):
                    yield LightningPanel(id="lightning-panel")

            # GPS/Chase Tab
            with TabPane("GPS/Chase", id="gps"):
                with Container(classes="panel"):
                    yield GPSPanel(id="gps-panel")

        yield Footer()

    async def on_mount(self) -> None:
        """Handle mount event."""
        # Initialize clients
        self.nws_client = NWSClient()
        self.nexrad_client = NEXRADClient()
        self.spc_client = SPCProductsClient()
        self.lightning_client = LightningClient()
        self.meso_client = MesoanalysisClient()

        # Start data refresh loops
        self.set_interval(config.alert_update_interval, self.refresh_alerts)
        self.set_interval(config.weather_update_interval, self.refresh_weather)
        self.set_interval(config.radar_update_interval, self.refresh_radar)
        self.set_interval(30, self.refresh_spc)
        self.set_interval(30, self.refresh_lightning)
        self.set_interval(5, self.refresh_gps)

        # Initial data load
        await self.refresh_all_data()

    async def refresh_all_data(self) -> None:
        """Refresh all weather data."""
        await asyncio.gather(
            self.refresh_alerts(),
            self.refresh_weather(),
            self.refresh_radar(),
            self.refresh_atmospheric(),
            self.refresh_spc(),
            self.refresh_lightning(),
            return_exceptions=True
        )

    async def refresh_alerts(self) -> None:
        """Refresh weather alerts."""
        if self.nws_client:
            self.alerts = await self.nws_client.get_alerts(
                self.location.latitude,
                self.location.longitude
            )

            # Update UI
            alerts_widget = self.query_one("#alerts", AlertsPanel)
            alerts_widget.alerts = self.alerts

            # Play sound for new tornado warnings
            for alert in self.alerts:
                if "Tornado Warning" in alert.event and self.sound_alerts.enabled:
                    self.sound_alerts.play_tornado_warning()
                    break

    async def refresh_weather(self) -> None:
        """Refresh current weather."""
        if self.nws_client:
            self.current_weather = await self.nws_client.get_observation(
                self.location.latitude,
                self.location.longitude
            )

            current_widget = self.query_one("#current", CurrentConditionsPanel)
            current_widget.weather = self.current_weather

    async def refresh_radar(self) -> None:
        """Refresh radar data."""
        if self.nexrad_client:
            # Find nearest station
            stations = self.nexrad_client.find_nearest_stations(
                self.location.latitude,
                self.location.longitude,
                count=1
            )
            station = stations[0][0] if stations else "KTLX"

            # Get radar data
            self.radar_data = await self.nexrad_client.get_reflectivity_data(
                station,
                self.location.latitude,
                self.location.longitude
            )

            if self.radar_data:
                # Detect storm cells
                self.storm_cells = await self.nexrad_client.detect_storm_cells(
                    self.radar_data,
                    threshold_dbz=40
                )

                # Update UI
                radar_widget = self.query_one("#radar", RadarPanel)
                radar_widget.radar_data = self.radar_data
                radar_widget.station = station

                cells_widget = self.query_one("#cells", StormCellsPanel)
                cells_widget.cells = self.storm_cells
                cells_widget.location = (self.location.latitude, self.location.longitude)
                cells_widget.gps_tracker = self.gps_tracker

    async def refresh_atmospheric(self) -> None:
        """Refresh atmospheric data."""
        if self.meso_client:
            self.atmospheric_data = await self.meso_client.get_atmospheric_parameters(
                self.location.latitude,
                self.location.longitude
            )

            atmos_widget = self.query_one("#atmospheric", AtmosphericPanel)
            atmos_widget.atmos_data = self.atmospheric_data

    async def refresh_spc(self) -> None:
        """Refresh SPC products."""
        if self.spc_client:
            summary = await self.spc_client.get_severe_weather_summary()

            self.spc_outlook = summary.get("outlooks", {}).get("day1")
            self.spc_mds = summary.get("mesoscale_discussions", [])
            self.spc_watches = summary.get("watches", [])

            spc_widget = self.query_one("#spc-products", SPCProductsPanel)
            spc_widget.outlook = self.spc_outlook
            spc_widget.mds = self.spc_mds
            spc_widget.watches = self.spc_watches

    async def refresh_lightning(self) -> None:
        """Refresh lightning data."""
        if self.lightning_client:
            self.lightning_strikes = await self.lightning_client.get_recent_strikes(
                self.location.latitude,
                self.location.longitude,
                radius_km=300,
                minutes=15
            )

            analysis = self.lightning_client.analyze_storm_electrification(
                self.lightning_strikes,
                time_window_minutes=15
            )

            ltg_widget = self.query_one("#lightning-panel", LightningPanel)
            ltg_widget.strikes = self.lightning_strikes
            ltg_widget.analysis = analysis

    async def refresh_gps(self) -> None:
        """Refresh GPS location."""
        location = self.gps_tracker.get_current_location()
        if location:
            self.location = location

        gps_widget = self.query_one("#gps-panel", GPSPanel)
        gps_widget.location = location
        gps_widget.gps_enabled = self.gps_tracker.is_tracking

    def action_refresh_all(self) -> None:
        """Refresh all data."""
        asyncio.create_task(self.refresh_all_data())

    def action_show_overview(self) -> None:
        """Show overview tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "overview"

    def action_show_spc(self) -> None:
        """Show SPC products tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "spc"

    def action_show_lightning(self) -> None:
        """Show lightning tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "lightning"

    def action_show_gps(self) -> None:
        """Show GPS tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "gps"

    def action_toggle_sound(self) -> None:
        """Toggle sound alerts."""
        self.sound_alerts.enabled = not self.sound_alerts.enabled
        status = "enabled" if self.sound_alerts.enabled else "disabled"
        self.notify(f"Sound alerts {status}")


def main():
    """Main entry point."""
    app = WXNETApp()
    app.run()


if __name__ == "__main__":
    main()
