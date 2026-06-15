"""SQLite FTS5 full-text search index for lyrics.

Handles building the search index from a music library and querying it.
Uses FTS5 for fast full-text search with fuzzy fallback via rapidfuzz.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Optional

from bumblebee.models import LyricLine, Match, Song
from bumblebee.lrc_parser import parse_lrc, parse_lrc_text
from rich.console import Console

console = Console()

DB_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS lyrics_fts USING fts5(
    lyric_text, artist, title, album, song_id,
    tokenize='porter'
);
CREATE TABLE IF NOT EXISTS songs (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    title TEXT,
    artist TEXT,
    album TEXT,
    duration_ms INT,
    lrc_path TEXT
);
CREATE TABLE IF NOT EXISTS lyrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id TEXT NOT NULL,
    timestamp_ms INT NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (song_id) REFERENCES songs(id)
);
CREATE INDEX IF NOT EXISTS idx_lyrics_song ON lyrics(song_id);
"""


def _get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Get a SQLite connection with proper settings."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _song_id_from_path(path: Path) -> str:
    """Generate a stable song ID from a file path."""
    return hashlib.sha256(str(path).encode()).hexdigest()[:16]


def _extract_mp3_metadata(path: Path) -> dict:
    """Extract metadata from an MP3 file using mutagen.

    Falls back to filename-based metadata if mutagen is unavailable
    or tags are missing.
    """
    metadata = {
        "title": path.stem,
        "artist": "",
        "album": "",
        "duration_ms": 0,
    }

    try:
        from mutagen.mp3 import MP3

        audio = MP3(path)
        metadata["duration_ms"] = int(audio.info.length * 1000)

        # Extract ID3 tags
        if audio.tags:
            from mutagen.id3 import ID3

            tags = audio.tags
            if "TIT2" in tags:
                metadata["title"] = str(tags["TIT2"])
            if "TPE1" in tags:
                metadata["artist"] = str(tags["TPE1"])
            if "TALB" in tags:
                metadata["album"] = str(tags["TALB"])
    except Exception:
        # Fall back to defaults
        pass

    return metadata


def _find_library_files(library_paths: list[Path]) -> list[tuple[Path, Optional[Path]]]:
    """Scan library directories for MP3 + LRC pairs.

    Returns list of (mp3_path, lrc_path_or_None) tuples.
    """
    results: list[tuple[Path, Optional[Path]]] = []
    seen = set()

    for lib_path in library_paths:
        if not lib_path.exists():
            continue

        for mp3_file in lib_path.rglob("*.mp3"):
            if mp3_file in seen:
                continue
            seen.add(mp3_file)

            # Look for matching .lrc file (same directory, same name)
            lrc_file: Optional[Path] = None
            lrc_file_path = mp3_file.with_suffix(".lrc")
            if lrc_file_path.exists():
                lrc_file = lrc_file_path
            else:
                lrc_file_txt = mp3_file.with_suffix(".lrc.txt")
                if lrc_file_txt.exists():
                    lrc_file = lrc_file_txt

            results.append((mp3_file, lrc_file))

    return results


def build_index(
    db_path: Path,
    library_paths: list[Path],
) -> tuple[int, int]:
    """Build the search index from a music library.

    Scans directories for MP3 + LRC pairs, parses LRC files, and populates
    the FTS5 index along with songs and lyrics tables.

    Args:
        db_path: Path to the SQLite database file.
        library_paths: List of directories to scan for music files.

    Returns:
        Tuple of (number of songs indexed, number of lyric lines indexed).
    """
    conn = _get_db_connection(db_path)

    try:
        # Create schema
        conn.executescript(DB_SCHEMA)

        # Clear existing data for rebuild
        conn.execute("DELETE FROM lyrics_fts")
        conn.execute("DELETE FROM lyrics")
        conn.execute("DELETE FROM songs")
        conn.commit()

        # Find all MP3 + LRC pairs
        files = _find_library_files(library_paths)
        song_count = 0
        lyric_count = 0

        for mp3_path, lrc_path in files:
            song_id = _song_id_from_path(mp3_path)

            # Extract metadata
            meta = _extract_mp3_metadata(mp3_path)

            # Parse LRC if available
            lyrics: list[LyricLine] = []
            lrc_meta = None
            if lrc_path and lrc_path.exists():
                try:
                    lrc_text = lrc_path.read_text(encoding="utf-8")
                    lrc_meta, lyrics = parse_lrc_text(lrc_text)
                except Exception:
                    lyrics = []

            # Override metadata from LRC if available
            title = meta["title"]
            artist = meta["artist"]
            album = meta["album"]

            if lrc_meta:
                if "ti" in lrc_meta and lrc_meta["ti"]:
                    title = lrc_meta["ti"]
                if "ar" in lrc_meta and lrc_meta["ar"]:
                    artist = lrc_meta["ar"]
                if "al" in lrc_meta and lrc_meta["al"]:
                    album = lrc_meta["al"]

            # Insert into songs table
            conn.execute(
                """INSERT INTO songs (id, path, title, artist, album, duration_ms, lrc_path)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    song_id,
                    str(mp3_path),
                    title,
                    artist,
                    album,
                    meta["duration_ms"],
                    str(lrc_path) if lrc_path else None,
                ),
            )

            # Insert lyrics into both tables
            for line in lyrics:
                conn.execute(
                    """INSERT INTO lyrics (song_id, timestamp_ms, text)
                       VALUES (?, ?, ?)""",
                    (song_id, line.timestamp_ms, line.text),
                )

                # Insert into FTS index
                conn.execute(
                    """INSERT INTO lyrics_fts (lyric_text, artist, title, album, song_id)
                       VALUES (?, ?, ?, ?, ?)""",
                    (line.text, artist, title, album, song_id),
                )

                lyric_count += 1

            song_count += 1

        conn.commit()

    finally:
        conn.close()

    return song_count, lyric_count


def _row_to_song(row: sqlite3.Row) -> Song:
    """Convert a database row to a Song object."""
    return Song(
        id=row["id"],
        file_path=Path(row["path"]),
        title=row["title"] or "",
        artist=row["artist"] or "",
        album=row["album"] or "",
        duration_ms=row["duration_ms"] or 0,
        lrc_path=Path(row["lrc_path"]) if row["lrc_path"] else None,
    )


def _get_context_lines(
    all_lines: list[LyricLine], match_idx: int, window: int = 2
) -> tuple[list[LyricLine], list[LyricLine]]:
    """Get context lines before and after a match index."""
    before = []
    after = []

    for i in range(max(0, match_idx - window), match_idx):
        before.append(all_lines[i])

    for i in range(match_idx + 1, min(len(all_lines), match_idx + window + 1)):
        after.append(all_lines[i])

    return before, after


def search(
    db_path: Path,
    query: str,
    limit: int = 20,
) -> list[Match]:
    """Search lyrics using FTS5 with fuzzy fallback.

    Strategy:
        1. Try FTS5 MATCH query for fast full-text search
        2. If FTS returns fewer than 5 results, fall back to rapidfuzz
        3. If still fewer than 3 results, try word-by-word matching

    Args:
        db_path: Path to the SQLite database.
        query: Search query string.
        limit: Maximum number of results to return.

    Returns:
        List of Match objects sorted by score descending.
    """
    import time

    from rapidfuzz import fuzz

    start_time = time.time()
    conn = _get_db_connection(db_path)
    matches: list[Match] = []

    try:
        # --- Strategy 1: FTS5 MATCH ---
        try:
            cursor = conn.execute(
                """SELECT song_id, lyric_text, rank
                   FROM lyrics_fts
                   WHERE lyric_text MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit * 2),
            )
            fts_rows = cursor.fetchall()
        except sqlite3.Error as e:
            console.print(f"[yellow]Warning:[/yellow] FTS search error: {e}")
            fts_rows = []

        # Build matches from FTS results
        seen_song_lines: set[tuple[str, str]] = set()
        for row in fts_rows:
            song_id = row["song_id"]
            lyric_text = row["lyric_text"]
            rank = row["rank"]

            key = (song_id, lyric_text)
            if key in seen_song_lines:
                continue
            seen_song_lines.add(key)

            # Get song info
            song_row = conn.execute(
                "SELECT * FROM songs WHERE id = ?", (song_id,)
            ).fetchone()
            if not song_row:
                continue

            song = _row_to_song(song_row)

            # Find the matching lyric line
            lyric_rows = conn.execute(
                """SELECT * FROM lyrics WHERE song_id = ? AND text = ?
                   ORDER BY ABS(length(text) - ?)
                   LIMIT 1""",
                (song_id, lyric_text, len(lyric_text)),
            ).fetchall()

            if not lyric_rows:
                continue

            lyric_row = lyric_rows[0]
            matched_line = LyricLine(
                timestamp_ms=lyric_row["timestamp_ms"], text=lyric_row["text"]
            )

            # Get all lyrics for context
            all_lyrics = get_song_lyrics(db_path, song_id, conn)
            match_idx = -1
            for i, line in enumerate(all_lyrics):
                if (
                    line.timestamp_ms == matched_line.timestamp_ms
                    and line.text == matched_line.text
                ):
                    match_idx = i
                    break

            if match_idx < 0:
                match_idx = 0

            before, after = _get_context_lines(all_lyrics, match_idx)

            # Score: FTS rank is negative (lower is better), normalize to 0-1
            # rank comes as negative values, smallest magnitude = best
            score = min(1.0, max(0.5, 1.0 - abs(rank) * 0.1))

            matches.append(
                Match(
                    song=song,
                    matched_line=matched_line,
                    context_before=before,
                    context_after=after,
                    match_score=score,
                    match_type="fts",
                )
            )

        # --- Strategy 2: Fuzzy fallback ---
        if len(matches) < 5:
            # Get all lyrics not already matched
            all_lyric_rows = conn.execute(
                """SELECT l.*, s.path, s.title, s.artist, s.album,
                          s.duration_ms, s.lrc_path
                   FROM lyrics l
                   JOIN songs s ON l.song_id = s.id"""
            ).fetchall()

            query_lower = query.lower()

            for row in all_lyric_rows:
                song_id = row["song_id"]
                lyric_text = row["text"]

                key = (song_id, lyric_text)
                if key in seen_song_lines:
                    continue

                score = fuzz.partial_ratio(query_lower, lyric_text.lower())

                if score >= 60:
                    seen_song_lines.add(key)

                    song = _row_to_song(row)
                    matched_line = LyricLine(
                        timestamp_ms=row["timestamp_ms"], text=lyric_text
                    )

                    all_lyrics = get_song_lyrics(db_path, song_id, conn)
                    match_idx = -1
                    for i, line in enumerate(all_lyrics):
                        if (
                            line.timestamp_ms == matched_line.timestamp_ms
                            and line.text == matched_line.text
                        ):
                            match_idx = i
                            break
                    if match_idx < 0:
                        match_idx = 0

                    before, after = _get_context_lines(all_lyrics, match_idx)

                    matches.append(
                        Match(
                            song=song,
                            matched_line=matched_line,
                            context_before=before,
                            context_after=after,
                            match_score=score / 100.0,
                            match_type="fuzzy",
                        )
                    )

        # --- Strategy 3: Word-by-word fallback ---
        if len(matches) < 3:
            words = [w for w in query_lower.split() if len(w) > 2]

            if words:
                all_lyric_rows = conn.execute(
                    """SELECT l.*, s.path, s.title, s.artist, s.album,
                              s.duration_ms, s.lrc_path
                       FROM lyrics l
                       JOIN songs s ON l.song_id = s.id"""
                ).fetchall()

                for row in all_lyric_rows:
                    song_id = row["song_id"]
                    lyric_text = row["text"]

                    key = (song_id, lyric_text)
                    if key in seen_song_lines:
                        continue

                    lyric_lower = lyric_text.lower()
                    matched_words = sum(1 for w in words if w in lyric_lower)
                    coverage = matched_words / len(words) if words else 0

                    if coverage > 0:
                        seen_song_lines.add(key)

                        song = _row_to_song(row)
                        matched_line = LyricLine(
                            timestamp_ms=row["timestamp_ms"], text=lyric_text
                        )

                        all_lyrics = get_song_lyrics(db_path, song_id, conn)
                        match_idx = -1
                        for i, line in enumerate(all_lyrics):
                            if (
                                line.timestamp_ms == matched_line.timestamp_ms
                                and line.text == matched_line.text
                            ):
                                match_idx = i
                                break
                        if match_idx < 0:
                            match_idx = 0

                        before, after = _get_context_lines(all_lyrics, match_idx)

                        matches.append(
                            Match(
                                song=song,
                                matched_line=matched_line,
                                context_before=before,
                                context_after=after,
                                match_score=coverage * 0.5,  # Lower base score for word matches
                                match_type="word",
                            )
                        )

        # Sort by score descending
        matches.sort(key=lambda m: m.match_score, reverse=True)

    finally:
        conn.close()

    elapsed = time.time() - start_time
    # Attach elapsed time as a module-level attribute for CLI/TUI use
    search._last_elapsed = elapsed  # type: ignore[attr-defined]

    return matches[:limit]


def get_song_lyrics(
    db_path: Path, song_id: str, conn: Optional[sqlite3.Connection] = None
) -> list[LyricLine]:
    """Get all lyric lines for a song. Accepts optional connection for reuse.

    Args:
        db_path: Path to the SQLite database.
        song_id: The song ID.
        conn: Optional existing connection to reuse.

    Returns:
        List of LyricLine objects sorted by timestamp.
    """
    should_close = conn is None
    if conn is None:
        conn = _get_db_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT timestamp_ms, text FROM lyrics
               WHERE song_id = ?
               ORDER BY timestamp_ms""",
            (song_id,),
        ).fetchall()

        return [LyricLine(timestamp_ms=r["timestamp_ms"], text=r["text"]) for r in rows]
    finally:
        if should_close:
            conn.close()


def get_song(db_path: Path, song_id: str) -> Optional[Song]:
    """Get a song by ID.

    Args:
        db_path: Path to the SQLite database.
        song_id: The song ID.

    Returns:
        Song object, or None if not found.
    """
    conn = _get_db_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM songs WHERE id = ?", (song_id,)
        ).fetchone()

        if not row:
            return None

        return _row_to_song(row)
    finally:
        conn.close()


if __name__ == "__main__":
    # Quick sanity test
    import tempfile

    print("Testing db module...")

    # Create a temp library with fake MP3s and LRCs
    with tempfile.TemporaryDirectory() as tmpdir:
        lib_path = Path(tmpdir)

        # Create a fake LRC file
        lrc_file = lib_path / "test_song.lrc"
        lrc_file.write_text("""[ti:Test Song]
[ar:Test Artist]
[al:Test Album]
[00:00.00]Line one
[00:05.00]Line two here
[00:10.00]Gonna be okay
[00:15.00]Line four
[00:20.00]Line five
""")

        # Create a fake MP3 (empty file with .mp3 extension)
        mp3_file = lib_path / "test_song.mp3"
        mp3_file.write_bytes(b"\xff\xf3\x44\xc0")  # Minimal MP3 header

        # Build index
        db_file = lib_path / ".bumblebee.db"
        song_count, lyric_count = build_index(db_file, [lib_path])

        print(f"  Indexed {song_count} songs, {lyric_count} lyric lines")
        assert song_count == 1, f"Expected 1 song, got {song_count}"
        assert lyric_count == 5, f"Expected 5 lines, got {lyric_count}"

        # Test get song
        song = get_song(db_file, _song_id_from_path(mp3_file))
        assert song is not None
        assert song.title == "Test Song"
        assert song.artist == "Test Artist"
        print(f"  get_song: OK ({song.display_name})")

        # Test get lyrics
        lyrics = get_song_lyrics(db_file, song.id)
        assert len(lyrics) == 5
        assert lyrics[2].text == "Gonna be okay"
        print("  get_song_lyrics: OK")

        # Test search (FTS)
        results = search(db_file, "Gonna be okay")
        assert len(results) > 0, "Expected at least one search result"
        assert results[0].matched_line.text == "Gonna be okay"
        print(f"  search FTS: OK ({len(results)} results)")

        # Test search (fuzzy)
        results = search(db_file, "gonna be oka")
        assert len(results) > 0, "Expected fuzzy match"
        print(f"  search fuzzy: OK ({len(results)} results)")

        # Test search (word fallback)
        results = search(db_file, "okay gonna")
        assert len(results) > 0
        print(f"  search word fallback: OK ({len(results)} results)")

    print("All DB tests passed!")
