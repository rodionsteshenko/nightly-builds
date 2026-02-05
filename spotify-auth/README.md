# Spotify OAuth Setup

Authorizes Clawdbot to access your Spotify account with full permissions.

## Quick Start

```bash
cd ~/clawd/nightly-build/projects/spotify-auth
python3 spotify_auth.py
```

This will:
1. Open your browser to Spotify's login page
2. Ask you to approve the app
3. Save tokens to `~/.spotify_tokens.json`
4. Test the connection

## Redirect URI Setup

If you get a "redirect URI mismatch" error, add this URI to your Spotify app:

1. Go to https://developer.spotify.com/dashboard
2. Select your app
3. Click "Edit Settings"
4. Add `http://localhost:8888/callback` to Redirect URIs
5. Save and try again

## Using the API

After auth, use `spotify_api.py`:

```python
from spotify_api import SpotifyAPI

api = SpotifyAPI()

# Get your profile
me = api.me()
print(f"Logged in as {me['display_name']}")

# Get recently played
for item in api.recently_played(limit=5)["items"]:
    print(item["track"]["name"])

# Get top tracks
for track in api.top_tracks(time_range="short_term")["items"]:
    print(track["name"])

# Control playback
api.play()
api.pause()
api.next()
```

## Permissions Granted

- Read your profile, email, followers
- Read/modify your library (liked songs)
- Read/modify your playlists
- Read your top tracks/artists
- Read recently played
- Control playback (play, pause, skip)
- Read current playback state
