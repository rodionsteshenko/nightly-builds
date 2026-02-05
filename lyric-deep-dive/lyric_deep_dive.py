#!/usr/bin/env python3
"""
lyric-deep-dive: Pop-Up Video style deep analysis of song lyrics.

Fetches lyrics, researches context, and generates a comprehensive deep dive
with themes, literary devices, historical context, and fun facts.
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class SongData:
    """Container for all gathered song information."""
    artist: str
    title: str
    lyrics: Optional[str] = None
    album: Optional[str] = None
    year: Optional[str] = None
    genius_url: Optional[str] = None
    genius_annotations: list = None
    context_snippets: list = None
    songfacts: Optional[str] = None
    
    def __post_init__(self):
        if self.genius_annotations is None:
            self.genius_annotations = []
        if self.context_snippets is None:
            self.context_snippets = []


class GeniusClient:
    """Client for Genius API to fetch lyrics and annotations."""
    
    BASE_URL = "https://api.genius.com"
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.environ.get("GENIUS_ACCESS_TOKEN")
        
    def _request(self, endpoint: str) -> Optional[dict]:
        """Make authenticated request to Genius API."""
        if not self.access_token:
            return None
            
        url = f"{self.BASE_URL}{endpoint}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self.access_token}")
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"[Genius API error: {e}]", file=sys.stderr)
            return None
    
    def search(self, query: str) -> Optional[dict]:
        """Search for a song on Genius."""
        encoded = urllib.parse.quote(query)
        return self._request(f"/search?q={encoded}")
    
    def get_song(self, song_id: int) -> Optional[dict]:
        """Get song details by ID."""
        return self._request(f"/songs/{song_id}")


class WebSearcher:
    """Web searcher using Google Custom Search JSON API or fallback."""
    
    @staticmethod
    def search(query: str, num_results: int = 5) -> list:
        """Search and return list of (title, url, snippet) tuples."""
        results = []
        
        # Try Google Custom Search API if keys available
        api_key = os.environ.get("GOOGLE_CUSTOM_SEARCH_API_KEY")
        cx = os.environ.get("GOOGLE_CUSTOM_SEARCH_CX")
        
        if api_key and cx:
            encoded = urllib.parse.quote(query)
            url = f"https://www.googleapis.com/customsearch/v1?q={encoded}&key={api_key}&cx={cx}&num={num_results}"
            
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode())
                    for item in data.get("items", []):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", "")
                        })
                    return results
            except Exception as e:
                print(f"[Google search error: {e}]", file=sys.stderr)
        
        # Fallback: try SearXNG public instances
        searxng_instances = [
            "https://searx.be/search",
            "https://search.bus-hit.me/search",
        ]
        
        for instance in searxng_instances:
            try:
                encoded = urllib.parse.quote(query)
                url = f"{instance}?q={encoded}&format=json&categories=general"
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "Mozilla/5.0 (compatible; lyric-deep-dive/1.0)")
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    for item in data.get("results", [])[:num_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("content", "")
                        })
                    if results:
                        return results
            except Exception:
                continue
        
        # Last resort: try a simple scrape approach that may work
        try:
            # Bing search (sometimes works)
            encoded = urllib.parse.quote(query)
            url = f"https://www.bing.com/search?q={encoded}"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode("utf-8", errors="ignore")
            
            # Extract Bing results
            pattern = r'<a[^>]+href="(https?://[^"]+)"[^>]*>([^<]+)</a>.*?<p[^>]*>([^<]{20,})'
            for match in re.finditer(pattern, html, re.DOTALL):
                href, title, snippet = match.groups()
                if 'bing.com' not in href and 'microsoft.com' not in href:
                    results.append({
                        "title": title.strip()[:100],
                        "url": href,
                        "snippet": snippet.strip()[:200]
                    })
                    if len(results) >= num_results:
                        break
        except Exception as e:
            print(f"[Search fallback error: {e}]", file=sys.stderr)
        
        return results


class LyricsFetcher:
    """Fetches lyrics from various sources."""
    
    @staticmethod
    def build_genius_url(artist: str, title: str) -> str:
        """Build a Genius URL from artist and title."""
        # Genius URL format: https://genius.com/Artist-name-song-title-lyrics
        def slugify(s):
            # Remove special chars, replace spaces with hyphens
            s = re.sub(r'[^\w\s-]', '', s)
            s = re.sub(r'\s+', '-', s.strip())
            return s.capitalize() if s else s
        
        artist_slug = '-'.join(word.capitalize() for word in re.sub(r'[^\w\s]', '', artist).split())
        title_slug = '-'.join(word.lower() for word in re.sub(r'[^\w\s]', '', title).split())
        
        return f"https://genius.com/{artist_slug}-{title_slug}-lyrics"
    
    @staticmethod
    def from_azlyrics(artist: str, title: str) -> Optional[str]:
        """Fetch lyrics from AZLyrics (no API key needed)."""
        # Normalize names for URL
        artist_clean = re.sub(r'[^a-z0-9]', '', artist.lower())
        title_clean = re.sub(r'[^a-z0-9]', '', title.lower())
        
        url = f"https://www.azlyrics.com/lyrics/{artist_clean}/{title_clean}.html"
        
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (compatible; lyric-deep-dive/1.0)")
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode("utf-8", errors="ignore")
        except Exception:
            return None
        
        # AZLyrics format: lyrics in a div after the comment "Usage of azlyrics.com content"
        match = re.search(
            r'<!-- Usage of azlyrics\.com content.*?-->\s*</div>\s*<div[^>]*>(.*?)</div>',
            html, re.DOTALL
        )
        if match:
            lyrics = match.group(1)
            # Clean HTML tags
            lyrics = re.sub(r'<br\s*/?>', '\n', lyrics)
            lyrics = re.sub(r'<[^>]+>', '', lyrics)
            lyrics = lyrics.strip()
            return lyrics
        return None
    
    @staticmethod
    def from_genius_scrape(url: str) -> Optional[str]:
        """Scrape lyrics from a Genius URL."""
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        req.add_header("Accept", "text/html,application/xhtml+xml")
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode("utf-8", errors="ignore")
        except Exception:
            return None
        
        import html as html_module
        
        # Genius uses data-lyrics-container divs
        lyrics_parts = []
        for match in re.finditer(r'data-lyrics-container="true"[^>]*>(.*?)</div>', html, re.DOTALL):
            part = match.group(1)
            # Convert br to newlines
            part = re.sub(r'<br\s*/?>', '\n', part)
            # Remove remaining HTML but preserve structure
            part = re.sub(r'<[^>]+>', '', part)
            part = html_module.unescape(part)
            lyrics_parts.append(part.strip())
        
        if lyrics_parts:
            lyrics = '\n\n'.join(lyrics_parts)
            # Clean up header cruft (contributor counts, etc.)
            lyrics = re.sub(r'^\d+\s+Contributors?.*?(?=\n|\[|[A-Z])', '', lyrics, flags=re.IGNORECASE)
            lyrics = re.sub(r'^Translations?\s*', '', lyrics, flags=re.IGNORECASE)
            return lyrics.strip()
        
        # Fallback: try JSON-LD embedded data
        json_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if isinstance(data, dict) and data.get("lyrics"):
                    return html_module.unescape(data["lyrics"].get("text", ""))
            except:
                pass
        
        return None


def gather_song_data(artist: str, title: str) -> SongData:
    """Gather all available data about a song."""
    data = SongData(artist=artist, title=title)
    
    print(f"🎵 Researching: {artist} - {title}", file=sys.stderr)
    
    # Try Genius API first
    genius = GeniusClient()
    search_results = genius.search(f"{artist} {title}")
    
    if search_results and search_results.get("response", {}).get("hits"):
        hit = search_results["response"]["hits"][0]["result"]
        data.genius_url = hit.get("url")
        
        # Get detailed song info
        song_details = genius.get_song(hit["id"])
        if song_details:
            song = song_details.get("response", {}).get("song", {})
            if song.get("album"):
                data.album = song["album"].get("name")
            data.year = song.get("release_date_for_display", "")[:4] if song.get("release_date_for_display") else None
        
        # Scrape lyrics from Genius
        if data.genius_url:
            print("  📝 Fetching lyrics from Genius...", file=sys.stderr)
            data.lyrics = LyricsFetcher.from_genius_scrape(data.genius_url)
    
    # If no Genius API token, try direct URL construction first
    if not data.genius_url:
        print("  🔍 Trying direct Genius URL...", file=sys.stderr)
        guessed_url = LyricsFetcher.build_genius_url(artist, title)
        print(f"  📝 Trying: {guessed_url}", file=sys.stderr)
        data.lyrics = LyricsFetcher.from_genius_scrape(guessed_url)
        if data.lyrics:
            data.genius_url = guessed_url
        else:
            # Fallback: try web search for Genius URL
            print("  🔍 Searching for Genius page...", file=sys.stderr)
            genius_search = WebSearcher.search(f'site:genius.com "{title}" {artist} lyrics')
            for result in genius_search:
                if 'genius.com' in result['url'] and '-lyrics' in result['url']:
                    data.genius_url = result['url']
                    print(f"  📝 Fetching lyrics from Genius...", file=sys.stderr)
                    data.lyrics = LyricsFetcher.from_genius_scrape(data.genius_url)
                    if data.lyrics:
                        break
    
    # Fallback to AZLyrics if no lyrics yet
    if not data.lyrics:
        print("  📝 Trying AZLyrics...", file=sys.stderr)
        data.lyrics = LyricsFetcher.from_azlyrics(artist, title)
    
    # Web search for context
    print("  🔍 Searching for song context...", file=sys.stderr)
    
    # Search for song meaning
    meaning_results = WebSearcher.search(f'"{title}" {artist} song meaning analysis')
    data.context_snippets.extend(meaning_results[:3])
    
    # Search for interviews
    interview_results = WebSearcher.search(f'{artist} interview "{title}" lyrics')
    data.context_snippets.extend(interview_results[:2])
    
    # Search Songfacts specifically
    songfacts_results = WebSearcher.search(f'site:songfacts.com "{title}" {artist}')
    if songfacts_results:
        data.context_snippets.insert(0, songfacts_results[0])
    
    return data


def analyze_lyrics(lyrics: str) -> dict:
    """Perform basic literary analysis of lyrics."""
    if not lyrics:
        return {}
    
    lines = [l for l in lyrics.split('\n') if l.strip()]
    words = lyrics.lower().split()
    
    # Word frequency (excluding common words)
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'to', 'of', 'in',
                  'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
                  'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either', 'neither',
                  'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just', 'i',
                  'me', 'my', 'myself', 'we', 'our', 'ours', 'you', 'your', 'yours',
                  'he', 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'they',
                  'them', 'their', 'this', 'that', 'these', 'those', 'am', 'if'}
    
    word_freq = {}
    for word in words:
        clean = re.sub(r'[^a-z]', '', word)
        if clean and clean not in stop_words and len(clean) > 2:
            word_freq[clean] = word_freq.get(clean, 0) + 1
    
    # Sort by frequency
    top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:10]
    
    # Find repeated lines (potential chorus/hook)
    line_freq = {}
    for line in lines:
        clean = line.strip().lower()
        if len(clean) > 10:  # Ignore short lines
            line_freq[clean] = line_freq.get(clean, 0) + 1
    
    repeated_lines = [(l, c) for l, c in line_freq.items() if c > 1]
    repeated_lines.sort(key=lambda x: -x[1])
    
    # Literary devices detection (simple heuristics)
    devices = []
    
    # Alliteration
    for line in lines:
        words_in_line = line.lower().split()
        if len(words_in_line) >= 3:
            first_letters = [w[0] for w in words_in_line if w and w[0].isalpha()]
            for i in range(len(first_letters) - 2):
                if first_letters[i] == first_letters[i+1] == first_letters[i+2]:
                    devices.append(("alliteration", line.strip()))
                    break
    
    # Rhyme scheme (check end words)
    end_words = []
    for line in lines:
        words_in_line = line.split()
        if words_in_line:
            end_words.append(re.sub(r'[^a-z]', '', words_in_line[-1].lower()))
    
    # Questions (rhetorical?)
    questions = [l for l in lines if '?' in l]
    if questions:
        devices.append(("rhetorical questions", len(questions)))
    
    # Repetition/anaphora
    line_starts = [l.split()[0].lower() if l.split() else '' for l in lines]
    start_freq = {}
    for start in line_starts:
        if start:
            start_freq[start] = start_freq.get(start, 0) + 1
    anaphora = [(w, c) for w, c in start_freq.items() if c >= 3]
    if anaphora:
        devices.append(("anaphora", anaphora))
    
    return {
        "line_count": len(lines),
        "word_count": len(words),
        "unique_words": len(set(words)),
        "top_words": top_words,
        "repeated_lines": repeated_lines[:5],
        "literary_devices": devices[:5],
        "questions": questions
    }


def generate_deep_dive(data: SongData, analysis: dict) -> str:
    """Generate the formatted deep dive output."""
    output = []
    
    # Header
    output.append(f"# {data.title}")
    output.append(f"**{data.artist}**", )
    if data.album or data.year:
        meta = []
        if data.album:
            meta.append(f"*{data.album}*")
        if data.year:
            meta.append(data.year)
        output.append(" · ".join(meta))
    output.append("")
    
    # Lyrics section
    if data.lyrics:
        output.append("## 📜 Lyrics")
        output.append("")
        # Format lyrics with some structure
        for para in data.lyrics.split('\n\n'):
            output.append(para.strip())
            output.append("")
    else:
        output.append("*Lyrics not found - try searching manually*")
        output.append("")
    
    # Analysis section
    output.append("## 🔬 Lyrical Analysis")
    output.append("")
    
    if analysis:
        output.append(f"- **Word count:** {analysis.get('word_count', 'N/A')}")
        output.append(f"- **Unique words:** {analysis.get('unique_words', 'N/A')}")
        output.append(f"- **Vocabulary density:** {analysis.get('unique_words', 0) / max(analysis.get('word_count', 1), 1):.1%}")
        output.append("")
        
        if analysis.get("top_words"):
            output.append("### Key Words")
            top = [f"**{w}** ({c})" for w, c in analysis["top_words"][:8]]
            output.append(", ".join(top))
            output.append("")
        
        if analysis.get("repeated_lines"):
            output.append("### Repeated Lines (Hook/Chorus)")
            for line, count in analysis["repeated_lines"][:3]:
                output.append(f"- *\"{line[:60]}{'...' if len(line) > 60 else ''}\"* (×{count})")
            output.append("")
        
        if analysis.get("literary_devices"):
            output.append("### Literary Devices Detected")
            for device in analysis["literary_devices"]:
                if device[0] == "rhetorical questions":
                    output.append(f"- **Rhetorical questions:** {device[1]} found")
                elif device[0] == "alliteration":
                    output.append(f"- **Alliteration:** *\"{device[1][:50]}...\"*")
                elif device[0] == "anaphora":
                    words = ", ".join([f"'{w}'" for w, _ in device[1][:3]])
                    output.append(f"- **Anaphora:** Lines beginning with {words}")
            output.append("")
    
    # Context section
    if data.context_snippets:
        output.append("## 📚 Context & Research")
        output.append("")
        for item in data.context_snippets[:6]:
            output.append(f"### [{item['title'][:60]}]({item['url']})")
            output.append(f"> {item['snippet'][:200]}{'...' if len(item['snippet']) > 200 else ''}")
            output.append("")
    
    # Links
    output.append("## 🔗 Resources")
    output.append("")
    if data.genius_url:
        output.append(f"- [Genius (lyrics + annotations)]({data.genius_url})")
    output.append(f"- [Songfacts](https://www.songfacts.com/search/songs/{urllib.parse.quote(data.title)})")
    output.append(f"- [YouTube search](https://www.youtube.com/results?search_query={urllib.parse.quote(f'{data.artist} {data.title}')})")
    output.append("")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a deep dive analysis of song lyrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Radiohead" "Fake Plastic Trees"
  %(prog)s "Taylor Swift" "All Too Well"
  %(prog)s --json "The National" "Fake Empire"
  
Environment variables:
  GENIUS_ACCESS_TOKEN  - Genius API token for better lyrics/metadata
        """
    )
    parser.add_argument("artist", help="Artist name")
    parser.add_argument("title", help="Song title")
    parser.add_argument("--json", "-j", action="store_true", 
                        help="Output raw data as JSON")
    parser.add_argument("--lyrics-only", "-l", action="store_true",
                        help="Only fetch and display lyrics")
    parser.add_argument("--no-analysis", action="store_true",
                        help="Skip lyrical analysis")
    
    args = parser.parse_args()
    
    # Gather data
    data = gather_song_data(args.artist, args.title)
    
    if args.lyrics_only:
        if data.lyrics:
            print(data.lyrics)
        else:
            print("Lyrics not found", file=sys.stderr)
            sys.exit(1)
        return
    
    # Analyze
    analysis = {} if args.no_analysis else analyze_lyrics(data.lyrics or "")
    
    if args.json:
        output = {
            "artist": data.artist,
            "title": data.title,
            "album": data.album,
            "year": data.year,
            "lyrics": data.lyrics,
            "genius_url": data.genius_url,
            "context": data.context_snippets,
            "analysis": analysis
        }
        print(json.dumps(output, indent=2))
    else:
        # Generate formatted output
        print(generate_deep_dive(data, analysis))


if __name__ == "__main__":
    main()
