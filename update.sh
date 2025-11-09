#!/usr/bin/env bash
###############################################################################
# WXNET Updater
# Checks for and installs updates
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="$HOME/.wxnet"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_header() {
    echo ""
    print_msg "$BLUE" "╔════════════════════════════════════════════════════════════╗"
    print_msg "$BLUE" "║              WXNET Update Checker                         ║"
    print_msg "$BLUE" "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

check_for_updates() {
    print_msg "$YELLOW" "Checking for updates..."

    # If installed version exists
    if [ -d "$INSTALL_DIR" ]; then
        cd "$INSTALL_DIR"

        if [ -d .git ]; then
            # Git repository - check remote
            git fetch origin 2>/dev/null || {
                print_msg "$RED" "Error: Unable to check for updates."
                exit 1
            }

            LOCAL=$(git rev-parse @)
            REMOTE=$(git rev-parse @{u} 2>/dev/null) || REMOTE=$LOCAL

            if [ "$LOCAL" = "$REMOTE" ]; then
                print_msg "$GREEN" "✓ WXNET is up to date!"

                # Show current version
                CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || echo "unknown")
                print_msg "$BLUE" "Current version: $CURRENT_VERSION"

                exit 0
            else
                # Show what's new
                print_msg "$YELLOW" "Updates available!"
                echo ""
                print_msg "$BLUE" "Changes:"
                git log --oneline --decorate --color=always HEAD..@{u} | head -n 5
                echo ""

                # Ask for confirmation
                read -p "Do you want to update now? (Y/n) " -n 1 -r
                echo

                if [[ $REPLY =~ ^[Nn]$ ]]; then
                    print_msg "$YELLOW" "Update cancelled."
                    exit 0
                fi

                return 0
            fi
        else
            print_msg "$YELLOW" "⚠ Not a git repository. Manual update required."
            print_msg "$YELLOW" "Please run the installer again to update."
            exit 1
        fi
    else
        print_msg "$RED" "Error: WXNET is not installed."
        print_msg "$YELLOW" "Run install.sh to install WXNET."
        exit 1
    fi
}

perform_update() {
    print_msg "$YELLOW" "Installing updates..."

    cd "$INSTALL_DIR"

    # Backup current config
    if [ -f .env ]; then
        cp .env .env.backup
        print_msg "$BLUE" "✓ Config backed up"
    fi

    # Pull updates
    git pull origin main || {
        print_msg "$RED" "Error: Update failed."
        exit 1
    }

    print_msg "$GREEN" "✓ Files updated"

    # Update dependencies
    print_msg "$YELLOW" "Updating dependencies..."

    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install --upgrade -r requirements.txt > /dev/null 2>&1
    deactivate

    print_msg "$GREEN" "✓ Dependencies updated"

    # Update GUI launcher if needed
    BIN_DIR="$HOME/.local/bin"
    if [ ! -f "$BIN_DIR/wxnet-gui" ]; then
        print_msg "$YELLOW" "Creating GUI launcher..."
        cat > "$BIN_DIR/wxnet-gui" << 'LAUNCHER_EOF'
#!/usr/bin/env bash
# WXNET Desktop GUI Launcher

INSTALL_DIR="$HOME/.wxnet"
cd "$INSTALL_DIR"
source venv/bin/activate
python3 wxnet-gui.py "$@"
deactivate
LAUNCHER_EOF
        chmod +x "$BIN_DIR/wxnet-gui"
        print_msg "$GREEN" "✓ GUI launcher created"

        # Ensure ~/.local/bin is in PATH
        if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
            print_msg "$YELLOW" "Adding $BIN_DIR to PATH..."

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
                # Check if already added
                if ! grep -q "export PATH=\"\$HOME/.local/bin:\$PATH\"" "$SHELL_CONFIG" 2>/dev/null; then
                    echo "" >> "$SHELL_CONFIG"
                    echo "# WXNET" >> "$SHELL_CONFIG"
                    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_CONFIG"
                    print_msg "$GREEN" "✓ Added to PATH in $SHELL_CONFIG"
                    print_msg "$YELLOW" "  Run: source $SHELL_CONFIG"
                fi
            else
                print_msg "$YELLOW" "⚠ Could not detect shell config. Add to PATH manually:"
                print_msg "$NC" "    export PATH=\"\$HOME/.local/bin:\$PATH\""
            fi
        fi
    fi

    # Restore config if backed up
    if [ -f .env.backup ]; then
        mv .env.backup .env
    fi

    echo ""
    print_msg "$GREEN" "╔════════════════════════════════════════════════════════════╗"
    print_msg "$GREEN" "║            Update Complete!                                ║"
    print_msg "$GREEN" "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Show new version
    NEW_VERSION=$(git describe --tags --always 2>/dev/null || echo "unknown")
    print_msg "$BLUE" "Updated to version: $NEW_VERSION"
    echo ""

    print_msg "$YELLOW" "What's New:"
    print_msg "$BLUE" "  • Desktop GUI now available! Run with: wxnet-gui"
    print_msg "$BLUE" "  • Professional PyQt6 interface with tabbed layout"
    print_msg "$BLUE" "  • Terminal interface still available: wxnet"
    echo ""

    # Check if user needs to source config
    BIN_DIR="$HOME/.local/bin"
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        print_msg "$YELLOW" "⚠ IMPORTANT: Run the following to use wxnet-gui:"
        if [ -f "$HOME/.bashrc" ]; then
            print_msg "$NC" "    source ~/.bashrc"
        elif [ -f "$HOME/.zshrc" ]; then
            print_msg "$NC" "    source ~/.zshrc"
        fi
        echo ""
    fi
}

main() {
    print_header
    check_for_updates
    perform_update
}

main
