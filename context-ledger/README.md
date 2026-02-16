# context-ledger

A CLI tool for capturing and handing off context between AI coding sessions.

When you switch between Claude Code, Cursor, Codex, or any AI coding agent, you lose context. You re-explain everything. context-ledger captures a structured snapshot of where you are and generates a handoff prompt for the next session.

## Install

```bash
pip install context-ledger
# or just copy the script
chmod +x context-ledger.py
```

## Usage

### Capture context at end of a session

```bash
# Auto-detect from git state
context-ledger capture

# With explicit details
context-ledger capture --task "Implementing OAuth flow" --blockers "Token refresh not working" --notes "Check the middleware order"

# Capture with specific files
context-ledger capture --files src/auth.py src/middleware.py
```

### Generate a handoff prompt for the next session

```bash
# Get a prompt to paste into your next AI session
context-ledger handoff

# Handoff a specific snapshot
context-ledger handoff --id 3

# Copy to clipboard
context-ledger handoff | pbcopy
```

### List past snapshots

```bash
context-ledger list
context-ledger show 3
```

### Diff between snapshots

```bash
context-ledger diff 3 5
```

## What it captures

- **Files touched** (from git diff or explicit)
- **Current task** description
- **Decisions made** during the session
- **Blockers** and open questions
- **Branch and commit** info
- **Free-form notes**
- **Timestamp and session duration**

## Storage

Snapshots are stored in `.context-ledger/` in your project root (JSON files). Add it to `.gitignore` or commit it — your call.

## Philosophy

This isn't a full project management tool. It's a sticky note for your AI sessions. Capture fast, handoff clean.
