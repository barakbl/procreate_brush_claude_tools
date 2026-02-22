# bbrush

Generate Procreate-compatible brushes from natural language using Claude Code.

## Quick Start

```sh
git clone https://github.com/barakbl/procreate_brush_claude_tools && cd procreate_brush_claude_tools
pip install Pillow numpy
```

Then in Claude Code:

```
/create-procreate-brush a soft pencil for architectural sketching
```

A `.brush` file appears in your project root. AirDrop it to your iPad and open in Procreate.

## Example Prompts

```
/create-procreate-brush a soft 6B pencil for gesture drawing
/create-procreate-brush a wet watercolor with heavy granulation
/create-procreate-brush a dry charcoal stick for expressive figure drawing
/create-procreate-brush a fine-tip technical pen for inking
/create-procreate-brush a thick oil paint brush with visible bristle texture
/create-procreate-brush a soft pastel for blending and layering
/create-procreate-brush a flat chisel marker for lettering
/create-procreate-brush a subtle airbrush for smooth gradients
/create-procreate-brush a gouache brush — opaque, flat, slight texture
/create-procreate-brush a dry brush for rough textured strokes
```

## How It Works

1. You describe a brush in plain English
2. Claude translates your description into a JSON brush spec (shape, grain, pressure dynamics, opacity, spacing, etc.)
3. `create_brush.py` generates the image assets (shape stamp, grain texture, thumbnail) and packages everything into a `.brush` file (ZIP archive containing `Brush.archive`, `Shape.png`, `Grain.png`, `QuickLook/Thumbnail.png`)
4. AirDrop or transfer the `.brush` file to your iPad

The brush spec supports two shape types:
- **Ellipse** — clean, precise stamps for pencils, pens, markers, and airbrushes
- **Blob** — organic, irregular stamps with sine-harmonic boundaries for watercolor, oil, charcoal, and pastel

Grain textures are generated as Gaussian noise with configurable mean, standard deviation, and blur — from smooth (pen) to heavily textured (charcoal).

## Installation

Just copy the `.claude/commands/` directory into any project:

```sh
cp -r .claude/commands/ /path/to/your/project/.claude/commands/
```

The skill is fully self-contained — `create-procreate-brush.md` (the prompt) and `create_brush.py` (the generator) are both inside `.claude/commands/`.

## Requirements

- Python 3.8+
- [Pillow](https://pypi.org/project/Pillow/)
- [numpy](https://pypi.org/project/numpy/)
- [Claude Code](https://claude.com/claude-code)

## Files

| File | Purpose |
|------|---------|
| `.claude/commands/create-procreate-brush.md` | Claude Code skill definition |
| `.claude/commands/create_brush.py` | Brush generator script |
| `procreate-brush-spec.md` | Procreate brush format reference |

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

This project is not affiliated with, endorsed by, or associated with Savage Interactive Pty Ltd or the Procreate application in any way. Procreate is a registered trademark of Savage Interactive Pty Ltd. All trademarks are the property of their respective owners. This tool generates brush files compatible with the Procreate format based on community-derived, reverse-engineered specifications.
