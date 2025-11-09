#!/usr/bin/env python3
"""WXNET - Severe Weather Monitoring Terminal launcher."""

import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wxnet.app import main

if __name__ == "__main__":
    main()
