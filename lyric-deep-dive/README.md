# lyric-deep-dive 🎤

Pop-Up Video style deep analysis of song lyrics. Fetches lyrics, researches context, and generates comprehensive breakdowns with literary analysis.

## Features

- **Lyrics fetching** from Genius (API) and AZLyrics (scraping)
- **Literary analysis**: word frequency, repeated lines (chorus detection), vocabulary density
- **Literary device detection**: alliteration, anaphora, rhetorical questions
- **Context research**: auto-searches for song meanings, artist interviews, Songfacts
- **Multiple outputs**: formatted markdown or raw JSON

## Usage

```bash
# Basic usage
./lyric_deep_dive.py "Artist" "Song Title"

# Examples
./lyric_deep_dive.py "Radiohead" "Fake Plastic Trees"
./lyric_deep_dive.py "Taylor Swift" "All Too Well"
./lyric_deep_dive.py "The National" "Fake Empire"

# Output as JSON (for further processing)
./lyric_deep_dive.py --json "Counting Crows" "A Long December"

# Just get lyrics
./lyric_deep_dive.py --lyrics-only "Nirvana" "Come As You Are"

# Skip analysis (faster)
./lyric_deep_dive.py --no-analysis "Oasis" "Wonderwall"
```

## Environment Variables

- `GENIUS_ACCESS_TOKEN` - Genius API token for better lyrics and metadata
  - Get one at: https://genius.com/api-clients
  - Without it, falls back to web scraping (still works!)

## Output Format

### Markdown (default)

```markdown
# Song Title
**Artist** · *Album* · Year

## 📜 Lyrics
[Full lyrics...]

## 🔬 Lyrical Analysis
- Word count, unique words, vocabulary density
- Key words with frequency
- Repeated lines (hook/chorus detection)
- Literary devices found

## 📚 Context & Research
[Links and snippets from web searches about song meaning, interviews, etc.]

## 🔗 Resources
- Genius, Songfacts, YouTube links
```

### JSON (`--json`)

```json
{
  "artist": "...",
  "title": "...",
  "album": "...",
  "year": "...",
  "lyrics": "...",
  "genius_url": "...",
  "context": [...],
  "analysis": {
    "word_count": ...,
    "unique_words": ...,
    "top_words": [...],
    "repeated_lines": [...],
    "literary_devices": [...]
  }
}
```

## Dependencies

None! Pure Python 3 standard library.

## How It Works

1. **Genius API** (if token provided) - searches for song, gets metadata
2. **Lyrics scraping** - tries Genius page first, falls back to AZLyrics
3. **Web search** - DuckDuckGo HTML search for context, meanings, interviews
4. **Analysis** - word frequency, pattern detection, literary device identification
5. **Output** - formatted markdown or structured JSON

## Tips

- Works best with well-known songs that have documentation online
- Use `--json` output to feed into Claude for deeper narrative analysis
- The literary device detection is heuristic-based (may miss subtle devices)
- Combine with the `song-deep-dive` skill for full narrative output

## Example Output

```
$ ./lyric_deep_dive.py "Counting Crows" "A Long December"

# A Long December
**Counting Crows** · *Recovering the Satellites* · 1996

## 📜 Lyrics
...

## 🔬 Lyrical Analysis
- **Word count:** 412
- **Unique words:** 198
- **Vocabulary density:** 48.1%

### Key Words
**long** (8), **december** (6), **year** (4), **drive** (3)...

### Repeated Lines (Hook/Chorus)
- *"A long December and there's reason to believe"* (×4)
...
```

## License

MIT - built during nightly-build 2026-01-29
