#!/usr/bin/env python3
"""
Spotify API helper - uses saved tokens from spotify_auth.py

Usage:
    from spotify_api import SpotifyAPI
    
    api = SpotifyAPI()
    
    # Get current user
    me = api.get("/me")
    
    # Get recently played
    recent = api.get("/me/player/recently-played", limit=10)
    
    # Get top tracks
    top = api.get("/me/top/tracks", time_range="short_term", limit=10)
    
    # Search
    results = api.get("/search", q="Miles Davis", type="artist")
    
    # Control playback
    api.put("/me/player/play")
    api.post("/me/player/next")
"""

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_FILE = Path.home() / ".spotify_tokens.json"
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
BASE_URL = "https://api.spotify.com/v1"


class SpotifyAPI:
    """Simple Spotify API client."""
    
    def __init__(self):
        self.access_token = self._get_valid_token()
    
    def _get_valid_token(self) -> str:
        """Get a valid access token, refreshing if needed."""
        if not TOKEN_FILE.exists():
            raise RuntimeError(
                "Not authorized. Run spotify_auth.py first."
            )
        
        tokens = json.loads(TOKEN_FILE.read_text())
        
        # Try the token
        try:
            self._request("GET", "/me", tokens["access_token"])
            return tokens["access_token"]
        except urllib.error.HTTPError as e:
            if e.code == 401 and "refresh_token" in tokens:
                # Refresh the token
                new_tokens = self._refresh_token(tokens["refresh_token"])
                if "refresh_token" not in new_tokens:
                    new_tokens["refresh_token"] = tokens["refresh_token"]
                TOKEN_FILE.write_text(json.dumps(new_tokens, indent=2))
                return new_tokens["access_token"]
            raise
    
    def _refresh_token(self, refresh_token: str) -> dict:
        """Refresh the access token."""
        import base64
        
        url = "https://accounts.spotify.com/api/token"
        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }).encode()
        
        credentials = base64.b64encode(
            f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
        ).decode()
        
        req = urllib.request.Request(url, data=data, headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    
    def _request(
        self,
        method: str,
        endpoint: str,
        token: str = None,
        data: dict = None,
        **params
    ) -> dict | None:
        """Make an API request."""
        token = token or self.access_token
        
        url = BASE_URL + endpoint
        if params:
            url += "?" + urllib.parse.urlencode(params)
        
        body = json.dumps(data).encode() if data else None
        
        req = urllib.request.Request(url, data=body, method=method, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        
        try:
            with urllib.request.urlopen(req) as resp:
                content = resp.read()
                if content:
                    return json.loads(content.decode())
                return None
        except urllib.error.HTTPError as e:
            if e.code == 204:  # No content
                return None
            raise
    
    def get(self, endpoint: str, **params) -> dict:
        """GET request."""
        return self._request("GET", endpoint, **params)
    
    def post(self, endpoint: str, data: dict = None, **params) -> dict:
        """POST request."""
        return self._request("POST", endpoint, data=data, **params)
    
    def put(self, endpoint: str, data: dict = None, **params) -> dict:
        """PUT request."""
        return self._request("PUT", endpoint, data=data, **params)
    
    def delete(self, endpoint: str, **params) -> dict:
        """DELETE request."""
        return self._request("DELETE", endpoint, **params)
    
    # Convenience methods
    
    def me(self) -> dict:
        """Get current user profile."""
        return self.get("/me")
    
    def now_playing(self) -> dict | None:
        """Get currently playing track."""
        return self.get("/me/player/currently-playing")
    
    def recently_played(self, limit: int = 20) -> dict:
        """Get recently played tracks."""
        return self.get("/me/player/recently-played", limit=limit)
    
    def top_tracks(self, time_range: str = "medium_term", limit: int = 20) -> dict:
        """Get user's top tracks.
        
        time_range: short_term (4 weeks), medium_term (6 months), long_term (years)
        """
        return self.get("/me/top/tracks", time_range=time_range, limit=limit)
    
    def top_artists(self, time_range: str = "medium_term", limit: int = 20) -> dict:
        """Get user's top artists."""
        return self.get("/me/top/artists", time_range=time_range, limit=limit)
    
    def search(self, query: str, types: str = "track,artist,album", limit: int = 10) -> dict:
        """Search for tracks, artists, albums, etc."""
        return self.get("/search", q=query, type=types, limit=limit)
    
    def play(self) -> None:
        """Resume playback."""
        self.put("/me/player/play")
    
    def pause(self) -> None:
        """Pause playback."""
        self.put("/me/player/pause")
    
    def next(self) -> None:
        """Skip to next track."""
        self.post("/me/player/next")
    
    def previous(self) -> None:
        """Go to previous track."""
        self.post("/me/player/previous")


def main():
    """Test the API."""
    api = SpotifyAPI()
    
    print("=== Spotify API Test ===\n")
    
    # User profile
    me = api.me()
    print(f"Logged in as: {me['display_name']} ({me.get('email', 'no email')})")
    print(f"Followers: {me['followers']['total']}")
    print()
    
    # Now playing
    playing = api.now_playing()
    if playing and playing.get("item"):
        track = playing["item"]
        artists = ", ".join(a["name"] for a in track["artists"])
        print(f"Now playing: {track['name']} by {artists}")
    else:
        print("Nothing currently playing")
    print()
    
    # Recent tracks
    print("Recently played:")
    recent = api.recently_played(limit=5)
    for item in recent.get("items", []):
        track = item["track"]
        artists = ", ".join(a["name"] for a in track["artists"])
        print(f"  - {track['name']} by {artists}")
    print()
    
    # Top tracks
    print("Your top tracks (last 4 weeks):")
    top = api.top_tracks(time_range="short_term", limit=5)
    for i, track in enumerate(top.get("items", []), 1):
        artists = ", ".join(a["name"] for a in track["artists"])
        print(f"  {i}. {track['name']} by {artists}")


if __name__ == "__main__":
    main()
