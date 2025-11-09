#!/usr/bin/env bash
###############################################################################
# WXNET Uninstaller
# Removes WXNET from the system
###############################################################################

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="$HOME/.wxnet"
BIN_DIR="$HOME/.local/bin"

print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_header() {
    echo ""
    print_msg "$RED" "╔════════════════════════════════════════════════════════════╗"
    print_msg "$RED" "║              WXNET Uninstaller                            ║"
    print_msg "$RED" "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

confirm_uninstall() {
    print_msg "$YELLOW" "This will completely remove WXNET from your system."
    print_msg "$YELLOW" "The following will be deleted:"
    echo ""
    print_msg "$BLUE" "  - Installation directory: $INSTALL_DIR"
    print_msg "$BLUE" "  - Launcher scripts in: $BIN_DIR"
    print_msg "$BLUE" "  - All configuration and cache data"
    echo ""
    print_msg "$RED" "This action cannot be undone!"
    echo ""

    read -p "Are you absolutely sure you want to uninstall WXNET? (yes/no) " -r
    echo

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_msg "$GREEN" "Uninstall cancelled."
        exit 0
    fi

    # Double confirmation
    read -p "Type 'DELETE' to confirm: " -r
    echo

    if [[ $REPLY != "DELETE" ]]; then
        print_msg "$GREEN" "Uninstall cancelled."
        exit 0
    fi
}

backup_config() {
    if [ -f "$INSTALL_DIR/.env" ]; then
        print_msg "$YELLOW" "Would you like to backup your configuration?"
        read -p "Save config backup? (Y/n) " -n 1 -r
        echo

        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            BACKUP_FILE="$HOME/wxnet-config-backup-$(date +%s).env"
            cp "$INSTALL_DIR/.env" "$BACKUP_FILE"
            print_msg "$GREEN" "✓ Config saved to: $BACKUP_FILE"
        fi
    fi
}

remove_files() {
    print_msg "$YELLOW" "Removing WXNET..."

    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        print_msg "$GREEN" "✓ Removed installation directory"
    fi

    # Remove launcher scripts
    if [ -f "$BIN_DIR/wxnet" ]; then
        rm -f "$BIN_DIR/wxnet"
        print_msg "$GREEN" "✓ Removed wxnet launcher"
    fi

    if [ -f "$BIN_DIR/wxnet-update" ]; then
        rm -f "$BIN_DIR/wxnet-update"
        print_msg "$GREEN" "✓ Removed update script"
    fi

    if [ -f "$BIN_DIR/wxnet-uninstall" ]; then
        rm -f "$BIN_DIR/wxnet-uninstall"
        print_msg "$GREEN" "✓ Removed uninstall script"
    fi
}

cleanup_path() {
    print_msg "$YELLOW" ""
    print_msg "$YELLOW" "Note: PATH modifications in your shell config were not automatically removed."
    print_msg "$YELLOW" "If you added ~/.local/bin to your PATH specifically for WXNET,"
    print_msg "$YELLOW" "you may want to remove it from your shell configuration file."
    print_msg "$YELLOW" "(Usually ~/.bashrc or ~/.zshrc)"
}

print_goodbye() {
    echo ""
    print_msg "$RED" "╔════════════════════════════════════════════════════════════╗"
    print_msg "$RED" "║          WXNET has been uninstalled                       ║"
    print_msg "$RED" "╚════════════════════════════════════════════════════════════╝"
    echo ""
    print_msg "$BLUE" "Thank you for using WXNET!"
    print_msg "$YELLOW" "Stay safe out there, storm chasers!"
    echo ""
}

main() {
    print_header

    # Check if installed
    if [ ! -d "$INSTALL_DIR" ]; then
        print_msg "$YELLOW" "WXNET does not appear to be installed."
        exit 0
    fi

    confirm_uninstall
    backup_config
    remove_files
    cleanup_path
    print_goodbye
}

main
