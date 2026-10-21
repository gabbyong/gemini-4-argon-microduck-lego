# LEGO Microduck 3D CAD & Assembly Studio (Set #MD-2026 // Rev 3.2)

**Live GitHub Pages Deployment:** [https://gabbyong.github.io/gemini-4-argon-microduck-lego/](https://gabbyong.github.io/gemini-4-argon-microduck-lego/)

Life-sized (**249.6 mm / 25.0 cm = 78 plates tall**), 945-piece, 101-lot, 129-step buildable LEGO replica of the open-source **Microduck** bipedal robot (by Hugging Face & Pollen Robotics), autonomously engineered and verified by **Gemini 4 Argon** using an Orchestrator–Implementer–Verifier multi-agent architecture.

---

## Demo & Explainer Video Made by Gemini 4 Argon

- **Watch / Download the Narrated Explainer Video (1080p60 MP4):** [`output/Microduck_Gemini4_Argon_Narrated_Full_1080p60.mp4`](output/Microduck_Gemini4_Argon_Narrated_Full_1080p60.mp4) ([Stream on GitHub Pages](https://gabbyong.github.io/gemini-4-argon-microduck-lego/output/Microduck_Gemini4_Argon_Narrated_Full_1080p60.mp4))
- **Also playable inline inside the live studio:** Click **EXPLAINER VIDEO** in the top navigation bar at [https://gabbyong.github.io/gemini-4-argon-microduck-lego/](https://gabbyong.github.io/gemini-4-argon-microduck-lego/).

### How Gemini 4 Argon Built This Demo & Explainer Video
1. **Parametric LEGO CAD & Subagent Physics Verifiers**: Acting as an Orchestrator, **Gemini 4 Argon** coordinated specialized Implementer subagents and independent black-box Verifier subagents (`cad/verifier.py` + `gbrowser`) to design a 945-piece, 129-step LEGO replica from first principles. When visual and mathematical audits flagged brick collisions at slanted leg/neck joints and single-shear pin flex, the verifier loop iteratively re-engineered the frame into **8/8 true double-shear clevis pin joints** (`28` horizontal `#2780` Technic pins + triangulated `#3701` struts) with **0 3D Oriented Bounding Box (OBB) collisions** across all `446,040` brick pairs.
2. **Autonomous Multimodal Video Production**: **Gemini 4 Argon** also produced the narrated explainer video (`output/Microduck_Gemini4_Argon_Narrated_Full_1080p60.mp4`) by inspecting the screen recording frame-by-frame, authoring a second-by-second time-aligned narration script, synthesizing the spoken voiceover with **Gemini 3.8 Flash TTS**, generating a custom chill-house background score with **Lyria 3.5**, and compositing synced single-line `Google Sans Flex` captions at 1080p60.

---

## Key Engineering Highlights

- **945 Authentic LEGO Pieces (101 Unique BrickLink Lots, 129 Build Steps)**: Built across 7 slanted and orthogonal modular sub-assemblies (`SA1: Bootie Feet 0°`, `SA2: Slanted Shins +24°`, `SA3: Slanted Thighs -26°`, `SA4: Hip Servos 0°`, `SA5: Torso & Spine 0°`, `SA6: Slanted Servo Neck +19.7°`, `SA7: Visor & Cyclops Camera 0°`).
- **8/8 True Double-Shear Clevis Pin Joints**: Every knee, ankle, hip, and neck joint uses dual coaxial Technic pins (`16` joint shear pins + `12` triangulated `#3701` strut lock pins = `28` horizontal X-axis `#2780` pins total) plus physical hard-stop cradle ledges.
- **8-Audit Mathematical & Structural Physics Verification (`cad/verifier.py`)**:
  - `0` local unit-cell collisions and `0` 3D OBB SAT world-space collisions across all `446,040` brick pairs (including `+1.70 mm` top studs).
  - `1` single connected component (`3,422` stud bonds, `0` floating bricks, `0` trapped step insertions).
  - Self-standing 3D Center of Gravity (`+0.15 mm, 149.06 mm, -0.83 mm`) with `40.83 mm` minimum support edge margin and `15.32°` static tipping angle over a `112 × 88 mm` foot support polygon.

## Included Deliverables

- **[Interactive 3D WebGL Studio](https://gabbyong.github.io/gemini-4-argon-microduck-lego/) (`index.html` / `web/`)** — Self-contained 3D WebGL CAD & 10-DoF Bipedal Walking Studio with built-in Explainer Video player.
- **[Narrated Explainer Video (1080p60 MP4)](https://gabbyong.github.io/gemini-4-argon-microduck-lego/output/Microduck_Gemini4_Argon_Narrated_Full_1080p60.mp4) (`output/Microduck_Gemini4_Argon_Narrated_Full_1080p60.mp4`)** — Demo video made by Gemini 4 Argon with Gemini 3.8 Flash TTS narration, Lyria 3.5 background music, and synced captions.
- **[47-Page Printable Instruction Manual (PDF)](https://gabbyong.github.io/gemini-4-argon-microduck-lego/output/microduck_instruction_manual.pdf) (`output/microduck_instruction_manual.pdf`)** — Vector PDF instruction manual with orthographic blueprints, step-by-step isometric build views, and illustrated BOM.
- **[BrickLink Wanted List XML](https://gabbyong.github.io/gemini-4-argon-microduck-lego/output/microduck_bricklink_wanted_list.xml) & [BOM CSV](https://gabbyong.github.io/gemini-4-argon-microduck-lego/output/microduck_bom.csv)** — Ready-to-upload BrickLink Wanted List XML and full Bill of Materials.
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
