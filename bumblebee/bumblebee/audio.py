"""Audio snippet extraction, playback, and export.

Uses pydub for audio processing. Supports:
- Loading MP3 files
- Extracting snippets by timestamp range
- Playing snippets (with crossfade)
- Exporting snippets as MP3 with copied tags
- Chaining multiple snippets with crossfade
"""

from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from pydub import AudioSegment


def load_audio(path: Path) -> AudioSegment:
    """Load an MP3 file via pydub.

    Args:
        path: Path to the MP3 file.

    Returns:
        AudioSegment object.

    Raises:
        FileNotFoundError: If the file does not exist.
        Exception: If pydub fails to load the file.
    """
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    return AudioSegment.from_mp3(str(path))


def extract_snippet(path: Path, start_ms: int, end_ms: int) -> AudioSegment:
    """Extract an audio snippet from an MP3 file.

    Args:
        path: Path to the MP3 file.
        start_ms: Start time in milliseconds.
        end_ms: End time in milliseconds.

    Returns:
        AudioSegment containing the snippet.

    Examples:
        >>> seg = extract_snippet(Path("song.mp3"), 10000, 15000)
        >>> len(seg)
        5000
    """
    audio = load_audio(path)

    # Clamp to valid range
    start_ms = max(0, start_ms)
    end_ms = min(len(audio), end_ms)

    if start_ms >= end_ms:
        # Return a short silent segment if range is invalid
        return AudioSegment.silent(duration=100)

    return audio[start_ms:end_ms]


def add_crossfade(
    seg1: AudioSegment, seg2: AudioSegment, duration: int = 150
) -> AudioSegment:
    """Chain two audio segments with a crossfade.

    Args:
        seg1: First audio segment.
        seg2: Second audio segment.
        duration: Crossfade duration in milliseconds.

    Returns:
        Combined audio segment with crossfade applied.
    """
    duration = min(duration, len(seg1) // 2, len(seg2) // 2)
    if duration <= 0:
        return seg1 + seg2

    return seg1.append(seg2, crossfade=duration)


def play_snippet(path: Path, start_ms: int, end_ms: int) -> None:
    """Play an audio snippet.

    Uses pydub.playback.play(). Adds a small crossfade (50ms) at
    boundaries to avoid click sounds.

    Args:
        path: Path to the MP3 file.
        start_ms: Start time in milliseconds.
        end_ms: End time in milliseconds.
    """
    from pydub.playback import play

    snippet = extract_snippet(path, start_ms, end_ms)

    # Add a tiny fade in/out to avoid clicks at boundaries
    snippet = snippet.fade_in(50).fade_out(50)

    play(snippet)


def play_full(path: Path) -> None:
    """Play an entire song.

    Args:
        path: Path to the MP3 file.
    """
    from pydub.playback import play

    audio = load_audio(path)
    play(audio)


def export_snippet(
    path: Path,
    start_ms: int,
    end_ms: int,
    output: Path,
    bitrate: str = "192k",
    crossfade_ms: int = 100,
) -> None:
    """Export an audio snippet as MP3 with tags copied from source.

    Args:
        path: Path to the source MP3 file.
        start_ms: Start time in milliseconds.
        end_ms: End time in milliseconds.
        output: Output file path.
        bitrate: MP3 bitrate (e.g., "192k", "320k").
        crossfade_ms: Crossfade duration at boundaries.

    Examples:
        >>> export_snippet(Path("song.mp3"), 10000, 15000,
        ...                Path("snippet.mp3"))
    """
    snippet = extract_snippet(path, start_ms, end_ms)

    # Apply crossfade fade in/out for professional sound
    if crossfade_ms > 0:
        snippet = snippet.fade_in(crossfade_ms).fade_out(crossfade_ms)

    # Ensure output directory exists
    output.parent.mkdir(parents=True, exist_ok=True)

    # Export snippet
    snippet.export(str(output), format="mp3", bitrate=bitrate)

    # Copy tags from source to output
    try:
        _copy_tags(path, output)
    except Exception:
        # Tag copying is best-effort
        pass


def export_chain(
    segments: list[tuple[Path, int, int]],
    output: Path,
    bitrate: str = "192k",
    crossfade_ms: int = 150,
) -> None:
    """Chain multiple snippets into a single MP3 with crossfades.

    Args:
        segments: List of (mp3_path, start_ms, end_ms) tuples.
        output: Output file path.
        bitrate: MP3 bitrate.
        crossfade_ms: Crossfade duration between segments.
    """
    if not segments:
        raise ValueError("No segments to chain")

    # Extract all snippets
    audio_segments: list[AudioSegment] = []
    for mp3_path, start_ms, end_ms in segments:
        seg = extract_snippet(mp3_path, start_ms, end_ms)
        if crossfade_ms > 0:
            seg = seg.fade_in(min(crossfade_ms, len(seg) // 3)).fade_out(
                min(crossfade_ms, len(seg) // 3)
            )
        audio_segments.append(seg)

    # Chain with crossfade
    result = audio_segments[0]
    for seg in audio_segments[1:]:
        result = add_crossfade(result, seg, duration=crossfade_ms)

    # Export
    output.parent.mkdir(parents=True, exist_ok=True)
    result.export(str(output), format="mp3", bitrate=bitrate)


def _copy_tags(src_path: Path, dst_path: Path) -> None:
    """Copy ID3 tags from source MP3 to destination MP3.

    Uses mutagen to copy tags. Best-effort: silently fails if mutagen
    is unavailable or tags are missing.
    """
    try:
        from mutagen.mp3 import MP3

        src_audio = MP3(src_path)
        if not src_audio.tags:
            return

        dst_audio = MP3(dst_path)
        dst_audio.tags = src_audio.tags
        dst_audio.save()
    except Exception:
        pass


def get_audio_duration(path: Path) -> int:
    """Get the duration of an MP3 file in milliseconds.

    Args:
        path: Path to the MP3 file.

    Returns:
        Duration in milliseconds.
    """
    audio = load_audio(path)
    return len(audio)


def format_duration_ms(ms: int) -> str:
    """Format duration in milliseconds as mm:ss.cc.

    Args:
        ms: Duration in milliseconds.

    Returns:
        Formatted string like "03:45.12".
    """
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    centis = (ms % 1000) // 10
    return f"{minutes:02d}:{seconds:02d}.{centis:02d}"


if __name__ == "__main__":
    import tempfile

    print("Testing audio module...")

    # Create a synthetic test MP3 (sine wave)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Generate a 5-second test audio file
        from pydub.generators import Sine

        test_audio = Sine(440).to_audio_segment(duration=5000)  # 5 seconds
        test_mp3 = tmp_path / "test.mp3"
        test_audio.export(str(test_mp3), format="mp3")

        # Test load_audio
        loaded = load_audio(test_mp3)
        assert len(loaded) == 5000, f"Expected 5000ms, got {len(loaded)}ms"
        print("  load_audio: OK")

        # Test extract_snippet
        snippet = extract_snippet(test_mp3, 1000, 3000)
        assert len(snippet) == 2000, f"Expected 2000ms, got {len(snippet)}ms"
        print("  extract_snippet: OK")

        # Test edge cases
        snippet = extract_snippet(test_mp3, 4000, 6000)  # Beyond end
        assert len(snippet) == 1000, f"Expected 1000ms, got {len(snippet)}ms"
        print("  extract_snippet (edge clamp): OK")

        snippet = extract_snippet(test_mp3, 6000, 7000)  # Start beyond end
        assert len(snippet) < 500, f"Expected near-silent, got {len(snippet)}ms"
        print("  extract_snippet (out of range): OK")

        # Test add_crossfade
        seg1 = extract_snippet(test_mp3, 0, 2000)
        seg2 = extract_snippet(test_mp3, 2000, 4000)
        combined = add_crossfade(seg1, seg2, duration=100)
        assert len(combined) < 4000  # Should be slightly less due to overlap
        assert len(combined) > 3800
        print("  add_crossfade: OK")

        # Test export_snippet
        export_path = tmp_path / "exported.mp3"
        export_snippet(test_mp3, 1000, 3000, export_path)
        assert export_path.exists()
        exported = load_audio(export_path)
        assert len(exported) == 2000
        print("  export_snippet: OK")

        # Test export_chain
        chain_segments = [
            (test_mp3, 0, 1000),
            (test_mp3, 2000, 3000),
            (test_mp3, 4000, 5000),
        ]
        chain_path = tmp_path / "chain.mp3"
        export_chain(chain_segments, chain_path)
        assert chain_path.exists()
        print("  export_chain: OK")

        # Test format_duration_ms
        assert format_duration_ms(83450) == "01:23.45"
        assert format_duration_ms(0) == "00:00.00"
        assert format_duration_ms(60000) == "01:00.00"
        print("  format_duration_ms: OK")

    print("All audio tests passed!")
