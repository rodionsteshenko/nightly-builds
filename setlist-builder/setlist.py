#!/usr/bin/env python3
"""
setlist-builder: Concert setlist generator
Arranges songs into an optimal concert flow based on energy, tempo, and show pacing.
"""

import argparse
import json
import sys
import subprocess
import random
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Track:
    name: str
    artist: str
    bpm: float = 120.0
    energy: float = 0.5  # 0-1 scale
    duration_ms: int = 200000
    key: int = 0  # 0-11 (C to B)
    mode: int = 1  # 1=major, 0=minor
    
    @property
    def duration_min(self) -> float:
        return self.duration_ms / 60000

def get_tracks_from_spogo(playlist_url: str) -> list[Track]:
    """Fetch tracks from Spotify playlist using spogo CLI."""
    try:
        # Get playlist tracks
        result = subprocess.run(
            ['spogo', 'playlist', 'tracks', playlist_url, '--json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise Exception(f"spogo error: {result.stderr}")
        
        data = json.loads(result.stdout)
        tracks = []
        
        for item in data.get('items', data) if isinstance(data, dict) else data:
            track_data = item.get('track', item) if isinstance(item, dict) else item
            if not track_data:
                continue
                
            # spogo may include audio features
            tracks.append(Track(
                name=track_data.get('name', 'Unknown'),
                artist=track_data.get('artists', [{}])[0].get('name', 'Unknown') if isinstance(track_data.get('artists'), list) else 'Unknown',
                bpm=track_data.get('tempo', 120),
                energy=track_data.get('energy', 0.5),
                duration_ms=track_data.get('duration_ms', 200000),
                key=track_data.get('key', 0),
                mode=track_data.get('mode', 1)
            ))
        
        return tracks
    except FileNotFoundError:
        print("Warning: spogo not found, using sample data", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Could not fetch from Spotify: {e}", file=sys.stderr)
        return []

def load_tracks_from_json(path: str) -> list[Track]:
    """Load tracks from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    
    tracks = []
    for item in data:
        tracks.append(Track(
            name=item.get('name', 'Unknown'),
            artist=item.get('artist', 'Unknown'),
            bpm=item.get('bpm', 120),
            energy=item.get('energy', 0.5),
            duration_ms=item.get('duration_ms', 200000),
            key=item.get('key', 0),
            mode=item.get('mode', 1)
        ))
    return tracks

def estimate_energy(track: Track) -> float:
    """Estimate energy if not provided, based on tempo."""
    if track.energy != 0.5:  # Already set
        return track.energy
    # Rough heuristic: higher tempo = higher energy
    return min(1.0, max(0.0, (track.bpm - 60) / 120))

def score_transition(current: Track, next_track: Track) -> float:
    """Score how good a transition between two tracks is (higher = better)."""
    score = 100.0
    
    # Tempo jump penalty (prefer smooth transitions)
    tempo_diff = abs(current.bpm - next_track.bpm)
    if tempo_diff > 40:
        score -= 30
    elif tempo_diff > 20:
        score -= 15
    elif tempo_diff > 10:
        score -= 5
    
    # Key compatibility (circle of fifths proximity)
    key_diff = min(abs(current.key - next_track.key), 12 - abs(current.key - next_track.key))
    if key_diff <= 1 or key_diff == 5 or key_diff == 7:  # Same, adjacent, or fifth
        score += 10
    elif key_diff >= 4:
        score -= 10
    
    # Mode change (major/minor) slight penalty
    if current.mode != next_track.mode:
        score -= 5
    
    return score

def build_setlist(tracks: list[Track], set_length: int = 0) -> list[Track]:
    """
    Build an optimal setlist using concert pacing principles.
    
    Typical concert flow:
    1. OPENER (15%): High energy, crowd-pleaser
    2. EARLY SET (25%): Keep momentum, fan favorites  
    3. MID-SET DIP (20%): Slower songs, ballads, breather
    4. BUILD (25%): Rising energy toward finale
    5. CLOSER (15%): Peak energy, biggest hits
    """
    if not tracks:
        return []
    
    if set_length <= 0 or set_length > len(tracks):
        set_length = len(tracks)
    
    # Sort by energy for categorization
    by_energy = sorted(tracks, key=lambda t: t.energy, reverse=True)
    
    # Categorize tracks
    high_energy = [t for t in tracks if t.energy >= 0.7]
    mid_energy = [t for t in tracks if 0.4 <= t.energy < 0.7]
    low_energy = [t for t in tracks if t.energy < 0.4]
    
    # If we don't have good energy distribution, use tempo as proxy
    if len(high_energy) < 2:
        by_tempo = sorted(tracks, key=lambda t: t.bpm, reverse=True)
        third = len(tracks) // 3
        high_energy = by_tempo[:third]
        mid_energy = by_tempo[third:2*third]
        low_energy = by_tempo[2*third:]
    
    setlist = []
    used = set()
    
    def pick_best(pool: list[Track], prefer_transition_from: Optional[Track] = None) -> Optional[Track]:
        available = [t for t in pool if id(t) not in used]
        if not available:
            return None
        
        if prefer_transition_from:
            # Score transitions and pick best
            scored = [(t, score_transition(prefer_transition_from, t)) for t in available]
            scored.sort(key=lambda x: x[1], reverse=True)
            choice = scored[0][0]
        else:
            choice = random.choice(available)
        
        used.add(id(choice))
        return choice
    
    # Calculate section sizes
    n = set_length
    opener_size = max(1, int(n * 0.15))
    early_size = max(1, int(n * 0.25))
    dip_size = max(1, int(n * 0.20))
    build_size = max(1, int(n * 0.25))
    closer_size = n - opener_size - early_size - dip_size - build_size
    
    # OPENER: High energy
    for _ in range(opener_size):
        track = pick_best(high_energy, setlist[-1] if setlist else None)
        if not track:
            track = pick_best(mid_energy, setlist[-1] if setlist else None)
        if track:
            setlist.append(track)
    
    # EARLY SET: Mix of high and mid
    early_pool = high_energy + mid_energy
    for _ in range(early_size):
        track = pick_best(early_pool, setlist[-1] if setlist else None)
        if track:
            setlist.append(track)
    
    # MID-SET DIP: Low energy, ballads
    for _ in range(dip_size):
        track = pick_best(low_energy, setlist[-1] if setlist else None)
        if not track:
            track = pick_best(mid_energy, setlist[-1] if setlist else None)
        if track:
            setlist.append(track)
    
    # BUILD: Rising energy (mid to high)
    build_pool = sorted(mid_energy + high_energy, key=lambda t: t.energy)
    for _ in range(build_size):
        track = pick_best(build_pool, setlist[-1] if setlist else None)
        if track:
            setlist.append(track)
    
    # CLOSER: Highest energy bangers
    for _ in range(closer_size):
        track = pick_best(high_energy, setlist[-1] if setlist else None)
        if not track:
            track = pick_best(mid_energy, setlist[-1] if setlist else None)
        if track:
            setlist.append(track)
    
    return setlist

def format_setlist(setlist: list[Track], show_details: bool = False) -> str:
    """Format setlist as readable text."""
    if not setlist:
        return "No tracks in setlist."
    
    lines = []
    lines.append("=" * 50)
    lines.append("🎸 SETLIST")
    lines.append("=" * 50)
    
    total_ms = 0
    sections = [
        ("OPENER", 0.15),
        ("EARLY SET", 0.25),
        ("MID-SET DIP", 0.20),
        ("BUILD", 0.25),
        ("CLOSER", 0.15),
    ]
    
    n = len(setlist)
    current_idx = 0
    
    for section_name, pct in sections:
        section_size = max(1, int(n * pct))
        if current_idx >= n:
            break
            
        lines.append(f"\n--- {section_name} ---")
        
        end_idx = min(current_idx + section_size, n)
        for i in range(current_idx, end_idx):
            track = setlist[i]
            total_ms += track.duration_ms
            
            if show_details:
                lines.append(f"{i+1:2}. {track.name}")
                lines.append(f"    {track.artist} | {track.bpm:.0f} BPM | Energy: {track.energy:.1f}")
            else:
                lines.append(f"{i+1:2}. {track.name} - {track.artist}")
        
        current_idx = end_idx
    
    # Any remaining tracks
    while current_idx < n:
        track = setlist[current_idx]
        total_ms += track.duration_ms
        lines.append(f"{current_idx+1:2}. {track.name} - {track.artist}")
        current_idx += 1
    
    total_min = total_ms / 60000
    lines.append(f"\n{'=' * 50}")
    lines.append(f"Total: {len(setlist)} songs | ~{total_min:.0f} minutes")
    lines.append("=" * 50)
    
    return "\n".join(lines)

def format_markdown(setlist: list[Track]) -> str:
    """Format setlist as markdown."""
    if not setlist:
        return "No tracks in setlist."
    
    lines = []
    lines.append("# 🎸 Concert Setlist\n")
    
    n = len(setlist)
    sections = [
        ("Opener", 0.15, "🔥"),
        ("Early Set", 0.25, "⚡"),
        ("Mid-Set Dip", 0.20, "💫"),
        ("Build", 0.25, "📈"),
        ("Closer", 0.15, "🎆"),
    ]
    
    current_idx = 0
    total_ms = 0
    
    for section_name, pct, emoji in sections:
        section_size = max(1, int(n * pct))
        if current_idx >= n:
            break
            
        lines.append(f"## {emoji} {section_name}\n")
        
        end_idx = min(current_idx + section_size, n)
        for i in range(current_idx, end_idx):
            track = setlist[i]
            total_ms += track.duration_ms
            lines.append(f"{i+1}. **{track.name}** - {track.artist}")
        
        lines.append("")
        current_idx = end_idx
    
    # Any remaining
    while current_idx < n:
        track = setlist[current_idx]
        total_ms += track.duration_ms
        lines.append(f"{current_idx+1}. **{track.name}** - {track.artist}")
        current_idx += 1
    
    total_min = total_ms / 60000
    lines.append(f"\n---\n*{len(setlist)} songs | ~{total_min:.0f} minutes*")
    
    return "\n".join(lines)

def create_sample_tracks() -> list[Track]:
    """Sample tracks for demo purposes."""
    return [
        Track("Everlong", "Foo Fighters", 158, 0.85, 250000),
        Track("Yellow", "Coldplay", 88, 0.45, 270000),
        Track("Mr. Brightside", "The Killers", 148, 0.92, 222000),
        Track("Losing My Religion", "R.E.M.", 126, 0.55, 270000),
        Track("Creep", "Radiohead", 92, 0.35, 237000),
        Track("Wonderwall", "Oasis", 87, 0.60, 258000),
        Track("Under the Bridge", "Red Hot Chili Peppers", 84, 0.40, 263000),
        Track("Smells Like Teen Spirit", "Nirvana", 117, 0.95, 278000),
        Track("Zombie", "The Cranberries", 82, 0.70, 305000),
        Track("Black Hole Sun", "Soundgarden", 100, 0.50, 318000),
        Track("Semi-Charmed Life", "Third Eye Blind", 104, 0.88, 269000),
        Track("Closing Time", "Semisonic", 102, 0.75, 276000),
        Track("Basket Case", "Green Day", 170, 0.90, 181000),
        Track("Interstate Love Song", "Stone Temple Pilots", 86, 0.65, 193000),
        Track("1979", "The Smashing Pumpkins", 126, 0.78, 265000),
    ]

def main():
    parser = argparse.ArgumentParser(
        description="Generate optimal concert setlists from a track list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  setlist --demo                    Use sample tracks for demo
  setlist --input songs.json        Load tracks from JSON file  
  setlist --playlist <url>          Fetch from Spotify (requires spogo)
  setlist --demo --length 10        Build 10-song setlist
  setlist --demo --markdown         Output as markdown
  setlist --demo --json             Output as JSON

JSON input format:
  [{"name": "Song", "artist": "Artist", "bpm": 120, "energy": 0.7}, ...]
        """
    )
    
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--demo', action='store_true', help='Use sample 90s rock tracks')
    source.add_argument('--input', '-i', metavar='FILE', help='Load tracks from JSON file')
    source.add_argument('--playlist', '-p', metavar='URL', help='Spotify playlist URL (requires spogo)')
    
    parser.add_argument('--length', '-n', type=int, default=0, help='Number of songs (0=all)')
    parser.add_argument('--details', '-d', action='store_true', help='Show BPM and energy')
    parser.add_argument('--markdown', '-m', action='store_true', help='Output as markdown')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    parser.add_argument('--shuffle', '-s', action='store_true', help='Add randomness to selection')
    
    args = parser.parse_args()
    
    # Load tracks
    if args.demo:
        tracks = create_sample_tracks()
        if args.shuffle:
            random.shuffle(tracks)
    elif args.input:
        tracks = load_tracks_from_json(args.input)
    elif args.playlist:
        tracks = get_tracks_from_spogo(args.playlist)
        if not tracks:
            print("Could not fetch playlist. Try --demo or --input", file=sys.stderr)
            sys.exit(1)
    
    if not tracks:
        print("No tracks loaded.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(tracks)} tracks", file=sys.stderr)
    
    # Build setlist
    setlist = build_setlist(tracks, args.length)
    
    # Output
    if args.json:
        print(json.dumps([asdict(t) for t in setlist], indent=2))
    elif args.markdown:
        print(format_markdown(setlist))
    else:
        print(format_setlist(setlist, args.details))

if __name__ == '__main__':
    main()
