"""Bumblebee CLI entry point.

Launches the lyric-based song search TUI and handles command-line arguments
for library path, database path, reindexing, and export directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from bumblebee.db import build_index
from bumblebee.tui import run_tui

console = Console()


def _print_welcome() -> None:
    """Print the welcome banner."""
    text = Text()
    text.append("\U0001f41d ", style="bold yellow")
    text.append("Bumblebee", style="bold yellow")
    text.append(" v1.0.0\n", style="dim")
    text.append("Speak Through Song", style="italic dim")
    console.print(Panel(text, border_style="yellow"))


def _print_indexing_progress(song_count: int, lyric_count: int) -> None:
    """Print indexing completion message."""
    text = Text()
    text.append("\u2713 ", style="bold green")
    text.append("Index built: ", style="white")
    text.append(f"{song_count}", style="bold yellow")
    text.append(" songs, ", style="white")
    text.append(f"{lyric_count}", style="bold yellow")
    text.append(" lyric lines", style="white")
    console.print(text)
    console.print()


def _ensure_db(db_path: Path, library_paths: list[Path], force_reindex: bool = False) -> bool:
    """Ensure the search index exists, building it if needed.

    Args:
        db_path: Path to the SQLite database.
        library_paths: List of library directories to index.
        force_reindex: If True, rebuild the index even if it exists.

    Returns:
        True if the database is ready, False on failure.
    """
    if db_path.exists() and not force_reindex:
        return True

    console.print("[dim]Building search index...[/dim]")
    console.print()

    try:
        song_count, lyric_count = build_index(db_path, library_paths)
        _print_indexing_progress(song_count, lyric_count)
        return True
    except Exception as e:
        console.print(f"[bold red]Error building index: {e}[/bold red]")
        return False


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Bumblebee — Speak Through Song",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bumblebee --library ~/Music
  bumblebee -l ~/Music -d ~/.bumblebee.db --reindex
  uv run -m bumblebee --library ~/Music --export-dir ~/Bumblebee
        """,
    )
    parser.add_argument(
        "--library",
        "-l",
        required=True,
        help="Path to music library (organized MP3s with LRC files)",
    )
    parser.add_argument(
        "--db",
        "-d",
        default=None,
        help="Path to search index (default: library/.bumblebee.db)",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Force rebuild of search index",
    )
    parser.add_argument(
        "--export-dir",
        default="./bumblebee_exports",
        help="Directory for exported snippets",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    args = parser.parse_args()

    # Resolve paths
    library_path = Path(args.library).expanduser().resolve()
    if not library_path.exists():
        console.print(f"[bold red]Library path does not exist: {library_path}[/bold red]")
        sys.exit(1)

    # Determine DB path
    if args.db:
        db_path = Path(args.db).expanduser().resolve()
    else:
        db_path = library_path / ".bumblebee.db"

    export_dir = Path(args.export_dir).expanduser().resolve()

    # Welcome banner
    _print_welcome()
    console.print()

    # Ensure DB exists
    if not _ensure_db(db_path, [library_path], force_reindex=args.reindex):
        sys.exit(1)

    # Launch TUI
    try:
        run_tui(db_path, export_dir)
    except KeyboardInterrupt:
        console.print()
        console.print("[dim]Interrupted. Goodbye! \U0001f41d[/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
