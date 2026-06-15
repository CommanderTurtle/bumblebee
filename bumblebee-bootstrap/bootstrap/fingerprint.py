"""
Audio fingerprinting module for bumblebee-bootstrap.

Provides a three-tier fallback strategy for audio identification:
1. Read existing fingerprint tags from the MP3 file (via mutagen)
2. Call the fpcalc binary via subprocess (if available on the system)
3. Fall back to metadata-based identification (use existing ID3 tags)

Also includes AcoustID API lookup for fingerprint-based track identification.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from mutagen.mp3 import MP3


def _read_existing_fingerprint(path: Path) -> Optional[str]:
    """
    Try to read an existing Chromaprint fingerprint stored in the file's tags.

    Some tagging tools (e.g., Picard, beets) store fingerprints in custom tags.
    We check for common tag names like 'chromaprint' or 'acoustid_fingerprint'.
    """
    try:
        audio = MP3(path)
        if audio.tags is None:
            return None

        # Check common fingerprint tag names
        for tag_name in (
            "TXXX:chromaprint",
            "TXXX:acoustid_fingerprint",
            "TXXX:fingerprint",
            "TXXX:Acoustid Fingerprint",
            "TXXX:Chromaprint",
        ):
            if tag_name in audio.tags:
                value = audio.tags[tag_name]
                if hasattr(value, "text"):
                    return str(value.text[0]) if value.text else None
                return str(value)

        return None
    except Exception:
        return None


def _call_fpcalc(path: Path) -> Optional[str]:
    """
    Call the fpcalc binary to compute a Chromaprint fingerprint.

    Requires the fpcalc binary (from chromaprint-tools) to be installed and on PATH.
    Returns None if the binary is not available or the call fails.
    """
    fpcalc_path = shutil.which("fpcalc")
    if fpcalc_path is None:
        return None

    try:
        result = subprocess.run(
            [fpcalc_path, "-raw", str(path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None

        # Parse fpcalc output: lines like "FINGERPRINT=AQAD..."
        for line in result.stdout.splitlines():
            if line.startswith("FINGERPRINT="):
                return line[len("FINGERPRINT="):].strip()

        return None
    except (subprocess.TimeoutExpired, OSError):
        return None


def fingerprint_file(path: Path) -> Optional[str]:
    """
    Generate a Chromaprint fingerprint for an audio file.

    Uses a three-tier fallback strategy:
    1. Read existing fingerprint tag from the file (if present)
    2. Call fpcalc binary (if installed)
    3. Return None (metadata-based identification will be used as fallback)

    Args:
        path: Path to the audio file.

    Returns:
        The fingerprint string, or None if no fingerprint could be generated.
    """
    # Tier 1: Read existing fingerprint tag
    existing = _read_existing_fingerprint(path)
    if existing:
        return existing

    # Tier 2: Call fpcalc binary
    fpcalc_result = _call_fpcalc(path)
    if fpcalc_result:
        return fpcalc_result

    # Tier 3: No fingerprint available
    return None


def _acoustid_lookup(fingerprint: str, duration: float) -> Optional[dict]:
    """
    Query the AcoustID API to identify a track from its fingerprint.

    Args:
        fingerprint: The Chromaprint fingerprint string.
        duration: Track duration in seconds.

    Returns:
        A dict with acoustid_id, mb_recording_id, and mb_release_id if found,
        or None if the lookup fails or returns no results.
    """
    # Built-in client ID for the free AcoustID tier
    client_id = "8XaBELgH"
    url = (
        f"https://api.acoustid.org/v2/lookup"
        f"?client={client_id}"
        f"&meta=recordings+releases+tracks"
        f"&fingerprint={urllib.parse.quote(fingerprint)}"
        f"&duration={int(duration)}"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "bumblebee-bootstrap/1.0.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            import json

            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "ok":
            return None

        results = data.get("results", [])
        if not results:
            return None

        best_result = results[0]
        acoustid_id = best_result.get("id")

        recordings = best_result.get("recordings", [])
        if not recordings:
            return {"acoustid_id": acoustid_id} if acoustid_id else None

        recording = recordings[0]
        mb_recording_id = recording.get("id")

        # Try to find a release (album) ID
        mb_release_id = None
        releases = recording.get("releases", [])
        if releases:
            mb_release_id = releases[0].get("id")

        return {
            "acoustid_id": acoustid_id,
            "mb_recording_id": mb_recording_id,
            "mb_release_id": mb_release_id,
        }

    except Exception:
        return None


def identify_track(path: Path, duration: float, fingerprint: Optional[str] = None) -> Optional[dict]:
    """
    Identify a track using its fingerprint and duration.

    This is the main entry point for AcoustID-based identification.
    Rate limiting is applied (sleep between requests to respect the free tier).

    Args:
        path: Path to the audio file (used for fingerprint generation).
        duration: Track duration in seconds.
        fingerprint: Optional pre-computed fingerprint to avoid re-computation.

    Returns:
        A dict with identification results (acoustid_id, mb_recording_id, mb_release_id),
        or None if identification fails.
    """
    fp = fingerprint or fingerprint_file(path)
    if not fp:
        return None

    # Rate limiting: max ~3 req/sec for AcoustID free tier
    time.sleep(0.4)

    return _acoustid_lookup(fp, duration)
