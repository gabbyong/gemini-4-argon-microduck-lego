# LEGO Microduck 3D CAD & Assembly Studio (Set #MD-2026 // Rev 3.2)

Life-sized (**249.6 mm / 25.0 cm = 78 plates tall**), 945-piece, 101-lot, 129-step buildable LEGO replica of the open-source **Microduck** bipedal robot (by Hugging Face & Pollen Robotics), complete with an 8-audit 3D Oriented Bounding Box (OBB) physics verifier, 47-page printable vector PDF instruction manual, and interactive Three.js 3D WebGL 10-DoF walking studio.

## Key Engineering Highlights

- **945 Authentic LEGO Pieces (101 Unique BrickLink Lots, 129 Build Steps)**: Built across 7 slanted and orthogonal modular sub-assemblies (`SA1: Bootie Feet 0°`, `SA2: Slanted Shins +24°`, `SA3: Slanted Thighs -26°`, `SA4: Hip Servos 0°`, `SA5: Torso & Spine 0°`, `SA6: Slanted Servo Neck +19.7°`, `SA7: Visor & Cyclops Camera 0°`).
- **8/8 True Double-Shear Clevis Pin Joints**: Every knee, ankle, hip, and neck joint uses dual coaxial Technic pins (`16` joint shear pins + `12` triangulated `#3701` strut lock pins = `28` horizontal X-axis `#2780` pins total) plus physical hard-stop cradle ledges.
- **8-Audit Mathematical & Structural Physics Verification (`cad/verifier.py`)**:
  - `0` local unit-cell collisions and `0` 3D OBB SAT world-space collisions across all `446,040` brick pairs (including `+1.70 mm` top studs).
  - `1` single connected component (`3,422` stud bonds, `0` floating bricks, `0` trapped step insertions).
  - Self-standing 3D Center of Gravity (`+0.15 mm, 149.06 mm, -0.83 mm`) with `40.83 mm` minimum support edge margin and `15.32°` static tipping angle over a `112 × 88 mm` foot support polygon.

## Included Deliverables

- **`index.html` / `web/`** — Self-contained interactive 3D WebGL CAD & 10-DoF Bipedal Walking Studio (works directly on GitHub Pages with zero build step).
- **`output/microduck_instruction_manual.pdf`** — 47-page printable vector PDF instruction manual with orthographic blueprints, step-by-step isometric build views, and illustrated BOM.
- **`output/microduck_bricklink_wanted_list.xml` & `output/microduck_bom.csv`** — Ready-to-upload BrickLink Wanted List XML and full Bill of Materials.
- **`output/microduck.mpd` & `output/microduck.ldr`** — Standard LDraw multi-part and single-part CAD models.
- **`output/verification_report.json`** — Complete 8-audit physics and buildability telemetry report.

## Running Locally

```bash
python3 server.py 8765
# Open http://localhost:8765
```

## Running the Physics & Buildability Verifier

```bash
python3 -m cad.verifier
python3 -m unittest discover -s tests -v
```
