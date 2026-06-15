"""Core data models for Bumblebee."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class LyricLine:
    """A single lyric line with its timestamp."""

    timestamp_ms: int  # e.g. 12340 for 00:12.340
    text: str

    @property
    def timestamp_str(self) -> str:
        """Format timestamp as mm:ss.cc (centiseconds)."""
        minutes = self.timestamp_ms // 60000
        seconds = (self.timestamp_ms % 60000) // 1000
        centis = (self.timestamp_ms % 1000) // 10
        return f"{minutes:02d}:{seconds:02d}.{centis:02d}"

    def __repr__(self) -> str:
        return f"[{self.timestamp_str}] {self.text}"

    def __hash__(self) -> int:
        return hash((self.timestamp_ms, self.text))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LyricLine):
            return NotImplemented
        return self.timestamp_ms == other.timestamp_ms and self.text == other.text


@dataclass
class Song:
    """A song in the library."""

    id: str  # sha256 of file path (truncated to 16 chars)
    file_path: Path
    title: str
    artist: str
    album: str
    duration_ms: int
    lrc_path: Optional[Path]

    @property
    def display_name(self) -> str:
        """Human-readable song identifier."""
        parts = [self.title]
        if self.artist:
            parts.append(f" — {self.artist}")
        return "".join(parts)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Song):
            return NotImplemented
        return self.id == other.id


@dataclass
class Match:
    """A search match result."""

    song: Song
    matched_line: LyricLine
    context_before: list[LyricLine] = field(default_factory=list)  # 2 lines before
    context_after: list[LyricLine] = field(default_factory=list)  # 2 lines after
    match_score: float = 0.0  # 0.0 - 1.0
    match_type: str = ""  # "fts", "fuzzy", "word"

    @property
    def score_percent(self) -> str:
        """Score as a percentage string."""
        return f"{self.match_score * 100:.0f}%"

    def context_lines(self) -> list[LyricLine]:
        """All context lines including the match."""
        return self.context_before + [self.matched_line] + self.context_after
