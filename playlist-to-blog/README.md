# playlist-to-blog

Turn a Spotify playlist into a narrative blog post.

## Usage

```bash
# Basic usage (outputs to stdout)
python3 playlist_to_blog.py <playlist_url_or_id>

# Save to file
python3 playlist_to_blog.py https://open.spotify.com/playlist/ABC123 -o post.md

# Different writing styles
python3 playlist_to_blog.py ABC123 --style casual     # Relaxed, conversational
python3 playlist_to_blog.py ABC123 --style formal     # Academic, analytical
python3 playlist_to_blog.py ABC123 --style nostalgic  # Default, reflective

# Get raw analysis as JSON
python3 playlist_to_blog.py ABC123 --json
```

## Requirements

- Python 3.7+
- Environment variables:
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`

No external dependencies (uses stdlib only).

## What It Does

1. Fetches playlist metadata and all tracks
2. Analyzes:
   - Top artists (most tracks)
   - Decade distribution
   - Total duration
   - Unique artist count
3. Generates a markdown blog post with:
   - Header with stats
   - Decade breakdown
   - Artist highlights
   - Sample tracks
   - Spotify link

## Example Output

```markdown
# My 90s Playlist

*638 tracks · 42h 15m · 312 artists*

There's a playlist I keep coming back to...

## The Sound of Time
This playlist spans: **1990s** (78%), **2000s** (15%)...

## The Artists
- **Counting Crows** (28 tracks)
- **Wilco** (19 tracks)
...
```

## Styles

- **nostalgic** (default): Reflective, memory-focused, emotional
- **casual**: Laid back, conversational, "give it a listen"
- **formal**: Analytical, descriptive, neutral

## Notes

- Works with public playlists only (uses client credentials flow)
- For private playlists, you'd need OAuth user authorization
- Large playlists (1000+ tracks) may take a moment to fetch

## Built

Nightly Build - January 28, 2026
