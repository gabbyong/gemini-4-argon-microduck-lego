# DESIGN.md — LEGO Microduck Master Builder Workshop & Technical Manual

## 1. Visual Aesthetic & Direction
**Archetype**: Swiss Technical Manual × Botanical Sage / Pure White LEGO Master Builder Workshop  
**Subject**: Set `#MD-2026` — 1:1 Life-Sized LEGO Microduck Robot (`249.6 mm` / `78 plates`, `991 pieces`, `93 BrickLink lots`, `132 build steps`, `7 modular sub-assemblies`)  
**Inspiration**: Braun / Rams industrial specification sheets, official LEGO Architecture & Master Builder Series instruction manuals, and Pollen Robotics × Hugging Face open-source robotics documentation.

---

## 2. Color Palette & Surface Tokens

| Token | Hex | Role |
| :--- | :--- | :--- |
| `--bg-canvas` | `#F8FAF7` | Primary warm Botanical Sage laboratory canvas & 3D viewport surround |
| `--bg-surface` | `#FFFFFF` | Pure White technical cards, step callout panels, BOM drawers, and PDF pages |
| `--bg-elevated` | `#F3F6F4` | Secondary recessed telemetry headers, part callout wells, and table headers |
| `--border-hairline` | `#D8E0DC` | Crisp `1px solid` structural hairlines dividing all panels and grid cells |
| `--border-strong` | `#11181C` | High-contrast `1.5px` active callout borders and blueprint dimension frames |
| `--text-primary` | `#11181C` | Primary deep slate engineering ink for headings, labels, and specifications |
| `--text-secondary` | `#4A5559` | Secondary technical annotations, sub-assembly descriptions, and notes |
| `--text-muted` | `#748287` | De-emphasized grid coordinates, inactive step numbers, and axis labels |
| `--accent-amber` | `#F8BB3D` | Hugging Face / Microduck Bright Light Orange (`BL #110`) highlight accent |
| `--accent-orange` | `#FE8A18` | Active step brick highlight, callout borders, and interactive primary action (`BL #4`) |
| `--accent-teal` | `#1C4F59` | Deep Engineering Teal for verified badges, CoG stability vectors, and active tabs |
| `--accent-emerald` | `#2F5B37` | Static balance & 6-audit verification pass status (`ALL 6 AUDITS PASSED`) |
| `--accent-crimson` | `#D9381E` | New-brick step insertion outline & placement drop-in callout indicator |

### Official LEGO Element Colorway (`cad/parts_catalog.py`)
- **White (`BL #1` / `LDraw 15`)**: `#F4F4F4` — Primary cranial dome, torso shell, and leg fairings
- **Tan (`BL #2` / `LDraw 19`)**: `#E4CD9E` — Chest shield, cheek accents, and under-wing feathering
- **Bright Light Orange (`BL #110` / `LDraw 191`)**: `#F8BB3D` — Webbed duck feet and articulated grasping beak
- **Orange (`BL #4` / `LDraw 25`)**: `#FE8A18` — Beak inner palate/tongue and foot toe bevels
- **Dark Bluish Gray (`BL #85` / `LDraw 72`)**: `#6C6E68` — Internal Technic spine, ankle/knee/hip joints, and rear counterweight
- **Light Bluish Gray (`BL #86` / `LDraw 71`)**: `#A0A5A9` — Structural cross-plates, servo brackets, and neck ring
- **Black (`BL #11` / `LDraw 0`)**: `#1B2A34` — Expressive eye pupils, 8x8 LiDAR housing, acoustic grilles, and foot grip pads
- **Trans-Light Blue (`BL #15` / `LDraw 43`)**: `#AEEFEC` — Active 8x8 ToF LiDAR cells, RGB camera lens, and status LEDs

---

## 3. Typography & Hierarchy
- **Display & UI Sans**: `'Inter'`, `'Helvetica Neue'`, system sans-serif — tight tracking (`-0.02em`) for headers, crisp uppercase section labels (`0.75rem`, `letter-spacing: 0.08em`, `font-weight: 700`).
- **Technical Telemetry & Coordinates**: `'JetBrains Mono'`, `'IBM Plex Mono'`, monospace with `font-variant-numeric: tabular-nums` for step counters (`STEP 001 / 132`), grid coordinates (`X, Y, Z`), Center of Gravity readouts (`+0.02, 115.60, -2.47 mm`), and BrickLink part IDs (`#3021`, `#85984`, `#2412b`).

---

## 4. Layout, Geometry & Spacing Rules
- **90° Crisp Square Corners**: Enforce `border-radius: 0px` (`rx=0` in SVG/PDF) on all containers, cards, buttons, badges, inputs, and modals.
- **Hairline Grid Architecture**: Use exposed `1px solid #D8E0DC` borders with zero heavy drop shadows. Active interactive buttons use a tactile `2px` solid offset or high-contrast `#11181C` / `#1C4F59` fill.
- **8px Spatial Rhythm**: All padding, gaps, and control heights align to a strict `4px` / `8px` grid.

---

## 5. Mandatory Anti-Slop Rules (`## Don't`)
- **NO purple, indigo, or neon-violet gradients** anywhere in the UI, 3D scene, or PDF manual.
- **NO rounded corners (`border-radius > 0`)** or generic Tailwind cards with left-side accent borders (`border-l-4`) or fuzzy drop shadows (`shadow-lg`).
- **NO emoji** in headings, navigation bars, sub-assembly tabs, or button labels — use crisp geometric SVG icons or typographic codes (`SA-01` .. `SA-07`).
- **NO fake telemetry** — every number, mass, bond count, CoG coordinate, and BrickLink lot quantity must derive directly from the verified `microduck_model.json` and `verification_report.json`.
- **NO centered body prose** or unstyled default browser inputs.
