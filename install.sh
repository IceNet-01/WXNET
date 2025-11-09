#!/usr/bin/env bash
###############################################################################
# WXNET Installer
# One-line install: curl -sSL https://raw.githubusercontent.com/IceNet-01/WXNET/claude/weather-monitoring-terminal-011CUxi4g9UvRcxQaB6Yc3qQ/install.sh | bash
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.wxnet"
BIN_DIR="$HOME/.local/bin"
REPO_URL="https://github.com/IceNet-01/WXNET.git"

# Print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Print header
print_header() {
    echo ""
    print_msg "$BLUE" "╔════════════════════════════════════════════════════════════╗"
    print_msg "$BLUE" "║        WXNET - Severe Weather Monitoring Terminal         ║"
    print_msg "$BLUE" "║                     Installation Script                    ║"
    print_msg "$BLUE" "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_msg "$YELLOW" "Checking prerequisites..."

    # Check for Python 3.8+
    if ! command_exists python3; then
        print_msg "$RED" "Error: Python 3 is not installed."
        print_msg "$YELLOW" "Please install Python 3.8 or higher and try again."
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.8"

    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_msg "$RED" "Error: Python 3.8+ required. Found version $PYTHON_VERSION"
        exit 1
    fi

    print_msg "$GREEN" "✓ Python $PYTHON_VERSION found"

    # Check for pip
    if ! command_exists pip3; then
        print_msg "$RED" "Error: pip3 is not installed."
        print_msg "$YELLOW" "Please install pip3 and try again."
        exit 1
    fi

    print_msg "$GREEN" "✓ pip3 found"

    # Check for git (optional, for updates)
    if command_exists git; then
        print_msg "$GREEN" "✓ git found (enables automatic updates)"
    else
        print_msg "$YELLOW" "⚠ git not found (manual updates only)"
    fi
}

# Create installation directory
create_install_dir() {
    print_msg "$YELLOW" "Creating installation directory..."

    if [ -d "$INSTALL_DIR" ]; then
        print_msg "$YELLOW" "Existing installation found. Backing up..."
        mv "$INSTALL_DIR" "$INSTALL_DIR.backup.$(date +%s)"
    fi

    mkdir -p "$INSTALL_DIR"
    print_msg "$GREEN" "✓ Installation directory created"
}

# Install WXNET
install_wxnet() {
    print_msg "$YELLOW" "Installing WXNET..."

    # If running from local directory (development install)
    if [ -f "$(dirname "$0")/wxnet.py" ]; then
        print_msg "$YELLOW" "Installing from local directory..."
        cp -r "$(dirname "$0")"/* "$INSTALL_DIR/"
    # If running from downloaded script
    elif command_exists git; then
        print_msg "$YELLOW" "Cloning from repository..."
        git clone "$REPO_URL" "$INSTALL_DIR"
    else
        # Download as tarball
        print_msg "$YELLOW" "Downloading archive..."
        curl -sSL "$REPO_URL/archive/main.tar.gz" | tar -xz -C "$INSTALL_DIR" --strip-components=1
    fi

    print_msg "$GREEN" "✓ WXNET files installed"
}

# Install Python dependencies
install_dependencies() {
    print_msg "$YELLOW" "Installing Python dependencies..."

    cd "$INSTALL_DIR"

    # Create virtual environment
    python3 -m venv venv

    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1

    deactivate

    print_msg "$GREEN" "✓ Dependencies installed"
}

# Create launcher script
create_launcher() {
    print_msg "$YELLOW" "Creating launcher script..."

    mkdir -p "$BIN_DIR"

    cat > "$BIN_DIR/wxnet" << 'EOF'
#!/usr/bin/env bash
# WXNET Launcher

INSTALL_DIR="$HOME/.wxnet"
cd "$INSTALL_DIR"
source venv/bin/activate
python3 wxnet.py "$@"
deactivate
EOF

    chmod +x "$BIN_DIR/wxnet"

    print_msg "$GREEN" "✓ Launcher created"
}

# Create configuration file
create_config() {
    print_msg "$YELLOW" "Creating configuration file..."

    if [ ! -f "$INSTALL_DIR/.env" ]; then
        cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
        print_msg "$GREEN" "✓ Configuration file created"
        print_msg "$YELLOW" "  Edit $INSTALL_DIR/.env to customize settings"
    else
        print_msg "$YELLOW" "⚠ Configuration file already exists, skipping"
    fi
}

# Add to PATH
add_to_path() {
    print_msg "$YELLOW" "Configuring PATH..."

    # Check if already in PATH
    if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
        print_msg "$GREEN" "✓ $BIN_DIR already in PATH"
        return
    fi

    # Determine shell config file
    SHELL_CONFIG=""
    if [ -n "$BASH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    else
        # Try to detect
        if [ -f "$HOME/.bashrc" ]; then
            SHELL_CONFIG="$HOME/.bashrc"
        elif [ -f "$HOME/.zshrc" ]; then
            SHELL_CONFIG="$HOME/.zshrc"
        fi
    fi

    if [ -n "$SHELL_CONFIG" ]; then
        echo "" >> "$SHELL_CONFIG"
        echo "# WXNET" >> "$SHELL_CONFIG"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_CONFIG"
        print_msg "$GREEN" "✓ Added to PATH in $SHELL_CONFIG"
        print_msg "$YELLOW" "  Run 'source $SHELL_CONFIG' or restart your terminal"
    else
        print_msg "$YELLOW" "⚠ Could not detect shell config file"
        print_msg "$YELLOW" "  Please add $BIN_DIR to your PATH manually"
    fi
}

# Create updater script
create_updater() {
    print_msg "$YELLOW" "Creating updater script..."

    cat > "$BIN_DIR/wxnet-update" << 'EOF'
#!/usr/bin/env bash
# WXNET Updater

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="$HOME/.wxnet"

echo -e "${YELLOW}Checking for updates...${NC}"

cd "$INSTALL_DIR"

if [ -d .git ]; then
    # Git repository - use git pull
    git fetch origin
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})

    if [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "${GREEN}WXNET is up to date!${NC}"
        exit 0
    fi

    echo -e "${YELLOW}Updates available! Updating...${NC}"
    git pull origin main

    # Update dependencies
    source venv/bin/activate
    pip install --upgrade -r requirements.txt > /dev/null 2>&1
    deactivate

    echo -e "${GREEN}✓ WXNET updated successfully!${NC}"
else
    echo -e "${YELLOW}Git repository not found. Please reinstall WXNET for automatic updates.${NC}"
    exit 1
fi
EOF

    chmod +x "$BIN_DIR/wxnet-update"

    print_msg "$GREEN" "✓ Updater created"
}

# Create uninstaller script
create_uninstaller() {
    print_msg "$YELLOW" "Creating uninstaller script..."

    cat > "$BIN_DIR/wxnet-uninstall" << 'EOF'
#!/usr/bin/env bash
# WXNET Uninstaller

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}This will completely remove WXNET from your system.${NC}"
read -p "Are you sure? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 1
fi

echo -e "${YELLOW}Removing WXNET...${NC}"

# Remove installation directory
rm -rf "$HOME/.wxnet"

# Remove launcher scripts
rm -f "$HOME/.local/bin/wxnet"
rm -f "$HOME/.local/bin/wxnet-update"
rm -f "$HOME/.local/bin/wxnet-uninstall"

echo -e "${RED}WXNET has been uninstalled.${NC}"
echo -e "${YELLOW}Note: PATH modifications in your shell config were not removed.${NC}"
EOF

    chmod +x "$BIN_DIR/wxnet-uninstall"

    print_msg "$GREEN" "✓ Uninstaller created"
}

# Print success message
print_success() {
    echo ""
    print_msg "$GREEN" "╔════════════════════════════════════════════════════════════╗"
    print_msg "$GREEN" "║          WXNET Installation Complete!                     ║"
    print_msg "$GREEN" "╚════════════════════════════════════════════════════════════╝"
    echo ""
    print_msg "$YELLOW" "Quick Start:"
    print_msg "$BLUE" "  1. Configure your location:"
    print_msg "$NC" "     Edit $INSTALL_DIR/.env"
    echo ""
    print_msg "$BLUE" "  2. Run WXNET:"
    print_msg "$NC" "     wxnet"
    echo ""
    print_msg "$BLUE" "  3. Update WXNET:"
    print_msg "$NC" "     wxnet-update"
    echo ""
    print_msg "$BLUE" "  4. Uninstall WXNET:"
    print_msg "$NC" "     wxnet-uninstall"
    echo ""
    print_msg "$YELLOW" "Note: You may need to run 'source ~/.bashrc' or restart your terminal"
    print_msg "$YELLOW" "      for the 'wxnet' command to be available."
    echo ""
}

# Main installation process
main() {
    print_header
    check_prerequisites
    create_install_dir
    install_wxnet
    install_dependencies
    create_launcher
    create_config
    add_to_path
    create_updater
    create_uninstaller
    print_success
}

# Run installation
main
