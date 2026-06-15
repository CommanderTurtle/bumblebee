# Bumblebee — Project Specification

## Overview

**Bumblebee** is a full-scale project with two major components:

1. **`bumblebee-bootstrap/`** — Automated Jellyfin library bootstrap for disorganized MP3 collections
2. **`bumblebee/`** — Interactive "speak like Bumblebee" engine (CLI + Web UI) for lyric-based song search, audio snippet playback, and MP3 export

---

## Part 1: bumblebee-bootstrap/

### Purpose
Take a folder of disorganized MP3s (unknown filenames, missing/wrong metadata, no album art) and produce a fully structured, metadata-enriched library ready for Jellyfin with the lyrics plugin.

### Key Features
- **Audio fingerprinting** (AcoustID/Chromaprint) — identifies songs regardless of filename/tags
- **Metadata enrichment** from MusicBrainz + lrclib.net
- **Album art fetching** and embedding
- **Directory restructuring**: `Artist/Album/01 - Title.mp3`
- **LRC lyrics download** from lrclib.net (same source as the Jellyfin plugin)
- **Jellyfin Docker Compose** setup with auto-install of lyrics plugin
- **One-command operation**: `uv run bootstrap.py /path/to/mp3s`

### Directory Structure
```
bumblebee-bootstrap/
├── pyproject.toml              # uv project, dependencies
├── uv.lock                     # pinned deps
├── README.md
├── docker-compose.yml          # Jellyfin server + plugin setup
├── bootstrap.py                # main entry point (argparse CLI)
├── bootstrap/
                ├── __init__.py
├── fingerprint.py        # Chromaprint/AcoustID integration
├── metadata.py           # MusicBrainz metadata enrichment
├── lyrics.py             # lrclib.net LRC download
├── organize.py           # Directory restructuring + file ops
├── jellyfin.py           # Docker compose, plugin install, library scan
├── console.py            # Rich-based progress UI
└── utils.py              # helpers, path sanitization, etc.
```

### Core Data Models

```python
# models.py — shared dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class TrackInfo:
    source_path: Path           # original file location
    fingerprint: str            # chromaprint fingerprint
    acoustid_id: Optional[str]  # AcoustID track ID
    mb_recording_id: Optional[str]   # MusicBrainz recording ID
    mb_release_id: Optional[str]     # MusicBrainz release (album) ID
    
    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    album_artist: Optional[str]
    track_number: Optional[int]
    disc_number: Optional[int]
    year: Optional[int]
    genre: Optional[str]
    duration_ms: int
    
    album_art_url: Optional[str]
    has_lyrics: bool = False
    
    dest_path: Optional[Path] = None  # computed destination

@dataclass  
class LibraryConfig:
    source_dir: Path
    output_dir: Path            # organized library root
    jellyfin_data_dir: Path     # Jellyfin config/data volume
    musicbrainz_enabled: bool = True
    lyrics_enabled: bool = True
    album_art_enabled: bool = True
    copy_mode: bool = True      # True=copy, False=move
```

### Module Specifications

#### `fingerprint.py`
- **Function**: Generate Chromaprint fingerprints, query AcoustID API
- **Dependencies**: `pyacoustid` (or subprocess `fpcalc`)
- **Key functions**:
  - `fingerprint_file(path: Path) -> str` — generate fingerprint
  - `lookup_fingerprint(fingerprint: str, duration: float) -> dict` — query AcoustID
- **AcoustID API**: `https://api.acoustid.org/v2/lookup`
- **Rate limiting**: built-in, max 3 req/sec (free tier)

#### `metadata.py`
- **Function**: Enrich TrackInfo from MusicBrainz
- **Dependencies**: `musicbrainzngs`
- **Key functions**:
  - `enrich_from_musicbrainz(track: TrackInfo) -> TrackInfo`
  - `fetch_album_art(mbid: str) -> Optional[bytes]`
  - `embed_metadata(path: Path, track: TrackInfo, art: Optional[bytes])`
- **Uses**: mutagen (ID3/MP3 metadata writing), requests (album art download)

#### `lyrics.py`
- **Function**: Download synced lyrics (.lrc) from lrclib.net
- **API**: `https://lrclib.net/api/search?q={artist}+{title}` or `?track_name={}&artist_name={}&album_name={}&duration={}`
- **Key functions**:
  - `search_lyrics(artist: str, title: str, duration: int, album: Optional[str]) -> Optional[dict]`
  - `download_lrc(track: TrackInfo, output_dir: Path) -> Optional[Path]`
- **Output**: `.lrc` file saved alongside MP3 (Jellyfin convention: same name, `.lrc` extension)

#### `organize.py`
- **Function**: Directory restructuring and file operations
- **Key functions**:
  - `compute_destination(track: TrackInfo, root: Path) -> Path`
  - `sanitize_filename(name: str) -> str` — remove/replace illegal chars
  - `organize_tracks(tracks: list[TrackInfo], config: LibraryConfig) -> list[TrackInfo]`
- **Naming**: `Artist Name/Album Name/01 - Track Title.mp3`
- **Compilations**: `Various Artists/Album Name/...`

#### `jellyfin.py`
- **Function**: Docker Compose management, plugin setup, library scanning
- **Key functions**:
  - `ensure_docker_compose(config: LibraryConfig)` — write docker-compose.yml
  - `start_jellyfin(config: LibraryConfig)` — docker compose up -d
  - `install_lyrics_plugin(config: LibraryConfig)` — API call to install plugin
  - `trigger_library_scan(config: LibraryConfig)` — API call
- **Docker Image**: `jellyfin/jellyfin:latest`
- **Plugin Repo**: `https://raw.githubusercontent.com/Felitendo/jellyfin-plugin-lyrics/master/manifest.json`
- **Ports**: 8096 (HTTP)

#### `console.py`
- **Function**: Rich-based TUI for progress display
- **Dependencies**: `rich`
- **Components**: Progress bars, status panels, file count stats, spinner

#### `bootstrap.py` (main entry)
```python
def main():
    # argparse: source_dir, output_dir, --jellyfin-data, --move, --skip-fingerprint, etc.
    # 1. Discover all MP3 files (recursive)
    # 2. Fingerprint each file
    # 3. Lookup AcoustID -> MusicBrainz metadata
    # 4. Download lyrics from lrclib.net
    # 5. Download album art, embed metadata
    # 6. Restructure into Artist/Album/ format
    # 7. Write docker-compose.yml, start Jellyfin
    # 8. Install lyrics plugin, trigger scan
```

### Dependencies (pyproject.toml)
```toml
dependencies = [
    "mutagen>=1.47",
    "pyacoustid>=1.3",
    "musicbrainzngs>=0.7",
    "requests>=2.31",
    "rich>=13.0",
    "pillow>=10.0",
]
```

---

## Part 2: bumblebee/

### Purpose
Interactive "speak like Bumblebee" engine. Search your music library by lyrics, find the exact line, play or export audio snippets. Uses the LRC files and MP3s from Part 1.

### Architecture
```
bumblebee/
├── pyproject.toml              # uv project
├── uv.lock
├── README.md
├── bumblebee-cli.py            # CLI entry point
├── bumblebee/
│   ├── __init__.py
│   ├── __main__.py
│   ├── search.py               # Full-text lyric search engine
│   ├── lrc_parser.py           # LRC file parser (timestamps -> lyrics)
│   ├── audio.py                # pydub-based audio slicing + playback
│   ├── db.py                   # SQLite FTS index builder + querier
│   ├── tui.py                  # Rich-based interactive TUI
│   ├── models.py               # dataclasses
│   └── utils.py
└── web/                        # Vite/React/Tailwind web app
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── types.ts
        ├── components/
        │   ├── SearchBar.tsx
        │   ├── ResultsList.tsx
        │   ├── LyricViewer.tsx
        │   ├── AudioPlayer.tsx
        │   ├── SnippetExporter.tsx
        │   └── Navbar.tsx
        └── hooks/
            ├── useAudio.ts
            └── useSearch.ts
```

### Core Data Models

```python
# models.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class LyricLine:
    timestamp_ms: int       # e.g., 12340 for 00:12.340
    text: str
    
    @property
    def timestamp_str(self) -> str:
        minutes = self.timestamp_ms // 60000
        seconds = (self.timestamp_ms % 60000) // 1000
        centis = (self.timestamp_ms % 1000) // 10
        return f"{minutes:02d}:{seconds:02d}.{centis:02d}"

@dataclass
class Song:
    id: str                 # sha256 of file path
    file_path: Path
    title: str
    artist: str
    album: str
    duration_ms: int
    lrc_path: Optional[Path]
    
@dataclass
class Match:
    song: Song
    matched_line: LyricLine
    context_before: list[LyricLine]  # 2 lines before
    context_after: list[LyricLine]   # 2 lines after
    match_score: float               # 0.0 - 1.0
```

### Module Specifications

#### `lrc_parser.py`
- **Function**: Parse `.lrc` files into structured LyricLine objects
- **Format**: `[mm:ss.xx]Lyric text` or `[mm:ss.xxx]` (3-digit centis)
- **Key functions**:
  - `parse_lrc(path: Path) -> list[LyricLine]`
  - `get_line_at_timestamp(lines: list[LyricLine], ts_ms: int) -> Optional[LyricLine]`
  - `timestamp_to_ms(ts: str) -> int` — `[01:23.45]` -> 83450

#### `db.py`
- **Function**: SQLite FTS5 full-text search index
- **Key functions**:
  - `build_index(library_paths: list[Path])` — scan all LRC files, populate FTS
  - `search(query: str, limit: int = 20) -> list[Match]` — FTS query
  - `get_song_lyrics(song_id: str) -> list[LyricLine]`
- **Schema**:
  ```sql
  CREATE VIRTUAL TABLE lyrics_fts USING fts5(
      lyric_text, artist, title, album, song_id
  );
  CREATE TABLE songs (
      id TEXT PRIMARY KEY,
      path TEXT, title TEXT, artist TEXT, 
      album TEXT, duration_ms INT
  );
  ```

#### `search.py`
- **Function**: Fuzzy lyric search with fallbacks
- **Dependencies**: `rapidfuzz` (faster than thefuzz)
- **Key functions**:
  - `search(query: str, db_path: Path) -> list[Match]`
  - `search_with_fallbacks(query: str, db_path: Path) -> list[Match]`
    1. Try exact FTS match
    2. Try fuzzy match on individual lines (rapidfuzz.partial_ratio)
    3. Try word-by-word narrowing (match any word, score by coverage)
    4. Return best matches sorted by score
- **Scoring**: Combines FTS rank + fuzzy ratio + word coverage

#### `audio.py`
- **Function**: Audio snippet extraction and playback
- **Dependencies**: `pydub`, `ffmpeg` (system dependency)
- **Key functions**:
  - `play_snippet(file_path: Path, start_ms: int, end_ms: int)` — playback
  - `export_snippet(file_path: Path, start_ms: int, end_ms: int, output: Path)` — MP3 export
  - `get_preview_path(file_path: Path) -> Path` — cached preview
- **Playback**: Uses `pydub.playback` (simpleaudio/pyaudio) for CLI
- **Export**: pydub `.export(format="mp3")` with proper bitrate

#### `tui.py`
- **Function**: Rich interactive terminal UI
- **Dependencies**: `rich`, `textual` (optional upgrade)
- **Screens**:
  1. **Search**: Input prompt for lyric query
  2. **Results**: Table with Song, Artist, Matched Line, Score
  3. **Lyric View**: Full lyrics with line numbers, highlight match
  4. **Action Menu**: Play snippet / Export snippet / Select range
- **Interactive flow**:
  ```
  > Enter lyrics to search: gonna be okay
  
  Results:
  #  Song                    Artist       Matched Line              Score
  ─────────────────────────────────────────────────────────────────────────
  1  Just Dance              Lady Gaga    "Gonna be okay"           98%
  2  Poker Face              Lady Gaga    "...gonna be alright..."  72%
  
  > Select result (number): 1
  
  Just Dance (feat. Colby O'Donis) — Lady Gaga
  ─────────────────────────────────────────────────
   38  [01:23.45]  Gonna be okay
   39  [01:25.12]  Da-da-da-dance, dance, dance
   40  [01:28.00]  Just, j-j-just dance
  
  > Select line number or range (e.g., 38 or 38-40): 38-39
  
  [P]lay snippet  |  [E]xport MP3  |  [B]ack  |  [Q]uit
  > Action: e
  > Export filename [bumblebee_snippet.mp3]: 
  ✓ Exported: ./bumblebee_snippet.mp3 (3.2s, 128kbps)
  ```

### Web UI (React + Vite + Tailwind)

#### Components

**`SearchBar.tsx`**
- Large centered input with autocomplete
- Debounced 300ms search
- History dropdown

**`ResultsList.tsx`**
- Expandable cards per result
- Shows matched line + context
- Click to expand full lyrics

**`LyricViewer.tsx`**
- Full lyric display with line numbers
- Matched line highlighted in amber
- Click line to set start, shift+click to set end
- Visual range indicator

**`AudioPlayer.tsx`**
- HTML5 `<audio>` element with custom controls
- Waveform visualization (Web Audio API + Canvas)
- Playhead synced to lyrics (auto-scroll)
- Play selected range only

**`SnippetExporter.tsx`**
- Export dialog: filename, quality (128/192/320 kbps)
- Progress indicator
- Download link on completion

#### Web API Integration
- **Backend**: The web UI communicates with a local Python FastAPI server (or uses the CLI as a subprocess)
- **Endpoints**:
  - `GET /api/search?q={query}` -> list of matches
  - `GET /api/song/{id}/lyrics` -> full lyrics
  - `POST /api/play` -> stream audio snippet
  - `POST /api/export` -> download MP3 snippet

### Dependencies

**CLI/Python:**
```toml
dependencies = [
    "pydub>=0.25",
    "rich>=13.0",
    "rapidfuzz>=3.0",
    "requests>=2.31",
    "fastapi>=0.100",      # for web API server
    "uvicorn>=0.23",       # ASGI server
]
```

**Web:**
```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",
    "tailwindcss": "^3.4.19",
    "wavesurfer.js": "^7.0.0",
    "lucide-react": "^0.400.0"
  },
  "devDependencies": {
    "vite": "^7.2.4",
    "typescript": "^5.3.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0"
  }
}
```

---

## Workflows

### Workflow 1: Fresh User (Bootstrap + Bumblebee)
```bash
# 1. Install uv (one-liner)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone bumblebee
git clone https://github.com/CommanderTurtle/bumblebee bumblebee
cd bumblebee

# 3. Run bootstrap — organizes MP3s, sets up Jellyfin
uv run bumblebee-bootstrap/bootstrap.py \
  --source ~/Downloads/my_mp3s \
  --output ~/Music/Library \
  --with-jellyfin

# 4. Jellyfin is now running at http://localhost:8096
#    Lyrics plugin installed, library scanned

# 5. Run Bumblebee CLI
uv run bumblebee/bumblebee-cli.py \
  --library ~/Music/Library

# 6. Or run Bumblebee Web UI
uv run --package fastapi uvicorn bumblebee.web_api:app --port 8000
cd bumblebee/web && npm install && npm run dev
# Open http://localhost:5173
```

### Workflow 2: Existing Jellyfin User (Bumblebee only)
```bash
# Skip bootstrap, just point to existing library with LRC files
uv run bumblebee/bumblebee-cli.py --library ~/Music
```

### Workflow 3: "Speak Like Bumblebee" Session
```
> Search lyrics: gonna be okay

  Result: Just Dance — Lady Gaga
  Line 38: "Gonna be okay" (01:23)
  Line 39: "Da-da-da-dance, dance, dance" (01:25)

> Select range: 38-39
> Action: export
> Filename: gonna_be_okay.mp3

  Exported: 2.1s snippet at ~/bumblebee_exports/gonna_be_okay.mp3

# Chain multiple snippets into a message:
> Chain mode: gonna be okay + don't stop believin + we are the champions
  [exports concatenated MP3 with crossfade]
```

---

## Design Principles

1. **Portability**: `uv` for Python (no pip, no venv activation), `bun` optional for web
2. **Minimal commands**: Every workflow is ≤3 commands
3. **Fingerprint-first**: Never rely on existing metadata for identification
4. **Rich interactive UI**: Both CLI (Rich TUI) and Web (React) are first-class
5. **Professional export**: High-quality MP3 exports with proper encoding
