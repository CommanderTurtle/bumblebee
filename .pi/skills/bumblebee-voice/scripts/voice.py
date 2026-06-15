#!/usr/bin/env python3
"""
Bumblebee Voice — Find the perfect song snippet for any context.

Usage:
    voice.py "context description"                  # Search music library
    voice.py --fallback "context description"       # Use built-in quotes
    voice.py --list                                 # List all fallback lines
    voice.py --category success                     # List by category

Environment:
    BUMBLEBEE_LIBRARY    Path to music library (default: ~/Music)
    BUMBLEBEE_DB         Path to search index (default: auto)
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# ── Curated Voice Lines (fallback when no music library) ──────────────────

VOICE_LINES: list[dict] = [
    # Success / Completion
    {"line": "Gonna be okay", "song": "Just Dance", "artist": "Lady Gaga",
     "category": "success", "keywords": ["okay", "fine", "fixed", "alright", "done"]},
    {"line": "Da-da-da-dance, dance, dance", "song": "Just Dance", "artist": "Lady Gaga",
     "category": "success", "keywords": ["dance", "celebrate", "party", "fun"]},
    {"line": "We are the champions, my friends", "song": "We Are the Champions", "artist": "Queen",
     "category": "success", "keywords": ["champion", "win", "victory", "best", "top"]},
    {"line": "And we'll keep on fighting till the end", "song": "We Are the Champions", "artist": "Queen",
     "category": "success", "keywords": ["fight", "persevere", "endure", "keep going"]},
    {"line": "Don't stop believin'", "song": "Don't Stop Believin'", "artist": "Journey",
     "category": "perseverance", "keywords": ["believe", "hope", "keep going", "don't quit"]},
    {"line": "Hold on to that feelin'", "song": "Don't Stop Believin'", "artist": "Journey",
     "category": "perseverance", "keywords": ["feel", "hold on", "remember", "stay"]},
    {"line": "Eye of the tiger", "song": "Eye of the Tiger", "artist": "Survivor",
     "category": "perseverance", "keywords": ["tiger", "fight", "strong", "survive", "tough"]},
    {"line": "Rising up to the challenge", "song": "Eye of the Tiger", "artist": "Survivor",
     "category": "perseverance", "keywords": ["challenge", "rise", "up", "overcome"]},
    {"line": "I will survive", "song": "I Will Survive", "artist": "Gloria Gaynor",
     "category": "perseverance", "keywords": ["survive", "make it", "persist", "alive"]},
    {"line": "Stayin' alive", "song": "Stayin' Alive", "artist": "Bee Gees",
     "category": "perseverance", "keywords": ["alive", "living", "life", "going"]},
    {"line": "Ah, ha, ha, ha, stayin' alive", "song": "Stayin' Alive", "artist": "Bee Gees",
     "category": "perseverance", "keywords": ["alive", "stay", "living"]},
    # Start / Begin
    {"line": "Let's get it started", "song": "Let's Get It Started", "artist": "The Black Eyed Peas",
     "category": "start", "keywords": ["start", "begin", "go", "let's", "now"]},
    {"line": "Here we go", "song": "Let's Get It Started", "artist": "The Black Eyed Peas",
     "category": "start", "keywords": ["go", "here", "start", "now"]},
    {"line": "A whole new world", "song": "A Whole New World", "artist": "Aladdin",
     "category": "start", "keywords": ["new", "world", "begin", "fresh", "start"]},
    {"line": "It's the final countdown", "song": "The Final Countdown", "artist": "Europe",
     "category": "completion", "keywords": ["final", "countdown", "end", "last", "deploy"]},
    {"line": "The show must go on", "song": "The Show Must Go On", "artist": "Queen",
     "category": "perseverance", "keywords": ["show", "go on", "continue", "keep"]},
    # Bug / Fix
    {"line": "It's gonna be alright", "song": "Three Little Birds", "artist": "Bob Marley",
     "category": "success", "keywords": ["alright", "okay", "fine", "worry", "don't worry"]},
    {"line": "Don't worry about a thing", "song": "Three Little Birds", "artist": "Bob Marley",
     "category": "success", "keywords": ["worry", "calm", "relax", "fine"]},
    {"line": "Every little thing is gonna be alright", "song": "Three Little Birds", "artist": "Bob Marley",
     "category": "success", "keywords": ["alright", "everything", "fine", "bug fixed"]},
    {"line": "I get knocked down, but I get up again", "song": "Tubthumping", "artist": "Chumbawamba",
     "category": "perseverance", "keywords": ["knocked down", "get up", "resilient", "fail"]},
    {"line": "You're never gonna keep me down", "song": "Tubthumping", "artist": "Chumbawamba",
     "category": "perseverance", "keywords": ["keep down", "never", "persist", "resilient"]},
    # Power / Strength
    {"line": "I am the champion", "song": "Roar", "artist": "Katy Perry",
     "category": "power", "keywords": ["champion", "roar", "power", "strong", "loud"]},
    {"line": "I got the eye of the tiger", "song": "Roar", "artist": "Katy Perry",
     "category": "power", "keywords": ["tiger", "roar", "power", "fight"]},
    {"line": "Can't stop the feeling", "song": "Can't Stop the Feeling", "artist": "Justin Timberlake",
     "category": "success", "keywords": ["feeling", "good", "happy", "great", "vibe"]},
    {"line": "Nothing's gonna stop us now", "song": "Nothing's Gonna Stop Us Now", "artist": "Starship",
     "category": "perseverance", "keywords": ["stop", "nothing", "unstoppable", "go"]},
    {"line": "I'm still standing", "song": "I'm Still Standing", "artist": "Elton John",
     "category": "perseverance", "keywords": ["standing", "still", "upright", "strong"]},
    {"line": "Better than I ever did", "song": "I'm Still Standing", "artist": "Elton John",
     "category": "perseverance", "keywords": ["better", "improved", "stronger", "upgrade"]},
    # Fun / Coding Vibes
    {"line": "Another one bites the dust", "song": "Another One Bites the Dust", "artist": "Queen",
     "category": "fun", "keywords": ["bug", "crush", "kill", "fix", "destroy"]},
    {"line": "Under pressure", "song": "Under Pressure", "artist": "Queen & David Bowie",
     "category": "fun", "keywords": ["pressure", "stress", "deadline", "push"]},
    {"line": "Pressure pushing down on me", "song": "Under Pressure", "artist": "Queen & David Bowie",
     "category": "fun", "keywords": ["pressure", "push", "stress", "crunch"]},
    {"line": "It's a kind of magic", "song": "A Kind of Magic", "artist": "Queen",
     "category": "fun", "keywords": ["magic", "amazing", "wow", "incredible", "awesome"]},
    {"line": "I want to break free", "song": "I Want to Break Free", "artist": "Queen",
     "category": "fun", "keywords": ["break", "free", "refactor", "escape", "liberate"]},
    {"line": "I want to ride my bicycle", "song": "Bicycle Race", "artist": "Queen",
     "category": "fun", "keywords": ["ride", "go", "fast", "speed", "deploy"]},
    {"line": "Bohemian Rhapsody", "song": "Bohemian Rhapsody", "artist": "Queen",
     "category": "fun", "keywords": ["epic", "masterpiece", "complex", "grand"]},
    {"line": "Is this the real life? Is this just fantasy?", "song": "Bohemian Rhapsody", "artist": "Queen",
     "category": "fun", "keywords": ["reality", "fantasy", "dream", "unreal"]},
    {"line": "Thunderbolts and lightning, very very frightening", "song": "Bohemian Rhapsody", "artist": "Queen",
     "category": "fun", "keywords": ["lightning", "fast", "scary", "intense", "power"]},
    {"line": "We will rock you", "song": "We Will Rock You", "artist": "Queen",
     "category": "power", "keywords": ["rock", "dominate", "crush", "power"]},
    {"line": "We are the champions", "song": "We Are the Champions", "artist": "Queen",
     "category": "success", "keywords": ["champion", "win", "best", "victory"]},
    # Tech / Modern
    {"line": "Harder, better, faster, stronger", "song": "Harder Better Faster Stronger", "artist": "Daft Punk",
     "category": "power", "keywords": ["better", "faster", "stronger", "improve", "optimize"]},
    {"line": "Work it harder, make it better", "song": "Harder Better Faster Stronger", "artist": "Daft Punk",
     "category": "power", "keywords": ["work", "hard", "improve", "better"]},
    {"line": "Around the world", "song": "Around the World", "artist": "Daft Punk",
     "category": "fun", "keywords": ["world", "global", "deploy", "scale"]},
    {"line": "One more time", "song": "One More Time", "artist": "Daft Punk",
     "category": "fun", "keywords": ["again", "retry", "repeat", "once more"]},
    {"line": "Technologic", "song": "Technologic", "artist": "Daft Punk",
     "category": "fun", "keywords": ["tech", "code", "program", "digital"]},
    {"line": "Buy it, use it, break it, fix it", "song": "Technologic", "artist": "Daft Punk",
     "category": "fun", "keywords": ["fix", "break", "use", "build", "code"]},
    # Classic Anthems
    {"line": "Livin' on a prayer", "song": "Livin' on a Prayer", "artist": "Bon Jovi",
     "category": "perseverance", "keywords": ["prayer", "hope", "halfway", "there"]},
    {"line": "Whoa, we're halfway there", "song": "Livin' on a Prayer", "artist": "Bon Jovi",
     "category": "perseverance", "keywords": ["halfway", "progress", "midpoint", "there"]},
    {"line": "Shot through the heart", "song": "You Give Love a Bad Name", "artist": "Bon Jovi",
     "category": "fun", "keywords": ["heart", "pain", "bug", "hurt"]},
    {"line": "Sweet child o' mine", "song": "Sweet Child O' Mine", "artist": "Guns N' Roses",
     "category": "fun", "keywords": ["sweet", "child", "baby", "new", "fresh"]},
    {"line": "Welcome to the jungle", "song": "Welcome to the Jungle", "artist": "Guns N' Roses",
     "category": "fun", "keywords": ["jungle", "wild", "chaos", "crazy", "intense"]},
    {"line": "Here I go again on my own", "song": "Here I Go Again", "artist": "Whitesnake",
     "category": "start", "keywords": ["go", "own", "solo", "start", "begin"]},
    {"line": "Final", "song": "The Final Countdown", "artist": "Europe",
     "category": "completion", "keywords": ["final", "countdown", "deploy", "release", "ship"]},
    {"line": "It's the end of the world as we know it", "song": "It's the End of the World", "artist": "R.E.M.",
     "category": "fun", "keywords": ["end", "world", "apocalypse", "major change"]},
    {"line": "And I feel fine", "song": "It's the End of the World", "artist": "R.E.M.",
     "category": "success", "keywords": ["fine", "okay", "calm", "relaxed"]},
    {"line": "With a little help from my friends", "song": "With a Little Help", "artist": "The Beatles",
     "category": "collaboration", "keywords": ["friend", "help", "team", "together", "support"]},
    {"line": "All you need is love", "song": "All You Need Is Love", "artist": "The Beatles",
     "category": "success", "keywords": ["love", "care", "passion", "dedication"]},
    {"line": "Here comes the sun", "song": "Here Comes the Sun", "artist": "The Beatles",
     "category": "success", "keywords": ["sun", "bright", "hope", "new day", "better"]},
    {"line": "Let it be", "song": "Let It Be", "artist": "The Beatles",
     "category": "success", "keywords": ["be", "calm", "accept", "peace", "done"]},
    {"line": "Twist and shout", "song": "Twist and Shout", "artist": "The Beatles",
     "category": "fun", "keywords": ["twist", "shout", "excited", "energy"]},
    {"line": "We built this city on rock and roll", "song": "We Built This City", "artist": "Starship",
     "category": "power", "keywords": ["built", "city", "create", "build", "foundation"]},
    {"line": "Carry on wayward son", "song": "Carry On Wayward Son", "artist": "Kansas",
     "category": "perseverance", "keywords": ["carry on", "wayward", "continue", "journey"]},
    {"line": "There'll be peace when you are done", "song": "Carry On Wayward Son", "artist": "Kansas",
     "category": "completion", "keywords": ["peace", "done", "finished", "complete"]},
    {"line": "Don't fear the reaper", "song": "Don't Fear the Reaper", "artist": "Blue Öyster Cult",
     "category": "fun", "keywords": ["fear", "danger", "brave", "face it"]},
    {"line": "More than a feeling", "song": "More Than a Feeling", "artist": "Boston",
     "category": "success", "keywords": ["feeling", "good", "vibe", "amazing"]},
    {"line": "Peace of mind", "song": "Peace of Mind", "artist": "Boston",
     "category": "success", "keywords": ["peace", "calm", "mind", "relaxed", "done"]},
    # Epic / Cinematic
    {"line": "He's a pirate", "song": "He's a Pirate", "artist": "Hans Zimmer",
     "category": "epic", "keywords": ["pirate", "epic", "adventure", "quest"]},
    {"line": "Now you're playing with power", "song": "Power", "artist": "Kanye West",
     "category": "power", "keywords": ["power", "strength", "force", "might"]},
    {"line": "Stronger", "song": "Stronger", "artist": "Kanye West",
     "category": "power", "keywords": ["stronger", "better", "harder", "improve"]},
    {"line": "Can't tell me nothing", "song": "Can't Tell Me Nothing", "artist": "Kanye West",
     "category": "power", "keywords": ["nothing", "unstoppable", "confident", "sure"]},
    {"line": "This is the way", "song": "The Mandalorian", "artist": "Ludwig Göransson",
     "category": "epic", "keywords": ["way", "path", "correct", "right", "method"]},
    {"line": "I am Iron Man", "song": "Iron Man", "artist": "Black Sabbath",
     "category": "epic", "keywords": ["iron", "man", "hero", "strong", "build"]},
]


# ── Scoring ───────────────────────────────────────────────────────────────

def score_line(line: dict, query: str) -> float:
    """Score a voice line against the query. Returns 0.0-1.0."""
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    score = 0.0
    
    # Exact match in the lyric line
    line_lower = line["line"].lower()
    if query_lower in line_lower:
        score += 0.5
    
    # Word overlap with keywords
    keyword_matches = sum(1 for kw in line["keywords"] if kw in query_lower)
    score += (keyword_matches / max(len(line["keywords"]), 1)) * 0.3
    
    # Category match (check if query mentions category-like words)
    category_boosts = {
        "success": ["done", "complete", "finished", "work", "fix", "solve", "yes", "great", "perfect"],
        "perseverance": ["hard", "difficult", "tough", "struggle", "keep", "persist", "continue"],
        "power": ["strong", "power", "force", "mighty", "epic", "huge", "big"],
        "fun": ["fun", "cool", "awesome", "lol", "haha", "nice", "great"],
        "completion": ["ship", "deploy", "release", "launch", "final", "countdown"],
        "start": ["start", "begin", "new", "create", "init", "first", "go"],
        "collaboration": ["team", "help", "together", "friend", "pair", "assist"],
        "epic": ["epic", "legendary", "amazing", "incredible", "wow"],
    }
    for cat, words in category_boosts.items():
        if line["category"] == cat and any(w in query_words for w in words):
            score += 0.2
    
    return min(1.0, score)


def search_fallback(query: str, limit: int = 5) -> list[dict]:
    """Search the curated voice line database."""
    scored = [(score_line(line, query), line) for line in VOICE_LINES]
    scored.sort(key=lambda x: (-x[0], x[1]["line"]))
    
    results = []
    for score, line in scored[:limit]:
        results.append({
            "voice_line": line["line"],
            "song": line["song"],
            "artist": line["artist"],
            "category": line["category"],
            "confidence": round(score, 2),
        })
    
    return results


def search_bumblebee_library(query: str, library_path: Optional[str] = None, limit: int = 5) -> list[dict]:
    """Search the Bumblebee music library if available."""
    library = library_path or os.environ.get("BUMBLEBEE_LIBRARY", str(Path.home() / "Music"))
    db_path = os.environ.get("BUMBLEBEE_DB", str(Path(library) / ".bumblebee.db"))
    
    db_file = Path(db_path)
    if not db_file.exists():
        return []
    
    try:
        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row
        
        # Use FTS5 if available
        cursor = conn.execute(
            """SELECT l.text, l.timestamp_ms, s.title, s.artist, s.album
               FROM lyrics l
               JOIN songs s ON l.song_id = s.id
               WHERE l.text LIKE ?
               ORDER BY l.timestamp_ms
               LIMIT ?""",
            (f"%{query}%", limit * 3)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        # Score and rank
        def _format_ts(ms: int) -> str:
            m = ms // 60000
            s = (ms % 60000) // 1000
            cs = (ms % 1000) // 10
            return f"{m:02d}:{s:02d}.{cs:02d}"
        
        results = []
        for row in rows[:limit]:
            text = row["text"]
            # Simple relevance: longer match = higher score
            match_len = len(query) / max(len(text), 1)
            confidence = 0.5 + match_len * 0.5
            
            results.append({
                "voice_line": text,
                "song": row["title"],
                "artist": row["artist"],
                "timestamp": _format_ts(row["timestamp_ms"]),
                "confidence": round(confidence, 2),
            })
        
        return results
    
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return []


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bumblebee Voice — Find voice lines")
    parser.add_argument("query", nargs="?", default="", help="Context to search for")
    parser.add_argument("--fallback", action="store_true", help="Use built-in voice lines only")
    parser.add_argument("--list", action="store_true", help="List all voice lines")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--library", help="Path to Bumblebee music library")
    parser.add_argument("--limit", type=int, default=5, help="Max results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--best", action="store_true", help="Output only the best match")
    
    args = parser.parse_args()
    
    if args.list:
        lines = VOICE_LINES
        if args.category:
            lines = [l for l in lines if l["category"] == args.category]
        for line in lines:
            print(f"[{line['category']:15}] \"{line['line']}\" — {line['song']}, {line['artist']}")
        return
    
    if not args.query:
        print("Usage: voice.py \"<context description>\"", file=sys.stderr)
        print("       voice.py --list                    # List all lines", file=sys.stderr)
        print("       voice.py --fallback \"<context>\"    # Use built-in only", file=sys.stderr)
        sys.exit(1)
    
    # Try music library first (unless --fallback)
    results = []
    if not args.fallback:
        results = search_bumblebee_library(args.query, args.library, args.limit)
    
    # Fall back to curated lines
    if not results:
        results = search_fallback(args.query, args.limit)
    
    if not results:
        print(json.dumps({"error": "No voice lines found"})) if args.json else print("No voice lines found.")
        sys.exit(1)
    
    if args.best:
        results = results[:1]
    
    if args.json:
        output = {
            "best": results[0],
            "alternatives": results[1:] if len(results) > 1 else [],
            "source": "library" if not args.fallback and len(results) > 0 else "fallback",
        }
        print(json.dumps(output, indent=2))
    else:
        best = results[0]
        print(f"🐝 Best match ({int(best['confidence'] * 100)}% confidence):")
        print(f"   \"{best['voice_line']}\"")
        print(f"   — {best['song']}, {best['artist']}", end="")
        if "timestamp" in best:
            print(f" ({best['timestamp']})")
        else:
            print()
        
        if len(results) > 1:
            print(f"\n   Alternatives:")
            for alt in results[1:3]:
                print(f"   • \"{alt['voice_line']}\" — {alt['song']}")


if __name__ == "__main__":
    main()
