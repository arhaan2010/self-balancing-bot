#!/usr/bin/env python3
"""
Self-Balancing Bot Main Entry Point
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from balance_controller import main

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
