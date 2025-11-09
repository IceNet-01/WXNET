# WXNET Quick Start Guide

Get up and running with WXNET in under 5 minutes!

## 1. Install (One Command)

```bash
curl -sSL https://raw.githubusercontent.com/IceNet-01/WXNET/main/install.sh | bash

```

**Or** if you've cloned the repository:

```bash
cd WXNET
chmod +x install.sh
./install.sh
```

## 2. Refresh Your Shell

```bash
source ~/.bashrc  # For bash users

# OR

source ~/.zshrc   # For zsh users
```

## 3. Configure Your Location

```bash
nano ~/.wxnet/.env
```

Change these lines to your location:
```
DEFAULT_LATITUDE=35.0      # Your latitude
DEFAULT_LONGITUDE=-97.5    # Your longitude
DEFAULT_LOCATION=Your City, State
```

**Don't know your coordinates?**
- Google Maps: Right-click → "What's here?"
- Or search: "my coordinates" in Google

## 4. Run WXNET

```bash
wxnet
```

That's it! You're now monitoring severe weather!

## Quick Tips

### Keyboard Shortcuts
- `q` - Quit
- `r` - Refresh data
- `↑/↓` - Scroll
- `Tab` - Switch panels

### What You're Seeing

**Left Column:**
- 🚨 **Top**: Active weather alerts (warnings, watches)
- 🌡️ **Middle**: Current weather conditions
- 📊 **Bottom**: Atmospheric parameters (for severe weather potential)

**Right Column:**
- 📡 **Top**: ASCII radar display
- ⛈️ **Bottom**: Detected storm cells with tracking info

### Understanding Alerts

Colors indicate severity:
- 🔴 **Red/Bright Red** - EXTREME/SEVERE (Take action NOW!)
- 🟡 **Yellow** - MODERATE (Be prepared)
- 🔵 **Blue** - MINOR (Be aware)

### Storm Cell Indicators

- **TVS** 🌪️ - Tornado Vortex Signature (TAKE SHELTER!)
- **MESO** - Mesocyclone (Rotating supercell)
- **High dBZ** (>55) - Heavy rain/large hail

### Updating WXNET

```bash
wxnet-update
```

### Getting Help

View full documentation:
```bash
cat ~/.wxnet/README.md
```

Or online: https://github.com/IceNet-01/WXNET

## Example Locations

Popular storm chasing areas (for testing):

```bash
# Oklahoma City (Tornado Alley)
DEFAULT_LATITUDE=35.47
DEFAULT_LONGITUDE=-97.52

# Wichita, KS
DEFAULT_LATITUDE=37.69
DEFAULT_LONGITUDE=-97.34

# Norman, OK (NSSL)
DEFAULT_LATITUDE=35.22
DEFAULT_LONGITUDE=-97.44

# Amarillo, TX
DEFAULT_LATITUDE=35.22
DEFAULT_LONGITUDE=-101.83
```

## Troubleshooting

### "wxnet: command not found"
```bash
source ~/.bashrc  # Or restart your terminal
```

### No data showing
1. Check internet connection
2. Verify location in config: `nano ~/.wxnet/.env`
3. Wait 30 seconds for initial data load

### Installation failed
Make sure you have:
- Python 3.8+ (`python3 --version`)
- pip3 (`pip3 --version`)
- Internet connection

### Still having issues?
```bash
# Reinstall
wxnet-uninstall
curl -sSL [install-url] | bash
```

## Safety Reminder

⚠️ **WXNET is for information only!**

- Always follow official NWS warnings
- Never chase storms without proper training
- Have multiple weather information sources
- Know your escape routes
- **When in doubt, take shelter!**

## Next Steps

1. **Explore the interface** - Try different keyboard shortcuts
2. **Monitor a few storms** - Learn to read the data
3. **Customize settings** - Edit `~/.wxnet/.env`
4. **Read full docs** - Check out README.md for advanced features

---

**Happy (safe) storm chasing!** ⛈️

```
     ⚡
    ⛈️  WXNET
   🌪️   Ready to track!
```
