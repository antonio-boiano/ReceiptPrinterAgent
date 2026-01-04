#!/usr/bin/env python3
"""Notion synchronization entry point."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.notion import main

if __name__ == "__main__":
    main()
