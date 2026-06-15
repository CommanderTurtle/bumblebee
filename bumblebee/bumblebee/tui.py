"""Rich interactive terminal UI for Bumblebee.

Provides a premium CLI experience with:
- SearchScreen: Input prompt for lyric queries + results table
- LyricScreen: Full lyrics display with line numbers, highlight match, range selection
- ActionMenu: Play/Export/Back/New/Quit options

Uses Rich panels, tables, prompts, and layouts for a polished look.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from rich.align import Align
from rich.box import DOUBLE_EDGE, HEAVY, ROUNDED
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from bumblebee.audio import (
    export_snippet,
    format_duration_ms,
    play_snippet,
)
from bumblebee.models import LyricLine, Match, Song
from bumblebee.search import search as search_engine

console = Console()

# ── Styling ───────────────────────────────────────────────────────────

THEME = {
    "header": "bold yellow",
    "subtitle": "dim white",
    "match_star": "bold yellow",
    "line_number": "dim cyan",
    "timestamp": "dim green",
    "highlight": "bold white on dark_goldenrod",
    "border": "yellow",
    "score_high": "bold green",
    "score_mid": "bold yellow",
    "score_low": "bold red",
    "success": "bold green",
    "error": "bold red",
    "prompt": "bold cyan",
    "info": "italic dim",
}


def _header() -> Panel:
    """Create the application header panel."""
    text = Text()
    text.append("\U0001f41d ", style="bold yellow")
    text.append("BUMBLEBEE", style="bold yellow underline")
    text.append(" — Speak Through Song", style=THEME["subtitle"])
    return Panel(
        Align.center(text),
        border_style=THEME["border"],
        box=DOUBLE_EDGE,
        padding=(0, 0),
    )


def _footer() -> Panel:
    """Create the footer panel."""
    text = Text("Search your library by lyrics. Find any line, play or export it.", style=THEME["info"])
    return Panel(text, border_style="dim", box=ROUNDED, padding=(0, 1))


def _score_style(score: float) -> str:
    """Get style for a score value."""
    if score >= 0.85:
        return THEME["score_high"]
    elif score >= 0.6:
        return THEME["score_mid"]
    return THEME["score_low"]


# ── SearchScreen ──────────────────────────────────────────────────────

class SearchScreen:
    """Screen for entering search queries and viewing results."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.last_results: list[Match] = []
        self.last_query: str = ""

    def display(self) -> None:
        """Display the search screen header."""
        console.clear()
        console.print(_header())
        console.print()

    def get_query(self) -> str:
        """Prompt for a search query."""
        console.print()
        query = Prompt.ask(
            Text.assemble(("Enter lyrics to search", THEME["prompt"])),
            choices=["quit", "q"],
            show_choices=False,
        )
        return query.strip()

    def show_results(self, query: str, results: list[Match], elapsed: float) -> None:
        """Display search results in a formatted table."""
        self.last_results = results
        self.last_query = query

        console.print()
        if not results:
            console.print(
                Panel(
                    Text(f'No matches found for "{query}"', style=THEME["error"]),
                    border_style=THEME["error"],
                    box=ROUNDED,
                )
            )
            return

        # Summary line
        count_text = Text()
        count_text.append(f"Found ", style="white")
        count_text.append(str(len(results)), style="bold yellow")
        count_text.append(f" matches in ", style="white")
        count_text.append(f"{elapsed:.2f}s", style="bold cyan")
        count_text.append(":", style="white")
        console.print(count_text)
        console.print()

        # Results table
        table = Table(
            show_header=True,
            header_style="bold yellow",
            border_style="dim",
            box=HEAVY,
            pad_edge=False,
            padding=(0, 1),
        )
        table.add_column("#", style="bold", width=3, justify="right")
        table.add_column("Song", min_width=20, max_width=28)
        table.add_column("Artist", min_width=12, max_width=16)
        table.add_column("Matched Line", min_width=25, max_width=35)
        table.add_column("Score", width=6, justify="right")

        for i, match in enumerate(results, 1):
            score_style = _score_style(match.match_score)
            # Truncate matched line for display
            line_text = match.matched_line.text
            if len(line_text) > 33:
                line_text = line_text[:30] + "..."

            table.add_row(
                str(i),
                match.song.title[:27],
                match.song.artist[:15],
                f'"{line_text}"',
                Text(match.score_percent, style=score_style),
            )

        console.print(table)

    def select_result(self) -> Optional[int]:
        """Prompt user to select a result. Returns 0-based index or None."""
        if not self.last_results:
            return None

        console.print()
        max_choice = len(self.last_results)
        valid_choices = [str(i) for i in range(1, max_choice + 1)] + ["n", "new", "q", "quit"]

        choice = Prompt.ask(
            Text.assemble((f"Select result (1-{max_choice}), or ", "white"),
                         ("'new search'", THEME["prompt"])),
            choices=valid_choices,
            show_choices=False,
        )

        if choice.lower() in ("q", "quit"):
            return -1  # Signal quit
        if choice.lower() in ("n", "new"):
            return None  # Signal new search

        try:
            idx = int(choice) - 1
            if 0 <= idx < max_choice:
                return idx
        except ValueError:
            pass

        return None

    def run(self) -> Optional[Match]:
        """Run the search screen loop. Returns selected Match or None."""
        while True:
            self.display()
            query = self.get_query()

            if query.lower() in ("q", "quit"):
                return None

            if not query:
                continue

            # Perform search
            start = time.time()
            results = search_engine(self.db_path, query)
            elapsed = time.time() - start

            self.show_results(query, results, elapsed)

            if not results:
                if not Confirm.ask("Try another search?", default=True):
                    return None
                continue

            idx = self.select_result()
            if idx == -1:
                return None
            if idx is not None:
                return results[idx]
            # None means new search, loop again


# ── LyricScreen ───────────────────────────────────────────────────────

class LyricScreen:
    """Screen for viewing full lyrics with match highlight and selecting ranges."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def display_lyrics(
        self,
        song: Song,
        lyrics: list[LyricLine],
        match_line: Optional[LyricLine] = None,
        match_idx: Optional[int] = None,
    ) -> None:
        """Display full lyrics with line numbers and match highlight."""
        console.clear()
        console.print(_header())
        console.print()

        # Song info header
        info_text = Text()
        info_text.append(song.title, style="bold white")
        if song.artist:
            info_text.append(f" — {song.artist}", style="bold cyan")
        if song.album:
            info_text.append(f" — {song.album}", style=THEME["subtitle"])
        console.print(
            Panel(info_text, border_style=THEME["border"], box=ROUNDED, padding=(0, 1))
        )
        console.print()

        # Lyrics display
        if not lyrics:
            console.print("  [dim]No lyrics available for this song.[/dim]")
            return

        # Build table
        table = Table(
            show_header=False,
            box=None,
            pad_edge=False,
            padding=(0, 1),
        )
        table.add_column("#", width=4, justify="right", style=THEME["line_number"])
        table.add_column("Time", width=12, style=THEME["timestamp"])
        table.add_column("Lyric", min_width=40)

        for i, line in enumerate(lyrics, 1):
            is_match = match_line is not None and (
                line.timestamp_ms == match_line.timestamp_ms
                and line.text == match_line.text
            )
            is_match = is_match or (match_idx is not None and i - 1 == match_idx)

            line_text = line.text
            if is_match:
                # Highlight the matched line
                display = Text()
                display.append(line_text, style=THEME["highlight"])
                display.append(" ", style="")
                display.append("⭐", style=THEME["match_star"])
                table.add_row(
                    Text(str(i), style=f"bold {THEME['line_number']}"),
                    Text(line.timestamp_str, style=f"bold {THEME['timestamp']}"),
                    display,
                )
            else:
                table.add_row(str(i), line.timestamp_str, line_text)

        console.print(table)

    def select_lines(self, max_line: int) -> Optional[tuple[int, int]]:
        """Prompt user to select a line number or range.

        Returns:
            Tuple of (start_line_0based, end_line_0based) or None.
        """
        console.print()
        valid_single = [str(i) for i in range(1, max_line + 1)]
        valid_choices = valid_single + ["b", "back", "n", "new", "q", "quit"]

        choice = Prompt.ask(
            Text.assemble(
                ("Select line number or range (e.g., 38 or 38-40)", THEME["prompt"])
            ),
            choices=valid_choices,
            show_choices=False,
        )

        if choice.lower() in ("q", "quit"):
            return None  # Signal quit
        if choice.lower() in ("b", "back"):
            return (-1, -1)  # Signal back
        if choice.lower() in ("n", "new"):
            return (-2, -2)  # Signal new search

        # Parse single number or range
        try:
            if "-" in choice:
                parts = choice.split("-", 1)
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                if 1 <= start <= end <= max_line:
                    return (start - 1, end - 1)
            else:
                line_num = int(choice)
                if 1 <= line_num <= max_line:
                    return (line_num - 1, line_num - 1)
        except (ValueError, IndexError):
            pass

        return None

    def run(self, match: Match, all_lyrics: list[LyricLine]) -> Optional[tuple[int, int]]:
        """Run the lyric screen. Returns selected line range (0-based) or None."""
        # Find match index
        match_idx = -1
        for i, line in enumerate(all_lyrics):
            if (
                line.timestamp_ms == match.matched_line.timestamp_ms
                and line.text == match.matched_line.text
            ):
                match_idx = i
                break

        while True:
            self.display_lyrics(match.song, all_lyrics, match_idx=match_idx)
            result = self.select_lines(len(all_lyrics))

            if result is None:
                return None  # Quit
            if result == (-1, -1):
                return None  # Back
            if result == (-2, -2):
                return result  # New search

            return result


# ── ActionMenu ────────────────────────────────────────────────────────

class ActionMenu:
    """Menu for actions on a selected snippet (play/export/back/new/quit)."""

    def __init__(self, db_path: Path, export_dir: Path) -> None:
        self.db_path = db_path
        self.export_dir = export_dir

    def show_snippet_info(
        self, song: Song, start_ms: int, end_ms: int, selected_lyrics: list[LyricLine]
    ) -> None:
        """Display information about the selected snippet."""
        console.print()
        duration = end_ms - start_ms

        info = Text()
        info.append(f"\n  Song: ", style="dim")
        info.append(f"{song.title}", style="bold white")
        if song.artist:
            info.append(f" — {song.artist}", style="bold cyan")
        info.append(f"\n  Snippet: ", style="dim")
        info.append(f"{format_duration_ms(start_ms)}", style="bold green")
        info.append(" → ", style="dim")
        info.append(f"{format_duration_ms(end_ms)}", style="bold green")
        info.append(f" ({duration / 1000:.2f}s)", style="bold yellow")

        if selected_lyrics:
            info.append(f"\n  Lyrics:", style="dim")
            for line in selected_lyrics:
                info.append(f"\n    [{line.timestamp_str}] {line.text}", style="white")

        console.print(
            Panel(info, title="Snippet Preview", border_style=THEME["border"], box=ROUNDED)
        )

    def display_actions(self) -> str:
        """Display action menu and get user choice."""
        console.print()

        actions = Table(show_header=False, box=None, padding=(0, 2))
        actions.add_column("Key", style="bold yellow")
        actions.add_column("Action", style="white")

        actions.add_row("[p]", "Play snippet")
        actions.add_row("[e]", "Export as MP3")
        actions.add_row("[b]", "Back to results")
        actions.add_row("[n]", "New search")
        actions.add_row("[q]", "Quit")

        console.print(
            Panel(actions, title="Actions", border_style=THEME["border"], box=ROUNDED)
        )
        console.print()

        choice = Prompt.ask(
            Text.assemble(("Action", THEME["prompt"])),
            choices=["p", "e", "b", "n", "q", "play", "export", "back", "new", "quit"],
            show_choices=False,
        )
        return choice.lower()

    def do_play(self, song: Song, start_ms: int, end_ms: int) -> None:
        """Play the snippet."""
        console.print(f"\n  [dim]Playing snippet ({(end_ms - start_ms) / 1000:.2f}s)...[/dim]")
        try:
            play_snippet(song.file_path, start_ms, end_ms)
        except Exception as e:
            console.print(f"  [{THEME['error']}]Error playing audio: {e}[/{THEME['error']}]")

    def do_export(
        self,
        song: Song,
        start_ms: int,
        end_ms: int,
        selected_lyrics: list[LyricLine],
    ) -> bool:
        """Export the snippet as MP3. Returns True on success."""
        console.print()

        # Default filename from lyrics
        default_name = "bumblebee_snippet"
        if selected_lyrics:
            # Use first lyric line as filename hint
            safe = "".join(c if c.isalnum() or c == " " else "_" for c in selected_lyrics[0].text)
            default_name = safe.replace(" ", "_").lower()[:40] or "bumblebee_snippet"

        filename = Prompt.ask(
            Text.assemble(("Export filename", THEME["prompt"])),
            default=default_name,
        )
        if not filename.endswith(".mp3"):
            filename += ".mp3"

        bitrate = Prompt.ask(
            Text.assemble(("Bitrate", THEME["prompt"])),
            default="192k",
            choices=["128k", "192k", "256k", "320k"],
        )

        output_path = self.export_dir / filename

        try:
            export_snippet(song.file_path, start_ms, end_ms, output_path, bitrate=bitrate)

            duration = end_ms - start_ms
            success_msg = Text()
            success_msg.append("\u2713 ", style="bold green")
            success_msg.append("Exported: ", style="white")
            success_msg.append(str(output_path), style="bold cyan")
            success_msg.append(f" ({duration / 1000:.2f}s, {bitrate})", style="dim")

            console.print()
            console.print(
                Panel(success_msg, border_style="green", box=ROUNDED)
            )
            return True

        except Exception as e:
            error_msg = Text()
            error_msg.append("\u2717 ", style="bold red")
            error_msg.append(f"Export failed: {e}", style="white")
            console.print(Panel(error_msg, border_style="red", box=ROUNDED))
            return False

    def run(
        self,
        song: Song,
        start_ms: int,
        end_ms: int,
        selected_lyrics: list[LyricLine],
    ) -> Optional[str]:
        """Run the action menu loop.

        Returns:
            "back", "new", None (quit), or loops internally.
        """
        self.show_snippet_info(song, start_ms, end_ms, selected_lyrics)

        while True:
            choice = self.display_actions()

            if choice in ("p", "play"):
                self.do_play(song, start_ms, end_ms)

            elif choice in ("e", "export"):
                self.do_export(song, start_ms, end_ms, selected_lyrics)

            elif choice in ("b", "back"):
                return "back"

            elif choice in ("n", "new"):
                return "new"

            elif choice in ("q", "quit"):
                return None


# ── Main TUI ──────────────────────────────────────────────────────────

def run_tui(db_path: Path, export_dir: Path) -> None:
    """Run the interactive Bumblebee TUI.

    Args:
        db_path: Path to the SQLite search index.
        export_dir: Directory for exported snippets.
    """
    console.clear()
    console.print(_header())
    console.print(_footer())
    console.print()

    search_screen = SearchScreen(db_path)
    lyric_screen = LyricScreen(db_path)
    action_menu = ActionMenu(db_path, export_dir)

    # Ensure export directory exists
    export_dir.mkdir(parents=True, exist_ok=True)

    current_match: Optional[Match] = None

    while True:
        # Search screen
        match = search_screen.run()
        if match is None:
            console.print()
            console.print(
                Panel(
                    Text("Goodbye! \U0001f41d", style="bold yellow"),
                    border_style=THEME["border"],
                    box=ROUNDED,
                )
            )
            break

        current_match = match

        # Get full lyrics for the song
        from bumblebee.db import get_song_lyrics

        all_lyrics = get_song_lyrics(db_path, match.song.id)

        if not all_lyrics:
            console.print(f"\n[{THEME['error']}]No lyrics found for this song.[/{THEME['error']}]")
            continue

        # Lyric screen (line selection)
        while True:
            line_range = lyric_screen.run(match, all_lyrics)

            if line_range is None:
                # Quit
                console.print()
                console.print(
                    Panel(
                        Text("Goodbye! \U0001f41d", style="bold yellow"),
                        border_style=THEME["border"],
                        box=ROUNDED,
                    )
                )
                return

            if line_range == (-2, -2):
                # New search
                break

            start_idx, end_idx = line_range

            # Calculate timestamps
            start_ms = all_lyrics[start_idx].timestamp_ms
            # For end, use the next line after the selection (or add 3s)
            if end_idx + 1 < len(all_lyrics):
                end_ms = all_lyrics[end_idx + 1].timestamp_ms
            else:
                end_ms = start_ms + 3000  # Default 3s for last line

            selected_lyrics = all_lyrics[start_idx:end_idx + 1]

            # Action menu
            action = action_menu.run(match.song, start_ms, end_ms, selected_lyrics)

            if action is None:
                # Quit
                console.print()
                console.print(
                    Panel(
                        Text("Goodbye! \U0001f41d", style="bold yellow"),
                        border_style=THEME["border"],
                        box=ROUNDED,
                    )
                )
                return

            if action == "new":
                break
            # "back" loops to lyric screen again


if __name__ == "__main__":
    # Quick test - just verify the classes can be instantiated
    import tempfile

    print("Testing TUI module...")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / ".test.db"
        export_dir = Path(tmpdir) / "exports"

        # Create a mock DB
        from bumblebee.db import build_index

        lib_path = Path(tmpdir) / "music"
        lib_path.mkdir()

        lrc_file = lib_path / "test.lrc"
        lrc_file.write_text("""[ti:Test]
[ar:Artist]
[00:00.00]Line one
[00:05.00]Line two
[00:10.00]Gonna be okay
[00:15.00]Line four
""")
        mp3_file = lib_path / "test.mp3"
        mp3_file.write_bytes(b"\xff\xf3\x44\xc0")

        build_index(db_path, [lib_path])

        # Test SearchScreen creation
        search_screen = SearchScreen(db_path)
        assert search_screen.db_path == db_path
        print("  SearchScreen: OK")

        # Test LyricScreen creation
        lyric_screen = LyricScreen(db_path)
        assert lyric_screen.db_path == db_path
        print("  LyricScreen: OK")

        # Test ActionMenu creation
        action_menu = ActionMenu(db_path, export_dir)
        assert action_menu.export_dir == export_dir
        print("  ActionMenu: OK")

        # Test _header, _footer
        h = _header()
        assert "BUMBLEBEE" in str(h.render(console))
        print("  _header: OK")

        f = _footer()
        assert "Search" in str(f.render(console))
        print("  _footer: OK")

        # Test score styles
        assert "green" in _score_style(0.9)
        assert "yellow" in _score_style(0.7)
        assert "red" in _score_style(0.4)
        print("  _score_style: OK")

    print("All TUI tests passed!")
