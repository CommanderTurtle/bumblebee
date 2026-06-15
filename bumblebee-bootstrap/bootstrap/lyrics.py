"""
Lyrics management module for bumblebee-bootstrap.

Provides functions to search for and download synced lyrics (.lrc files)
from lrclib.net — the same source used by the Jellyfin lyrics plugin.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from bootstrap.models import TrackInfo
from bootstrap.utils import safe_makedirs


def search_lyrics(
    artist: str,
    title: str,
    duration: int,
    album: Optional[str] = None,
) -> Optional[dict]:
    """
    Search for synced lyrics from lrclib.net.

    Queries the lrclib.net API with track metadata to find matching lyrics.
    Returns both synced (timestamped) and plain lyrics if available.

    Args:
        artist: The track artist name.
        title: The track title.
        duration: Track duration in seconds.
        album: Optional album name for more precise matching.

    Returns:
        A dict with 'syncedLyrics' and 'plainLyrics' keys, or None if no lyrics found.
        Example return value:
            {
                "syncedLyrics": "[00:12.34]Line one\\n[00:15.67]Line two\\n...",
                "plainLyrics": "Line one\\nLine two\\n..."
            }
    """
    base_url = "https://lrclib.net/api/search"
    params: dict[str, str] = {
        "track_name": title,
        "artist_name": artist,
        "duration": str(duration),
    }
    if album:
        params["album_name"] = album

    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "bumblebee-bootstrap/1.0.0",
                "Accept": "application/json",
            },
        )

        # Rate limiting: be polite to the lrclib API
        time.sleep(0.3)

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        # lrclib returns a list of results
        if not isinstance(data, list) or not data:
            return None

        # Pick the best match (first result is usually the best)
        best_match = data[0]

        synced = best_match.get("syncedLyrics")
        plain = best_match.get("plainLyrics")

        if not synced and not plain:
            return None

        result: dict[str, str] = {}
        if synced:
            result["syncedLyrics"] = synced
        if plain:
            result["plainLyrics"] = plain

        return result if result else None

    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            # No lyrics found for this track
            return None
        return None
    except Exception:
        return None


def download_lrc(track: TrackInfo) -> Optional[Path]:
    """
    Download and save a .lrc file alongside the organized MP3.

    The .lrc file is saved with the same base name as the MP3 but with .lrc extension.
    This follows the Jellyfin convention for lyrics file naming.

    Args:
        track: The TrackInfo containing lyrics data (from search_lyrics).

    Returns:
        The path to the saved .lrc file, or None if no lyrics were available.
    """
    if not track.dest_path:
        return None

    # Get lyrics data attached to the track
    lyrics_data = getattr(track, "lyrics_data", None)
    if not lyrics_data:
        return None

    synced = lyrics_data.get("syncedLyrics")
    plain = lyrics_data.get("plainLyrics")

    if not synced and not plain:
        return None

    # Use synced lyrics if available, otherwise fall back to plain
    lrc_content = synced or plain

    # The .lrc file goes next to the MP3 with the same base name
    lrc_path = track.dest_path.with_suffix(".lrc")

    try:
        safe_makedirs(lrc_path.parent)
        lrc_path.write_text(lrc_content, encoding="utf-8")
        return lrc_path
    except OSError:
        return None
