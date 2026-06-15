---
name: bumblebee-voice
description: >
  Bumblebee Voice — Communicate through song snippets. Use after completing tasks,
  writing summaries, or whenever the user asks for a 'Bumblebee voice' or 'speak like
  Bumblebee'. Searches the user's music library for lyrics that match the context of
  what was accomplished, then presents the result as a song snippet 'voice line'.
  Requires the Bumblebee music library (with .lrc files) to be set up. If no library
  exists, falls back to a curated set of iconic voice lines.
license: AGPL-3.0
compatibility: python>=3.10, bumblebee-engine
metadata:
  version: 1.0.0
  author: bumblebee-project
  category: fun/creative
---

# Bumblebee Voice

> *When words aren't enough... speak through song.*

This skill lets you — the Pi coding agent — communicate through song snippets
just like Bumblebee from Transformers. After completing a task, instead of a
boring text summary, you can find a lyric that captures the spirit of what was
accomplished and present it as your "voice line."

## When to Use

- **After completing any task**: Search for a lyric that matches the mood/outcome
- **When the user asks**: "Speak like Bumblebee", "Give me a voice line", "Bumblebee summary"
- **On success**: Find celebratory lyrics ("We Are the Champions", "Gonna be okay")
- **On challenge**: Find persevering lyrics ("Don't Stop Believin'", "Eye of the Tiger")
- **On completion**: Find closing lyrics ("It's the end of the world as we know it")
- **For fun**: Any time the user wants a musical summary

## Setup

### First-time Setup (run once)

```bash
# The Bumblebee engine must be available
# It's expected at the project root (relative to this skill)
cd {baseDir}/../../../bumblebee
uv sync

# Ensure the search index exists
uv run -m bumblebee --library ~/Music --reindex
```

### Environment

- `BUMBLEBEE_LIBRARY`: Path to the organized music library (default: `~/Music`)
- `BUMBLEBEE_DB`: Path to the SQLite search index (default: `{library}/.bumblebee.db`)

## Workflow

### Step 1: Understand the Context

After completing a task, reflect on what was done. Extract 1-3 keywords that
capture the essence:

| Task Type | Keywords | Example |
|-----------|----------|---------|
| Bug fixed | "okay", "fixed", "alright" | "gonna be okay" |
| Feature added | "champion", "winner", "best" | "we are the champions" |
| Refactored | "clean", "better", "new" | "a whole new world" |
| Deployed | "alive", "living", "life" | "staying alive" |
| Completed | "end", "finish", "done" | "it's the final countdown" |
| Started | "begin", "start", "go" | "let's get it started" |
| Hard problem | "fight", "survive", "strong" | "eye of the tiger" |
| Collaboration | "together", "friend", "team" | "with a little help from my friends" |

### Step 2: Find the Voice Line

Run the voice search script:

```bash
./scripts/voice.py "{context keywords}"
```

This searches the Bumblebee lyric database and returns the best matches.

**Output format:**
```json
{
  "voice_line": "Gonna be okay",
  "song": "Just Dance",
  "artist": "Lady Gaga",
  "timestamp": "01:23.45",
  "confidence": 0.98,
  "alternatives": [...]
}
```

### Step 3: Present the Voice Line

Present the result to the user in this format:

```
*activates vocal synthesizer...*

🐝 Bumblebee says: "Gonna be okay"
   — Just Dance, Lady Gaga (01:23)

*deactivates vocal synthesizer*
```

If the user wants to hear it, offer to export:

```bash
./scripts/voice-line.py export "Just Dance" "01:23.45" "01:25.00"
```

### Step 4: (Optional) Export as MP3

If the user wants the actual audio snippet:

```bash
# Export the voice line as MP3
./scripts/voice-line.py export --song "{song}" --start "{timestamp}" --duration 5
```

This creates `bumblebee_voice_line.mp3` that the user can play.

## Fallback Mode (No Music Library)

If the user doesn't have a Bumblebee music library set up, use the built-in
fallback script which has a curated database of iconic voice lines:

```bash
./scripts/voice.py --fallback "{context}"
```

This uses 50+ pre-selected iconic lyrics covering common coding scenarios.

## Voice Line Categories

See [references/examples.md](references/examples.md) for a full catalog of
categorized voice lines and when to use them.

## Prompt Templates

See [assets/prompts.md](assets/prompts.md) for reusable prompt templates that
can be used with Pi's `/template` system.

## Integration with Task Completion

For automatic voice lines after every task, add to the project's `.pi/settings.json`:

```json
{
  "skills": {
    "autoTrigger": ["bumblebee-voice"]
  }
}
```

Or simply ask the user: *"Want me to give you a Bumblebee voice summary of
what we just did?"*
