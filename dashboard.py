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
    # Get defaults from environment variables
    default_host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    default_port = int(os.getenv("DASHBOARD_PORT", "5000"))
    default_email_interval = int(os.getenv("DASHBOARD_EMAIL_CHECK_INTERVAL", "1"))

    parser = argparse.ArgumentParser(description="Task Management Dashboard")
    parser.add_argument(
        "--host",
        default=default_host,
        help=f"Host to bind to (default: {default_host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port to bind to (default: {default_port})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Run in debug mode (default: False)",
    )
    parser.add_argument(
        "--email-check-interval",
        type=int,
        default=default_email_interval,
        help=f"Interval in minutes for periodic email checking (default: {default_email_interval})",
    )

    args = parser.parse_args()

    print("=" * 50)
    print("TASK DASHBOARD")
    print("=" * 50)
    print(f"\n🌐 Starting dashboard at http://{args.host}:{args.port}")
    if args.email_check_interval > 0:
        print(f"📧 Periodic email check: every {args.email_check_interval} minutes")
    print("\nPress Ctrl+C to stop the server.\n")

    run_dashboard(
        host=args.host,
        port=args.port,
        debug=args.debug,
        email_check_interval=args.email_check_interval
    )


if __name__ == "__main__":
    main()
