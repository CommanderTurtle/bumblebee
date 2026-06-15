#!/usr/bin/env python3
"""
Bumblebee Voice Line — Export a specific lyric snippet as MP3.

Usage:
    voice-line.py export --song "Just Dance" --start "01:23.45" --duration 5
    voice-line.py export --song-id just-dance-001 --start-ms 83450 --end-ms 85120
    voice-line.py list                                           # List available songs
    voice-line.py play --song "Just Dance" --start "01:23.45"    # Preview (requires backend)
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


def find_song_file(song_title: str, library_path: Optional[str] = None) -> Optional[Path]:
    """Find the MP3 file for a song in the library."""
    library = library_path or os.environ.get("BUMBLEBEE_LIBRARY", str(Path.home() / "Music"))
    lib = Path(library)
    
    # Search recursively for matching MP3
    for mp3_file in lib.rglob("*.mp3"):
        if song_title.lower() in mp3_file.stem.lower():
            return mp3_file
    
    return None


def find_song_by_id(song_id: str, library_path: Optional[str] = None) -> Optional[Path]:
    """Find MP3 by song ID from the database."""
    library = library_path or os.environ.get("BUMBLEBEE_LIBRARY", str(Path.home() / "Music"))
    db_path = os.environ.get("BUMBLEBEE_DB", str(Path(library) / ".bumblebee.db"))
    
    if not Path(db_path).exists():
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT path FROM songs WHERE id = ?", (song_id,)).fetchone()
        conn.close()
        if row:
            return Path(row[0]) if Path(row[0]).exists() else None
    except Exception:
        pass
    
    return None


def timestamp_to_ms(ts: str) -> int:
    """Convert mm:ss.xx to milliseconds."""
    parts = ts.replace("[", "").replace("]", "").split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid timestamp: {ts}")
    
    minutes = int(parts[0])
    
    if "." in parts[1]:
        sec_part = parts[1].split(".")
        seconds = int(sec_part[0])
        centis = int(sec_part[1].ljust(2, "0")[:2])
        return minutes * 60000 + seconds * 1000 + centis * 10
    else:
        seconds = int(parts[1])
        return minutes * 60000 + seconds * 1000


def export_snippet(
    mp3_path: Path,
    start_ms: int,
    end_ms: int,
    output: Path,
    bitrate: str = "192k",
) -> bool:
    """Export a snippet using ffmpeg (or pydub as fallback)."""
    
    # Try ffmpeg first
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(mp3_path),
        "-ss", f"{start_ms / 1000:.3f}",
        "-to", f"{end_ms / 1000:.3f}",
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        str(output),
    ]
    
    try:
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fallback to pydub
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(str(mp3_path))
        snippet = audio[start_ms:end_ms]
        snippet.export(str(output), format="mp3", bitrate=bitrate)
        return True
    except ImportError:
        print("Error: Neither ffmpeg nor pydub is available.", file=sys.stderr)
        print("Install one of them to export voice lines.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error exporting: {e}", file=sys.stderr)
        return False


def list_songs(library_path: Optional[str] = None) -> list[dict]:
    """List available songs in the library."""
    library = library_path or os.environ.get("BUMBLEBEE_LIBRARY", str(Path.home() / "Music"))
    db_path = os.environ.get("BUMBLEBEE_DB", str(Path(library) / ".bumblebee.db"))
    
    if not Path(db_path).exists():
        # Scan directory
        songs = []
        for mp3 in Path(library).rglob("*.mp3"):
            songs.append({"title": mp3.stem, "path": str(mp3)})
        return songs
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, title, artist, album, path FROM songs ORDER BY artist, title").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return []


def play_snippet(mp3_path: Path, start_ms: int, end_ms: int) -> bool:
    """Play a snippet using system audio player."""
    # Export to temp file first
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    if not export_snippet(mp3_path, start_ms, end_ms, tmp_path):
        return False
    
    # Try various players
    players = [
        ["ffplay", "-autoexit", "-nodisp", str(tmp_path)],
        ["afplay", str(tmp_path)],  # macOS
        ["mpg123", str(tmp_path)],
        ["cvlc", "--play-and-exit", str(tmp_path)],
    ]
    
    for player in players:
        try:
            subprocess.run(player, capture_output=True, timeout=30)
            tmp_path.unlink(missing_ok=True)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    tmp_path.unlink(missing_ok=True)
    print("Error: No audio player found. Install ffplay, afplay, mpg123, or vlc.", file=sys.stderr)
    return False


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bumblebee Voice Line — Export/play snippets")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Export
    export_parser = subparsers.add_parser("export", help="Export a voice line as MP3")
    export_parser.add_argument("--song", help="Song title")
    export_parser.add_argument("--song-id", help="Song ID from database")
    export_parser.add_argument("--start", help="Start timestamp (mm:ss.xx)")
    export_parser.add_argument("--start-ms", type=int, help="Start time in milliseconds")
    export_parser.add_argument("--end-ms", type=int, help="End time in milliseconds")
    export_parser.add_argument("--duration", type=float, default=5, help="Duration in seconds")
    export_parser.add_argument("--output", default="bumblebee_voice_line.mp3", help="Output filename")
    export_parser.add_argument("--bitrate", default="192k", help="MP3 bitrate")
    export_parser.add_argument("--library", help="Music library path")
    
    # Play
    play_parser = subparsers.add_parser("play", help="Preview a voice line")
    play_parser.add_argument("--song", required=True, help="Song title")
    play_parser.add_argument("--start", required=True, help="Start timestamp (mm:ss.xx)")
    play_parser.add_argument("--duration", type=float, default=5, help="Duration in seconds")
    play_parser.add_argument("--library", help="Music library path")
    
    # List
    list_parser = subparsers.add_parser("list", help="List available songs")
    list_parser.add_argument("--library", help="Music library path")
    
    args = parser.parse_args()
    
    if args.command == "list":
        songs = list_songs(args.library)
        if not songs:
            print("No songs found. Set up a Bumblebee library first:")
            print("  uv run bumblebee-bootstrap/bootstrap.py --source /path/to/mp3s --output ~/Music")
            sys.exit(1)
        
        print(f"📁 {len(songs)} songs in library:")
        for song in songs[:20]:
            artist = song.get("artist", "Unknown")
            title = song.get("title", song.get("path", "Unknown"))
            print(f"   • {title} — {artist}")
        if len(songs) > 20:
            print(f"   ... and {len(songs) - 20} more")
        return
    
    if args.command == "export":
        # Resolve song file
        if args.song_id:
            mp3_path = find_song_by_id(args.song_id, args.library)
        elif args.song:
            mp3_path = find_song_file(args.song, args.library)
        else:
            print("Error: --song or --song-id required", file=sys.stderr)
            sys.exit(1)
        
        if not mp3_path:
            print(f"Error: Could not find MP3 for '{args.song or args.song_id}'", file=sys.stderr)
            print("Run 'voice-line.py list' to see available songs.", file=sys.stderr)
            sys.exit(1)
        
        # Resolve timestamps
        if args.start_ms is not None:
            start_ms = args.start_ms
        elif args.start:
            start_ms = timestamp_to_ms(args.start)
        else:
            print("Error: --start or --start-ms required", file=sys.stderr)
            sys.exit(1)
        
        if args.end_ms is not None:
            end_ms = args.end_ms
        else:
            end_ms = start_ms + int(args.duration * 1000)
        
        output = Path(args.output)
        duration_sec = (end_ms - start_ms) / 1000
        
        print(f"🎵 Exporting voice line...")
        print(f"   Song: {mp3_path.name}")
        print(f"   Range: {start_ms}ms → {end_ms}ms ({duration_sec:.1f}s)")
        print(f"   Output: {output.absolute()}")
        
        if export_snippet(mp3_path, start_ms, end_ms, output, args.bitrate):
            size_kb = output.stat().st_size / 1024
            print(f"\n✅ Exported! {size_kb:.1f} KB @ {args.bitrate}")
            print(f"   Play it: ffplay {output}  (or any audio player)")
        else:
            sys.exit(1)
    
    if args.command == "play":
        mp3_path = find_song_file(args.song, args.library)
        if not mp3_path:
            print(f"Error: Could not find MP3 for '{args.song}'", file=sys.stderr)
            sys.exit(1)
        
        start_ms = timestamp_to_ms(args.start)
        end_ms = start_ms + int(args.duration * 1000)
        
        print(f"🔊 Playing snippet from '{args.song}'...")
        if play_snippet(mp3_path, start_ms, end_ms):
            print("✅ Done!")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
