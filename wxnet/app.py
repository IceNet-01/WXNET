"""Main WXNET application."""

import asyncio
from datetime import datetime
from typing import Optional, List
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Label, DataTable, TabbedContent, TabPane
from textual.reactive import reactive
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.console import Group

from .config import config
from .models import WeatherAlert, CurrentWeather, StormCell, AtmosphericData
from .api.nws import NWSClient
from .api.radar import RadarClient
from .api.atmospheric import AtmosphericClient, SPCClient
from .utils import (
    format_temperature, format_wind, format_pressure,
    get_alert_color, get_alert_symbol, format_distance,
    calculate_distance, calculate_bearing, format_bearing,
    render_radar_ascii, get_reflectivity_color, format_time_ago,
    format_cape, format_helicity
)


class AlertsWidget(Static):
    """Widget for displaying weather alerts."""

    alerts: reactive[List[WeatherAlert]] = reactive(list, recompose=True)

    def compose(self) -> ComposeResult:
        """Compose alert display."""
        if not self.alerts:
            yield Label("[dim]No active alerts[/dim]")
            return

        for alert in self.alerts[:5]:  # Show top 5 alerts
            severity_color = get_alert_color(alert.severity.value)
            symbol = get_alert_symbol(alert.event)

            alert_text = Text()
            alert_text.append(f"{symbol} ", style="bold")
            alert_text.append(alert.event, style=f"bold {severity_color}")

            if alert.areas:
                alert_text.append(f"\n   {', '.join(alert.areas[:2])}", style="dim")

            if alert.expires:
                time_str = format_time_ago(alert.expires)
                alert_text.append(f"\n   Expires: {time_str}", style="dim")

            yield Static(alert_text)


class CurrentConditionsWidget(Static):
    """Widget for current weather conditions."""

    weather: reactive[Optional[CurrentWeather]] = reactive(None, recompose=True)

    def compose(self) -> ComposeResult:
        """Compose current conditions display."""
        if not self.weather:
            yield Label("[dim]Loading weather data...[/dim]")
            return

        w = self.weather

        # Create conditions table
        table = RichTable.grid(padding=(0, 2))
        table.add_column(style="bold cyan")
        table.add_column()

        table.add_row("Temperature:", format_temperature(w.temperature))
        table.add_row("Feels Like:", format_temperature(w.feels_like))

        if w.dewpoint:
            table.add_row("Dewpoint:", format_temperature(w.dewpoint))

        table.add_row("Humidity:", f"{w.humidity}%")
        table.add_row("Pressure:", format_pressure(w.pressure))
        table.add_row("Wind:", format_wind(w.wind_speed, w.wind_direction, w.wind_gust))

        if w.visibility:
            table.add_row("Visibility:", f"{w.visibility:.1f} mi")

        table.add_row("Conditions:", w.conditions)
        table.add_row("Updated:", format_time_ago(w.timestamp))

        yield Static(table)


class RadarWidget(Static):
    """Widget for radar display."""

    radar_data: reactive[Optional[any]] = reactive(None, recompose=True)
    product_type: reactive[str] = reactive("reflectivity")

    def compose(self) -> ComposeResult:
        """Compose radar display."""
        if not self.radar_data:
            yield Label("[dim]Loading radar data...[/dim]")
            return

        # Render ASCII radar
        ascii_lines = render_radar_ascii(
            self.radar_data.data,
            width=80,
            height=30
        )

        header = Text(f"RADAR: {self.radar_data.station} - {self.product_type.upper()}", style="bold green")
        timestamp = Text(f"Time: {self.radar_data.timestamp.strftime('%H:%M:%S UTC')}", style="dim")

        content = Text("\n".join(ascii_lines))

        yield Static(header)
        yield Static(timestamp)
        yield Static(content)


class StormCellsWidget(Static):
    """Widget for storm cell information."""

    cells: reactive[List[StormCell]] = reactive(list, recompose=True)
    location: reactive[tuple] = reactive((35.0, -97.5))

    def compose(self) -> ComposeResult:
        """Compose storm cells display."""
        if not self.cells:
            yield Label("[dim]No storm cells detected[/dim]")
            return

        lat, lon = self.location

        for i, cell in enumerate(self.cells[:10], 1):  # Show top 10 cells
            # Calculate distance and bearing to cell
            dist = calculate_distance(lat, lon, cell.latitude, cell.longitude)
            bearing = calculate_bearing(lat, lon, cell.latitude, cell.longitude)
            bearing_str = format_bearing(bearing)

            # Create cell info
            cell_info = Text()
            cell_info.append(f"CELL {i}: ", style="bold yellow")
            cell_info.append(f"{cell.intensity} dBZ  ", style="bold red" if cell.intensity > 55 else "yellow")

            if cell.tvs:
                cell_info.append("[TVS] ", style="bold bright_red")
            elif cell.meso:
                cell_info.append("[MESO] ", style="bold red")

            cell_info.append(f"\n   Location: {format_distance(dist)} {bearing_str}")
            cell_info.append(f"\n   Movement: {format_bearing(cell.movement_direction)} @ {cell.movement_speed:.0f} mph")

            if cell.has_rotation:
                cell_info.append(f"\n   Rotation: {cell.rotation_strength:.3f}", style="red")

            if cell.max_hail_size:
                cell_info.append(f"\n   Max Hail: {cell.max_hail_size}\"", style="bright_yellow")

            yield Static(cell_info)


class AtmosphericWidget(Static):
    """Widget for atmospheric parameters."""

    atmos_data: reactive[Optional[AtmosphericData]] = reactive(None, recompose=True)

    def compose(self) -> ComposeResult:
        """Compose atmospheric display."""
        if not self.atmos_data:
            yield Label("[dim]Loading atmospheric data...[/dim]")
            return

        data = self.atmos_data

        table = RichTable.grid(padding=(0, 2))
        table.add_column(style="bold cyan")
        table.add_column()
        table.add_column(style="dim")

        if data.cape is not None:
            cape_val, cape_interp = format_cape(data.cape)
            table.add_row("CAPE:", cape_val, cape_interp)

        if data.cin is not None:
            table.add_row("CIN:", f"{data.cin:.0f} J/kg", "")

        if data.helicity is not None:
            hel_val, hel_interp = format_helicity(data.helicity)
            table.add_row("0-3km Helicity:", hel_val, hel_interp)

        if data.shear is not None:
            table.add_row("0-6km Shear:", f"{data.shear:.0f} kts", "")

        if data.lifted_index is not None:
            table.add_row("Lifted Index:", f"{data.lifted_index:.1f}", "")

        if data.k_index is not None:
            table.add_row("K Index:", f"{data.k_index:.0f}", "")

        table.add_row("Updated:", format_time_ago(data.timestamp), "")

        yield Static(table)


class WXNETApp(App):
    """WXNET - Severe Weather Monitoring Terminal."""

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

    .panel {
        border: solid $primary;
        height: auto;
        margin: 1;
        padding: 1;
    }

    #alerts-panel {
        background: $surface;
        border: solid red;
        height: auto;
        max-height: 15;
    }

    #current-panel {
        background: $surface;
        height: auto;
    }

    #radar-panel {
        background: $surface;
        height: auto;
    }

    #cells-panel {
        background: $surface;
        height: auto;
        max-height: 20;
    }

    #atmos-panel {
        background: $surface;
        height: auto;
    }

    #left-column {
        width: 50%;
    }

    #right-column {
        width: 50%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("1", "show_dashboard", "Dashboard"),
        ("2", "show_radar", "Radar"),
        ("3", "show_forecast", "Forecast"),
    ]

    TITLE = "WXNET - Severe Weather Monitoring"

    def __init__(self):
        """Initialize application."""
        super().__init__()
        self.location = (config.default_latitude, config.default_longitude)
        self.location_name = config.default_location

        # Data stores
        self.alerts: List[WeatherAlert] = []
        self.current_weather: Optional[CurrentWeather] = None
        self.radar_data = None
        self.storm_cells: List[StormCell] = []
        self.atmospheric_data: Optional[AtmosphericData] = None

        # Clients
        self.nws_client: Optional[NWSClient] = None
        self.radar_client: Optional[RadarClient] = None
        self.atmos_client: Optional[AtmosphericClient] = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()

        with Horizontal():
            with Vertical(id="left-column"):
                with Container(id="alerts-panel", classes="panel"):
                    yield Static("[bold red]⚠ ACTIVE ALERTS[/bold red]")
                    yield AlertsWidget(id="alerts")

                with Container(id="current-panel", classes="panel"):
                    yield Static("[bold cyan]🌡 CURRENT CONDITIONS[/bold cyan]")
                    yield Static(f"[dim]{self.location_name}[/dim]")
                    yield CurrentConditionsWidget(id="current")

                with Container(id="atmos-panel", classes="panel"):
                    yield Static("[bold magenta]📊 ATMOSPHERIC DATA[/bold magenta]")
                    yield AtmosphericWidget(id="atmospheric")

            with Vertical(id="right-column"):
                with Container(id="radar-panel", classes="panel"):
                    yield Static("[bold green]📡 RADAR[/bold green]")
                    yield RadarWidget(id="radar")

                with ScrollableContainer(id="cells-panel", classes="panel"):
                    yield Static("[bold yellow]⛈ STORM CELLS[/bold yellow]")
                    yield StormCellsWidget(id="cells")

        yield Footer()

    async def on_mount(self) -> None:
        """Handle mount event."""
        # Initialize clients
        self.nws_client = NWSClient()
        self.radar_client = RadarClient()
        self.atmos_client = AtmosphericClient()

        # Start data refresh loop
        self.set_interval(config.alert_update_interval, self.refresh_alerts)
        self.set_interval(config.weather_update_interval, self.refresh_weather)
        self.set_interval(config.radar_update_interval, self.refresh_radar)

        # Initial data load
        await self.refresh_all_data()

    async def refresh_all_data(self) -> None:
        """Refresh all weather data."""
        await asyncio.gather(
            self.refresh_alerts(),
            self.refresh_weather(),
            self.refresh_radar(),
            self.refresh_atmospheric()
        )

    async def refresh_alerts(self) -> None:
        """Refresh weather alerts."""
        if self.nws_client:
            lat, lon = self.location
            self.alerts = await self.nws_client.get_alerts(lat, lon)

            alerts_widget = self.query_one("#alerts", AlertsWidget)
            alerts_widget.alerts = self.alerts

    async def refresh_weather(self) -> None:
        """Refresh current weather."""
        if self.nws_client:
            lat, lon = self.location
            self.current_weather = await self.nws_client.get_observation(lat, lon)

            current_widget = self.query_one("#current", CurrentConditionsWidget)
            current_widget.weather = self.current_weather

    async def refresh_radar(self) -> None:
        """Refresh radar data."""
        if self.radar_client:
            lat, lon = self.location
            station = self.radar_client.find_nearest_station(lat, lon)
            self.radar_data = await self.radar_client.get_reflectivity_data(station, lat, lon)

            if self.radar_data:
                self.storm_cells = await self.radar_client.detect_storm_cells(self.radar_data)

                radar_widget = self.query_one("#radar", RadarWidget)
                radar_widget.radar_data = self.radar_data

                cells_widget = self.query_one("#cells", StormCellsWidget)
                cells_widget.cells = self.storm_cells
                cells_widget.location = self.location

    async def refresh_atmospheric(self) -> None:
        """Refresh atmospheric data."""
        if self.atmos_client:
            lat, lon = self.location
            self.atmospheric_data = await self.atmos_client.get_atmospheric_data(lat, lon)

            atmos_widget = self.query_one("#atmospheric", AtmosphericWidget)
            atmos_widget.atmos_data = self.atmospheric_data

    def action_refresh(self) -> None:
        """Refresh all data."""
        asyncio.create_task(self.refresh_all_data())

    def action_show_dashboard(self) -> None:
        """Show dashboard view."""
        pass

    def action_show_radar(self) -> None:
        """Show radar view."""
        pass

    def action_show_forecast(self) -> None:
        """Show forecast view."""
        pass


def main():
    """Main entry point."""
    app = WXNETApp()
    app.run()


if __name__ == "__main__":
    main()
