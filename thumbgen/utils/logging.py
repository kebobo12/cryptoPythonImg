"""
Lightweight, colorized logging utilities for thumbgen.

These helper functions standardize all console output from the CLI and
internal modules. They produce clean, readable messages without relying
on external logging frameworks.
"""

from __future__ import annotations

import sys
from typing import Any


# ------------------------------------------------------------
# ANSI color codes (Windows 10+ & modern terminals support this)
# ------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def info(message: str) -> None:
    """Print a neutral informational message."""
    print(f"{CYAN}{message}{RESET}")


def ok(message: str) -> None:
    """Print a green success message."""
    print(f"{GREEN}[OK]{RESET} {message}")


def warn(message: str) -> None:
    """Print a yellow warning message."""
    print(f"{YELLOW}[WARN]{RESET} {message}", file=sys.stderr)


def error(message: str) -> None:
    """Print a red error message."""
    print(f"{RED}[ERROR]{RESET} {message}", file=sys.stderr)


def heading(title: str) -> None:
    """Print a bold section heading."""
    print(f"{BOLD}{title}{RESET}")
