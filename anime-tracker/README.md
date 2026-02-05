# anime-tracker

Track your anime watching progress from the command line.

## Features

- Track what episode you're on for each show
- Episode counts and status from AniList (free API, no auth needed)
- "What's next" recommendations based on progress and airing status
- Search for new anime to track
- Progress bars and visual indicators

## Installation

```bash
# Copy to somewhere in your PATH
cp anime ~/.local/bin/
# Or run directly
./anime --help
```

## Usage

```bash
# Add a show (fetches info from AniList automatically)
anime add "One Piece" --episode 1200
anime add "Jujutsu Kaisen" -e 24

# Update your progress
anime update "One Piece" 1205
anime update "jjk" 48  # fuzzy matching works

# See all tracked shows
anime list

# Get detailed info
anime info "Attack on Titan"

# What should I watch next?
anime next

# Search for anime
anime search "demon slayer"

# Remove a show
anime remove "One Piece"
```

## Storage

Shows are stored in `~/.config/anime/shows.json`.

## Dependencies

- Python 3.8+
- No external packages (stdlib only)
- Internet connection for AniList API

## Example Output

```
📺 Tracked Anime

🟢 ONE PIECE
  Episode 1205/? 

✓ Jujutsu Kaisen
  Episode 24/24 [███████████████] 100%

⏳ Chainsaw Man Part 2
  Episode 0/? 
```

Status indicators:
- 🟢 Currently airing
- ✓ Finished
- ⏳ Not yet released
- • Unknown status
