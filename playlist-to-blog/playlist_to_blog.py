#!/usr/bin/env python3
"""
playlist-to-blog: Turn a Spotify playlist into a blog post.

Takes a Spotify playlist URL, fetches track info, and generates
a narrative blog post about the music.

Usage:
    playlist-to-blog <playlist_url_or_id> [--output FILE] [--style casual|formal|nostalgic]
"""

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from collections import Counter


def get_spotify_token():
    """Get Spotify access token using client credentials flow."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set")
    
    auth_string = f"{client_id}:{client_secret}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()
    
    req = Request(
        "https://accounts.spotify.com/api/token",
        data=urlencode({"grant_type": "client_credentials"}).encode(),
        headers={
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    with urlopen(req) as resp:
        data = json.loads(resp.read())
        return data["access_token"]


def extract_playlist_id(url_or_id):
    """Extract playlist ID from URL or return as-is."""
    # Handle full URLs
    match = re.search(r"playlist[/:]([a-zA-Z0-9]+)", url_or_id)
    if match:
        return match.group(1)
    # Assume it's already an ID
    return url_or_id


def fetch_playlist(token, playlist_id):
    """Fetch playlist details and tracks."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get playlist metadata
    req = Request(
        f"https://api.spotify.com/v1/playlists/{playlist_id}",
        headers=headers
    )
    with urlopen(req) as resp:
        playlist = json.loads(resp.read())
    
    # Get all tracks (handle pagination)
    tracks = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=100"
    
    while url:
        req = Request(url, headers=headers)
        with urlopen(req) as resp:
            data = json.loads(resp.read())
            tracks.extend(data["items"])
            url = data.get("next")
    
    return playlist, tracks


def analyze_playlist(playlist, tracks):
    """Analyze playlist for interesting patterns."""
    artists = Counter()
    albums = Counter()
    decades = Counter()
    genres_raw = []
    
    for item in tracks:
        track = item.get("track")
        if not track:
            continue
            
        # Count artists
        for artist in track.get("artists", []):
            artists[artist["name"]] += 1
        
        # Count albums
        album = track.get("album", {})
        if album.get("name"):
            albums[album["name"]] += 1
        
        # Decade from release date
        release_date = album.get("release_date", "")
        if release_date:
            try:
                year = int(release_date[:4])
                decade = f"{year // 10 * 10}s"
                decades[decade] += 1
            except ValueError:
                pass
    
    return {
        "top_artists": artists.most_common(10),
        "top_albums": albums.most_common(5),
        "decades": decades.most_common(),
        "total_tracks": len(tracks),
        "unique_artists": len(artists)
    }


def format_duration(ms):
    """Format milliseconds as hours and minutes."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def generate_blog_post(playlist, tracks, analysis, style="nostalgic"):
    """Generate a narrative blog post about the playlist."""
    name = playlist.get("name", "Untitled Playlist")
    description = playlist.get("description", "")
    owner = playlist.get("owner", {}).get("display_name", "Unknown")
    total_duration = sum(
        (item.get("track") or {}).get("duration_ms", 0) 
        for item in tracks
    )
    
    # Style-specific intros
    intros = {
        "casual": f"So I've been listening to this playlist called **{name}** and honestly? It slaps.",
        "formal": f"This post examines the musical composition of \"{name},\" a carefully curated collection.",
        "nostalgic": f"There's a playlist I keep coming back to. It's called **{name}**, and it's like a time capsule."
    }
    
    intro = intros.get(style, intros["nostalgic"])
    
    # Build the post
    lines = []
    lines.append(f"# {name}\n")
    lines.append(f"*{analysis['total_tracks']} tracks · {format_duration(total_duration)} · {analysis['unique_artists']} artists*\n")
    
    if description:
        lines.append(f"> {description}\n")
    
    lines.append(intro + "\n")
    
    # Decade breakdown
    if analysis["decades"]:
        lines.append("## The Sound of Time\n")
        decade_parts = []
        for decade, count in sorted(analysis["decades"], key=lambda x: x[0]):
            pct = round(count / analysis["total_tracks"] * 100)
            decade_parts.append(f"**{decade}** ({pct}%)")
        lines.append("This playlist spans: " + ", ".join(decade_parts) + "\n")
        
        # Find dominant decade
        top_decade, top_count = analysis["decades"][0]
        if top_count / analysis["total_tracks"] > 0.4:
            lines.append(f"The {top_decade} dominate here, and you can hear it. ")
            if top_decade == "90s":
                lines.append("There's that unmistakable sound - the distorted guitars, the angst, the hooks that still get stuck in your head.\n")
            elif top_decade == "80s":
                lines.append("Synths, big drums, and that glossy production that defined the era.\n")
            elif top_decade == "2000s":
                lines.append("Post-grunge echoes, emo's rise, and indie rock finding its footing.\n")
    
    # Top artists section
    lines.append("## The Artists\n")
    lines.append("Some names keep coming back:\n")
    for artist, count in analysis["top_artists"][:5]:
        if count > 1:
            lines.append(f"- **{artist}** ({count} tracks)")
        else:
            lines.append(f"- **{artist}**")
    lines.append("")
    
    top_artist = analysis["top_artists"][0][0] if analysis["top_artists"] else None
    if top_artist:
        lines.append(f"The most represented artist is {top_artist}. That tells you something about what this playlist means.\n")
    
    # Sample tracks section
    lines.append("## Standout Tracks\n")
    lines.append("A few tracks that define the vibe:\n")
    
    # Pick some representative tracks (first, middle, and a few randoms)
    sample_indices = [0, len(tracks)//3, len(tracks)//2, len(tracks)*2//3, -1]
    seen = set()
    for i in sample_indices:
        if i < len(tracks):
            track = tracks[i].get("track")
            if track and track["name"] not in seen:
                seen.add(track["name"])
                artist_names = ", ".join(a["name"] for a in track.get("artists", [])[:2])
                album = track.get("album", {}).get("name", "")
                lines.append(f"- **\"{track['name']}\"** by {artist_names}")
                if len(seen) >= 5:
                    break
    lines.append("")
    
    # Closing
    closings = {
        "casual": "Anyway, give it a listen if you're into this kind of thing. No pressure.",
        "formal": "This playlist represents a thoughtful curation of musical works worthy of consideration.",
        "nostalgic": "Music like this doesn't just play in the background. It takes you somewhere. Every track is a door to a different memory, a different version of yourself."
    }
    
    lines.append("---\n")
    lines.append(closings.get(style, closings["nostalgic"]) + "\n")
    
    # Spotify link
    playlist_url = playlist.get("external_urls", {}).get("spotify", "")
    if playlist_url:
        lines.append(f"\n[Listen on Spotify]({playlist_url})")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Turn a Spotify playlist into a blog post"
    )
    parser.add_argument("playlist", help="Spotify playlist URL or ID")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument(
        "-s", "--style", 
        choices=["casual", "formal", "nostalgic"],
        default="nostalgic",
        help="Writing style (default: nostalgic)"
    )
    parser.add_argument("--json", action="store_true", help="Output raw data as JSON")
    
    args = parser.parse_args()
    
    try:
        # Get token and fetch playlist
        token = get_spotify_token()
        playlist_id = extract_playlist_id(args.playlist)
        playlist, tracks = fetch_playlist(token, playlist_id)
        
        # Analyze
        analysis = analyze_playlist(playlist, tracks)
        
        if args.json:
            output = json.dumps({
                "playlist": {
                    "name": playlist.get("name"),
                    "description": playlist.get("description"),
                    "url": playlist.get("external_urls", {}).get("spotify")
                },
                "analysis": analysis
            }, indent=2)
        else:
            output = generate_blog_post(playlist, tracks, analysis, args.style)
        
        # Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"✓ Written to {args.output}", file=sys.stderr)
        else:
            print(output)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
