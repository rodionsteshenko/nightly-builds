# quote-bank

Personal quote collector and retriever. Save memorable lines from TV shows, movies, books, and life.

## Installation

```bash
chmod +x quote
# Optionally symlink to your PATH:
ln -s $(pwd)/quote /usr/local/bin/quote
```

## Usage

### Add quotes

```bash
quote add "I've made a huge mistake." --source "Arrested Development" --speaker "Gob"
quote add "Cool. Cool cool cool." --source "Community" --speaker "Abed" --tags sitcom,catchphrase
quote add "Whatever you do, do it well." --source "Walt Disney" --tags wisdom,motivation
```

### Get a random quote

```bash
quote random              # Any quote (fortune cookie style)
quote random --tag wisdom # Only quotes tagged 'wisdom'
quote random --source Community  # Only from Community
```

### Search

```bash
quote search "mistake"   # Full-text search
quote search "Community" # Also searches sources
quote search "wisdom"    # And tags
```

### List and filter

```bash
quote list                        # All quotes (most recent first)
quote list --source "Community"   # Filter by source
quote list --tag catchphrase      # Filter by tag
quote list --speaker "Abed"       # Filter by speaker
quote list --sort source          # Sort by source instead of date
quote list --limit 10             # Show only 10
quote list --ids                  # Include IDs for deletion
```

### View sources and tags

```bash
quote sources   # List all sources with counts
quote tags      # List all tags with counts
quote stats     # Collection statistics
```

### Export

```bash
quote export                    # Markdown to stdout
quote export --by-source        # Grouped by source
quote export -o quotes.md       # Write to file
quote export --source Community # Export only Community quotes
```

### Import

```bash
quote import quotes.json
```

Import format (array of objects):
```json
[
  {"text": "The quote", "source": "Source", "speaker": "Speaker", "tags": ["tag1"]}
]
```

### Delete

```bash
quote list --ids     # Find the ID
quote delete 42      # Delete by ID
```

## Storage

Quotes are stored in `~/.config/quotes/quotes.json`.

## Tips

- Run `quote` with no arguments to get a random quote (if you have any)
- Add your terminal startup script: `quote random` in `.bashrc` or `.zshrc`
- Use tags for moods: `--tags funny,sad,inspiring`
- Quote yourself! `--source "Me" --tags shower-thoughts`

## Zero Dependencies

Just Python 3.6+ standard library.
