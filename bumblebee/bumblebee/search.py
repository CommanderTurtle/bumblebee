"""Multi-strategy lyric search engine.

Provides a unified search interface that combines:
1. FTS5 full-text search (fast, exact)
2. RapidFuzz fuzzy matching (handles typos)
3. Word-by-word fallback (broad coverage)

Also provides context extraction utilities for building Match objects
with surrounding lyric lines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rapidfuzz import fuzz

from bumblebee.db import search as db_search, get_song_lyrics
from bumblebee.models import LyricLine, Match, Song


def get_context(
    lines: list[LyricLine],
    match_idx: int,
    window: int = 2,
) -> tuple[list[LyricLine], LyricLine, list[LyricLine]]:
    """Get context lines around a matched lyric index.

    Args:
        lines: Complete list of lyric lines for a song.
        match_idx: Index of the matched line.
        window: Number of lines before/after to include.

    Returns:
        Tuple of (context_before, matched_line, context_after).

    Examples:
        >>> lines = [LyricLine(0, "A"), LyricLine(1000, "B"),
        ...          LyricLine(2000, "C"), LyricLine(3000, "D"),
        ...          LyricLine(4000, "E")]
        >>> before, match, after = get_context(lines, 2, window=1)
        >>> [l.text for l in before]
        ['B']
        >>> match.text
        'C'
        >>> [l.text for l in after]
        ['D']
    """
    if not lines:
        return [], LyricLine(0, ""), []

    if match_idx < 0 or match_idx >= len(lines):
        raise IndexError(f"match_idx {match_idx} out of range for {len(lines)} lines")

    matched_line = lines[match_idx]

    start_idx = max(0, match_idx - window)
    end_idx = min(len(lines), match_idx + window + 1)

    context_before = lines[start_idx:match_idx]
    context_after = lines[match_idx + 1:end_idx]

    return context_before, matched_line, context_after


def search(
    db_path: Path,
    query: str,
    limit: int = 20,
) -> list[Match]:
    """Search lyrics using multi-strategy approach.

    Strategies (in order):
        1. **FTS Search**: Use SQLite FTS5 MATCH for fast full-text search.
        2. **Fuzzy Fallback**: If FTS returns fewer than 5 results, scan all
           lyrics with rapidfuzz.partial_ratio. Threshold: 60.
        3. **Word-by-word Fallback**: If still fewer than 3 results, split
           query into words and find lines matching ANY word.

    Results are sorted by match_score descending, then by FTS rank.

    Args:
        db_path: Path to the SQLite database.
        query: Search query string (lyrics to search for).
        limit: Maximum number of results.

    Returns:
        List of Match objects with context.

    Examples:
        >>> results = search(Path(".bumblebee.db"), "gonna be okay")
        >>> len(results) > 0
        True
    """
    # Delegate to db.search which handles all three strategies internally
    return db_search(db_path, query, limit)


def fuzzy_score(query: str, text: str) -> float:
    """Compute a fuzzy match score between query and text.

    Uses rapidfuzz\'s partial_ratio for substring matching.

    Args:
        query: The search query.
        text: The text to compare against.

    Returns:
        Score between 0.0 and 1.0.

    Examples:
        >>> fuzzy_score("hello", "hello world")
        1.0
        >>> fuzzy_score("helo", "hello")
        0.87
    """
    return fuzz.partial_ratio(query.lower(), text.lower()) / 100.0


def word_coverage_score(query: str, text: str) -> float:
    """Compute word coverage score (fraction of query words found in text).

    Args:
        query: The search query.
        text: The text to compare against.

    Returns:
        Score between 0.0 and 1.0.

    Examples:
        >>> word_coverage_score("hello world", "hello there world")
        1.0
        >>> word_coverage_score("hello world", "hello")
        0.5
    """
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    if not query_words:
        return 0.0

    text_lower = text.lower()
    matched = sum(1 for w in query_words if w in text_lower)
    return matched / len(query_words)


def find_line_index(lines: list[LyricLine], target: LyricLine) -> int:
    """Find the index of a lyric line in a list.

    Args:
        lines: List of LyricLine objects.
        target: The line to find.

    Returns:
        Index of the line, or -1 if not found.
    """
    for i, line in enumerate(lines):
        if line.timestamp_ms == target.timestamp_ms and line.text == target.text:
            return i
    return -1


def create_match(
    song: Song,
    matched_line: LyricLine,
    all_lyrics: list[LyricLine],
    match_score: float,
    match_type: str,
    window: int = 2,
) -> Match:
    """Create a Match object with context from lyrics.

    Args:
        song: The Song object.
        matched_line: The matched LyricLine.
        all_lyrics: Complete list of lyrics for the song.
        match_score: Score between 0.0 and 1.0.
        match_type: Type of match ("fts", "fuzzy", "word").
        window: Number of context lines.

    Returns:
        A Match object with context.
    """
    match_idx = find_line_index(all_lyrics, matched_line)
    if match_idx < 0:
        match_idx = 0

    before, matched, after = get_context(all_lyrics, match_idx, window=window)

    return Match(
        song=song,
        matched_line=matched,
        context_before=before,
        context_after=after,
        match_score=match_score,
        match_type=match_type,
    )


if __name__ == "__main__":
    import tempfile

    print("Testing search module...")

    # Test context extraction
    lines = [
        LyricLine(0, "Line one"),
        LyricLine(5000, "Line two"),
        LyricLine(10000, "Line three"),
        LyricLine(15000, "Line four"),
        LyricLine(20000, "Line five"),
    ]

    before, match, after = get_context(lines, 2, window=2)
    assert [l.text for l in before] == ["Line one", "Line two"]
    assert match.text == "Line three"
    assert [l.text for l in after] == ["Line four", "Line five"]
    print("  get_context (full window): OK")

    before, match, after = get_context(lines, 0, window=2)
    assert before == []
    assert match.text == "Line one"
    assert [l.text for l in after] == ["Line two", "Line three"]
    print("  get_context (start edge): OK")

    before, match, after = get_context(lines, 4, window=2)
    assert [l.text for l in before] == ["Line three", "Line four"]
    assert match.text == "Line five"
    assert after == []
    print("  get_context (end edge): OK")

    # Test fuzzy_score
    assert fuzzy_score("hello", "hello world") == 1.0
    assert fuzzy_score("helo", "hello") >= 0.8
    print("  fuzzy_score: OK")

    # Test word_coverage_score
    assert word_coverage_score("hello world", "hello there world") == 1.0
    assert word_coverage_score("hello world", "hello") == 0.5
    assert word_coverage_score("a b", "c d") == 0.0
    print("  word_coverage_score: OK")

    # Test find_line_index
    assert find_line_index(lines, LyricLine(10000, "Line three")) == 2
    assert find_line_index(lines, LyricLine(999, "No")) == -1
    print("  find_line_index: OK")

    # Test create_match
    song = Song(
        id="test123",
        file_path=Path("/test.mp3"),
        title="Test",
        artist="Artist",
        album="Album",
        duration_ms=30000,
        lrc_path=None,
    )
    match = create_match(song, LyricLine(10000, "Line three"), lines, 0.95, "fts")
    assert match.song == song
    assert match.matched_line.text == "Line three"
    assert match.match_score == 0.95
    assert match.match_type == "fts"
    assert len(match.context_before) == 2
    assert len(match.context_after) == 2
    print("  create_match: OK")

    # Integration test with real DB
    with tempfile.TemporaryDirectory() as tmpdir:
        lib_path = Path(tmpdir)
        lrc_file = lib_path / "test_song.lrc"
        lrc_file.write_text("""[ti:My Song]
[ar:My Artist]
[00:00.00]First line of the song
[00:05.00]Second line is here
[00:10.00]Gonna be okay tonight
[00:15.00]Another line follows
[00:20.00]Final line ends it
""")
        mp3_file = lib_path / "test_song.mp3"
        mp3_file.write_bytes(b"\xff\xf3\x44\xc0")

        db_path = lib_path / ".test.db"
        from bumblebee.db import build_index

        build_index(db_path, [lib_path])

        # Test search
        results = search(db_path, "gonna be okay")
        assert len(results) >= 1, f"Expected >= 1 result, got {len(results)}"
        assert results[0].matched_line.text == "Gonna be okay tonight"
        print(f"  search integration: OK ({len(results)} results)")

        # Test fuzzy search (typo)
        results = search(db_path, "gonna be okaay")
        assert len(results) >= 1, f"Expected fuzzy match, got {len(results)}"
        print(f"  search fuzzy: OK ({len(results)} results)")

        # Test word search
        results = search(db_path, "okay tonight gonna")
        assert len(results) >= 1
        print(f"  search word: OK ({len(results)} results)")

    print("All search tests passed!")
