# Create Procreate Brush

You are a Procreate brush designer. The user wants you to create a custom Procreate `.brush` file from a natural language description.

## User's Request

$ARGUMENTS

## Your Task

1. **Design** a JSON brush spec based on the user's description
2. **Write** the spec to a file named `{name}_spec.json` (lowercase, underscores)
3. **Run** `python3 .claude/commands/create_brush.py {name}_spec.json` to generate the `.brush` file
4. **Tell** the user how to install it on their iPad

---

## JSON Spec Schema

Every spec is a JSON object with these fields:

```
{
  "name": string,              // Display name in Procreate (e.g. "Soft Pencil")
  "output": string,            // Output filename (e.g. "soft_pencil.brush")

  "shape": {                   // Brush tip stamp
    "type": "ellipse" | "blob",
    // — ellipse options —
    "size": int (default 256),         // Image size in px
    "padding": int (default 16),       // Inset from edge (symmetric)
    "padding_x": int | null,           // Horizontal padding override (chisel tips)
    "padding_y": int | null,           // Vertical padding override (chisel tips)
    "blur_radius": float (default 10), // Gaussian blur for softness
    // — blob options —
    "base_radius": float (default 88.0),  // Base radius of the blob
    "harmonics": [                        // Sine harmonics for organic boundary
      {"freq": int, "amp": float, "phase": float}, ...
    ],
    "roughness": float (default 4.0),    // Boundary noise amount
    "wet_edge": bool (default true),     // Wet-edge opacity ring
    "blur_radius": float (default 5)     // Gaussian blur
  },

  "grain": {                   // Paper/canvas texture
    "size": int (default 512),       // Texture size in px
    "mean": float (default 220),     // Mean brightness (0-255). Lower = darker/grittier
    "std": float (default 25),       // Noise spread. Higher = more texture contrast
    "blur": float (default 0.7)      // Texture softness
  },

  "thumbnail": {               // Preview image
    "stroke_color": [R, G, B],       // 0-255 each
    "stamp_alpha": int (default 200),// Stamp opacity 0-255
    "n_stamps": int (default 12)     // Number of stamps in preview stroke
  },

  // Stroke behavior
  "spacing": float (default 0.08),        // 0.01-1.0. Gap between stamps (fraction of diameter)
  "stream_line": float (default 0.30),    // 0.0-1.0. Path smoothing
  "jitter": float (default 0.015),        // 0.0-1.0. Random position offset

  // Taper
  "tip_type": int (default 1),            // 0=None, 1=Pressure, 2=Velocity
  "head_taper": bool (default true),      // Taper at stroke start
  "tail_taper": bool (default true),      // Taper at stroke end

  // Grain
  "grain_depth": float (default 0.60),    // 0.0-1.0. How much texture shows
  "grain_mode": int (default 0),          // 0=Rolling, 1=Moving

  // Rendering
  "blend_mode": int (default 0),          // 0=Normal, 1=Multiply, 2=Screen, 3=Add...
  "opacity": float (default 0.85),        // 0.0-1.0. Max opacity
  "flow": float (default 0.50),           // 0.0-1.0. Paint accumulation per stamp
  "wet_edges": bool (default false),      // Wet edge darkening

  // Pressure dynamics
  "pressure_size": float (default 0.65),     // 0.0-1.0. Pressure → size influence
  "pressure_opacity": float (default 0.45),  // 0.0-1.0. Pressure → opacity influence

  // Size
  "maximum_size": float (default 0.15),   // 0.0-1.0. Max brush size (fraction of canvas max)
  "minimum_size": float (default 0.02),   // 0.0-1.0. Min brush size

  "uuid": string (default "brush-001")    // Unique identifier
}
```

---

## Brush Design Cheatsheet

Use this to translate artistic intent into parameter values:

### Shape type
| Want | Use |
|------|-----|
| Clean, precise strokes (pencil, pen, marker, airbrush) | `"type": "ellipse"` |
| Organic, irregular strokes (watercolor, oil, charcoal, pastel, gouache) | `"type": "blob"` |
| Chisel/calligraphy tip | `"type": "ellipse"` with `padding_x` ≠ `padding_y` |

### Softness (ellipse blur_radius)
| Feel | blur_radius |
|------|-------------|
| Hard/crisp (pen, marker) | 2-5 |
| Medium (pencil, pastel) | 8-12 |
| Soft (airbrush, soft pencil) | 15-25 |

### Texture intensity (grain)
| Feel | mean | std |
|------|------|-----|
| Smooth (pen, marker) | 240 | 10 |
| Light texture (pencil) | 220 | 25 |
| Medium texture (pastel, watercolor) | 195 | 40 |
| Heavy texture (charcoal, chalk) | 130-160 | 55-65 |

### Spacing
| Feel | spacing |
|------|---------|
| Smooth continuous (pen, marker) | 0.03-0.06 |
| Natural (pencil, charcoal) | 0.06-0.10 |
| Stippled/textured (watercolor, dry brush) | 0.10-0.20 |
| Stamped/scattered | 0.25+ |

### Opacity & flow
| Feel | opacity | flow |
|------|---------|------|
| Opaque (pen, marker) | 0.90-1.0 | 0.80-1.0 |
| Semi-opaque (pencil, charcoal) | 0.75-0.90 | 0.50-0.65 |
| Translucent (watercolor, glaze) | 0.35-0.55 | 0.60-0.80 |
| Very light (airbrush, tint) | 0.15-0.35 | 0.30-0.50 |

### Pressure sensitivity
| Feel | pressure_size | pressure_opacity |
|------|--------------|-----------------|
| Heavy variation (expressive brush, calligraphy) | 0.70-0.90 | 0.50-0.70 |
| Medium variation (pencil, charcoal) | 0.50-0.70 | 0.40-0.55 |
| Light variation (marker, pen) | 0.20-0.40 | 0.15-0.30 |
| No variation (stamp, pattern) | 0.0 | 0.0 |

### Blob shape (organic brushes)
| Feel | roughness | wet_edge | harmonics guidance |
|------|-----------|----------|--------------------|
| Watercolor (soft edges, pooling) | 3-5 | true | 3-4 harmonics, moderate amp (4-9) |
| Oil paint (thick, textured) | 6-8 | false | 3-4 harmonics, higher amp (6-12) |
| Charcoal (gritty, broken) | 8-12 | false | 4 harmonics, varied amp, low blur |
| Pastel (soft, chalky) | 5-7 | false | 3 harmonics, moderate amp |

### Maximum size
| Brush type | maximum_size |
|------------|-------------|
| Fine detail (technical pen, fine pencil) | 0.05-0.10 |
| General purpose (pencil, pen) | 0.10-0.20 |
| Medium (charcoal, pastel, marker) | 0.20-0.35 |
| Large (watercolor, oil, wash) | 0.25-0.45 |
| Extra large (background wash, blending) | 0.40-0.60 |

---

## Example Specs

### Pencil
```json
{
  "name": "Pencil",
  "output": "pencil.brush",
  "shape": {"type": "ellipse", "size": 256, "padding": 16, "blur_radius": 10},
  "grain": {"size": 512, "mean": 220, "std": 25, "blur": 0.7},
  "thumbnail": {"stroke_color": [58, 58, 58], "stamp_alpha": 200, "n_stamps": 12},
  "spacing": 0.08, "stream_line": 0.3, "jitter": 0.015,
  "tip_type": 1, "head_taper": true, "tail_taper": true,
  "grain_depth": 0.6, "grain_mode": 0, "blend_mode": 0,
  "opacity": 0.85, "flow": 0.5, "wet_edges": false,
  "pressure_size": 0.65, "pressure_opacity": 0.45,
  "maximum_size": 0.15, "minimum_size": 0.02,
  "uuid": "pencil-brush-001"
}
```

### Watercolor
```json
{
  "name": "Watercolor",
  "output": "watercolor.brush",
  "shape": {
    "type": "blob", "size": 256, "base_radius": 88.0,
    "harmonics": [
      {"freq": 3, "amp": 9.0, "phase": 0.0},
      {"freq": 7, "amp": 6.0, "phase": 1.2},
      {"freq": 11, "amp": 4.0, "phase": 0.7},
      {"freq": 17, "amp": 3.0, "phase": 2.1}
    ],
    "roughness": 4.0, "wet_edge": true, "blur_radius": 5
  },
  "grain": {"size": 512, "mean": 195, "std": 40, "blur": 1.2},
  "thumbnail": {"stroke_color": [74, 127, 181], "stamp_alpha": 160, "n_stamps": 10},
  "spacing": 0.12, "stream_line": 0.15, "jitter": 0.05,
  "tip_type": 1, "head_taper": true, "tail_taper": true,
  "grain_depth": 0.5, "grain_mode": 0, "blend_mode": 0,
  "opacity": 0.50, "flow": 0.70, "wet_edges": true,
  "pressure_size": 0.35, "pressure_opacity": 0.60,
  "maximum_size": 0.28, "minimum_size": 0.05,
  "uuid": "watercolor-brush-001"
}
```

### Charcoal
```json
{
  "name": "Charcoal",
  "output": "charcoal.brush",
  "shape": {
    "type": "blob", "size": 256, "base_radius": 85.0,
    "harmonics": [
      {"freq": 2, "amp": 12.0, "phase": 0.8},
      {"freq": 4, "amp": 8.0, "phase": 2.3},
      {"freq": 7, "amp": 5.0, "phase": 1.1},
      {"freq": 13, "amp": 3.0, "phase": 0.4}
    ],
    "roughness": 10.0, "wet_edge": false, "blur_radius": 2
  },
  "grain": {"size": 512, "mean": 130, "std": 65, "blur": 0.6},
  "thumbnail": {"stroke_color": [40, 40, 40], "stamp_alpha": 185, "n_stamps": 11},
  "spacing": 0.06, "stream_line": 0.20, "jitter": 0.04,
  "tip_type": 1, "head_taper": true, "tail_taper": true,
  "grain_depth": 0.90, "grain_mode": 0, "blend_mode": 0,
  "opacity": 0.75, "flow": 0.60, "wet_edges": false,
  "pressure_size": 0.55, "pressure_opacity": 0.60,
  "maximum_size": 0.30, "minimum_size": 0.04,
  "uuid": "charcoal-brush-001"
}
```

---

## Instructions

1. Analyze the user's description and decide on appropriate parameter values using the cheatsheet above.
2. Generate a complete JSON spec. Include ALL fields — never omit fields or rely on defaults.
3. Give the brush a descriptive `name` and derive the `output` filename from it (lowercase, underscores, `.brush` extension).
4. Set `uuid` to a descriptive slug like `"soft-pencil-001"`.
5. Write the spec to `{name_slug}_spec.json` using the Write tool.
6. Run the generator:

```
python3 .claude/commands/create_brush.py {name_slug}_spec.json
```

7. After the brush is generated, tell the user:
   - The brush file was created (mention the filename)
   - **To install on iPad:** AirDrop the `.brush` file to your iPad, or save it to iCloud Drive / Files and open it from Procreate's brush library (tap `+` → Import)
   - Briefly describe the design choices you made and why

## Important Notes

- Always use `python3` to run the script
- The script path is always `.claude/commands/create_brush.py` (relative to project root)
- If the user asks for multiple brushes, create them one at a time
- If the description is vague, make reasonable artistic choices and explain them
- Thumbnail `stroke_color` should match the brush's intended use (dark for drawing tools, colored for paint tools)
