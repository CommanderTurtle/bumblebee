"""FastAPI backend for the Bumblebee Web UI.

Provides REST endpoints for:
- Searching lyrics
- Getting song lyrics
- Streaming audio (full or snippet)
- Exporting snippets as MP3
"""

from __future__ import annotations

import io
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydub import AudioSegment

from bumblebee.audio import extract_snippet, export_snippet, load_audio
from bumblebee.db import build_index, get_song, get_song_lyrics
from bumblebee.models import LyricLine, Match, Song
from bumblebee.search import search as search_engine

# Global state (initialized at startup)
_db_path: Optional[Path] = None
_library_path: Optional[Path] = None
_export_dir: Optional[Path] = None


def _get_env_path(var_name: str, default: Path) -> Path:
    """Get a path from environment variable or default."""
    value = os.environ.get(var_name)
    if value:
        return Path(value).expanduser().resolve()
    return default


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: startup and shutdown."""
    global _db_path, _library_path, _export_dir

    # Startup: resolve paths
    _library_path = _get_env_path("BUMBLEBEE_LIBRARY", Path.home() / "Music")
    _db_path = _get_env_path(
        "BUMBLEBEE_DB", _library_path / ".bumblebee.db"
    )
    _export_dir = _get_env_path(
        "BUMBLEBEE_EXPORT_DIR", Path.cwd() / "bumblebee_exports"
    )
    _export_dir.mkdir(parents=True, exist_ok=True)

    # Build index if needed
    if not _db_path.exists() and _library_path.exists():
        build_index(_db_path, [_library_path])

    yield

    # Shutdown: cleanup
    pass


app = FastAPI(
    title="Bumblebee API",
    description="Lyric-based song search and audio snippet API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic response models ──────────────────────────────────────────

from pydantic import BaseModel


class LyricLineResponse(BaseModel):
    timestamp_ms: int
    text: str
    timestamp_str: str


class SongResponse(BaseModel):
    id: str
    title: str
    artist: str
    album: str
    duration_ms: int
    lrc_path: Optional[str]


class MatchResponse(BaseModel):
    song: SongResponse
    matched_line: LyricLineResponse
    context_before: list[LyricLineResponse]
    context_after: list[LyricLineResponse]
    match_score: float
    match_type: str
    score_percent: str


class SearchResponse(BaseModel):
    query: str
    count: int
    elapsed_ms: float
    results: list[MatchResponse]


class LyricsResponse(BaseModel):
    song: SongResponse
    lyrics: list[LyricLineResponse]
    count: int


class ExportRequest(BaseModel):
    song_id: str
    start_ms: int
    end_ms: int
    filename: str = "snippet.mp3"
    bitrate: str = "192k"


class ExportResponse(BaseModel):
    success: bool
    filename: str
    path: str
    duration_ms: int
    bitrate: str


def _lyric_to_response(line: LyricLine) -> LyricLineResponse:
    return LyricLineResponse(
        timestamp_ms=line.timestamp_ms,
        text=line.text,
        timestamp_str=line.timestamp_str,
    )


def _song_to_response(song: Song) -> SongResponse:
    return SongResponse(
        id=song.id,
        title=song.title,
        artist=song.artist,
        album=song.album,
        duration_ms=song.duration_ms,
        lrc_path=str(song.lrc_path) if song.lrc_path else None,
    )


def _match_to_response(match: Match) -> MatchResponse:
    return MatchResponse(
        song=_song_to_response(match.song),
        matched_line=_lyric_to_response(match.matched_line),
        context_before=[_lyric_to_response(l) for l in match.context_before],
        context_after=[_lyric_to_response(l) for l in match.context_after],
        match_score=match.match_score,
        match_type=match.match_type,
        score_percent=match.score_percent,
    )


# ── API Endpoints ─────────────────────────────────────────────────────

@app.get("/")
def root() -> dict:
    """Root endpoint - API info."""
    return {
        "name": "Bumblebee API",
        "version": "1.0.0",
        "description": "Speak Through Song - Lyric search and audio snippets",
        "endpoints": {
            "search": "/api/search?q={query}",
            "lyrics": "/api/song/{song_id}/lyrics",
            "audio": "/api/song/{song_id}/audio?start={ms}&end={ms}",
            "export": "POST /api/export",
        },
    }


@app.get("/api/search")
def api_search(
    q: str = Query(..., description="Search query (lyrics)"),
    limit: int = Query(20, ge=1, le=100),
) -> SearchResponse:
    """Search lyrics and return matches.

    Uses multi-strategy search: FTS5 -> fuzzy -> word-by-word fallback.
    """
    if _db_path is None or not _db_path.exists():
        raise HTTPException(status_code=500, detail="Search index not available")

    import time

    start = time.time()
    results = search_engine(_db_path, q, limit=limit)
    elapsed = (time.time() - start) * 1000  # ms

    return SearchResponse(
        query=q,
        count=len(results),
        elapsed_ms=round(elapsed, 2),
        results=[_match_to_response(m) for m in results],
    )


@app.get("/api/song/{song_id}/lyrics")
def api_lyrics(song_id: str) -> LyricsResponse:
    """Get full lyrics for a song."""
    if _db_path is None or not _db_path.exists():
        raise HTTPException(status_code=500, detail="Search index not available")

    song = get_song(_db_path, song_id)
    if not song:
        raise HTTPException(status_code=404, detail=f"Song not found: {song_id}")

    lyrics = get_song_lyrics(_db_path, song_id)

    return LyricsResponse(
        song=_song_to_response(song),
        lyrics=[_lyric_to_response(l) for l in lyrics],
        count=len(lyrics),
    )


@app.get("/api/song/{song_id}/audio")
def api_audio(
    song_id: str,
    start: int = 0,
    end: Optional[int] = None,
) -> StreamingResponse:
    """Stream audio (full song or snippet).

    Args:
        song_id: The song ID.
        start: Start time in milliseconds.
        end: End time in milliseconds (None = end of song).
    """
    if _db_path is None or not _db_path.exists():
        raise HTTPException(status_code=500, detail="Search index not available")

    song = get_song(_db_path, song_id)
    if not song:
        raise HTTPException(status_code=404, detail=f"Song not found: {song_id}")

    if not song.file_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Audio file not found: {song.file_path}"
        )

    try:
        if start == 0 and end is None:
            # Full file - stream directly
            return FileResponse(
                path=song.file_path,
                media_type="audio/mpeg",
                filename=song.file_path.name,
            )

        # Extract snippet
        snippet = extract_snippet(song.file_path, start, end or (start + 3000))

        # Export to buffer
        buf = io.BytesIO()
        snippet.export(buf, format="mp3", bitrate="192k")
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="audio/mpeg",
            headers={"Content-Disposition": 'inline; filename="snippet.mp3"'},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing error: {e}")


@app.post("/api/export")
def api_export(req: ExportRequest) -> ExportResponse:
    """Export an audio snippet as MP3 and return the file.

    Args:
        req: Export request with song_id, start_ms, end_ms, filename, and bitrate.
    """
    if _db_path is None or not _db_path.exists():
        raise HTTPException(status_code=500, detail="Search index not available")

    if _export_dir is None:
        raise HTTPException(status_code=500, detail="Export directory not configured")

    song = get_song(_db_path, req.song_id)
    if not song:
        raise HTTPException(status_code=404, detail=f"Song not found: {req.song_id}")

    if not song.file_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Audio file not found: {song.file_path}"
        )

    # Ensure .mp3 extension
    filename = req.filename
    if not filename.endswith(".mp3"):
        filename += ".mp3"

    output_path = _export_dir / filename

    try:
        export_snippet(
            song.file_path, req.start_ms, req.end_ms, output_path, bitrate=req.bitrate
        )

        return ExportResponse(
            success=True,
            filename=filename,
            path=str(output_path),
            duration_ms=req.end_ms - req.start_ms,
            bitrate=req.bitrate,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


@app.get("/api/export/download/{filename}")
def api_export_download(filename: str) -> FileResponse:
    """Download an exported snippet file."""
    if _export_dir is None:
        raise HTTPException(status_code=500, detail="Export directory not configured")

    file_path = _export_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename,
    )


@app.get("/api/songs")
def api_songs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    """List all songs in the library."""
    if _db_path is None or not _db_path.exists():
        raise HTTPException(status_code=500, detail="Search index not available")

    import sqlite3

    conn = sqlite3.connect(str(_db_path))
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.execute(
            "SELECT * FROM songs LIMIT ? OFFSET ?", (limit, offset)
        )
        rows = cursor.fetchall()

        songs = []
        for row in rows:
            songs.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "artist": row["artist"],
                    "album": row["album"],
                    "duration_ms": row["duration_ms"],
                    "path": row["path"],
                    "lrc_path": row["lrc_path"],
                }
            )

        # Get total count
        count_row = conn.execute("SELECT COUNT(*) FROM songs").fetchone()
        total = count_row[0] if count_row else 0

        return {
            "songs": songs,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn

    # Run with: uvicorn bumblebee.web_api:app --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
