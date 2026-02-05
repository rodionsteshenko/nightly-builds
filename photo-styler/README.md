# photo-styler

Transform your Apple Photos into different art styles using Gemini AI.

## Usage

```bash
# Random photo from your library → anime style
photo-styler

# Specific style
photo-styler --style ghibli
photo-styler --style watercolor
photo-styler --style cyberpunk

# Transform a specific image
photo-styler --input ~/photo.jpg --style oil-painting

# Custom output path
photo-styler --output ~/Desktop/my-art.png

# Custom style prompt
photo-styler --custom-prompt "Transform into a Renaissance painting"

# List all styles
photo-styler --list-styles
```

## Available Styles

- **anime** - Classic anime/manga style
- **ghibli** - Studio Ghibli aesthetic
- **watercolor** - Soft watercolor painting
- **oil-painting** - Dutch masters style
- **pixel-art** - 16-bit retro game style
- **comic** - Comic book/graphic novel
- **cyberpunk** - Neon futuristic
- **sketch** - Pencil drawing
- **pop-art** - Andy Warhol style
- **impressionist** - Monet-like

## Requirements

- macOS with Photos app
- Gemini API key (auto-detected from OpenClaw config)
- Python 3 with `requests` library

## How it works

1. Picks a random photo from your Apple Photos library
2. Sends it to Gemini's image generation API with a style prompt
3. Saves the transformed image and opens it

The result appears on your Desktop by default.
