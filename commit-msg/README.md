# commit-msg

AI-assisted git commit message generator using Claude CLI.

## Features

- Reads staged diff and generates conventional commit messages
- Learns from your recent commit style (optional)
- Interactive mode: accept, edit, regenerate, or quit
- Supports all conventional commit types (feat, fix, docs, etc.)
- Handles large diffs by intelligent truncation

## Installation

```bash
# Copy to your PATH
cp commit-msg ~/.local/bin/
# or symlink
ln -s ~/clawd/nightly-build/projects/commit-msg/commit-msg ~/.local/bin/commit-msg
```

Requires:
- Python 3.7+
- Claude CLI (`npm install -g @anthropic-ai/claude-cli`)
- Git

## Usage

```bash
# Basic usage - stage changes, run commit-msg
git add .
commit-msg

# Auto-commit without prompting
commit-msg -y

# Specify scope
commit-msg -s api

# Hint at commit type
commit-msg --type fix

# Preview without committing
commit-msg --dry-run

# Skip style analysis
commit-msg --no-style
```

## Workflow

1. Stage your changes with `git add`
2. Run `commit-msg`
3. Review the suggested message
4. Choose:
   - **[a]ccept** - commit with the message
   - **[e]dit** - open in your $EDITOR
   - **[r]egenerate** - ask Claude for a new suggestion
   - **[q]uit** - abort

## Conventional Commits

Generated messages follow the conventional commit format:

```
<type>(<scope>): <description>
```

Types:
- `feat` - new feature
- `fix` - bug fix
- `docs` - documentation
- `style` - formatting
- `refactor` - code restructuring
- `perf` - performance improvement
- `test` - adding/fixing tests
- `build` - build system changes
- `ci` - CI configuration
- `chore` - other changes
- `revert` - reverting commits

## Git Hook (optional)

Use as a prepare-commit-msg hook:

```bash
# .git/hooks/prepare-commit-msg
#!/bin/bash
if [ -z "$2" ]; then
    commit-msg --dry-run > "$1"
fi
```

## Examples

```
$ git add src/api/users.py
$ commit-msg

📁 Staged changes:
 src/api/users.py | 23 ++++++++++++-----------
 1 file changed, 12 insertions(+), 11 deletions(-)

🤖 Generating commit message...

💬 Suggested message:
   refactor(api): simplify user validation logic

[a]ccept, [e]dit, [r]egenerate, [q]uit? a
✅ Committed!
```

## Notes

- Uses Claude CLI (your existing subscription, not API)
- Truncates large diffs to ~8000 chars to stay within context limits
- Analyzes last 5 commits for style matching (disable with --no-style)
