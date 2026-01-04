#!/usr/bin/env python3
"""Notion synchronization entry point."""

import os
import sys

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv

load_dotenv()

from src.notion import main

if __name__ == "__main__":
    main()
