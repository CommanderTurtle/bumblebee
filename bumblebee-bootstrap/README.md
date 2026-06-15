# Bumblebee Bootstrap

Automated Jellyfin library bootstrapper for disorganized MP3 collections.

Takes a folder of messy MP3s -- with unknown filenames, missing or wrong metadata, and no album art -- and produces a fully structured, metadata-enriched library ready for Jellyfin with the lyrics plugin.

## Features

- **Audio fingerprinting** (AcoustID/Chromaprint) -- identifies songs regardless of filename or tags
- **Metadata enrichment** from MusicBrainz + lrclib.net
- **Album art fetching** and embedding into MP3 files
- **Directory restructuring**: `Artist/Album/01 - Title.mp3`
- **LRC lyrics download** from lrclib.net (same source as the Jellyfin plugin)
- **Jellyfin Docker Compose** setup with lyrics plugin guidance
- **One-command operation** with Rich progress display

## Quick Start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run bootstrap
uv run bumblebee-bootstrap --source ~/Downloads/my_mp3s

# With options
uv run bumblebee-bootstrap \
  --source ~/Downloads/my_mp3s \
  --output ~/Music/Library \
  --move \
  --workers 8
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source` | Source directory with MP3 files | *(required)* |
| `--output` | Output directory for organized library | `./organized_library` |
| `--jellyfin-data` | Jellyfin data/config directory | `./jellyfin_data` |
| `--move` | Move files instead of copying | *(flag, default: copy)* |
| `--skip-fingerprint` | Skip AcoustID fingerprinting | *(flag)* |
| `--workers` | Parallel workers for processing | `4` |
| `--no-lyrics` | Skip lyrics download | *(flag)* |
| `--no-album-art` | Skip album art fetch | *(flag)* |
| `--no-jellyfin` | Skip Docker Compose setup | *(flag)* |

## Architecture

```
bumblebee-bootstrap/
├── pyproject.toml
├── README.md
├── bootstrap/
│   ├── __init__.py      # CLI entry point with main()
│   ├── models.py        # TrackInfo and LibraryConfig dataclasses
│   ├── console.py       # Rich progress UI and summary tables
│   ├── utils.py         # MP3 discovery, path helpers, formatting
│   ├── fingerprint.py   # Chromaprint + AcoustID with fallback
│   ├── metadata.py      # MusicBrainz enrichment + ID3 tag management
│   ├── lyrics.py        # lrclib.net LRC download
│   ├── organize.py      # Directory restructuring + file operations
│   └── jellyfin.py      # Docker Compose + plugin setup
```

## Pipeline Stages

1. **Discovery** -- Recursively find all MP3 files in the source directory
2. **Metadata Reading** -- Extract existing ID3 tags (title, artist, album, etc.)
3. **Fingerprinting** -- Generate Chromaprint fingerprints, query AcoustID API
4. **Enrichment** -- Query MusicBrainz for detailed metadata
5. **Album Art** -- Fetch and embed cover images from Cover Art Archive
6. **Lyrics** -- Download synced lyrics (.lrc) from lrclib.net
7. **Organization** -- Restructure into `Artist/Album/Track` hierarchy
8. **Jellyfin Setup** -- Write docker-compose.yml, start container

## Fingerprint Fallback Strategy

Since the `fpcalc` binary may not be available on all systems, the fingerprinting
module uses a three-tier fallback:

1. Read existing fingerprint tags from the MP3 (e.g., from previous Picard/beets runs)
2. Call `fpcalc` binary via subprocess (if installed)
3. Fall back to metadata-based identification using existing ID3 tags

This ensures the bootstrapper works well even without Chromaprint installed.
