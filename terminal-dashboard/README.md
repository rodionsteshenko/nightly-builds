# terminal-dashboard (tdb)

A tmux layout manager. Create, save, and restore tmux layouts with zero dependencies.

## Installation

```bash
# Make executable
chmod +x tdb.py

# Optional: symlink to path
ln -s $(pwd)/tdb.py ~/.local/bin/tdb
```

Requires: `tmux` (no Python dependencies)

## Usage

```bash
# List all available layouts
tdb list

# Apply a preset
tdb apply dev          # Inside tmux: splits current window
tdb apply monitor      # Outside tmux: creates new session

# Create new session with specific name
tdb apply dev -s myproject

# Show layout details
tdb show git

# Save current tmux layout
tdb save mysetup -d "My custom setup"

# Create new layout interactively
tdb create

# Delete saved layout
tdb delete mysetup
```

## Built-in Presets

| Name | Description |
|------|-------------|
| `dev` | Editor (60%) + logs (25%) + shell (15%) |
| `monitor` | htop (50%) + disk watch (25%) + netstat (25%) |
| `logs` | Three horizontal panes for log tailing |
| `git` | Git status watch + log + shell |
| `simple` | 50/50 vertical split |
| `quad` | Four equal quadrants |

## Custom Layouts

Layouts are JSON files stored in `~/.config/tdb/layouts/`:

```json
{
  "name": "myproject",
  "description": "My project development layout",
  "panes": [
    {"name": "editor", "size": 60, "command": "nvim ."},
    {"name": "server", "size": 20, "split": "horizontal", "command": "npm run dev"},
    {"name": "tests", "size": 20, "split": "horizontal", "command": "npm test --watch"}
  ]
}
```

### Pane options

- `name`: Pane identifier (for your reference)
- `size`: Percentage of remaining space
- `split`: `horizontal` or `vertical` (default: horizontal)
- `command`: Command to run (supports env vars like `$EDITOR`)
- `target`: Which pane index to split from (for complex layouts like quad)

## How it works

- **Inside tmux**: Splits the current window into panes
- **Outside tmux**: Creates a new detached session

The tool handles both cases automatically.

## Examples

### Quick monitoring session
```bash
tdb apply monitor -s sysmon
tmux attach -t sysmon
```

### Development environment
```bash
cd ~/myproject
tdb apply dev
```

### Save your current layout for later
```bash
# After arranging panes how you like them
tdb save projectx -d "ProjectX dev setup"

# Later, recreate it
tdb apply projectx
```

## Why this exists

Setting up tmux layouts manually is tedious. This tool lets you:
- Apply consistent dev environments across projects
- Share layouts with your team
- Switch contexts quickly (dev → monitoring → debugging)
- Save layouts you've manually crafted
