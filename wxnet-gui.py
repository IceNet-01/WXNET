#!/usr/bin/env python3
"""
WXNET Desktop GUI Launcher
"""

import sys
import os

# Add wxnet to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check for PyQt6
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
except ImportError:
    print("ERROR: PyQt6 is not installed.")
    print("Please install it with: pip install PyQt6")
    sys.exit(1)

# Launch GUI
from wxnet.gui_app import main

if __name__ == "__main__":
    main()
