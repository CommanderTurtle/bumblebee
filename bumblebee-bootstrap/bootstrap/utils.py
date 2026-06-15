"""
Utility functions for bumblebee-bootstrap.

Provides common helpers for file discovery, path manipulation,
and formatting used across the bootstrap pipeline.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from rich.console import Console
console = Console()


def discover_mp3s(root: Path) -> list[Path]:
    """
    Recursively discover all MP3 files under the given root directory.

    Args:
        root: The root directory to search.

    Returns:
        A list of Path objects for all found MP3 files.
    """
    mp3_files: list[Path] = []
    if not root.exists() or not root.is_dir():
        return mp3_files

    for path in root.rglob("*.mp3"):
        if path.is_file():
            mp3_files.append(path.resolve())

    # Also check for .MP3 (case-insensitive)
    for path in root.rglob("*.MP3"):
        if path.is_file() and path not in mp3_files:
            mp3_files.append(path.resolve())

    return sorted(mp3_files)


def safe_makedirs(path: Path) -> None:
    """
    Create a directory and all its parents, with error handling.

    Args:
        path: The directory path to create.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        console.print(f"[yellow]Warning:[/yellow] Could not create directory {path}: {exc}")


def format_duration(ms: int) -> str:
    """
    Format a duration in milliseconds as MM:SS.

    Args:
        ms: Duration in milliseconds.

    Returns:
        A string in the format "M:SS" (e.g., "3:42" for 222000ms).
    """
    if ms <= 0:
        return "0:00"
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def sanitize_filename(name: str) -> str:
    r"""
    Remove or replace characters that are illegal in file paths.

    Replaces: ``/ \ ? % * : | " < > .``

    Args:
        name: The original filename or directory name.

    Returns:
        A sanitized string safe for use as a filename.
    """
    if not name:
        return "Unknown"

    illegal_chars = '\\/?%*:|"<>.'
    sanitized = ""
    for char in name:
        if char in illegal_chars:
            sanitized += "_"
        else:
            sanitized += char

    # Strip leading/trailing whitespace and dots
    sanitized = sanitized.strip(" .")

    # Collapse multiple underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")

    return sanitized or "Unknown"
