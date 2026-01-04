#!/usr/bin/env python3
"""Run the local dashboard for task management."""

import argparse
import os
import sys

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv

load_dotenv()

from src.dashboard import run_dashboard


def main():
    """Main entry point for the dashboard."""
    parser = argparse.ArgumentParser(description="Task Management Dashboard")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Run in debug mode (default: False)",
    )

    args = parser.parse_args()

    print("=" * 50)
    print("TASK DASHBOARD")
    print("=" * 50)
    print(f"\n🌐 Starting dashboard at http://{args.host}:{args.port}")
    print("\nPress Ctrl+C to stop the server.\n")

    run_dashboard(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
