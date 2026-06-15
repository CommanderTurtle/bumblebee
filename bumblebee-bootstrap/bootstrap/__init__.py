"""
Bumblebee Bootstrap — Jellyfin Library Setup Tool

Automated Jellyfin library bootstrapper for disorganized MP3 collections.
Discovers, fingerprints, enriches metadata, downloads lyrics, and organizes
your music library into a Jellyfin-ready structure.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bootstrap.console import console, ProgressManager, show_header, show_summary
from bootstrap.fingerprint import fingerprint_file, identify_track
from bootstrap.jellyfin import (
    install_lyrics_plugin,
    print_jellyfin_guide,
    start_jellyfin,
    write_docker_compose,
)
from bootstrap.lyrics import download_lrc, search_lyrics
from bootstrap.metadata import (
    embed_metadata,
    enrich_from_musicbrainz,
    fetch_album_art,
    read_existing_metadata,
)
from bootstrap.models import LibraryConfig, TrackInfo
from bootstrap.organize import organize_tracks
from bootstrap.utils import discover_mp3s, format_duration, safe_makedirs


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="bumblebee-bootstrap",
        description=(
            "Automated Jellyfin library bootstrapper for disorganized MP3 collections. "
            "Discovers MP3s, fingerprints them, enriches metadata, downloads lyrics, "
            "and produces a Jellyfin-ready library structure."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --source ~/Downloads/my_mp3s
  %(prog)s --source ~/Music --output ~/organized_library --move
  %(prog)s --source ~/Music --skip-fingerprint --workers 8
        """,
    )
    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Source directory containing disorganized MP3 files (recursive scan)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./organized_library"),
        help="Output directory for the organized library (default: ./organized_library)",
    )
    parser.add_argument(
        "--jellyfin-data",
        type=Path,
        default=Path("./jellyfin_data"),
        help="Directory for Jellyfin data/config volume (default: ./jellyfin_data)",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        default=False,
        help="Move files instead of copying (DESTRUCTIVE -- removes originals)",
    )
    parser.add_argument(
        "--skip-fingerprint",
        action="store_true",
        default=False,
        help="Skip AcoustID fingerprinting; use existing metadata only",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers for processing (default: 4)",
    )
    parser.add_argument(
        "--no-lyrics",
        action="store_true",
        default=False,
        help="Skip downloading lyrics from lrclib.net",
    )
    parser.add_argument(
        "--no-album-art",
        action="store_true",
        default=False,
        help="Skip fetching and embedding album art",
    )
    parser.add_argument(
        "--no-jellyfin",
        action="store_true",
        default=False,
        help="Skip Jellyfin Docker Compose setup",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> LibraryConfig:
    """Build LibraryConfig from parsed CLI arguments."""
    return LibraryConfig(
        source_dir=args.source.resolve(),
        output_dir=args.output.resolve(),
        jellyfin_data_dir=args.jellyfin_data.resolve(),
        musicbrainz_enabled=not args.skip_fingerprint,
        lyrics_enabled=not args.no_lyrics,
        album_art_enabled=not args.no_album_art,
        copy_mode=not args.move,
        workers=args.workers,
    )


def process_single_track(
    track: TrackInfo,
    config: LibraryConfig,
    progress: ProgressManager,
) -> TrackInfo:
    """Process a single track through fingerprinting, enrichment, lyrics, and album art."""
    try:
        # Step 1: Fingerprint (if enabled)
        if config.musicbrainz_enabled:
            progress.update_fingerprint(track.source_path.name)
            fp = fingerprint_file(track.source_path)
            if fp:
                track.fingerprint = fp
                result = identify_track(track.source_path, track.duration_ms / 1000.0, fingerprint=fp)
                if result:
                    track.acoustid_id = result.get("acoustid_id")
                    track.mb_recording_id = result.get("mb_recording_id")
                    track.mb_release_id = result.get("mb_release_id")

        # Step 2: Enrich from MusicBrainz
        if track.mb_recording_id or (track.title and track.artist):
            progress.update_metadata(track.source_path.name)
            track = enrich_from_musicbrainz(track)

        # Step 3: Album art
        if config.album_art_enabled and track.mb_release_id:
            progress.update_album_art(track.source_path.name)
            art = fetch_album_art(track.mb_release_id)
            if art:
                # Store temporarily on the track object
                track._album_art_data = art  # type: ignore[attr-defined]

        # Step 4: Lyrics
        if config.lyrics_enabled and track.title and track.artist:
            progress.update_lyrics(track.source_path.name)
            lyrics = search_lyrics(
                artist=track.artist,
                title=track.title,
                duration=track.duration_ms // 1000,
                album=track.album,
            )
            if lyrics:
                track.has_lyrics = True
                track._lyrics_data = lyrics  # type: ignore[attr-defined]

        progress.mark_success()
        return track

    except Exception as exc:
        progress.mark_failure(str(exc))
        return track


def main() -> int:
    """Main entry point for the bumblebee-bootstrap CLI."""
    args = parse_args()
    config = build_config(args)

    # Show banner
    show_header()

    # Validate source directory
    if not config.source_dir.exists():
        console.print(f"[red]Error:[/red] Source directory does not exist: {config.source_dir}")
        return 1
    if not config.source_dir.is_dir():
        console.print(f"[red]Error:[/red] Source path is not a directory: {config.source_dir}")
        return 1

    # Ensure output directories exist
    safe_makedirs(config.output_dir)
    safe_makedirs(config.jellyfin_data_dir)

    # -- Stage 1: Discovery --
    print("\n[bold cyan]Stage 1: Discovering MP3 files...[/bold cyan]")
    mp3_paths = discover_mp3s(config.source_dir)
    if not mp3_paths:
        console.print("[yellow]No MP3 files found in the source directory.[/yellow]")
        return 0

    print(f"[green]Found {len(mp3_paths)} MP3 file(s)[/green]")

    # -- Stage 2: Read existing metadata --
    print("\n[bold cyan]Stage 2: Reading existing metadata...[/bold cyan]")
    tracks: list[TrackInfo] = []
    for path in mp3_paths:
        try:
            track = read_existing_metadata(path)
            tracks.append(track)
        except Exception as exc:
            console.print(f"[yellow]Warning:[/yellow] Could not read metadata for {path}: {exc}")
            tracks.append(
                TrackInfo(
                    source_path=path,
                    duration_ms=0,
                )
            )

    # -- Stage 3: Fingerprint + Enrich + Lyrics + Album Art --
    print("\n[bold cyan]Stage 3: Enriching tracks (fingerprint, metadata, lyrics, album art)...[/bold cyan]")
    with ProgressManager() as progress:
        progress.start_overall(len(tracks))

        with ThreadPoolExecutor(max_workers=config.workers) as executor:
            futures = {
                executor.submit(process_single_track, track, config, progress): track
                for track in tracks
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    print(f"[yellow]Warning:[/yellow] Track processing failed: {exc}")

    # -- Stage 4: Organize files --
    print("\n[bold cyan]Stage 4: Organizing library structure...[/bold cyan]")
    tracks = organize_tracks(tracks, config)

    # -- Stage 5: Embed metadata & album art --
    print("\n[bold cyan]Stage 5: Embedding metadata and album art...[/bold cyan]")
    for track in tracks:
        if track.dest_path and track.dest_path.exists():
            try:
                art = getattr(track, "_album_art_data", None)
                embed_metadata(track.dest_path, track, art)

                # Save lyrics as .lrc file alongside the MP3
                lyrics_data = getattr(track, "_lyrics_data", None)
                if lyrics_data and track.dest_path:
                    # Temporarily attach lyrics_data for download_lrc
                    track.lyrics_data = lyrics_data  # type: ignore[attr-defined]
                    download_lrc(track)
            except Exception as exc:
                console.print(f"[yellow]Warning:[/yellow] Could not embed metadata for {track.dest_path.name}: {exc}")

    # -- Stage 6: Show summary --
    print()
    show_summary(tracks)

    # -- Stage 7: Jellyfin setup --
    if not args.no_jellyfin:
        print("\n[bold cyan]Stage 7: Setting up Jellyfin...[/bold cyan]")
        write_docker_compose(config)

        # Check if docker is available
        if shutil.which("docker"):
            print("[green]Docker found. Starting Jellyfin...[/green]")
            start_jellyfin(config)
            install_lyrics_plugin(config)
            print_jellyfin_guide()
        else:
            print("[yellow]Docker not found. Skipping Jellyfin startup.[/yellow]")
            print("[dim]To start Jellyfin manually:[/dim]")
            print(f"[dim]  cd {Path.cwd()} && docker compose up -d[/dim]")

    print("\n[bold green]Bumblebee Bootstrap complete![/bold green]")
    print(f"[dim]Organized library:[/dim] {config.output_dir}")
    if not args.no_jellyfin:
        print("[dim]Jellyfin URL:[/dim] http://localhost:8096")

    return 0


if __name__ == "__main__":
    sys.exit(main())
