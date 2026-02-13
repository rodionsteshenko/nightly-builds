# ports

The process/port commands you could never remember.

```
          ┌─────────────────────────────────────┐
          │  "What's on port 3000?"            │
          │                                     │
          │  lsof -iTCP:3000 -sTCP:LISTEN -P -n │
          │                                     │
          │  ...who can remember that?          │
          └─────────────────────────────────────┘
```

## Install

```bash
# Clone and link (or just copy the script)
ln -sf ~/clawd/nightly-build/projects/ports/ports /usr/local/bin/ports

# Or just run directly
./ports who 3000
```

## Usage

### What's using a port?

```bash
ports who 3000
ports who :8080  # colon prefix works too
```

Output:
```
Port 3000 is in use:

  Process:  node
  PID:      12345
  User:     rodion
  CWD:      /Users/rodion/myapp
  Command:  node server.js
  Started:  Thu Feb 12 20:30:00 2026
```

### List all listening ports

```bash
ports list
```

Output:
```
Listening ports:

  PORT     PID      PROCESS             
  -------- -------- --------------------
  3000     12345    node                
  5173     12346    node                
  8080     12347    java
```

### Kill a process by port

```bash
ports kill 3000           # asks for confirmation
ports kill 3000 -y        # skip confirmation
ports kill 3000 -y -f     # force kill (SIGKILL) if grace period expires
ports kill 3000 -g 5      # wait 5 seconds before force kill
```

### Check if a port is free

```bash
ports free 3000 && echo "Let's go!" || echo "Occupied"
```

Returns exit code 0 if free, 1 if in use. Great for scripts.

### Learn the incantations

The real power: understand what's happening under the hood.

```bash
ports explain who
```

Output:
```
who:

  Command:
    lsof -iTCP:3000 -sTCP:LISTEN -P -n

  Explanation:
    lsof = list open files (including network sockets)
      -iTCP:3000  → filter to TCP connections on this port
      -sTCP:LISTEN  → only show listeners (not clients)
      -P            → don't convert port numbers to names
      -n            → don't resolve hostnames (faster)

  Platform: macOS
```

Or explain everything:

```bash
ports explain all
```

## Philosophy

1. **Safety first** — `kill` asks for confirmation by default
2. **Explainability** — learn the real commands, don't just cargo-cult
3. **Cross-platform** — works on macOS (lsof) and Linux (ss)
4. **No dependencies** — pure Python 3, uses only standard library

## Why?

Because every time you need to find what's on a port, you end up googling "lsof port" or "netstat port mac" and copying some incantation you don't understand.

This tool:
- Wraps the common operations with memorable verbs
- Adds safety rails (confirmation before kill)
- **Teaches you** what's happening (the `explain` command)

Eventually, you'll learn the real commands. Until then, `ports` has your back.

## Platform Support

| Command | macOS | Linux |
|---------|-------|-------|
| `who`   | lsof  | ss    |
| `list`  | lsof  | ss    |
| `kill`  | lsof → kill | ss → kill |
| `free`  | lsof  | ss    |

## License

MIT
