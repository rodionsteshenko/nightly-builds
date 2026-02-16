#!/usr/bin/env python3
"""context-ledger: AI session context handoff CLI."""

import argparse
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

LEDGER_DIR = ".context-ledger"
SNAPSHOTS_FILE = "snapshots.json"


def get_project_root():
    """Find project root by looking for .git, or use cwd."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            return parent
    return cwd


def get_ledger_path():
    root = get_project_root()
    ledger = root / LEDGER_DIR
    ledger.mkdir(exist_ok=True)
    return ledger


def load_snapshots():
    path = get_ledger_path() / SNAPSHOTS_FILE
    if path.exists():
        return json.loads(path.read_text())
    return []


def save_snapshots(snapshots):
    path = get_ledger_path() / SNAPSHOTS_FILE
    path.write_text(json.dumps(snapshots, indent=2))


def run_git(*args):
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def git_context():
    """Gather context from git state."""
    ctx = {}
    ctx["branch"] = run_git("branch", "--show-current") or "unknown"
    ctx["last_commit"] = run_git("log", "-1", "--oneline") or "no commits"

    # Files changed (staged + unstaged + untracked)
    diff_files = run_git("diff", "--name-only", "HEAD") or ""
    staged = run_git("diff", "--name-only", "--cached") or ""
    untracked = run_git("ls-files", "--others", "--exclude-standard") or ""

    all_files = set()
    for chunk in [diff_files, staged, untracked]:
        all_files.update(f for f in chunk.split("\n") if f)

    ctx["files_changed"] = sorted(all_files)

    # Recent commits (last 5)
    log = run_git("log", "--oneline", "-5")
    ctx["recent_commits"] = log.split("\n") if log else []

    # Diff summary
    stat = run_git("diff", "--stat", "HEAD")
    ctx["diff_summary"] = stat or "no changes"

    return ctx


def cmd_capture(args):
    """Capture a context snapshot."""
    snapshots = load_snapshots()
    next_id = max((s["id"] for s in snapshots), default=0) + 1

    git = git_context()

    # Merge explicit files with git-detected files
    files = list(set(git.get("files_changed", []) + (args.files or [])))

    snapshot = {
        "id": next_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "branch": git.get("branch", "unknown"),
        "last_commit": git.get("last_commit", ""),
        "recent_commits": git.get("recent_commits", []),
        "diff_summary": git.get("diff_summary", ""),
        "files_touched": files,
        "task": args.task or "",
        "decisions": args.decisions or [],
        "blockers": args.blockers or "",
        "notes": args.notes or "",
    }

    snapshots.append(snapshot)
    save_snapshots(snapshots)

    print(f"✓ Snapshot #{next_id} captured ({len(files)} files)")
    if not snapshot["task"]:
        print("  Tip: use --task to describe what you were working on")
    return snapshot


def cmd_handoff(args):
    """Generate a handoff prompt from the latest (or specified) snapshot."""
    snapshots = load_snapshots()
    if not snapshots:
        print("No snapshots found. Run 'capture' first.", file=sys.stderr)
        sys.exit(1)

    if args.id:
        snap = next((s for s in snapshots if s["id"] == args.id), None)
        if not snap:
            print(f"Snapshot #{args.id} not found.", file=sys.stderr)
            sys.exit(1)
    else:
        snap = snapshots[-1]

    # Build handoff prompt
    lines = [
        "## Session Context Handoff",
        "",
        f"**Previous session:** {snap['timestamp']}",
        f"**Branch:** {snap['branch']}",
        f"**Last commit:** {snap['last_commit']}",
    ]

    if snap.get("task"):
        lines += ["", f"### Current Task", snap["task"]]

    if snap.get("files_touched"):
        lines += ["", "### Files Touched"]
        for f in snap["files_touched"]:
            lines.append(f"- `{f}`")

    if snap.get("decisions"):
        lines += ["", "### Decisions Made"]
        for d in snap["decisions"]:
            lines.append(f"- {d}")

    if snap.get("blockers"):
        lines += ["", "### Blockers / Open Questions", snap["blockers"]]

    if snap.get("notes"):
        lines += ["", "### Notes", snap["notes"]]

    if snap.get("diff_summary"):
        lines += ["", "### Recent Changes", "```", snap["diff_summary"], "```"]

    if snap.get("recent_commits"):
        lines += ["", "### Recent Commits"]
        for c in snap["recent_commits"]:
            lines.append(f"- {c}")

    lines += [
        "",
        "---",
        "Please review the above context and continue where the previous session left off.",
        "Ask clarifying questions if anything is unclear.",
    ]

    prompt = "\n".join(lines)

    if args.format == "json":
        print(json.dumps(snap, indent=2))
    else:
        print(prompt)


def cmd_list(args):
    """List all snapshots."""
    snapshots = load_snapshots()
    if not snapshots:
        print("No snapshots yet.")
        return

    for s in snapshots:
        ts = s["timestamp"][:19].replace("T", " ")
        task = s.get("task", "")[:50] or "(no task)"
        files = len(s.get("files_touched", []))
        branch = s.get("branch", "?")
        print(f"  #{s['id']:3d}  {ts}  [{branch}]  {files} files  {task}")


def cmd_show(args):
    """Show a specific snapshot."""
    snapshots = load_snapshots()
    snap = next((s for s in snapshots if s["id"] == args.id), None)
    if not snap:
        print(f"Snapshot #{args.id} not found.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(snap, indent=2))


def cmd_diff(args):
    """Compare two snapshots."""
    snapshots = load_snapshots()
    a = next((s for s in snapshots if s["id"] == args.id_a), None)
    b = next((s for s in snapshots if s["id"] == args.id_b), None)

    if not a or not b:
        print("One or both snapshots not found.", file=sys.stderr)
        sys.exit(1)

    files_a = set(a.get("files_touched", []))
    files_b = set(b.get("files_touched", []))

    added = files_b - files_a
    removed = files_a - files_b
    common = files_a & files_b

    print(f"Comparing #{a['id']} → #{b['id']}")
    print(f"  Time gap: {a['timestamp'][:19]} → {b['timestamp'][:19]}")

    if a.get("branch") != b.get("branch"):
        print(f"  Branch: {a.get('branch')} → {b.get('branch')}")

    if added:
        print(f"\n  New files ({len(added)}):")
        for f in sorted(added):
            print(f"    + {f}")
    if removed:
        print(f"\n  Dropped files ({len(removed)}):")
        for f in sorted(removed):
            print(f"    - {f}")
    if common:
        print(f"\n  Continued files ({len(common)}):")
        for f in sorted(common):
            print(f"    = {f}")

    if a.get("task") != b.get("task"):
        print(f"\n  Task changed:")
        print(f"    Was: {a.get('task', '(none)')}")
        print(f"    Now: {b.get('task', '(none)')}")


def cmd_clean(args):
    """Remove old snapshots, keeping the latest N."""
    snapshots = load_snapshots()
    keep = args.keep or 10
    if len(snapshots) <= keep:
        print(f"Only {len(snapshots)} snapshots, nothing to clean.")
        return
    removed = len(snapshots) - keep
    snapshots = snapshots[-keep:]
    save_snapshots(snapshots)
    print(f"Removed {removed} old snapshots, kept {keep}.")


def main():
    parser = argparse.ArgumentParser(
        prog="context-ledger",
        description="AI session context handoff CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # capture
    p = sub.add_parser("capture", help="Capture a context snapshot")
    p.add_argument("--task", "-t", help="What you're working on")
    p.add_argument("--files", "-f", nargs="*", help="Specific files to track")
    p.add_argument("--decisions", "-d", nargs="*", help="Decisions made this session")
    p.add_argument("--blockers", "-b", help="Blockers or open questions")
    p.add_argument("--notes", "-n", help="Free-form notes")

    # handoff
    p = sub.add_parser("handoff", help="Generate handoff prompt")
    p.add_argument("--id", type=int, help="Snapshot ID (default: latest)")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")

    # list
    sub.add_parser("list", help="List all snapshots")

    # show
    p = sub.add_parser("show", help="Show a snapshot")
    p.add_argument("id", type=int)

    # diff
    p = sub.add_parser("diff", help="Compare two snapshots")
    p.add_argument("id_a", type=int)
    p.add_argument("id_b", type=int)

    # clean
    p = sub.add_parser("clean", help="Remove old snapshots")
    p.add_argument("--keep", "-k", type=int, default=10)

    args = parser.parse_args()

    commands = {
        "capture": cmd_capture,
        "handoff": cmd_handoff,
        "list": cmd_list,
        "show": cmd_show,
        "diff": cmd_diff,
        "clean": cmd_clean,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
