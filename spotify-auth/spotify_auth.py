#!/usr/bin/env python3
"""
Spotify OAuth Authorization Flow

Run this script to authorize Clawdbot to access your Spotify account.
Opens a browser, you approve, and tokens are saved for future use.

Usage:
    python spotify_auth.py

Tokens saved to: ~/.spotify_tokens.json
"""

import http.server
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

# Spotify OAuth settings
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8888/callback"
TOKEN_FILE = Path.home() / ".spotify_tokens.json"

# Scopes we need for full access
SCOPES = [
    "user-read-private",
    "user-read-email",
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "user-read-recently-played",
    "user-top-read",
    "user-library-read",
    "user-library-modify",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-follow-read",
    "user-follow-modify",
]


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handle the OAuth callback from Spotify."""
    
    auth_code = None
    state = None
    error = None
    
    def do_GET(self):
        """Handle GET request (the callback)."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if parsed.path == "/callback":
            if "code" in params:
                OAuthCallbackHandler.auth_code = params["code"][0]
                OAuthCallbackHandler.state = params.get("state", [None])[0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                    <head><title>Spotify Authorization</title></head>
                    <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                        <h1>Authorization Successful!</h1>
                        <p>You can close this window and return to the terminal.</p>
                    </body>
                    </html>
                """)
            elif "error" in params:
                OAuthCallbackHandler.error = params["error"][0]
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f"""
                    <html>
                    <head><title>Authorization Failed</title></head>
                    <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                        <h1>Authorization Failed</h1>
                        <p>Error: {OAuthCallbackHandler.error}</p>
                    </body>
                    </html>
                """.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress logging."""
        pass


def get_auth_url(state: str) -> str:
    """Build the Spotify authorization URL."""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": state,
        "show_dialog": "true",
    }
    return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access and refresh tokens."""
    url = "https://accounts.spotify.com/api/token"
    
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }).encode()
    
    # Basic auth header
    import base64
    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def refresh_access_token(refresh_token: str) -> dict:
    """Use refresh token to get a new access token."""
    url = "https://accounts.spotify.com/api/token"
    
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()
    
    import base64
    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def save_tokens(tokens: dict) -> None:
    """Save tokens to file."""
    TOKEN_FILE.write_text(json.dumps(tokens, indent=2))
    print(f"Tokens saved to {TOKEN_FILE}")


def load_tokens() -> dict | None:
    """Load tokens from file."""
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return None


def get_valid_token() -> str | None:
    """Get a valid access token, refreshing if needed."""
    tokens = load_tokens()
    if not tokens:
        return None
    
    # Try to use the access token
    # If it fails, refresh it
    try:
        # Test the token
        req = urllib.request.Request(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        urllib.request.urlopen(req)
        return tokens["access_token"]
    except urllib.error.HTTPError as e:
        if e.code == 401 and "refresh_token" in tokens:
            # Token expired, refresh it
            print("Access token expired, refreshing...")
            new_tokens = refresh_access_token(tokens["refresh_token"])
            # Keep the refresh token if not returned
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = tokens["refresh_token"]
            save_tokens(new_tokens)
            return new_tokens["access_token"]
        raise


def test_connection(access_token: str) -> dict:
    """Test the connection by fetching user profile."""
    req = urllib.request.Request(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    """Run the OAuth flow."""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set")
        sys.exit(1)
    
    # Check if we already have valid tokens
    existing_token = None
    try:
        existing_token = get_valid_token()
    except:
        pass
    
    if existing_token:
        print("Already authorized! Testing connection...")
        user = test_connection(existing_token)
        print(f"Connected as: {user.get('display_name')} ({user.get('email')})")
        print(f"Token file: {TOKEN_FILE}")
        return
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(16)
    
    # Start local server
    server = http.server.HTTPServer(("localhost", 8888), OAuthCallbackHandler)
    
    # Open browser to auth URL
    auth_url = get_auth_url(state)
    print("Opening browser for Spotify authorization...")
    print(f"If it doesn't open, visit: {auth_url}")
    webbrowser.open(auth_url)
    
    # Wait for callback
    print("Waiting for authorization...")
    server.handle_request()
    
    if OAuthCallbackHandler.error:
        print(f"Authorization failed: {OAuthCallbackHandler.error}")
        sys.exit(1)
    
    if not OAuthCallbackHandler.auth_code:
        print("No authorization code received")
        sys.exit(1)
    
    if OAuthCallbackHandler.state != state:
        print("State mismatch - possible CSRF attack")
        sys.exit(1)
    
    # Exchange code for tokens
    print("Exchanging code for tokens...")
    tokens = exchange_code_for_tokens(OAuthCallbackHandler.auth_code)
    save_tokens(tokens)
    
    # Test the connection
    print("Testing connection...")
    user = test_connection(tokens["access_token"])
    print(f"\n✓ Successfully connected as: {user.get('display_name')} ({user.get('email')})")
    print(f"✓ Tokens saved to: {TOKEN_FILE}")
    print("\nYou're all set! Spotify integration is ready.")


if __name__ == "__main__":
    main()
