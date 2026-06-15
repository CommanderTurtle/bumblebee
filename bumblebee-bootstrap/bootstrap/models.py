"""
Data models for bumblebee-bootstrap.

Defines the core dataclasses used throughout the bootstrap pipeline:
- TrackInfo: represents a single music track with all its metadata
- LibraryConfig: global configuration for the bootstrap process
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TrackInfo:
    """Represents a single music track with all associated metadata."""

    source_path: Path
    fingerprint: Optional[str] = None
    acoustid_id: Optional[str] = None
    mb_recording_id: Optional[str] = None
    mb_release_id: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    duration_ms: int = 0
    album_art_url: Optional[str] = None
    has_lyrics: bool = False
    dest_path: Optional[Path] = None


@dataclass
class LibraryConfig:
    """Global configuration for the bootstrap process."""

    source_dir: Path
    output_dir: Path = field(default_factory=lambda: Path("./organized_library"))
    jellyfin_data_dir: Path = field(default_factory=lambda: Path("./jellyfin_data"))
    musicbrainz_enabled: bool = True
    lyrics_enabled: bool = True
    album_art_enabled: bool = True
    copy_mode: bool = True
    workers: int = 4
