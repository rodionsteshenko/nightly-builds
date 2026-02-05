#!/usr/bin/env python3
"""
terminal-dashboard (tdb) - Tmux layout manager

Create, save, and restore tmux layouts from simple config files.
No external dependencies.
"""

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".config" / "tdb"
LAYOUTS_DIR = CONFIG_DIR / "layouts"

# Built-in presets
PRESETS = {
    "dev": {
        "name": "dev",
        "description": "Development layout: editor + logs + shell",
        "panes": [
            {"name": "editor", "size": 60, "command": "$EDITOR ."},
            {"name": "logs", "size": 25, "command": "tail -f /dev/null", "split": "horizontal"},
            {"name": "shell", "size": 15, "command": None, "split": "horizontal"}
        ]
    },
    "monitor": {
        "name": "monitor", 
        "description": "System monitoring: htop + disk + network",
        "panes": [
            {"name": "htop", "size": 50, "command": "htop || top"},
            {"name": "disk", "size": 25, "command": "watch -n 5 df -h", "split": "horizontal"},
            {"name": "net", "size": 25, "command": "watch -n 2 'netstat -an | head -30'", "split": "horizontal"}
        ]
    },
    "logs": {
        "name": "logs",
        "description": "Log watching: multiple tail panes",
        "panes": [
            {"name": "main", "size": 50, "command": None},
            {"name": "log1", "size": 25, "command": None, "split": "horizontal"},
            {"name": "log2", "size": 25, "command": None, "split": "horizontal"}
        ]
    },
    "git": {
        "name": "git",
        "description": "Git workflow: status + log + shell",
        "panes": [
            {"name": "status", "size": 40, "command": "watch -n 2 git status -s"},
            {"name": "log", "size": 30, "command": "git log --oneline -20; read", "split": "horizontal"},
            {"name": "shell", "size": 30, "command": None, "split": "horizontal"}
        ]
    },
    "simple": {
        "name": "simple",
        "description": "Simple 50/50 horizontal split",
        "panes": [
            {"name": "left", "size": 50, "command": None},
            {"name": "right", "size": 50, "command": None, "split": "vertical"}
        ]
    },
    "quad": {
        "name": "quad",
        "description": "Four equal quadrants",
        "panes": [
            {"name": "tl", "size": 50, "command": None},
            {"name": "tr", "size": 50, "command": None, "split": "vertical"},
            {"name": "bl", "size": 50, "command": None, "split": "horizontal", "target": 0},
            {"name": "br", "size": 50, "command": None, "split": "horizontal", "target": 1}
        ]
    }
}


def ensure_config_dir():
    """Create config directories if they don't exist."""
    LAYOUTS_DIR.mkdir(parents=True, exist_ok=True)


def is_in_tmux() -> bool:
    """Check if we're running inside tmux."""
    return os.environ.get("TMUX") is not None


def run_tmux(args: list, capture: bool = False) -> tuple[int, str]:
    """Run a tmux command."""
    try:
        result = subprocess.run(
            ["tmux"] + args,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout.strip()
    except FileNotFoundError:
        print("Error: tmux not found. Please install tmux first.")
        sys.exit(1)


def get_layout(name: str) -> Optional[dict]:
    """Get a layout by name (preset or saved)."""
    # Check presets first
    if name in PRESETS:
        return PRESETS[name]
    
    # Check saved layouts
    layout_file = LAYOUTS_DIR / f"{name}.json"
    if layout_file.exists():
        with open(layout_file) as f:
            return json.load(f)
    
    return None


def list_layouts():
    """List all available layouts."""
    print("\n📐 Available Layouts\n")
    
    print("Built-in presets:")
    print("-" * 50)
    for name, layout in PRESETS.items():
        desc = layout.get("description", "No description")
        print(f"  {name:12} {desc}")
    
    # Check for saved layouts
    ensure_config_dir()
    saved = list(LAYOUTS_DIR.glob("*.json"))
    if saved:
        print("\nSaved layouts:")
        print("-" * 50)
        for f in sorted(saved):
            name = f.stem
            try:
                with open(f) as file:
                    layout = json.load(file)
                    desc = layout.get("description", "Custom layout")
                    print(f"  {name:12} {desc}")
            except:
                print(f"  {name:12} (error reading)")
    
    print()


def apply_layout(layout: dict, session_name: Optional[str] = None):
    """Apply a layout to create tmux panes."""
    panes = layout.get("panes", [])
    if not panes:
        print("Error: Layout has no panes defined.")
        return False
    
    layout_name = layout.get("name", "custom")
    
    if is_in_tmux():
        # We're inside tmux - apply to current window
        print(f"🔧 Applying layout '{layout_name}' to current window...")
        
        # Get current pane ID
        _, base_pane = run_tmux(["display-message", "-p", "#{pane_id}"], capture=True)
        
        # Track created panes
        created_panes = [base_pane]
        
        # Create additional panes
        for i, pane in enumerate(panes[1:], 1):
            split_type = "-h" if pane.get("split") == "vertical" else "-v"
            size = pane.get("size", 50)
            target_idx = pane.get("target", 0)
            target_pane = created_panes[target_idx] if target_idx < len(created_panes) else base_pane
            
            result = subprocess.run(
                ["tmux", "split-window", split_type, "-p", str(size), "-t", target_pane, "-P", "-F", "#{pane_id}"],
                capture_output=True,
                text=True
            )
            new_pane = result.stdout.strip()
            created_panes.append(new_pane)
        
        # Send commands to panes
        for i, pane in enumerate(panes):
            cmd = pane.get("command")
            if cmd and i < len(created_panes):
                cmd = os.path.expandvars(cmd)
                subprocess.run(["tmux", "send-keys", "-t", created_panes[i], cmd, "Enter"])
        
        # Select first pane
        subprocess.run(["tmux", "select-pane", "-t", created_panes[0]])
        
        print(f"✅ Created {len(panes)} panes")
        
    else:
        # Not in tmux - create new session
        sess = session_name or f"tdb-{layout_name}"
        print(f"🚀 Creating tmux session '{sess}' with layout '{layout_name}'...")
        
        # Kill existing session with same name
        run_tmux(["kill-session", "-t", sess])
        
        # Create session with first pane
        first_cmd = panes[0].get("command")
        if first_cmd:
            first_cmd = os.path.expandvars(first_cmd)
            subprocess.run(["tmux", "new-session", "-d", "-s", sess, "-x", "200", "-y", "50", first_cmd])
        else:
            subprocess.run(["tmux", "new-session", "-d", "-s", sess, "-x", "200", "-y", "50"])
        
        # Get first pane ID
        _, first_pane = run_tmux(["list-panes", "-t", sess, "-F", "#{pane_id}"], capture=True)
        created_panes = [first_pane.split('\n')[0]]
        
        # Create additional panes
        for i, pane in enumerate(panes[1:], 1):
            split_type = "-h" if pane.get("split") == "vertical" else "-v"
            size = pane.get("size", 50)
            target_idx = pane.get("target", 0)
            target = f"{sess}:0.{target_idx}"
            
            cmd = pane.get("command", "")
            if cmd:
                cmd = os.path.expandvars(cmd)
            
            result = subprocess.run(
                ["tmux", "split-window", split_type, "-p", str(size), "-t", target, "-P", "-F", "#{pane_id}"],
                capture_output=True,
                text=True
            )
            created_panes.append(result.stdout.strip())
            
            if cmd:
                subprocess.run(["tmux", "send-keys", "-t", created_panes[-1], cmd, "Enter"])
        
        # Select first pane
        subprocess.run(["tmux", "select-pane", "-t", f"{sess}:0.0"])
        
        print(f"✅ Session '{sess}' created with {len(panes)} panes")
        print(f"   Attach: tmux attach -t {sess}")
    
    return True


def save_layout(name: str, layout: dict):
    """Save a layout to config directory."""
    ensure_config_dir()
    layout_file = LAYOUTS_DIR / f"{name}.json"
    
    with open(layout_file, 'w') as f:
        json.dump(layout, f, indent=2)
    
    print(f"✅ Layout saved to {layout_file}")


def save_current(name: str, description: str = ""):
    """Save current tmux layout (simplified)."""
    if not is_in_tmux():
        print("Error: Not in a tmux session. Can't save current layout.")
        return False
    
    # Get pane count
    _, output = run_tmux(["list-panes", "-F", "#{pane_index}"], capture=True)
    pane_count = len(output.strip().split('\n')) if output else 1
    
    panes = []
    for i in range(pane_count):
        pane = {"name": f"pane{i}", "size": 50, "command": None}
        if i > 0:
            pane["split"] = "horizontal"
        panes.append(pane)
    
    layout = {
        "name": name,
        "description": description or "Saved layout",
        "panes": panes
    }
    
    save_layout(name, layout)
    return True


def create_layout_interactive():
    """Interactive layout creator."""
    print("\n🎨 Create New Layout\n")
    
    name = input("Layout name: ").strip()
    if not name:
        print("Cancelled.")
        return
    
    description = input("Description: ").strip()
    
    panes = []
    print("\nDefine panes (empty name to finish):\n")
    
    while True:
        pane_num = len(panes) + 1
        pane_name = input(f"Pane {pane_num} name: ").strip()
        if not pane_name:
            break
        
        pane = {"name": pane_name}
        
        if pane_num > 1:
            split = input("  Split (h=horizontal, v=vertical) [h]: ").strip().lower()
            pane["split"] = "vertical" if split == 'v' else "horizontal"
        
        size = input("  Size % [50]: ").strip()
        pane["size"] = int(size) if size.isdigit() else 50
        
        cmd = input("  Command (optional): ").strip()
        pane["command"] = cmd if cmd else None
        
        panes.append(pane)
        print()
    
    if not panes:
        print("No panes defined. Cancelled.")
        return
    
    layout = {
        "name": name,
        "description": description,
        "panes": panes
    }
    
    save_layout(name, layout)
    print(f"\n✅ Layout '{name}' created with {len(panes)} panes")


def show_layout(name: str):
    """Show details of a layout."""
    layout = get_layout(name)
    if not layout:
        print(f"Layout '{name}' not found.")
        return
    
    print(f"\n📐 Layout: {layout.get('name', name)}")
    desc = layout.get('description')
    if desc:
        print(f"   {desc}")
    print()
    
    panes = layout.get('panes', [])
    print("   #   Name         Split       Size  Command")
    print("   " + "-" * 55)
    for i, pane in enumerate(panes):
        split = pane.get('split', '-') if i > 0 else '-'
        cmd = pane.get('command') or '(shell)'
        if len(cmd) > 20:
            cmd = cmd[:17] + "..."
        size = f"{pane.get('size', 50)}%"
        print(f"   {i}   {pane.get('name', f'pane{i}'):12} {split:11} {size:5} {cmd}")
    print()


def delete_layout(name: str):
    """Delete a saved layout."""
    if name in PRESETS:
        print(f"Error: Can't delete built-in preset '{name}'")
        return
    
    layout_file = LAYOUTS_DIR / f"{name}.json"
    if layout_file.exists():
        layout_file.unlink()
        print(f"✅ Deleted layout '{name}'")
    else:
        print(f"Layout '{name}' not found.")


def main():
    parser = argparse.ArgumentParser(
        description="tdb - Terminal Dashboard (tmux layout manager)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tdb list                    List all layouts
  tdb apply dev               Apply 'dev' preset
  tdb apply monitor -s mon    Create session 'mon' with monitor layout  
  tdb show git                Show details of 'git' layout
  tdb create                  Interactive layout creator
  tdb save mysetup            Save current tmux layout
  tdb delete mysetup          Delete a saved layout
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # list
    subparsers.add_parser("list", aliases=["ls", "l"], help="List available layouts")
    
    # apply
    apply_p = subparsers.add_parser("apply", aliases=["a", "use"], help="Apply a layout")
    apply_p.add_argument("name", help="Layout name")
    apply_p.add_argument("-s", "--session", help="Session name (when not in tmux)")
    
    # show
    show_p = subparsers.add_parser("show", aliases=["info"], help="Show layout details")
    show_p.add_argument("name", help="Layout name")
    
    # create
    subparsers.add_parser("create", aliases=["new"], help="Create new layout interactively")
    
    # save
    save_p = subparsers.add_parser("save", help="Save current tmux layout")
    save_p.add_argument("name", help="Name for saved layout")
    save_p.add_argument("-d", "--description", default="", help="Description")
    
    # delete
    del_p = subparsers.add_parser("delete", aliases=["rm"], help="Delete a saved layout")
    del_p.add_argument("name", help="Layout name to delete")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cmd = args.command
    
    if cmd in ("list", "ls", "l"):
        list_layouts()
    
    elif cmd in ("apply", "a", "use"):
        layout = get_layout(args.name)
        if layout:
            apply_layout(layout, args.session)
        else:
            print(f"Layout '{args.name}' not found. Use 'tdb list' to see available.")
    
    elif cmd in ("show", "info"):
        show_layout(args.name)
    
    elif cmd in ("create", "new"):
        create_layout_interactive()
    
    elif cmd == "save":
        save_current(args.name, args.description)
    
    elif cmd in ("delete", "rm"):
        delete_layout(args.name)


if __name__ == "__main__":
    main()
