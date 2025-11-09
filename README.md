# WXNET - Severe Weather Monitoring Terminal

```
╔════════════════════════════════════════════════════════════╗
║        WXNET - Severe Weather Monitoring Terminal         ║
║           Real-time Storm Tracking & Analysis             ║
╚════════════════════════════════════════════════════════════╝
```

A comprehensive terminal-based severe weather monitoring, alert, and tracking system designed for storm chasers, weather enthusiasts, and emergency management professionals. Built with a beautiful TUI (Terminal User Interface) inspired by NomadNet.

## Features

### 🌪️ Severe Weather Alerts
- **Real-time NOAA/NWS alerts** with automatic updates
- **Color-coded severity levels** (Extreme, Severe, Moderate, Minor)
- **Alert types:**
  - Tornado Warnings & Watches
  - Severe Thunderstorm Warnings & Watches
  - Flash Flood Warnings
  - Special Weather Statements
  - And more...
- **Visual indicators** with emoji symbols
- **Expiration tracking** with countdown timers

### 📡 Radar Visualization
- **ASCII/Unicode radar display** in your terminal
- **Multiple radar products:**
  - Reflectivity (Base/Composite)
  - Velocity
  - Storm Total Precipitation
- **NEXRAD station support** across the United States
- **Automatic station selection** based on your location
- **Color-coded intensity** (dBZ scale)
- **Real-time updates** every 2 minutes

### ⛈️ Storm Cell Tracking
- **Automatic storm cell detection** from radar data
- **Individual cell analysis:**
  - Maximum reflectivity intensity (dBZ)
  - Storm top height
  - Movement speed and direction
  - Distance and bearing from your location
- **Rotation detection:**
  - Mesocyclone signatures (MESO)
  - Tornado Vortex Signatures (TVS)
  - Rotation strength measurements
- **Hail probability and size estimates**
- **Storm path prediction**

### 🌡️ Current Weather Conditions
- **Temperature** (actual and feels-like)
- **Dewpoint** (comfort index)
- **Humidity** (relative humidity %)
- **Barometric pressure** (inHg)
- **Wind speed, direction, and gusts**
- **Visibility** (miles)
- **Sky conditions**
- **Auto-refresh** every 5 minutes

### 📊 Atmospheric Parameters
Essential data for severe weather analysis:
- **CAPE** (Convective Available Potential Energy) - Instability measure
- **CIN** (Convective Inhibition) - Cap strength
- **Helicity** (0-3km) - Rotation potential
- **Wind Shear** (0-6km) - Storm organization
- **Lifted Index** - Thunderstorm potential
- **K-Index** - Thunderstorm probability
- **Total Totals** - Severe weather index

### 🗺️ Location Features
- **GPS/Manual location entry**
- **Auto-detection** of nearest radar stations
- **Distance and bearing calculations** to storms
- **Multi-location support**
- **Coordinate formats** (lat/lon, decimal degrees)

### ⚡ Additional Features
- **Beautiful TUI** with multiple panels and tabs
- **Keyboard shortcuts** for quick navigation
- **Real-time data refresh**
- **Configurable update intervals**
- **Data caching** for offline review
- **Low bandwidth mode** option
- **Color customization**

## Installation

### One-Line Install

The easiest way to install WXNET:

```bash
curl -sSL https://raw.githubusercontent.com/your-repo/WXNET/main/install.sh | bash
```

### Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/WXNET.git
   cd WXNET
   ```

2. **Run the installer:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Activate your shell changes:**
   ```bash
   source ~/.bashrc  # or ~/.zshrc for zsh users
   ```

### Requirements

- **Python 3.8 or higher**
- **pip3** (Python package installer)
- **git** (for automatic updates)
- **Internet connection** (for weather data)

The installer will check for these and guide you through any missing dependencies.

## Configuration

After installation, configure your location:

```bash
nano ~/.wxnet/.env
```

### Configuration Options

```bash
# Default location (required)
DEFAULT_LATITUDE=35.0
DEFAULT_LONGITUDE=-97.5
DEFAULT_LOCATION=Oklahoma City, OK

# API Keys (optional - uses free APIs by default)
OPENWEATHER_API_KEY=your_key_here
NWS_USER_AGENT=WXNET Weather Terminal (your@email.com)

# Update intervals (seconds)
WEATHER_UPDATE_INTERVAL=300    # 5 minutes
ALERT_UPDATE_INTERVAL=60       # 1 minute
RADAR_UPDATE_INTERVAL=120      # 2 minutes

# Display settings
USE_COLOR=true
ALERT_SOUND=false
ANIMATION_SPEED=medium
```

## Usage

### Starting WXNET

Simply run:
```bash
wxnet
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit WXNET |
| `r` | Refresh all data |
| `1` | Dashboard view |
| `2` | Radar view |
| `3` | Forecast view |
| `4` | Alerts view |
| `↑/↓` | Scroll panels |
| `Tab` | Switch between panels |
| `Ctrl+C` | Emergency exit |

### Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│ WXNET - Severe Weather Monitoring                          │
├───────────────────┬─────────────────────────────────────────┤
│ ⚠ ACTIVE ALERTS   │ 📡 RADAR                                │
│                   │                                         │
│ [Alert List]      │ [ASCII Radar Display]                  │
│                   │                                         │
├───────────────────┤                                         │
│ 🌡 CURRENT        │                                         │
│                   │                                         │
│ [Conditions]      │                                         │
│                   ├─────────────────────────────────────────┤
├───────────────────┤ ⛈ STORM CELLS                          │
│ 📊 ATMOSPHERIC    │                                         │
│                   │ [Cell List with Details]               │
│ [Parameters]      │                                         │
│                   │                                         │
└───────────────────┴─────────────────────────────────────────┘
│ q: Quit | r: Refresh | 1-4: Views | ↑/↓: Scroll           │
└─────────────────────────────────────────────────────────────┘
```

## Updating WXNET

### Automatic Update Check

Run the update script:
```bash
wxnet-update
```

Or from the repository:
```bash
./update.sh
```

The updater will:
1. Check for available updates
2. Show you what's changed
3. Ask for confirmation
4. Update the software
5. Update dependencies
6. Preserve your configuration

### Manual Update

```bash
cd ~/.wxnet
git pull origin main
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Uninstalling

### Using the Uninstaller

```bash
wxnet-uninstall
```

Or from the repository:
```bash
./uninstall.sh
```

The uninstaller will:
1. Ask for confirmation (twice, for safety!)
2. Offer to backup your configuration
3. Remove all WXNET files
4. Remove launcher scripts
5. Provide instructions for manual PATH cleanup

### Manual Uninstall

```bash
rm -rf ~/.wxnet
rm -f ~/.local/bin/wxnet
rm -f ~/.local/bin/wxnet-update
rm -f ~/.local/bin/wxnet-uninstall
```

## Data Sources

WXNET aggregates data from multiple authoritative sources:

- **NOAA/NWS** - National Weather Service API
  - Weather alerts and warnings
  - Current observations
  - Forecast data
  - Point forecasts

- **NEXRAD** - Next Generation Weather Radar
  - Level 2 and Level 3 radar data
  - Base reflectivity
  - Storm relative velocity
  - Composite products

- **SPC** - Storm Prediction Center
  - Convective outlooks
  - Mesoscale discussions
  - Watch products

- **Mesoanalysis** - Real-time atmospheric parameters
  - CAPE, Shear, Helicity
  - Surface observations
  - Upper air data

## Understanding the Data

### Alert Severity Levels

- **🔴 Extreme**: Extraordinary threat to life/property
- **🟠 Severe**: Significant threat to life/property
- **🟡 Moderate**: Possible threat to life/property
- **🔵 Minor**: Minimal threat to life/property

### Radar Reflectivity Scale

| dBZ | Color | Meaning |
|-----|-------|---------|
| <15 | - | No significant weather |
| 15-25 | 🔵 Blue | Light rain |
| 25-35 | 🟢 Green | Moderate rain |
| 35-45 | 🟡 Yellow | Heavy rain |
| 45-55 | 🟠 Orange | Very heavy rain / small hail |
| 55-65 | 🔴 Red | Intense rain / large hail |
| >65 | ⚫ Purple | Extreme precipitation / giant hail |

### Storm Cell Indicators

- **TVS** - Tornado Vortex Signature (strong rotation, possible tornado)
- **MESO** - Mesocyclone (rotating updraft, supercell characteristic)
- **High dBZ** - Strong reflectivity (heavy rain, hail)
- **High tops** - Tall storm (strong updraft, severe potential)

### Atmospheric Parameters

#### CAPE (J/kg)
- <1000: Weak instability
- 1000-2500: Moderate instability
- 2500-4000: Strong instability
- >4000: Extreme instability (violent storms possible)

#### Helicity (m²/s²)
- <150: Weak rotation potential
- 150-300: Moderate rotation potential
- 300-450: Strong rotation potential (supercells likely)
- >450: Extreme rotation potential (violent tornadoes possible)

#### Wind Shear (knots)
- <20: Weak shear (storms disorganized)
- 20-40: Moderate shear (organized storms possible)
- 40-60: Strong shear (supercells likely)
- >60: Extreme shear (violent storms possible)

## Use Cases

### Storm Chasers
- Real-time storm position and movement
- Distance and bearing calculations for intercept
- Rotation signatures and tornado potential
- Multiple storms tracking simultaneously

### Emergency Management
- Active alert monitoring for jurisdiction
- Storm impact prediction
- Population warning dissemination
- Resource allocation planning

### Weather Enthusiasts
- Educational tool for understanding severe weather
- Real-time data visualization
- Atmospheric parameter analysis
- Weather pattern recognition

### Research & Education
- Data collection for study
- Real-time case study analysis
- Severe weather parameter correlation
- Teaching tool for meteorology

## Advanced Features

### Custom Alert Filters
Configure which alerts you want to see based on:
- Severity level
- Event type
- Geographic area
- Time to expiration

### Data Export
Export data for analysis:
```bash
wxnet --export-alerts alerts.json
wxnet --export-radar radar.csv
wxnet --export-cells cells.json
```

### Headless Mode
Run WXNET without the TUI for scripting:
```bash
wxnet --headless --watch-alerts
```

### Multiple Locations
Monitor multiple locations simultaneously:
```bash
wxnet --locations "OKC,35,-97" "TUL,36,-95" "ICT,37,-97"
```

## Troubleshooting

### WXNET won't start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Reinstall dependencies
cd ~/.wxnet
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### No data showing
- Check your internet connection
- Verify your location in `~/.wxnet/.env`
- Check NWS API status: https://api.weather.gov/

### Radar not displaying
- Ensure you're in the United States (NEXRAD coverage)
- Check if nearest radar station is operational
- Try manual station selection in config

### Updates not working
```bash
# Ensure git repository
cd ~/.wxnet
git status

# If not a git repo, reinstall
curl -sSL [install-url] | bash
```

## Contributing

We welcome contributions! Areas for improvement:

- Additional radar products
- Lightning data integration
- Satellite imagery
- Enhanced cell tracking algorithms
- Mobile/tablet support
- International weather services
- Sound alerts
- Push notifications

## Safety Notice

⚠️ **IMPORTANT**: WXNET is a tool for weather monitoring and should be used alongside, not instead of, official warnings and professional meteorological guidance.

- Always follow official National Weather Service warnings
- Never put yourself in danger chasing storms
- Have multiple sources of weather information
- Know your escape routes and safe locations
- When in doubt, take shelter immediately

**Your safety is the top priority!**

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Credits

Created for storm chasers, by storm chasers.

### Data Providers
- NOAA National Weather Service
- NEXRAD Radar Network
- Storm Prediction Center

### Technologies
- Python 3.8+
- Textual TUI Framework
- Rich Terminal Formatting
- aiohttp for async API calls

### Inspiration
- NomadNet terminal interface
- GRLevel3 radar software
- Traditional storm chasing tools

## Support

- **Issues**: https://github.com/your-repo/WXNET/issues
- **Discussions**: https://github.com/your-repo/WXNET/discussions
- **Email**: support@wxnet.example.com

## Changelog

### Version 1.0.0 (Initial Release)
- Real-time NWS alerts
- NEXRAD radar visualization
- Storm cell detection and tracking
- Atmospheric parameters display
- Current weather conditions
- Beautiful TUI interface
- Auto-installer and updater
- Multi-location support

---

**Stay informed. Stay safe. Chase responsibly.**

```
     ⚡
    ⛈️  WXNET
   🌪️   Your Weather Command Center
```
