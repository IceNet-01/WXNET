# Changelog

All notable changes to WXNET will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Initial Release

#### Added
- **Real-time Weather Alerts**
  - NOAA/NWS integration
  - Tornado, severe thunderstorm, and flood warnings
  - Color-coded severity levels
  - Automatic alert updates every 60 seconds

- **Radar Visualization**
  - ASCII radar display in terminal
  - NEXRAD station support
  - Reflectivity and velocity products
  - Auto-refresh every 2 minutes
  - Nearest station detection

- **Storm Cell Tracking**
  - Automatic cell detection from radar
  - Movement tracking (speed and direction)
  - Rotation detection (TVS, Mesocyclone)
  - Hail size estimation
  - Distance and bearing calculations
  - Up to 10 simultaneous cells

- **Current Weather**
  - Temperature and feels-like
  - Humidity and dewpoint
  - Barometric pressure
  - Wind speed, direction, and gusts
  - Visibility
  - Conditions description

- **Atmospheric Parameters**
  - CAPE (Convective Available Potential Energy)
  - CIN (Convective Inhibition)
  - Helicity (0-3km)
  - Wind Shear (0-6km)
  - Lifted Index
  - K-Index
  - Total Totals Index

- **Beautiful TUI Interface**
  - Multi-panel layout
  - Real-time data updates
  - Keyboard navigation
  - Color-coded information
  - Scrollable panels

- **Configuration System**
  - Location settings
  - API key support
  - Update intervals
  - Display preferences
  - Environment-based config

- **Installation & Maintenance**
  - One-line installer
  - Automatic dependency management
  - Update checker and updater
  - Clean uninstaller
  - Virtual environment isolation

- **Documentation**
  - Comprehensive README
  - Quick Start guide
  - Contributing guidelines
  - Safety disclaimers

### Technical Details
- Python 3.8+ support
- Async/await architecture
- Textual TUI framework
- Rich terminal rendering
- Pydantic data models
- aiohttp for async HTTP
- Configurable via .env file

### Data Sources
- NOAA National Weather Service API
- NEXRAD Radar Network
- Storm Prediction Center
- Mesoanalysis data

---

## [Unreleased]

### Planned Features
- Lightning strike data and visualization
- Satellite imagery integration
- Enhanced storm tracking algorithms
- Multiple location monitoring
- Historical data analysis
- Sound alerts for critical warnings
- Push notification support
- Mobile companion app
- Web dashboard
- International weather service support

### Known Issues
- Radar data is simulated (pending NEXRAD Level 2 integration)
- Lightning data not yet implemented
- Limited to United States coverage
- No offline mode (requires internet)

---

## Version History

- **1.0.0** (2024-01-15) - Initial public release
- **0.9.0** (2024-01-10) - Beta release for testing
- **0.5.0** (2024-01-05) - Alpha release with core features
- **0.1.0** (2024-01-01) - Initial development version

---

## Migration Guides

### Upgrading to 1.0.0
This is the initial release, no migration needed.

---

For detailed information about each release, see the [GitHub Releases](https://github.com/IceNet-01/WXNET/releases) page.
