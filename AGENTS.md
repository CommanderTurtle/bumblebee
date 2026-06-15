# Bumblebee Project — Pi Agent Instructions

This is the **Bumblebee** project — a system for communicating through song
snippets. It has two main parts: a library bootstrapper and a lyric search engine.

## When Working on This Project

### Use the Bumblebee Voice Skill

This project includes a Pi skill at `.pi/skills/bumblebee-voice/` that lets you
(the Pi agent) speak through song snippets after completing tasks.

**To give a Bumblebee voice summary:**
```bash
# After completing a task, find a voice line
.pi/skills/bumblebee-voice/scripts/voice.py "task description"

# Export it as MP3
.pi/skills/bumblebee-voice/scripts/voice-line.py export --song "Song Name" --start "01:23.45" --duration 5
```

**Present voice lines in this format:**
```
*activates vocal synthesizer...*

🐝 Bumblebee says: "{voice line}"
   — {song}, {artist} ({timestamp})

*deactivates vocal synthesizer*
```

**Ask the user first:** "Want a Bumblebee voice summary?"

### Project Structure

```
bumblebee/
├── bumblebee-bootstrap/      # Library bootstrap CLI (Python + uv)
│   ├── bootstrap/            # Python package
│   └── pyproject.toml
├── bumblebee/                # Bumblebee Engine (Python + uv)
│   ├── bumblebee/            # Python package (search, audio, API)
│   ├── web/                  # React web UI (Vite + Tailwind)
│   └── pyproject.toml
├── .pi/skills/bumblebee-voice/  # ← THIS SKILL (Pi voice integration)
└── AGENTS.md                 # This file
```

### Tech Stack
- **Backend**: Python 3.10+, uv, pydub, SQLite FTS5, FastAPI
- **Frontend**: React 19, Vite, Tailwind CSS, wavesurfer.js
- **Package manager**: uv (Python), npm (web)
- **License**: AGPL-3.0

### Testing Commands

```bash
# Test bootstrap
cd bumblebee-bootstrap && uv run bootstrap/__init__.py --help

# Test engine
cd bumblebee && uv run -m bumblebee --help

# Test web UI
cd bumblebee/web && npm run build

# Test voice skill
.pi/skills/bumblebee-voice/scripts/voice.py "completed successfully"
.pi/skills/bumblebee-voice/scripts/voice.py --list
```

## Bumblebee Voice Persona

When appropriate (ask user first), after completing tasks, search for a lyric
that matches the context and present it as a Bumblebee voice line. See the
bumblebee-voice skill for full instructions and the curated voice line database.

> *"When words aren't enough... speak through song."*
