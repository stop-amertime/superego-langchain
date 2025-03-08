#!/usr/bin/env python
"""
Run the CLI test harness for the Superego-LangChain agents.

Usage:
  python run_cli.py autogen [--system-prompt PROMPT]
  python run_cli.py superego [--constitution CONSTITUTION]
"""
import sys
import os

# Add the parent directory to the path so we can import the app module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.cli import main

if __name__ == "__main__":
    main()
