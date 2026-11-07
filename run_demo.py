#!/usr/bin/env python3
"""Launcher script for the Argumentation Engine Demonstration.

Supports:
  1. Interactive Web Dashboard (HTML5 GUI in browser):
       python run_demo.py --web
  2. Complete CLI walkthrough:
       python run_demo.py --cli
"""

import argparse
import os
import sys
import webbrowser
from pathlib import Path


def launch_web():
    html_path = Path(__file__).parent.resolve() / "demo.html"
    if not html_path.exists():
        print(f"Error: Could not locate demo.html at {html_path}")
        sys.exit(1)
    url = html_path.as_uri()
    print("=" * 70)
    print("LAUNCHING INTERACTIVE ARGUMENTATION WEB DASHBOARD")
    print("=" * 70)
    print(f"Opening in default browser: {url}")
    webbrowser.open(url)


def launch_cli():
    import main
    main.main()


def main_launcher():
    parser = argparse.ArgumentParser(
        description="Launch Argumentation Framework Demonstration (Web or CLI)"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--web",
        action="store_true",
        help="Open interactive web dashboard in default browser (default).",
    )
    group.add_argument(
        "--cli",
        action="store_true",
        help="Run terminal-based complete demonstration.",
    )
    args, unknown = parser.parse_known_args()

    if args.cli:
        launch_cli()
    else:
        launch_web()


if __name__ == "__main__":
    main_launcher()

