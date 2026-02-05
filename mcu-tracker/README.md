# mcu - MCU Progress Tracker

Track your Marvel Cinematic Universe watching progress from the command line.

## Features

- **Complete MCU Database**: All movies, shows, and specials through Phase 6
- **Multiple Watch Orders**: Release order or in-universe timeline
- **Post-Credits Reminders**: Never miss those crucial stingers
- **Progress Tracking**: See what you've watched and what's next
- **Statistics**: Visual progress by phase
- **Ratings**: Rate what you've watched

## Installation

```bash
# Copy to your path
cp mcu ~/.local/bin/
# or
alias mcu='~/clawd/nightly-build/projects/mcu-tracker/mcu'
```

## Usage

```bash
# List all MCU content
mcu list

# Show only unwatched
mcu list --unwatched

# Show Phase 3 only
mcu list --phase 3

# List by in-universe timeline
mcu list --timeline

# Mark as watched
mcu watch "Deadpool & Wolverine"

# Mark watched with rating
mcu watch "Avengers: Endgame" -r 10

# What should I watch next?
mcu next

# Next by timeline order
mcu next --timeline

# Show upcoming releases
mcu upcoming

# Show details for a title
mcu info "Iron Man"

# View your statistics
mcu stats
```

## Data Storage

Watched status stored in `~/.config/mcu/watched.json`

## Content Included

- **Phase 1-3**: The Infinity Saga (2008-2019)
- **Phase 4-5**: The Multiverse Saga (2021-2025)
- **Phase 6**: Upcoming (2025-2027)
- Movies, D+ shows, and specials (Werewolf by Night, Holiday Special)

## Post-Credits Guide

The tool tracks how many post-credits scenes each movie has:
- 🎬 1 = one scene
- 🎬 2 = mid-credits AND post-credits

## Example Output

```
✓ 🎬 Iron Man (2008) [🎬 1 post-credits]
✓ 🎬 The Avengers (2012) [🎬 2 post-credits]
○ 📺 WandaVision (2021) [9 eps]
○ 🎬 Deadpool & Wolverine (2024)
⏳ 🎬 Avengers: Doomsday (2026)

📊 35/54 watched (5 upcoming)
```

## License

MIT
