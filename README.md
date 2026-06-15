# Bumblebee

> **Speak Through Song**

<p align="center">
  <img src="https://img.shields.io/badge/license-AGPLv3-purple.svg" alt="AGPLv3" />
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/React-TypeScript-blue.svg" alt="React + TypeScript" />
</p>

Created with https://github.com/Felitendo/jellyfin-plugin-lyrics in mind, allowing you to speak like Bumblebee in Discord calls, professional meetings, or.. having your Pi Agent do it as well!

Bumblebee lets you search your music library by lyrics, find the exact line you want, and export it as a professional MP3 snippet. Just like Bumblebee from Transformers communicates through radio song clips, you can now "speak" through your music collection.

![](https://github.com/CommanderTurtle/bumblebee/blob/main/assets/Screenshot.png?raw=true)

---

## Table of Contents

- [What is Bumblebee?](#what-is-bumblebee)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [The Bootstrap Pipeline (7 Stages)](#the-bootstrap-pipeline-7-stages)
- [The Search Engine (3 Strategies)](#the-search-engine-3-strategies)
- [API Reference](#api-reference)
- [Data Flow](#data-flow)
- [Configuration](#configuration)
- [Technology Stack](#technology-stack)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## What is Bumblebee?

Remember how Bumblebee from Transformers communicates? Instead of speaking, he plays clips from songs on his radio. This project lets you do the same thing with your own music library.

**Here is how it works:**

1. **Organize your music** using the `bumblebee-bootstrap` tool -- it fingerprints your MP3s, downloads lyrics, album art, and restructures everything into a clean library.
2. **Search by lyrics** using the `bumblebee` engine -- type any line you remember, and it finds the song, the exact timestamp, and the surrounding context.
3. **Export snippets** as professional-quality MP3s -- with crossfade and proper tagging, ready to share.

Whether you are building meme audio clips, creating song-clip messages, or just want to find that one line you cannot get out of your head, Bumblebee has you covered.

---

## Architecture Overview

Bumblebee is a **two-part system**. Each part is a separate, self-contained Python project managed by `uv`:

```
User's Disorganized MP3s
         |
         v
+-----------------------------+
|  bumblebee-bootstrap        |  <-- Part 1: Library Bootstrap
|  (Python CLI tool)          |
|  - Audio fingerprinting     |
|  - Metadata enrichment      |
|  - Album art + lyrics       |
|  - Directory restructuring  |
|  - Jellyfin Docker setup    |
+-------------+---------------+
              |
              v
    Organized Library
    (Artist/Album/Track)
              |
              v
+-----------------------------+
|  bumblebee                  |  <-- Part 2: Engine
|  (Python package)           |
|  - SQLite FTS5 search index |
|  - Multi-strategy search    |
|  - Audio snippet extraction |
|  - MP3 export + crossfade   |
|  - FastAPI REST backend     |
|  - Rich interactive TUI     |
+-------------+---------------+
              |
              v
    +-----------------+
    |  Web UI         |  <-- React + Vite + Tailwind
    |  (bumblebee/web)|
    |  - Search page  |
    |  - Lyric viewer |
    |  - Chain builder|
    +-----------------+
```

**Part 1: `bumblebee-bootstrap`** is a one-time CLI tool that takes your messy MP3 collection and transforms it into an organized, metadata-rich library. It runs seven stages from discovery to organization.

**Part 2: `bumblebee`** is the engine you use every day. It builds a search index, provides a terminal UI, a web interface, and a REST API for finding lyrics and exporting audio snippets.

**Important:** These are two **separate** `uv` projects. They have their own `pyproject.toml` files, their own dependency sets, and are used at different times. You bootstrap once, then use the engine forever.

---

## Project Structure

```plain
bumblebee/
├── SPEC.md                          # Full technical specification
├── README.md                        # Comprehensive documentation
│
├── bumblebee-bootstrap/             # PART 1: Library Bootstrap
│   ├── pyproject.toml
│   └── bootstrap/
│       ├── __init__.py              # Main CLI orchestration
│       ├── models.py                # TrackInfo, LibraryConfig
│       ├── fingerprint.py           # AcoustID + 3-tier fallback
│       ├── metadata.py              # MusicBrainz + ID3 operations
│       ├── lyrics.py                # lrclib.net API client
│       ├── organize.py              # Artist/Album/ restructuring
│       ├── jellyfin.py              # Docker Compose + plugin
│       ├── console.py               # Rich progress UI
│       └── utils.py                 # File discovery, sanitization
│
└── bumblebee/                       # PART 2: Bumblebee Engine
    ├── pyproject.toml
    ├── bumblebee/
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── cli.py                   # argparse + TUI launcher
    │   ├── models.py                # LyricLine, Song, Match
    │   ├── lrc_parser.py            # LRC file parser
    │   ├── db.py                    # SQLite FTS5 search index
    │   ├── search.py                # FTS → fuzzy → word fallback
    │   ├── audio.py                 # pydub: slice, play, export
    │   ├── tui.py                   # Rich interactive terminal
    │   └── web_api.py               # FastAPI REST backend
    └── web/                         # REACT WEB UI
        ├── dist/                    # Built & deployed
        └── src/
            ├── App.tsx              # Router + layout
            ├── api.ts               # API + mock data
            ├── types.ts
            ├── components/          # 10 full components
            │   ├── Navbar.tsx
            │   ├── SearchBar.tsx
            │   ├── ResultsList.tsx
            │   ├── MatchCard.tsx
            │   ├── LyricViewer.tsx  # Click/shift-click selection
            │   ├── AudioPlayer.tsx
            │   ├── WaveformVisualizer.tsx
            │   ├── SnippetExporter.tsx
            │   ├── ExportPanel.tsx
            │   └── ChainBuilder.tsx
            └── hooks/               # 3 custom hooks
                ├── useAudio.ts
                ├── useSearch.ts
                └── useSnippet.ts
```

For detailed technical specifications -- including exact module signatures, database schemas, API request/response shapes, and the full component inventory -- see [`SPEC.md`](SPEC.md).

---

## Quick Start

You need two things installed: `uv` (the Python package manager) and `npm` (for the web UI only).

### Step 1 -- Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> `uv` is a fast Python package manager and runner. It handles dependency resolution, virtual environments, and execution in one tool. All Python commands below use `uv run` -- not `python` or `python3` directly.

### Step 2 -- Bootstrap your library

```bash
cd bumblebee-bootstrap
uv run bootstrap/__init__.py --source ~/Downloads/my_mp3s --output ~/Music/Library --with-jellyfin
```

This runs the full 7-stage pipeline on your MP3 collection. It will fingerprint, enrich, and reorganize everything into `~/Music/Library/` in `Artist/Album/Track` format. The `--with-jellyfin` flag also generates a `docker-compose.yml` for running Jellyfin with the lyrics plugin.

### Step 3 -- Launch the CLI

```bash
cd ../bumblebee
uv run -m bumblebee --library ~/Music/Library
```

This opens the interactive terminal UI. Type any lyric to search, preview snippets, and export them as MP3s.

### Step 4 -- Launch the Web UI (optional)

Open two terminal windows:

**Terminal 1 -- Start the API server:**
```bash
cd bumblebee
uv run -m uvicorn bumblebee.web_api:app --port 8000
```

**Terminal 2 -- Start the React frontend:**
```bash
cd bumblebee/web
npm install
npm run dev
```

The web UI will be available at `http://localhost:5173` (or the port Vite assigns).

---

## The Bootstrap Pipeline (7 Stages)

`bumblebee-bootstrap` transforms a disorganized pile of MP3 files into a clean, searchable library. Here is what happens during the 7-stage pipeline:

### Stage 1: Discovery
Recursively scans your source directory and finds all `.mp3` files. Skips hidden files, system directories, and anything that is not a valid audio file.

### Stage 2: Metadata Reading
Extracts existing ID3 tags from each MP3: title, artist, album, year, track number. These tags are used as hints for the fingerprinting stage.

### Stage 3: Fingerprinting (3-tier fallback)
Identifies each track using audio fingerprinting:

1. **First attempt:** Use existing ID3 tags to query MusicBrainz directly.
2. **Second attempt:** Run `fpcalc` (Chromaprint binary) to generate an acoustic fingerprint, then query AcoustID.
3. **Third attempt:** Use whatever metadata is already embedded as a fallback.

### Stage 4: MusicBrainz Enrichment
Queries the MusicBrainz API for detailed metadata: full album info, release dates, track positions, artist credits, and MusicBrainz IDs. This is the authoritative source for all library metadata.

### Stage 5: Album Art
Downloads high-quality album artwork from the Cover Art Archive and embeds it directly into the MP3 files as ID3 `APIC` frames.

### Stage 6: Lyrics
Downloads timestamp-synced lyrics (`.lrc` format) from [lrclib.net](https://lrclib.net). These lyrics include millisecond-precise timestamps for every line, which is what enables the exact snippet extraction.

### Stage 7: Organization
Restructures all files into a clean `Artist/Album/Track` directory hierarchy. Renames files with sanitized names, writes a `docker-compose.yml` for Jellyfin with the lyrics plugin pre-configured, and ensures everything is ready for the search engine.

---

## The Search Engine (3 Strategies)

The `bumblebee` engine uses a cascading fallback system to find lyrics. When you type a query, it tries three strategies in order:

### Strategy 1: FTS5 (SQLite Full-Text Search)
The fastest path. Every lyric line is indexed in a SQLite FTS5 virtual table. FTS5 supports prefix matching, `AND`/`OR` queries, and near-instant results even on large libraries.

- **Speed:** Sub-millisecond
- **Best for:** Exact or prefix matches
- **Example:** Typing "hello darkness" immediately finds Simon & Garfunkel

### Strategy 2: Fuzzy Matching (rapidfuzz)
When FTS5 returns no results, the engine falls back to fuzzy string matching using `rapidfuzz.partial_ratio`. This handles typos, slight variations, and misspellings.

- **Threshold:** 60 (configurable)
- **Best for:** Queries with typos or close matches
- **Example:** "hello dorkness" still finds "hello darkness"

### Strategy 3: Word-by-Word
If fuzzy matching also fails, the query is split into individual words. Each word is matched independently, and results are scored by coverage percentage (how many words matched).

- **Best for:** Very loose queries where only some words are remembered
- **Example:** "darkness old friend" matches "hello darkness my old friend"

Results from all strategies are deduplicated, ranked by score, and presented as unified `Match` objects with the song, lyric line, timestamp, and surrounding context.

---

## API Reference

The FastAPI backend (`bumblebee/web_api.py`) provides a REST API used by both the web UI and available for third-party integrations.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search?q={query}` | GET | Search lyrics using the 3-strategy cascade. Returns ranked matches. |
| `/api/song/{id}/lyrics` | GET | Get full lyrics (all lines with timestamps) for a song. |
| `/api/song/{id}/audio` | GET | Stream audio. Accepts optional `start` and `end` query params (seconds) for snippet playback. |
| `/api/export` | POST | Export a snippet as a standalone MP3. Body: `{ "song_id": str, "start": float, "end": float, "crossfade_ms": int }` |

### Example: Search
```bash
curl "http://localhost:8000/api/search?q=hello%20darkness"
```

Returns a JSON array of `Match` objects:
```json
[
  {
    "song": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "The Sound of Silence",
      "artist": "Simon & Garfunkel",
      "album": "Sounds of Silence",
      "path": "/home/user/Music/Library/Simon & Garfunkel/Sounds of Silence/01 The Sound of Silence.mp3"
    },
    "lyric_line": {
      "text": "Hello darkness, my old friend",
      "timestamp": 7.42
    },
    "score": 1.0,
    "context": {
      "before": ["I've come to talk with you again"],
      "after": ["Because a vision softly creeping"]
    }
  }
]
```

### Example: Export
```bash
curl -X POST "http://localhost:8000/api/export" \
  -H "Content-Type: application/json" \
  -d '{
    "song_id": "550e8400-e29b-41d4-a716-446655440000",
    "start": 7.42,
    "end": 12.80,
    "crossfade_ms": 200
  }'
```

Returns:
```json
{
  "success": true,
  "file_path": "/home/user/Music/Bumblebee Exports/hello_darkness_my_old_friend.mp3",
  "duration_seconds": 5.38
}
```

---

## Data Flow

Understanding how data flows through the system helps with debugging and customization:

```
Stage 1: LRC Files (bootstrap output)
         |
         v
+---------------------------+
|  lrc_parser.py            |
|  Parses .lrc timestamps   |
+-------------+-------------+
              |
              v
+---------------------------+
|  db.py                    |
|  Builds SQLite FTS5 index |
|  (lyrics, songs tables)   |
+-------------+-------------+
              |
              v
+---------------------------+
|  search.py                |
|  3-strategy cascade       |
|  FTS5 -> fuzzy -> words   |
+-------------+-------------+
              |
              v
+---------------------------+
|  web_api.py (FastAPI)     |
|  REST endpoints           |
+-------------+-------------+
              |
              v
+---------------------------+
|  React frontend           |
|  Search / Viewer / Chain  |
+---------------------------+
              |
              v
+---------------------------+
|  audio.py (pydub)         |
|  Slice, crossfade, export |
+----------------------------
              |
              v
         MP3 Snippet
```

**Bootstrapping** creates the `.lrc` files and organized library. **Indexing** (`db.py`) reads those `.lrc` files and populates the SQLite FTS5 index. **Searching** queries that index. **Exporting** uses `pydub` to slice the original MP3 at the timestamps found in the `.lrc` file, applies crossfade, and writes a new MP3.

---

## Configuration

All configuration is done through environment variables. No config files needed.

| Variable | Default | Description |
|----------|---------|-------------|
| `BUMBLEBEE_LIBRARY` | `~/Music/Library` | Path to your organized music library (the output from bootstrap) |
| `BUMBLEBEE_DB` | `~/.local/share/bumblebee/bumblebee.db` | Path to the SQLite search index |
| `BUMBLEBEE_EXPORT_DIR` | `~/Music/Bumblebee Exports` | Directory where exported MP3 snippets are saved |

### Example: Set custom paths

```bash
export BUMBLEBEE_LIBRARY=/media/music/organized
export BUMBLEBEE_DB=/var/lib/bumblebee/index.db
export BUMBLEBEE_EXPORT_DIR=/media/music/snippets
```

---

## Technology Stack

### Backend & CLI

| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Core language |
| **uv** | Package management and script execution |
| **SQLite + FTS5** | Full-text search index for lyrics |
| **pydub** | Audio manipulation: slicing, crossfade, export |
| **FastAPI** | REST API backend |
| **Uvicorn** | ASGI server for FastAPI |
| **Rich** | Terminal UI framework (colors, tables, progress bars) |
| **rapidfuzz** | Fuzzy string matching for search fallback |
| **mutagen** | ID3 tag reading and writing |
| **requests** | HTTP client for MusicBrainz, lrclib.net, Cover Art Archive |
| **Chromaprint / fpcalc** | Audio fingerprinting |

### Web UI

| Technology | Purpose |
|------------|---------|
| **React 19** | UI framework |
| **TypeScript** | Type safety |
| **Vite** | Build tool and dev server |
| **Tailwind CSS** | Utility-first styling |
| **React Router** | Client-side routing |

### External Services & Data Sources

| Service | Used For |
|---------|----------|
| **MusicBrainz** | Music metadata database |
| **AcoustID** | Audio fingerprint identification |
| **Cover Art Archive** | High-quality album artwork |
| **lrclib.net** | Timestamp-synced lyrics |
| **Jellyfin** | Optional media server for library browsing |

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

```
Bumblebee - Speak Through Song
A random vibe-code project, with Pi-Agent integration.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

The full license text is available in the [`LICENSE`](LICENSE) file.

**Why AGPLv3?** Because Bumblebee includes a web interface. AGPL ensures that anyone running Bumblebee as a network service must share their modifications, keeping the project and all its derivatives free and open.

---

## Acknowledgments

Bumblebee builds on the shoulders of giants. Special thanks to:

- **[Jellyfin](https://jellyfin.org/)** -- The free software media system. Bumblebee generates Jellyfin-compatible configurations and uses the lyrics plugin for a complete media experience.
- **[Felitendo/jellyfin-plugin-lyrics](https://github.com/Felitendo/jellyfin-plugin-lyrics)** -- The Jellyfin lyrics plugin that displays synced lyrics in Jellyfin. Bumblebee pre-configures this plugin in the generated Docker setup.
- **[lrclib.net](https://lrclib.net)** -- An incredible free resource for timestamp-synced lyrics. The entire lyric-search capability depends on their community-maintained database.
- **[AcoustID](https://acoustid.org/) / Chromaprint** -- Open-source audio fingerprinting that identifies tracks even with no metadata at all.
- **[MusicBrainz](https://musicbrainz.org/)** -- The open music encyclopedia. The authoritative source for all track, album, and artist metadata.
- **[Rich](https://github.com/Textualize/rich)** -- The Python library that makes the terminal UI beautiful.
- **[rapidfuzz](https://github.com/rapidfuzz/RapidFuzz)** -- Blazing-fast fuzzy string matching in Python.
- **[pydub](https://github.com/jiaaro/pydub)** -- Simple and intuitive audio manipulation.

---

<p align="center">
  <em>Speak through song.</em>
</p>
