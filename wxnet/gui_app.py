"""
WXNET Desktop GUI Application - PyQt6 Implementation
Professional severe weather monitoring with rich visualizations
"""

import sys
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit, QSplitter, QStatusBar,
    QMenuBar, QMenu, QToolBar, QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame, QGridLayout, QSystemTrayIcon, QMessageBox,
    QProgressBar, QGroupBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QSettings
)
from PyQt6.QtGui import (
    QAction, QIcon, QFont, QColor, QPalette, QTextCharFormat,
    QTextCursor, QPixmap
)

# Import WXNET backend
from .config import config
from .models import WeatherAlert, CurrentWeather, StormCell, AtmosphericData, LightningStrike, Location
from .api.nws import NWSClient
from .api.nexrad import NEXRADClient
from .api.spc import SPCProductsClient
from .api.lightning import LightningClient
from .api.mesoanalysis import MesoanalysisClient
from .tracking import GPSTracker, SoundAlerts, ChaseLogger
from .utils import (
    format_temperature, format_wind, format_pressure,
    get_alert_color, format_distance, calculate_distance,
    calculate_bearing, format_bearing, format_time_ago,
    format_cape, format_helicity
)


class DataFetchThread(QThread):
    """Thread for fetching weather data without blocking UI."""

    data_ready = pyqtSignal(str, object)  # (data_type, data)
    error_occurred = pyqtSignal(str, str)  # (data_type, error_message)

    def __init__(self, data_type: str, fetch_func, *args, **kwargs):
        super().__init__()
        self.data_type = data_type
        self.fetch_func = fetch_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """Run the data fetch in background."""
        try:
            # Run async function in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.fetch_func(*self.args, **self.kwargs))
            loop.close()

            self.data_ready.emit(self.data_type, result)
        except Exception as e:
            self.error_occurred.emit(self.data_type, str(e))


class AlertsPanel(QWidget):
    """Panel for displaying weather alerts."""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.alerts = []

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()

        # Header
        header = QLabel("⚠️  ACTIVE WEATHER ALERTS")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #ff4444; padding: 5px;")
        layout.addWidget(header)

        # Alerts text area
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.alerts_text)

        self.setLayout(layout)

    def update_alerts(self, alerts: List[WeatherAlert]):
        """Update alerts display."""
        self.alerts = alerts

        if not alerts:
            self.alerts_text.setHtml("<p style='color: #888;'>No active alerts</p>")
            return

        html = ""
        for alert in alerts:
            severity = alert.severity.value.upper()
            color = self._get_alert_color(severity)

            html += f"""
            <div style='border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background: #2a2a2a;'>
                <h3 style='color: {color}; margin: 0;'>{alert.event}</h3>
                <p style='color: #aaa; margin: 5px 0;'>{', '.join(alert.areas[:3])}</p>
                <p style='color: #fff; margin: 5px 0;'>{alert.description[:200]}...</p>
                <p style='color: #ffa500; margin: 5px 0;'>Expires: {format_time_ago(alert.expires)}</p>
            </div>
            """

        self.alerts_text.setHtml(html)

    def _get_alert_color(self, severity: str) -> str:
        """Get color for alert severity."""
        colors = {
            "EXTREME": "#ff0066",
            "SEVERE": "#ff4444",
            "MODERATE": "#ff8800",
            "MINOR": "#ffcc00",
            "UNKNOWN": "#888888"
        }
        return colors.get(severity, "#888888")


class CurrentWeatherPanel(QWidget):
    """Panel for current weather conditions."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()

        # Header
        header = QLabel("🌡️  CURRENT CONDITIONS")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #44aaff; padding: 5px;")
        layout.addWidget(header)

        self.location_label = QLabel("Location")
        self.location_label.setStyleSheet("color: #888; font-size: 10pt;")
        layout.addWidget(self.location_label)

        # Weather data grid
        self.weather_grid = QGridLayout()
        self.weather_labels = {}

        fields = [
            ("temp", "🌡️  Temperature:", 0, 0),
            ("feels", "🌡️  Feels Like:", 1, 0),
            ("dewpoint", "💧 Dewpoint:", 2, 0),
            ("humidity", "💦 Humidity:", 3, 0),
            ("pressure", "🔽 Pressure:", 0, 2),
            ("wind", "💨 Wind:", 1, 2),
            ("visibility", "👁️  Visibility:", 2, 2),
            ("conditions", "☁️  Conditions:", 3, 2),
        ]

        for key, label, row, col in fields:
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            label_widget.setStyleSheet("color: #44aaff;")

            value_widget = QLabel("--")
            value_widget.setStyleSheet("color: #fff; font-size: 11pt;")

            self.weather_grid.addWidget(label_widget, row, col)
            self.weather_grid.addWidget(value_widget, row, col + 1)
            self.weather_labels[key] = value_widget

        layout.addLayout(self.weather_grid)
        layout.addStretch()

        self.setLayout(layout)

    def update_weather(self, weather: Optional[CurrentWeather], location_name: str):
        """Update weather display."""
        self.location_label.setText(location_name)

        if not weather:
            for label in self.weather_labels.values():
                label.setText("--")
            return

        self.weather_labels["temp"].setText(format_temperature(weather.temperature))
        self.weather_labels["feels"].setText(format_temperature(weather.feels_like))
        self.weather_labels["dewpoint"].setText(format_temperature(weather.dewpoint) if weather.dewpoint else "--")
        self.weather_labels["humidity"].setText(f"{weather.humidity}%")
        self.weather_labels["pressure"].setText(format_pressure(weather.pressure))
        self.weather_labels["wind"].setText(format_wind(weather.wind_speed, weather.wind_direction, weather.wind_gust))
        self.weather_labels["visibility"].setText(f"{weather.visibility:.1f} mi" if weather.visibility else "--")
        self.weather_labels["conditions"].setText(weather.conditions)


class RadarPanel(QWidget):
    """Panel for radar display."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()

        # Header
        header = QLabel("📡 NEXRAD RADAR")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #44ff44; padding: 5px;")
        layout.addWidget(header)

        self.station_label = QLabel("Station: --")
        self.station_label.setStyleSheet("color: #aaa;")
        layout.addWidget(self.station_label)

        # Radar display area
        self.radar_text = QTextEdit()
        self.radar_text.setReadOnly(True)
        self.radar_text.setFont(QFont("Consolas", 8))
        self.radar_text.setStyleSheet("background: #000; color: #0f0;")
        layout.addWidget(self.radar_text)

        # Legend
        legend = QLabel("""
        <div style='background: #2a2a2a; padding: 10px;'>
        <b>REFLECTIVITY SCALE (dBZ):</b><br>
        <span style='color: #4444ff;'>15-25: Light</span> |
        <span style='color: #44ff44;'>25-35: Moderate</span> |
        <span style='color: #ffff44;'>35-45: Heavy</span> |
        <span style='color: #ff8844;'>45-55: Very Heavy</span> |
        <span style='color: #ff4444;'>55-65: Extreme</span> |
        <span style='color: #ff00ff;'>65+: Giant Hail</span>
        </div>
        """)
        legend.setWordWrap(True)
        layout.addWidget(legend)

        self.setLayout(layout)

    def update_radar(self, radar_data, station: str):
        """Update radar display."""
        self.station_label.setText(f"Station: {station}")

        if not radar_data:
            self.radar_text.setPlainText("Loading radar data...")
            return

        # For now, show placeholder - will implement proper visualization
        self.radar_text.setPlainText(f"Radar data loaded for {station}\nTimestamp: {radar_data.timestamp}\nProduct: {radar_data.product_type}")


class StormCellsPanel(QWidget):
    """Panel for storm cell tracking."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()

        # Header
        header = QLabel("⛈️  STORM CELLS")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffff44; padding: 5px;")
        layout.addWidget(header)

        # Storm cells text area
        self.cells_text = QTextEdit()
        self.cells_text.setReadOnly(True)
        self.cells_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.cells_text)

        self.setLayout(layout)

    def update_cells(self, cells: List[StormCell], location: tuple):
        """Update storm cells display."""
        if not cells:
            self.cells_text.setHtml("<p style='color: #888;'>No storm cells detected</p>")
            return

        lat, lon = location
        html = ""

        for i, cell in enumerate(cells, 1):
            dist = calculate_distance(lat, lon, cell.latitude, cell.longitude)
            bearing = calculate_bearing(lat, lon, cell.latitude, cell.longitude)
            bearing_str = format_bearing(bearing)

            intensity_color = "#ff4444" if cell.intensity > 60 else "#ffff44" if cell.intensity > 50 else "#44ff44"

            warnings = ""
            if cell.tvs:
                warnings += "<span style='color: #ff0066; font-weight: bold;'>[TVS]</span> "
            if cell.meso:
                warnings += "<span style='color: #ff4444; font-weight: bold;'>[MESO]</span> "
            if cell.max_hail_size and cell.max_hail_size > 1.0:
                warnings += f"<span style='color: #ff00ff; font-weight: bold;'>[HAIL {cell.max_hail_size}\"]</span> "

            html += f"""
            <div style='border: 2px solid {intensity_color}; padding: 10px; margin: 10px 0; background: #2a2a2a;'>
                <h3 style='color: {intensity_color}; margin: 0;'>CELL {i}: {cell.intensity} dBZ {warnings}</h3>
                <p style='margin: 5px 0;'>📍 Location: {format_distance(dist)} {bearing_str} ({bearing}°)</p>
                <p style='margin: 5px 0;'>🎯 Coordinates: {cell.latitude:.3f}°N, {cell.longitude:.3f}°W</p>
                <p style='margin: 5px 0;'>➡️  Movement: {format_bearing(cell.movement_direction)} @ {cell.movement_speed:.0f} mph</p>
            """

            if cell.has_rotation:
                html += f"<p style='color: #ff4444; margin: 5px 0;'>🌪️  Rotation: {cell.rotation_strength:.4f}</p>"
            if cell.top_height:
                html += f"<p style='color: #44aaff; margin: 5px 0;'>⬆️  Top: {cell.top_height:,} ft</p>"

            html += "</div>"

        self.cells_text.setHtml(html)


class AtmosphericPanel(QWidget):
    """Panel for atmospheric parameters."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()

        # Header
        header = QLabel("📊 ATMOSPHERIC DATA")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #ff44ff; padding: 5px;")
        layout.addWidget(header)

        # Parameters grid
        self.params_text = QTextEdit()
        self.params_text.setReadOnly(True)
        self.params_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.params_text)

        self.setLayout(layout)

    def update_atmospheric(self, data: Optional[AtmosphericData]):
        """Update atmospheric data display."""
        if not data:
            self.params_text.setHtml("<p style='color: #888;'>Loading atmospheric data...</p>")
            return

        html = "<div style='background: #2a2a2a; padding: 10px;'>"

        if data.cape is not None:
            cape_val, cape_interp = format_cape(data.cape)
            color = "#ff4444" if data.cape > 2500 else "#ffff44" if data.cape > 1000 else "#44ff44"
            html += f"<p><b style='color: #44aaff;'>⚡ CAPE:</b> <span style='color: {color};'>{cape_val}</span> <span style='color: #888;'>{cape_interp}</span></p>"

        if data.cin is not None:
            html += f"<p><b style='color: #44aaff;'>🔒 CIN:</b> {data.cin:.0f} J/kg</p>"

        if data.helicity is not None:
            hel_val, hel_interp = format_helicity(data.helicity)
            color = "#ff4444" if data.helicity > 300 else "#ffff44" if data.helicity > 150 else "#44ff44"
            html += f"<p><b style='color: #44aaff;'>🌀 0-3km Helicity:</b> <span style='color: {color};'>{hel_val}</span> <span style='color: #888;'>{hel_interp}</span></p>"

        if data.shear is not None:
            color = "#ff4444" if data.shear > 40 else "#ffff44" if data.shear > 20 else "#44ff44"
            html += f"<p><b style='color: #44aaff;'>💨 0-6km Shear:</b> <span style='color: {color};'>{data.shear:.0f} kts</span></p>"

        if data.lifted_index is not None:
            color = "#ff4444" if data.lifted_index < -4 else "#ffff44" if data.lifted_index < 0 else "#44ff44"
            html += f"<p><b style='color: #44aaff;'>📊 Lifted Index:</b> <span style='color: {color};'>{data.lifted_index:.1f}</span></p>"

        html += f"<p style='color: #888; margin-top: 10px;'>🕐 Updated: {format_time_ago(data.timestamp)}</p>"
        html += "</div>"

        self.params_text.setHtml(html)


class WXNETMainWindow(QMainWindow):
    """Main window for WXNET Desktop Application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WXNET - Professional Severe Weather Monitoring")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize data
        self.location = Location(
            latitude=config.default_latitude,
            longitude=config.default_longitude,
            name=config.default_location
        )

        # Initialize API clients
        self.nws_client = NWSClient()
        self.nexrad_client = NEXRADClient()
        self.spc_client = SPCProductsClient()
        self.lightning_client = LightningClient()
        self.meso_client = MesoanalysisClient()

        # Initialize utilities
        self.gps_tracker = GPSTracker()
        self.sound_alerts = SoundAlerts()
        self.chase_logger = ChaseLogger()

        # Data storage
        self.alerts = []
        self.current_weather = None
        self.radar_data = None
        self.storm_cells = []
        self.atmospheric_data = None

        # Setup UI
        self.init_ui()
        self.setup_timers()

        # Initial data fetch
        self.refresh_all_data()

    def init_ui(self):
        """Initialize the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 11))

        # Overview Tab
        overview_tab = self.create_overview_tab()
        self.tabs.addTab(overview_tab, "Overview")

        # SPC Products Tab
        spc_tab = self.create_spc_tab()
        self.tabs.addTab(spc_tab, "SPC Products")

        # Lightning Tab
        lightning_tab = self.create_lightning_tab()
        self.tabs.addTab(lightning_tab, "Lightning")

        # GPS/Chase Tab
        gps_tab = self.create_gps_tab()
        self.tabs.addTab(gps_tab, "GPS/Chase")

        main_layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar()

        # Apply dark theme
        self.apply_dark_theme()

    def create_overview_tab(self) -> QWidget:
        """Create the overview tab."""
        widget = QWidget()
        layout = QHBoxLayout()

        # Left column
        left_splitter = QSplitter(Qt.Orientation.Vertical)

        self.alerts_panel = AlertsPanel()
        left_splitter.addWidget(self.alerts_panel)

        self.weather_panel = CurrentWeatherPanel()
        left_splitter.addWidget(self.weather_panel)

        self.atmospheric_panel = AtmosphericPanel()
        left_splitter.addWidget(self.atmospheric_panel)

        # Right column
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        self.radar_panel = RadarPanel()
        right_splitter.addWidget(self.radar_panel)

        self.cells_panel = StormCellsPanel()
        right_splitter.addWidget(self.cells_panel)

        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([700, 700])

        layout.addWidget(main_splitter)
        widget.setLayout(layout)
        return widget

    def create_spc_tab(self) -> QWidget:
        """Create SPC products tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        header = QLabel("⚠️  STORM PREDICTION CENTER PRODUCTS")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffff44; padding: 10px;")
        layout.addWidget(header)

        self.spc_text = QTextEdit()
        self.spc_text.setReadOnly(True)
        self.spc_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.spc_text)

        widget.setLayout(layout)
        return widget

    def create_lightning_tab(self) -> QWidget:
        """Create lightning tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        header = QLabel("⚡ LIGHTNING DETECTION & ANALYSIS")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffff44; padding: 10px;")
        layout.addWidget(header)

        self.lightning_text = QTextEdit()
        self.lightning_text.setReadOnly(True)
        self.lightning_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.lightning_text)

        widget.setLayout(layout)
        return widget

    def create_gps_tab(self) -> QWidget:
        """Create GPS/Chase tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        header = QLabel("📍 GPS TRACKING & CHASE MANAGEMENT")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #44ff44; padding: 10px;")
        layout.addWidget(header)

        self.gps_text = QTextEdit()
        self.gps_text.setReadOnly(True)
        self.gps_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.gps_text)

        widget.setLayout(layout)
        return widget

    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        refresh_action = QAction("Refresh All", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all_data)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About WXNET", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_all_data)
        toolbar.addWidget(refresh_btn)

        toolbar.addSeparator()

        # Sound toggle
        self.sound_btn = QPushButton("🔔 Sound: ON" if self.sound_alerts.enabled else "🔕 Sound: OFF")
        self.sound_btn.clicked.connect(self.toggle_sound)
        toolbar.addWidget(self.sound_btn)

    def setup_timers(self):
        """Setup auto-refresh timers."""
        # Alerts timer
        self.alerts_timer = QTimer()
        self.alerts_timer.timeout.connect(self.refresh_alerts)
        self.alerts_timer.start(config.alert_update_interval * 1000)

        # Weather timer
        self.weather_timer = QTimer()
        self.weather_timer.timeout.connect(self.refresh_weather)
        self.weather_timer.start(config.weather_update_interval * 1000)

        # Radar timer
        self.radar_timer = QTimer()
        self.radar_timer.timeout.connect(self.refresh_radar)
        self.radar_timer.start(config.radar_update_interval * 1000)

    def refresh_all_data(self):
        """Refresh all weather data."""
        self.status_label.setText("Refreshing all data...")
        self.refresh_alerts()
        self.refresh_weather()
        self.refresh_radar()
        self.refresh_atmospheric()
        self.status_label.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    def refresh_alerts(self):
        """Refresh weather alerts."""
        thread = DataFetchThread(
            "alerts",
            self.nws_client.get_alerts,
            self.location.latitude,
            self.location.longitude
        )
        thread.data_ready.connect(self.on_alerts_ready)
        thread.start()
        self._alerts_thread = thread  # Keep reference

    def on_alerts_ready(self, data_type: str, alerts: List[WeatherAlert]):
        """Handle alerts data ready."""
        self.alerts = alerts
        self.alerts_panel.update_alerts(alerts)

        # Check for tornado warnings
        for alert in alerts:
            if "Tornado Warning" in alert.event and self.sound_alerts.enabled:
                self.sound_alerts.play_tornado_warning()
                break

    def refresh_weather(self):
        """Refresh current weather."""
        thread = DataFetchThread(
            "weather",
            self.nws_client.get_observation,
            self.location.latitude,
            self.location.longitude
        )
        thread.data_ready.connect(self.on_weather_ready)
        thread.start()
        self._weather_thread = thread

    def on_weather_ready(self, data_type: str, weather: Optional[CurrentWeather]):
        """Handle weather data ready."""
        self.current_weather = weather
        self.weather_panel.update_weather(weather, self.location.name)

    def refresh_radar(self):
        """Refresh radar data."""
        # Find nearest station
        stations = self.nexrad_client.find_nearest_stations(
            self.location.latitude,
            self.location.longitude,
            count=1
        )
        station = stations[0][0] if stations else "KTLX"

        thread = DataFetchThread(
            "radar",
            self.nexrad_client.get_reflectivity_data,
            station,
            self.location.latitude,
            self.location.longitude,
            radius_km=300
        )
        thread.data_ready.connect(lambda dt, data: self.on_radar_ready(dt, data, station))
        thread.start()
        self._radar_thread = thread

    def on_radar_ready(self, data_type: str, radar_data, station: str):
        """Handle radar data ready."""
        self.radar_data = radar_data
        self.radar_panel.update_radar(radar_data, station)

        # Detect storm cells
        if radar_data:
            thread = DataFetchThread(
                "cells",
                self.nexrad_client.detect_storm_cells,
                radar_data,
                threshold_dbz=40
            )
            thread.data_ready.connect(self.on_cells_ready)
            thread.start()
            self._cells_thread = thread

    def on_cells_ready(self, data_type: str, cells: List[StormCell]):
        """Handle storm cells data ready."""
        self.storm_cells = cells
        self.cells_panel.update_cells(cells, (self.location.latitude, self.location.longitude))

    def refresh_atmospheric(self):
        """Refresh atmospheric data."""
        thread = DataFetchThread(
            "atmospheric",
            self.meso_client.get_atmospheric_parameters,
            self.location.latitude,
            self.location.longitude
        )
        thread.data_ready.connect(self.on_atmospheric_ready)
        thread.start()
        self._atmos_thread = thread

    def on_atmospheric_ready(self, data_type: str, data: Optional[AtmosphericData]):
        """Handle atmospheric data ready."""
        self.atmospheric_data = data
        self.atmospheric_panel.update_atmospheric(data)

    def toggle_sound(self):
        """Toggle sound alerts."""
        self.sound_alerts.enabled = not self.sound_alerts.enabled
        self.sound_btn.setText("🔔 Sound: ON" if self.sound_alerts.enabled else "🔕 Sound: OFF")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About WXNET",
            """<h2>WXNET - Professional Severe Weather Monitoring</h2>
            <p>Version 2.0 - Desktop GUI Edition</p>
            <p>Real-time severe weather tracking and analysis system.</p>
            <p><b>Features:</b></p>
            <ul>
            <li>NWS Weather Alerts</li>
            <li>NEXRAD Radar (160+ stations)</li>
            <li>Storm Cell Detection & Tracking</li>
            <li>Storm Prediction Center Products</li>
            <li>Lightning Detection & Analysis</li>
            <li>GPS Tracking & Intercept Calculations</li>
            </ul>
            <p>© 2024 WXNET Project</p>
            """
        )

    def apply_dark_theme(self):
        """Apply dark theme to application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 10px 20px;
                margin: 2px;
                border: 1px solid #444;
                border-radius: 5px 5px 0 0;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                border-bottom: 2px solid #44aaff;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #44aaff;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QMenuBar {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #3a3a3a;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #444;
            }
            QMenu::item:selected {
                background-color: #44aaff;
            }
            QToolBar {
                background-color: #2a2a2a;
                border: 1px solid #444;
                spacing: 5px;
                padding: 5px;
            }
            QStatusBar {
                background-color: #2a2a2a;
                color: #aaa;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def closeEvent(self, event):
        """Handle window close event."""
        # Close all HTTP sessions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if self.nws_client and self.nws_client.session:
            loop.run_until_complete(self.nws_client.session.close())
        if self.nexrad_client and self.nexrad_client.session:
            loop.run_until_complete(self.nexrad_client.session.close())
        if self.spc_client and self.spc_client.session:
            loop.run_until_complete(self.spc_client.session.close())
        if self.lightning_client and self.lightning_client.session:
            loop.run_until_complete(self.lightning_client.session.close())
        if self.meso_client and self.meso_client.session:
            loop.run_until_complete(self.meso_client.session.close())

        loop.close()

        # Stop GPS tracking
        if self.gps_tracker:
            self.gps_tracker.stop_tracking()

        event.accept()


def main():
    """Main entry point for desktop GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("WXNET")
    app.setOrganizationName("WXNET")

    window = WXNETMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
