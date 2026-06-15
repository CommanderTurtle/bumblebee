"""
Library organization module for bumblebee-bootstrap.

Handles directory restructuring and file operations to produce a clean,
Jellyfin-compatible library structure: Artist/Album/01 - Title.mp3
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from bootstrap.console import console
from bootstrap.models import LibraryConfig, TrackInfo
from bootstrap.utils import safe_makedirs, sanitize_filename


def compute_destination(track: TrackInfo, root: Path) -> Path:
    """
    Compute the destination path for a track in the organized library.

    The path structure follows Jellyfin's expected format:
        root / Artist / Album / 01 - Title.mp3

    For compilation albums (no album_artist), uses "Various Artists".

    Args:
        track: The TrackInfo with metadata to derive the path from.
        root: The root directory of the organized library.

    Returns:
        The computed destination Path.
    """
    # Determine artist folder
    artist = track.album_artist or track.artist or "Unknown Artist"
    artist_folder = sanitize_filename(artist)

    # Determine album folder
    album = track.album or "Unknown Album"
    album_folder = sanitize_filename(album)

    # Determine filename
    track_num = track.track_number or 0
    title = track.title or track.source_path.stem or "Unknown Track"

    if track_num > 0:
        filename = f"{track_num:02d} - {sanitize_filename(title)}.mp3"
    else:
        filename = f"{sanitize_filename(title)}.mp3"

    return root / artist_folder / album_folder / filename


def organize_tracks(
    tracks: list[TrackInfo],
    config: LibraryConfig,
) -> list[TrackInfo]:
    """
    Copy or move files to the organized library structure.

    For each track, computes the destination path and either copies or moves
    the file depending on the copy_mode setting. Creates necessary directories
    and avoids overwriting existing files by appending a counter.

    Args:
        tracks: List of TrackInfo objects to organize.
        config: LibraryConfig controlling copy/move behavior and output paths.

    Returns:
        The updated list of TrackInfo objects with dest_path set.
    """
    for track in tracks:
        try:
            dest = compute_destination(track, config.output_dir)

            # Ensure the destination directory exists
            safe_makedirs(dest.parent)

            # Avoid overwriting existing files
            dest = _resolve_unique_path(dest)

            if config.copy_mode:
                shutil.copy2(track.source_path, dest)
            else:
                shutil.move(str(track.source_path), str(dest))

            track.dest_path = dest

        except Exception as exc:
            console.print(
                f"[yellow]Warning:[/yellow] Could not organize {track.source_path.name}: {exc}"
            )

    return tracks


def _resolve_unique_path(path: Path) -> Path:
    """
    Resolve a unique file path by appending a counter if the file already exists.

    Args:
        path: The desired file path.

    Returns:
        A unique Path that does not already exist.
    """
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1

    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
