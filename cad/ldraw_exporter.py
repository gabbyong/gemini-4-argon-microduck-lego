"""LDraw (.mpd and .ldr) Exporter for the Life-Sized Microduck LEGO Model (Rev 3.0).

Writes true 3D posed LDraw coordinates (wx / 0.4, -wy / 0.4, wz / 0.4) in LDU
and the full 3x3 orthogonal world_rotation_matrix for every brick (including
slanted sub-assemblies SA-02, SA-03, SA-06 and horizontal 2780 Technic pins),
with 0 STEP markers between instruction steps and modular sub-models.
"""

from pathlib import Path
from typing import Dict, List

from cad.microduck_builder import (
    MicroduckModel,
    PlacedBrick,
    SUBASSEMBLY_NAMES,
    SUBASSEMBLY_POSES,
)
from cad.parts_catalog import COLORS


def brick_to_ldraw_line(brick: PlacedBrick) -> str:
    """Format a PlacedBrick as an LDraw Type 1 part reference line with true 3D world pose."""
    ldraw_color = COLORS[brick.color_id].ldraw_id
    wx, wy, wz = brick.world_center_mm()
    x_ldu = wx / 0.4
    y_ldu = -wy / 0.4
    z_ldu = wz / 0.4
    mat = brick.world_rotation_matrix
    rot_str = " ".join(
        f"{mat[r][c]:.4f}" for r in range(3) for c in range(3)
    )
    dat_file = brick.spec.ldraw_dat
    return (
        f"1 {ldraw_color} {x_ldu:.2f} {y_ldu:.2f} {z_ldu:.2f} "
        f"{rot_str} {dat_file}"
    )


def export_ldr(model: MicroduckModel, output_path: Path) -> None:
    """Export a single-file LDraw (.ldr) model with 0 STEP markers for every step."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = [
        "0 Hugging Face x Pollen Robotics Microduck - Life-Sized LEGO Edition (Rev 3.0, 249.6 mm / 78 Plates)",
        "0 Name: microduck.ldr",
        "0 Author: Parametric LEGO CAD & Physics Engineering",
        "0 !LDRAW_ORG Unofficial_Model",
        "",
    ]

    steps: Dict[int, List[PlacedBrick]] = {}
    for b in model.bricks:
        steps.setdefault(b.step_id, []).append(b)

    current_sub = None
    for step_id in sorted(steps.keys()):
        step_bricks = steps[step_id]
        sub_id = step_bricks[0].subassembly_id
        if sub_id != current_sub:
            current_sub = sub_id
            pose = SUBASSEMBLY_POSES[sub_id]
            lines.append("0 // ==========================================================")
            lines.append(
                f"0 // Sub-Assembly {sub_id}: {SUBASSEMBLY_NAMES[sub_id]} (pitch={pose.pitch_deg:+.1f} deg)"
            )
            lines.append("0 // ==========================================================")
        lines.append(
            f"0 // Step {step_id} (local_y={step_bricks[0].y} plates, {len(step_bricks)} bricks)"
        )
        for b in step_bricks:
            lines.append(brick_to_ldraw_line(b))
        lines.append("0 STEP")
        lines.append("")

    lines.append("0 NOFILE")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def export_mpd(model: MicroduckModel, output_path: Path) -> None:
    """Export a Multi-Part LDraw Document (.mpd) with 7 sub-models and 0 STEP markers."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = [
        "0 FILE microduck_main.ldr",
        "0 Hugging Face x Pollen Robotics Microduck - Life-Sized LEGO Edition (Rev 3.0, 249.6 mm / 78 Plates)",
        "0 Name: microduck_main.ldr",
        "0 Author: Parametric LEGO CAD & Physics Engineering",
        "0 !LDRAW_ORG Unofficial_Model",
        "",
    ]

    for sub_id in sorted(SUBASSEMBLY_NAMES.keys()):
        sub_filename = f"subassembly_{sub_id}.ldr"
        pose = SUBASSEMBLY_POSES[sub_id]
        lines.append(
            f"0 // Attach Sub-Assembly {sub_id}: {SUBASSEMBLY_NAMES[sub_id]} (pitch={pose.pitch_deg:+.1f} deg)"
        )
        lines.append(f"1 16 0.0 0.0 0.0 1 0 0 0 1 0 0 0 1 {sub_filename}")
        lines.append("0 STEP")
        lines.append("")
    lines.append("0 NOFILE")
    lines.append("")

    for sub_id in sorted(SUBASSEMBLY_NAMES.keys()):
        sub_filename = f"subassembly_{sub_id}.ldr"
        pose = SUBASSEMBLY_POSES[sub_id]
        lines.append(f"0 FILE {sub_filename}")
        lines.append(
            f"0 Sub-Assembly {sub_id}: {SUBASSEMBLY_NAMES[sub_id]} (pitch={pose.pitch_deg:+.1f} deg)"
        )
        lines.append(f"0 Name: {sub_filename}")
        lines.append("0 Author: Parametric LEGO CAD & Physics Engineering")
        lines.append("")

        sub_bricks = [b for b in model.bricks if b.subassembly_id == sub_id]
        steps: Dict[int, List[PlacedBrick]] = {}
        for b in sub_bricks:
            steps.setdefault(b.step_id, []).append(b)

        for step_id in sorted(steps.keys()):
            step_bricks = steps[step_id]
            lines.append(
                f"0 // Global Step {step_id} (local_y={step_bricks[0].y} plates, {len(step_bricks)} bricks)"
            )
            for b in step_bricks:
                lines.append(brick_to_ldraw_line(b))
            lines.append("0 STEP")
            lines.append("")

        lines.append("0 NOFILE")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
