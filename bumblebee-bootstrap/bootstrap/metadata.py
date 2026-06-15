"""
Metadata management module for bumblebee-bootstrap.

Handles reading existing ID3 tags from MP3 files, enriching metadata from
MusicBrainz, fetching album art from the Cover Art Archive, and embedding
updated metadata (including album art) back into the MP3 files.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from mutagen.id3 import ID3, APIC, TALB, TCON, TIT2, TPE1, TPE2, TPOS, TRCK, TYER, TXXX
from mutagen.mp3 import MP3

from bootstrap.models import TrackInfo


def read_existing_metadata(path: Path) -> TrackInfo:
    """
    Read existing ID3 tags from an MP3 file.

    Extracts: title, artist, album, track number, disc number, year, genre, and duration.

    Args:
        path: Path to the MP3 file.

    Returns:
        A TrackInfo dataclass populated with the extracted metadata.
    """
    track = TrackInfo(source_path=path)

    try:
        audio = MP3(path)
        track.duration_ms = int(audio.info.length * 1000) if audio.info else 0

        if audio.tags is not None:
            tags = audio.tags

            # Title (TIT2)
            if "TIT2" in tags:
                track.title = str(tags["TIT2"])

            # Artist (TPE1)
            if "TPE1" in tags:
                track.artist = str(tags["TPE1"])

            # Album (TALB)
            if "TALB" in tags:
                track.album = str(tags["TALB"])

            # Album artist (TPE2)
            if "TPE2" in tags:
                track.album_artist = str(tags["TPE2"])

            # Track number (TRCK) — handles "3/12" format
            if "TRCK" in tags:
                trck = str(tags["TRCK"])
                if "/" in trck:
                    trck = trck.split("/")[0]
                try:
                    track.track_number = int(trck)
                except ValueError:
                    track.track_number = None

            # Disc number (TPOS) — handles "1/2" format
            if "TPOS" in tags:
                tpos = str(tags["TPOS"])
                if "/" in tpos:
                    tpos = tpos.split("/")[0]
                try:
                    track.disc_number = int(tpos)
                except ValueError:
                    track.disc_number = None

            # Year (TYER or TDRC)
            for year_tag in ("TYER", "TDRC"):
                if year_tag in tags:
                    year_str = str(tags[year_tag])
                    # Extract just the year from ISO dates like "2023-01-15"
                    if len(year_str) >= 4:
                        try:
                            track.year = int(year_str[:4])
                        except ValueError:
                            pass
                    break

            # Genre (TCON)
            if "TCON" in tags:
                track.genre = str(tags["TCON"])

            # Check for existing fingerprint (for reference)
            for fp_tag in ("TXXX:chromaprint", "TXXX:acoustid_fingerprint"):
                if fp_tag in tags:
                    fp_value = tags[fp_tag]
                    if hasattr(fp_value, "text") and fp_value.text:
                        track.fingerprint = str(fp_value.text[0])
                    else:
                        track.fingerprint = str(fp_value)
                    break

            # Check for MusicBrainz IDs
            if "TXXX:MusicBrainz Recording Id" in tags:
                track.mb_recording_id = str(tags["TXXX:MusicBrainz Recording Id"])
            if "TXXX:MusicBrainz Release Track Id" in tags:
                track.mb_release_id = str(tags["TXXX:MusicBrainz Release Track Id"])

    except Exception:
        # If mutagen fails to read the file, return TrackInfo with just the path
        pass

    return track


def enrich_from_musicbrainz(track: TrackInfo) -> TrackInfo:
    """
    Enrich a TrackInfo with metadata from the MusicBrainz API.

    If the track has a MusicBrainz recording ID (from AcoustID or existing tags),
    query the MusicBrainz API to get detailed metadata including title, artist,
    album, track number, and release information.

    Args:
        track: The TrackInfo to enrich.

    Returns:
        The enriched TrackInfo (modified in place and returned).
    """
    mbid = track.mb_recording_id
    if not mbid:
        # No MusicBrainz ID available — skip enrichment
        return track

    url = (
        f"https://musicbrainz.org/ws/2/recording/{mbid}"
        f"?inc=releases+artists&fmt=json"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "bumblebee-bootstrap/1.0.0 (github.com/bumblebee)",
                "Accept": "application/json",
            },
        )

        # Rate limiting: MusicBrainz allows max 1 req/sec for unauthenticated requests
        time.sleep(1.0)

        with urllib.request.urlopen(req, timeout=15) as response:
            import json

            data = json.loads(response.read().decode("utf-8"))

        # Extract recording info
        track.title = data.get("title") or track.title

        # Extract artist info
        artist_credit = data.get("artist-credit", [])
        if artist_credit and not track.artist:
            track.artist = artist_credit[0].get("name", track.artist)
            track.album_artist = track.artist

        # Extract release (album) info
        releases = data.get("releases", [])
        if releases:
            release = releases[0]
            track.album = release.get("title") or track.album
            track.mb_release_id = release.get("id") or track.mb_release_id

            # Try to get track number and year from the release
            date = release.get("date")
            if date and not track.year:
                # Parse date like "2023-01-15" or "2023-01" or "2023"
                try:
                    track.year = int(date[:4])
                except (ValueError, IndexError):
                    pass

            # Get track number from media/track-list
            media = release.get("media", [])
            if media:
                for medium in media:
                    track_list = medium.get("tracks", [])
                    for t in track_list:
                        if t.get("recording", {}).get("id") == mbid:
                            track.track_number = t.get("number") or track.track_number
                            track.disc_number = medium.get("position") or track.disc_number
                            break

    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            # Recording not found — keep existing metadata
            pass
    except Exception:
        # Network or parsing error — keep existing metadata
        pass

    return track


def fetch_album_art(mbid: str) -> Optional[bytes]:
    """
    Fetch album art from the Cover Art Archive.

    Args:
        mbid: MusicBrainz release ID.

    Returns:
        The raw image data as bytes, or None if the art could not be fetched.
    """
    url = f"https://coverartarchive.org/release/{mbid}/front"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "bumblebee-bootstrap/1.0.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            # No front cover available for this release
            pass
        return None
    except Exception:
        return None


def embed_metadata(
    path: Path,
    track: TrackInfo,
    art: Optional[bytes] = None,
) -> None:
    """
    Write ID3 tags and optional album art into an MP3 file.

    Updates/creates the following tags:
    - TIT2 (title)
    - TPE1 (artist)
    - TALB (album)
    - TPOS (disc number)
    - TRCK (track number)
    - TYER (year)
    - TCON (genre)
    - APIC (album art image)

    Args:
        path: Path to the MP3 file to modify.
        track: The TrackInfo containing the metadata to write.
        art: Optional raw image data to embed as album art.
    """
    try:
        audio = MP3(path)

        # Ensure tags exist
        if audio.tags is None:
            audio.add_tags()
        tags = audio.tags

        # Write metadata tags
        if track.title:
            tags["TIT2"] = TIT2(encoding=3, text=track.title)
        if track.artist:
            tags["TPE1"] = TPE1(encoding=3, text=track.artist)
        if track.album:
            tags["TALB"] = TALB(encoding=3, text=track.album)
        if track.album_artist:
            tags["TPE2"] = TPE2(encoding=3, text=track.album_artist)
        if track.disc_number is not None:
            tags["TPOS"] = TPOS(encoding=3, text=str(track.disc_number))
        if track.track_number is not None:
            tags["TRCK"] = TRCK(encoding=3, text=str(track.track_number))
        if track.year is not None:
            tags["TYER"] = TYER(encoding=3, text=str(track.year))
        if track.genre:
            tags["TCON"] = TCON(encoding=3, text=track.genre)

        # Embed album art if provided
        if art:
            # Detect MIME type from image header
            mime_type = "image/jpeg"
            if art[:8] == b"\x89PNG\r\n\x1a\n":
                mime_type = "image/png"
            elif art[:6] in (b"GIF87a", b"GIF89a"):
                mime_type = "image/gif"

            tags["APIC"] = APIC(
                encoding=3,
                mime=mime_type,
                type=3,  # Front cover
                desc="Cover",
                data=art,
            )

        # Save changes
        audio.save()

    except Exception:
        # If embedding fails, leave the file as-is
        pass
