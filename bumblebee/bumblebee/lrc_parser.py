"""LRC (synced lyrics) file parser.

Supports standard LRC format:
  [mm:ss.xx] Lyric text
  [mm:ss.xxx] Lyric text (3-digit centiseconds)
  [mm:ss] Lyric text (no centiseconds)
  [ar:Artist], [ti:Title], [al:Album] metadata tags
  [offset:+500] millisecond adjustment
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from bumblebee.models import LyricLine


# Regex patterns for LRC parsing
# Matches [mm:ss.xx] or [mm:ss.xxx] or [mm:ss]
TIMESTAMP_RE = re.compile(
    r"\[(\d{2}):(\d{2})\.?(\d{0,3})?\]"
)
# Metadata tags: [ar:Artist], [ti:Title], etc.
# Only matches known LRC metadata keys, not timestamps.
METADATA_RE = re.compile(r"\[(ar|ti|al|au|by|offset|re|ve|tool|length):(.+)\]")
# Offset tag: [offset:+500] or [offset:-500]
OFFSET_RE = re.compile(r"\[offset:([+-]?\d+)\]")


def timestamp_to_ms(ts: str) -> int:
    """Convert LRC timestamp string to milliseconds.

    Args:
        ts: Timestamp string like "[01:23.45]", "[01:23.450]", or "[01:23]"

    Returns:
        Milliseconds (e.g., 83450 for "[01:23.45]")

    Raises:
        ValueError: If the timestamp format is invalid.

    Examples:
        >>> timestamp_to_ms("[01:23.45]")
        83450
        >>> timestamp_to_ms("[00:12.340]")
        12340
        >>> timestamp_to_ms("[01:23]")
        83000
    """
    ts = ts.strip()
    # Remove surrounding brackets if present
    if ts.startswith("[") and ts.endswith("]"):
        ts = ts[1:-1]

    # Handle mm:ss.xx or mm:ss.xxx or mm:ss
    if "." in ts:
        time_part, centis_part = ts.split(".", 1)
        # Pad centis to 3 digits (milliseconds)
        centis_part = centis_part.ljust(3, "0")[:3]
        centis = int(centis_part)
    else:
        time_part = ts
        centis = 0

    minutes_str, seconds_str = time_part.split(":")
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    return minutes * 60000 + seconds * 1000 + centis


def ms_to_timestamp(ms: int) -> str:
    """Convert milliseconds to LRC timestamp string.

    Args:
        ms: Milliseconds (e.g., 83450)

    Returns:
        Timestamp string like "01:23.45"

    Examples:
        >>> ms_to_timestamp(83450)
        '01:23.45'
        >>> ms_to_timestamp(12340)
        '00:12.34'
    """
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    centis = (ms % 1000) // 10
    return f"{minutes:02d}:{seconds:02d}.{centis:02d}"


def parse_lrc_text(text: str) -> tuple[Optional[dict], list[LyricLine]]:
    """Parse LRC file text content.

    Args:
        text: Raw LRC file content.

    Returns:
        Tuple of (metadata dict or None, list of LyricLine objects).

    Examples:
        >>> meta, lines = parse_lrc_text("[ti:My Song]\n[00:12.34]Hello world")
        >>> meta["title"]
        'My Song'
        >>> len(lines)
        1
    """
    metadata: dict[str, str] = {}
    raw_lines: list[tuple[int, str]] = []  # (timestamp_ms, text)
    offset_ms = 0

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Check for offset tag first
        offset_match = OFFSET_RE.match(line)
        if offset_match:
            offset_ms = int(offset_match.group(1))
            continue

        # Check for metadata tags
        meta_match = METADATA_RE.match(line)
        if meta_match:
            key, value = meta_match.group(1), meta_match.group(2).strip()
            metadata[key] = value
            continue

        # Extract timestamps and lyric text
        timestamps = TIMESTAMP_RE.findall(line)
        # Remove all timestamps to get the text
        text_only = TIMESTAMP_RE.sub("", line).strip()

        if timestamps and text_only:
            # A line may have multiple timestamps (e.g., [00:01.00][00:03.00]Same text)
            for ts_match in timestamps:
                minutes, seconds, centis = ts_match
                centis = centis if centis else "0"
                # Pad centis to 3 digits
                centis = centis.ljust(3, "0")[:3]
                ts_ms = int(minutes) * 60000 + int(seconds) * 1000 + int(centis)
                ts_ms += offset_ms  # Apply offset
                raw_lines.append((ts_ms, text_only))

    # Sort by timestamp
    raw_lines.sort(key=lambda x: x[0])

    lyric_lines = [LyricLine(timestamp_ms=ts, text=text) for ts, text in raw_lines]

    return metadata if metadata else None, lyric_lines


def parse_lrc(path: Path) -> list[LyricLine]:
    """Parse an LRC file and return lyric lines.

    Args:
        path: Path to the .lrc file.

    Returns:
        List of LyricLine objects sorted by timestamp.

    Raises:
        FileNotFoundError: If the LRC file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"LRC file not found: {path}")

    text = path.read_text(encoding="utf-8")
    _, lines = parse_lrc_text(text)
    return lines


def get_line_at_timestamp(lines: list[LyricLine], ts_ms: int) -> Optional[LyricLine]:
    """Find the lyric line active at a given timestamp.

    Returns the most recent line that started before or at ts_ms.

    Args:
        lines: Sorted list of LyricLine objects.
        ts_ms: Target timestamp in milliseconds.

    Returns:
        The LyricLine active at ts_ms, or None.
    """
    if not lines:
        return None

    result = None
    for line in lines:
        if line.timestamp_ms > ts_ms:
            break
        result = line
    return result


if __name__ == "__main__":
    # Quick sanity tests
    print("Testing timestamp conversions...")

    # Test timestamp_to_ms
    assert timestamp_to_ms("[01:23.45]") == 83450, f"Got {timestamp_to_ms('[01:23.45]')}"
    assert timestamp_to_ms("[00:12.340]") == 12340, f"Got {timestamp_to_ms('[00:12.340]')}"
    assert timestamp_to_ms("[01:23]") == 83000, f"Got {timestamp_to_ms('[01:23]')}"
    assert timestamp_to_ms("[00:00.00]") == 0, f"Got {timestamp_to_ms('[00:00.00]')}"
    assert timestamp_to_ms("[12:34.567]") == 754567, f"Got {timestamp_to_ms('[12:34.567]')}"
    print("  timestamp_to_ms: OK")

    # Test ms_to_timestamp
    assert ms_to_timestamp(83450) == "01:23.45", f"Got {ms_to_timestamp(83450)}"
    assert ms_to_timestamp(12340) == "00:12.34", f"Got {ms_to_timestamp(12340)}"
    assert ms_to_timestamp(0) == "00:00.00", f"Got {ms_to_timestamp(0)}"
    print("  ms_to_timestamp: OK")

    # Test parse_lrc_text
    lrc_sample = """[ti:Test Song]
[ar:Test Artist]
[al:Test Album]
[offset:+500]
[00:12.34]First line
[00:15.00]Second line
[00:18.50]Third line with [00:20.00]duplicate
"""
    meta, lines = parse_lrc_text(lrc_sample)
    assert meta is not None
    assert meta["ti"] == "Test Song"
    assert meta["ar"] == "Test Artist"
    assert meta["al"] == "Test Album"
    assert len(lines) == 4, f"Expected 4 lines, got {len(lines)}"
    # First line should have offset applied: 12340 + 500 = 12840
    assert lines[0].timestamp_ms == 12840, f"Got {lines[0].timestamp_ms}"
    assert lines[0].text == "First line"
    print("  parse_lrc_text: OK")

    # Test get_line_at_timestamp
    assert get_line_at_timestamp(lines, 0) is None  # Before first line
    assert get_line_at_timestamp(lines, 12840) == lines[0]
    assert get_line_at_timestamp(lines, 15000) == lines[1]
    assert get_line_at_timestamp(lines, 999999) == lines[-1]
    print("  get_line_at_timestamp: OK")

    print("All LRC parser tests passed!")
