"""
Rich-based console UI for bumblebee-bootstrap.

Provides progress bars, summary tables, and styled output for the bootstrap pipeline.
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)
from rich.table import Table
from rich.text import Text

from bootstrap.models import TrackInfo
from bootstrap.utils import format_duration

# Shared console instance
console = Console()


BANNER = r"""
     _                              _
    | |                            | |
    | |__   _   _  _ __  _   _   __| |  ___  _ __  ___
    | '_ \/ | | || '__|| | | | / _` | / _ \| '__|/ _ \
    | |_) || |_| || |   | |_| || (_| ||  __/| |  |  __/
    |_.__/  \__,_||_|    \__,_| \__,_| \___||_|   \___|

    Bumblebee Bootstrap - Jellyfin Library Setup Tool
"""


def show_header() -> None:
    """Display the Bumblebee Bootstrap ASCII art banner."""
    console.print(Panel.fit(
        Text(BANNER, style="bold yellow"),
        title="🐝 Bumblebee Bootstrap — Jellyfin Library Setup",
        border_style="yellow",
        padding=(1, 2),
    ))


def show_summary(results: list[TrackInfo]) -> None:
    """
    Display a summary table of processed tracks.

    Shows counts for: processed, failed, fingerprinted, enriched, with lyrics, and with album art.
    """
    total = len(results)
    processed = sum(1 for t in results if t.dest_path is not None)
    failed = total - processed
    fingerprinted = sum(1 for t in results if t.fingerprint is not None)
    enriched = sum(1 for t in results if t.mb_recording_id is not None or t.title is not None)
    with_lyrics = sum(1 for t in results if t.has_lyrics)
    with_art = sum(1 for t in results if getattr(t, "album_art_data", None) is not None)

    table = Table(title="Processing Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Count", style="green", justify="right")

    table.add_row("Total tracks", str(total))
    table.add_row("Successfully organized", str(processed))
    table.add_row("Failed", str(failed))
    table.add_row("Fingerprinted", str(fingerprinted))
    table.add_row("Metadata enriched", str(enriched))
    table.add_row("Lyrics downloaded", str(with_lyrics))
    table.add_row("Album art fetched", str(with_art))

    console.print(table)


def show_track_table(tracks: list[TrackInfo], title: str = "Tracks") -> None:
    """
    Display a table of tracks with their metadata and status.

    Args:
        tracks: List of TrackInfo objects to display.
        title: Table title.
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Title", style="cyan", no_wrap=True)
    table.add_column("Artist", style="green")
    table.add_column("Album", style="blue")
    table.add_column("Duration", style="yellow", justify="right")
    table.add_column("Status", style="white")

    for track in tracks:
        status = "[green]OK[/green]" if track.dest_path else "[red]Pending[/red]"
        if track.fingerprint:
            status += " [dim](fp)[/dim]"
        if track.mb_recording_id:
            status += " [dim](mb)[/dim]"

        table.add_row(
            track.title or "Unknown",
            track.artist or "Unknown",
            track.album or "Unknown",
            format_duration(track.duration_ms),
            status,
        )

    console.print(table)


class ProgressManager:
    """
    Rich-based progress manager for the bootstrap pipeline.

    Provides a multi-stage progress display with spinners, bars,
    and per-stage status updates.
    """

    def __init__(self) -> None:
        self._progress: Optional[Progress] = None
        self._overall_task: Optional[int] = None
        self._current_task: Optional[int] = None
        self._success_count = 0
        self._failure_count = 0

    def __enter__(self) -> "ProgressManager":
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            MofNCompleteColumn(),
            console=console,
        )
        self._progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._progress:
            self._progress.__exit__(exc_type, exc_val, exc_tb)

    def start_overall(self, total: int) -> None:
        """Start the overall progress bar."""
        if self._progress:
            self._overall_task = self._progress.add_task(
                "[bold cyan]Overall progress[/bold cyan]",
                total=total,
            )

    def _advance_overall(self) -> None:
        """Advance the overall progress bar by one step."""
        if self._progress and self._overall_task is not None:
            self._progress.advance(self._overall_task, 1)

    def update_fingerprint(self, filename: str) -> None:
        """Update the current stage to fingerprinting."""
        if self._progress:
            desc = f"[yellow]Fingerprinting[/yellow] {filename}"
            if self._current_task is not None:
                self._progress.update(self._current_task, description=desc)
            else:
                self._current_task = self._progress.add_task(desc, total=None)

    def update_metadata(self, filename: str) -> None:
        """Update the current stage to metadata enrichment."""
        if self._progress:
            desc = f"[blue]Enriching metadata[/blue] {filename}"
            if self._current_task is not None:
                self._progress.update(self._current_task, description=desc)
            else:
                self._current_task = self._progress.add_task(desc, total=None)

    def update_album_art(self, filename: str) -> None:
        """Update the current stage to album art fetching."""
        if self._progress:
            desc = f"[magenta]Fetching album art[/magenta] {filename}"
            if self._current_task is not None:
                self._progress.update(self._current_task, description=desc)

    def update_lyrics(self, filename: str) -> None:
        """Update the current stage to lyrics download."""
        if self._progress:
            desc = f"[cyan]Downloading lyrics[/cyan] {filename}"
            if self._current_task is not None:
                self._progress.update(self._current_task, description=desc)

    def mark_success(self) -> None:
        """Mark the current track as successfully processed."""
        self._success_count += 1
        self._advance_overall()

    def mark_failure(self, reason: str = "") -> None:
        """Mark the current track as failed."""
        self._failure_count += 1
        if reason and self._progress:
            console.print(f"[red]Error:[/red] {reason}")
        self._advance_overall()

    @property
    def success_count(self) -> int:
        return self._success_count

    @property
    def failure_count(self) -> int:
        return self._failure_count
