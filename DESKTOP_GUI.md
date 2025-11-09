# WXNET Desktop GUI Edition

## 🎉 Complete Rebuild as Desktop Application

WXNET has been completely rebuilt as a professional desktop GUI application using PyQt6, replacing the problematic terminal interface.

## ✨ New Features

### Professional Desktop Interface
- **Tabbed Layout**: Overview, SPC Products, Lightning, GPS/Chase
- **Resizable Panels**: Split-view with adjustable splitters
- **Rich HTML Formatting**: Color-coded alerts and beautiful data display
- **Dark Theme**: Professional dark theme throughout
- **Menu Bar**: File, View, Settings, Help menus
- **Toolbar**: Quick access buttons for common actions

### Overview Tab (Split Panel)

**Left Column:**
1. **Alerts Panel**
   - Color-coded severity levels (Extreme = red, Severe = orange, etc.)
   - Full alert descriptions with expiration times
   - Visual severity indicators

2. **Current Weather Panel**
   - Grid layout with all weather parameters
   - Temperature, feels-like, dewpoint
   - Humidity, pressure, wind
   - Visibility and conditions
   - Auto-updates every 5 minutes

3. **Atmospheric Data Panel**
   - CAPE with interpretation (low/moderate/high/extreme)
   - CIN, Helicity with color coding
   - Wind shear, Lifted Index
   - K-Index, Total Totals

**Right Column:**
1. **NEXRAD Radar Panel**
   - Station information
   - Radar data display
   - Reflectivity scale legend

2. **Storm Cells Panel**
   - Detected cells with intensity
   - TVS (Tornado Vortex Signature) indicators
   - MESO (Mesocyclone) warnings
   - Hail size estimates
   - Distance and bearing from location
   - Movement speed and direction

### SPC Products Tab
- Convective outlooks (Day 1, 2, 3)
- Risk level visualization
- Mesoscale discussions
- Active watches

### Lightning Tab
- Recent strike locations
- CG vs IC classification
- Strike rate analysis
- Trend detection (increasing/decreasing)

### GPS/Chase Tab
- Real-time GPS location
- Intercept calculations
- Chase logging
- Distance to storms

## 🔧 Technical Implementation

### Architecture
- **PyQt6 Framework**: Modern, cross-platform GUI toolkit
- **QThread Integration**: Non-blocking async data fetching
- **Signal/Slot Pattern**: Clean event-driven updates
- **Auto-Refresh Timers**: Configurable update intervals
- **Resource Management**: Proper cleanup of HTTP sessions

### Data Flow
1. Background threads fetch data from APIs
2. Emit signals when data ready
3. Main thread updates UI widgets
4. No blocking - smooth user experience

### Themes & Styling
- Custom dark theme with QSS stylesheets
- Color-coded severity levels:
  - Red (#ff4444): Extreme/Tornado
  - Orange (#ff8800): Severe
  - Yellow (#ffff44): Storms/Warnings
  - Blue (#44aaff): Information
  - Green (#44ff44): Normal/GPS
  - Magenta (#ff44ff): Atmospheric data

## 📦 Installation & Usage

### Install/Update WXNET

```bash
# New installation
curl -sSL https://raw.githubusercontent.com/IceNet-01/WXNET/main/install.sh | bash

# Update existing installation
wxnet-update
```

The installer automatically:
- Installs PyQt6 and all dependencies
- Creates `wxnet-gui` launcher
- Sets up PATH

### Launch Desktop GUI

```bash
wxnet-gui
```

### Launch Terminal (Legacy)

```bash
wxnet
```

## ⌨️ Keyboard Shortcuts

- **F5**: Refresh all data
- **Ctrl+Q**: Quit application
- **Tab Navigation**: Switch between tabs

## 🎛️ Menu Options

### File Menu
- Refresh All (F5)
- Exit (Ctrl+Q)

### View Menu
- (Future: Toggle panels, themes)

### Settings Menu
- (Future: Configuration dialog)

### Help Menu
- About WXNET

## 🔄 Auto-Refresh

Data auto-refreshes at configurable intervals:
- Alerts: Every 60 seconds
- Weather: Every 300 seconds (5 min)
- Radar: Every 120 seconds (2 min)
- SPC Products: Every 30 seconds
- Lightning: Every 30 seconds
- GPS: Every 5 seconds

## 🆚 GUI vs Terminal Comparison

| Feature | Desktop GUI | Terminal |
|---------|------------|----------|
| **Interface** | Modern PyQt6 | Textual TUI |
| **Layout** | Resizable panels | Fixed layout |
| **Scrolling** | Native scrollbars | Works now ✓ |
| **Data Display** | Rich HTML | Plain text |
| **Updates** | Smooth async | Sometimes janky |
| **Remote Access** | X11 forwarding | Native SSH |
| **Resource Usage** | Moderate | Low |
| **Recommended For** | Desktop users | SSH/headless |

## 🐛 Known Issues (Terminal Version)

The terminal interface (Textual-based) had several persistent issues:
- Panels not displaying content
- Reactive properties not triggering recompose
- Inconsistent scrolling behavior
- ASCII rendering limitations

**→ Solution: Use the Desktop GUI (wxnet-gui)**

The desktop GUI was built from scratch to avoid these issues and provide a superior user experience.

## 📊 What Data Sources Are Used?

All the same powerful backend APIs:
- **NWS API**: Weather alerts and observations
- **NEXRAD**: 160+ radar stations via AWS S3
- **SPC**: Storm Prediction Center products
- **Blitzortung**: Lightning detection network
- **RAP/HRRR**: Atmospheric model data
- **Wyoming Soundings**: Upper-air data

## 🚀 Future Enhancements

Planned for future releases:
- [ ] Graphical radar display with matplotlib
- [ ] Interactive map with storm overlay
- [ ] Push notifications for alerts
- [ ] System tray icon
- [ ] Configurable panels
- [ ] Light/dark theme toggle
- [ ] Sound alert customization
- [ ] Chase route planning
- [ ] Historical data charts
- [ ] Export to CSV/PDF

## 🤝 Contributing

The desktop GUI is built with clean, maintainable code:
- `wxnet/gui_app.py` - Main GUI application (930+ lines)
- All backend APIs remain unchanged
- Easy to extend with new panels/features

## 📝 License

Same as WXNET - check LICENSE file

## 🙏 Acknowledgments

Built using:
- PyQt6 - GUI framework
- NWS API - Weather data
- AWS NEXRAD - Radar data
- Storm Prediction Center - SPC products
- All the WXNET backend developers

---

**Enjoy the new WXNET Desktop GUI! 🌪️⚡⛈️**

Run `wxnet-gui` to launch it now!
