# setlist-builder

Concert setlist generator that arranges songs into an optimal show flow.

## What It Does

Takes a list of tracks and arranges them following concert pacing principles:

1. **Opener (15%)** - High energy, crowd-pleaser
2. **Early Set (25%)** - Maintain momentum, fan favorites  
3. **Mid-Set Dip (20%)** - Slower songs, ballads, breather
4. **Build (25%)** - Rising energy toward finale
5. **Closer (15%)** - Peak energy, biggest hits

Uses BPM and energy levels to:
- Score transitions between songs
- Avoid jarring tempo jumps
- Consider key compatibility

## Usage

```bash
# Demo with sample 90s rock tracks
python3 setlist.py --demo

# From a JSON file
python3 setlist.py --input mytracks.json

# From Spotify playlist (requires spogo CLI)
python3 setlist.py --playlist "https://open.spotify.com/playlist/..."

# Options
python3 setlist.py --demo --length 10     # 10-song set
python3 setlist.py --demo --details       # Show BPM/energy
python3 setlist.py --demo --markdown      # Markdown output
python3 setlist.py --demo --json          # JSON output
python3 setlist.py --demo --shuffle       # Randomize selection
```

## JSON Input Format

```json
[
  {
    "name": "Mr. Brightside",
    "artist": "The Killers",
    "bpm": 148,
    "energy": 0.92,
    "duration_ms": 222000
  }
]
```

Fields:
- `name`, `artist`: Required
- `bpm`: Beats per minute (default: 120)
- `energy`: 0-1 scale (default: 0.5)
- `duration_ms`: Track length (default: 200000)
- `key`: 0-11, C to B (default: 0)
- `mode`: 1=major, 0=minor (default: 1)

## Sample Output

```
==================================================
🎸 SETLIST
==================================================

--- OPENER ---
 1. Mr. Brightside - The Killers
 2. Smells Like Teen Spirit - Nirvana

--- EARLY SET ---
 3. Everlong - Foo Fighters
 4. Semi-Charmed Life - Third Eye Blind
 5. 1979 - The Smashing Pumpkins
 6. Basket Case - Green Day

--- MID-SET DIP ---
 7. Creep - Radiohead
 8. Under the Bridge - Red Hot Chili Peppers
 9. Yellow - Coldplay

--- BUILD ---
10. Losing My Religion - R.E.M.
11. Wonderwall - Oasis
12. Interstate Love Song - Stone Temple Pilots

--- CLOSER ---
13. Zombie - The Cranberries
14. Closing Time - Semisonic
15. Black Hole Sun - Soundgarden

==================================================
Total: 15 songs | ~66 minutes
==================================================
```

## Install

No dependencies required. Just Python 3.10+.

```bash
# Make executable
chmod +x setlist.py

# Link to PATH (optional)
ln -s $(pwd)/setlist.py ~/.local/bin/setlist
```

## Why This Exists

Real concerts follow a deliberate energy arc. You don't open with a ballad or close with a slow burn. This tool helps playlist-makers think like concert promoters.
