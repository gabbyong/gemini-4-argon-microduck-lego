"""Parametric 3D LEGO CAD & Kinematic Builder for the Hugging Face x Pollen Robotics Microduck (Rev 3.0).

Constructs a life-sized (249.6 mm = 25.0 cm tall, 78.0 plates equivalent) LEGO replica
matching the real open-source Hugging Face x Pollen Robotics Microduck bipedal robot
with True 3D Slanted Sub-Assemblies & Coaxial Horizontal Technic Pin Joints:
  - SA-01 (local_y = 0..8,   pitch =   0.0 deg): Two-Tone Orange & Yellow Robotic Bootie Feet with Ankle Pin Brackets (L & R)
  - SA-02 (local_y = 0..16,  pitch = +24.0 deg): Slanted Lower Shin Servos & Angled Grey Knee Linkages (L & R)
  - SA-03 (local_y = 0..15,  pitch = -26.0 deg): Slanted Upper Thigh Servos & Diagonal White Outer Thigh Armor Shields (L & R)
  - SA-04 (local_y = 0..11,  pitch =   0.0 deg): Level Exposed Black Hip Servo Cluster & Cylindrical Grey Hip-Roll Hubs
  - SA-05 (local_y = 0..11,  pitch =   0.0 deg): Level Compact Rounded White Torso Pod & Flush Rear Black Battery Column
  - SA-06 (local_y = 0..16,  pitch = +16.0 deg): Slanted Slender 4x4 Black & Grey Multi-Servo Neck Stalk
  - SA-07 (local_y = 0..23,  pitch =   0.0 deg): Wide Curved White Visor Hood, Orange Base Rim & Cyclops Yellow-Ring Camera Head
"""

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from cad.parts_catalog import (
    COLORS,
    COLOR_BLACK,
    COLOR_BRIGHT_LIGHT_ORANGE,
    COLOR_DARK_BLUISH_GRAY,
    COLOR_LIGHT_BLUISH_GRAY,
    COLOR_ORANGE,
    COLOR_TRANS_LIGHT_BLUE,
    COLOR_WHITE,
    COLOR_YELLOW,
    PARTS_CATALOG,
    PLATE_MM,
    PartSpec,
    STUD_MM,
)


SUBASSEMBLY_NAMES: Dict[int, str] = {
    1: "SA-01: Two-Tone Orange & Yellow Robotic Bootie Feet with Ankle Pin Brackets (Left & Right)",
    2: "SA-02: Slanted Lower Shin Servos & Angled Grey Knee Linkages (Left & Right)",
    3: "SA-03: Slanted Upper Thigh Servos & Diagonal White Outer Thigh Armor Shields (Left & Right)",
    4: "SA-04: Exposed Black Hip Servo Cluster & Cylindrical Grey Hip-Roll Hubs",
    5: "SA-05: Compact Rounded White Torso Pod & Flush Rear Black Battery Column",
    6: "SA-06: Slanted Slender 4x4 Black & Grey Multi-Servo Neck Stalk",
    7: "SA-07: Wide Curved White Visor Hood, Orange Base Rim & Cyclops Yellow-Ring Camera Head",
}


# ---------------------------------------------------------------------------
# Exact Kinematic Chain & 3D World Pose Transforms for All 7 Sub-Assemblies
# ---------------------------------------------------------------------------
# SA-01: Ankle Pin at local_y = 6.5 plates (20.8 mm), local_z = -2.0 studs (-16.0 mm)
ANKLE_Y_MM: float = 6.5 * PLATE_MM  # 20.8 mm
ANKLE_Z_MM: float = -2.0 * STUD_MM  # -16.0 mm

# SA-02: Tilted forward by +24.0 deg around Ankle Pin; pin-to-pin length = 13 plates (41.6 mm)
SA02_PITCH_DEG: float = 24.0
SA02_LEN_MM: float = 13.0 * PLATE_MM  # 41.6 mm
KNEE_Y_MM: float = ANKLE_Y_MM + SA02_LEN_MM * math.cos(math.radians(SA02_PITCH_DEG))  # 58.803505 mm
KNEE_Z_MM: float = ANKLE_Z_MM + SA02_LEN_MM * math.sin(math.radians(SA02_PITCH_DEG))  # +0.920250 mm

# SA-03: Tilted backward by -26.0 deg around Knee Pin; pin-to-pin length = 11 plates (35.2 mm)
SA03_PITCH_DEG: float = -26.0
SA03_LEN_MM: float = 11.0 * PLATE_MM  # 35.2 mm
HIP_Y_MM: float = KNEE_Y_MM + SA03_LEN_MM * math.cos(math.radians(SA03_PITCH_DEG))  # 90.441052 mm
HIP_Z_MM: float = KNEE_Z_MM + SA03_LEN_MM * math.sin(math.radians(SA03_PITCH_DEG))  # -14.510410 mm

# SA-04: Level (0.0 deg), Hip Pin at local_y = 4.5 plates (14.4 mm), local_z = -2.0 studs (-16.0 mm)
SA04_PITCH_DEG: float = 0.0
SA04_ORIGIN_Y_MM: float = HIP_Y_MM - 4.5 * PLATE_MM  # 76.041052 mm
SA04_ORIGIN_Z_MM: float = HIP_Z_MM - (-2.0 * STUD_MM)  # +1.489590 mm
SA04_TOP_Y_MM: float = SA04_ORIGIN_Y_MM + 11.0 * PLATE_MM  # 111.241052 mm

# SA-05: Level (0.0 deg), stacked directly on SA-04; Lower Neck Pin at local_y = 9.5 plates (30.4 mm), local_z = 0.0
SA05_PITCH_DEG: float = 0.0
SA05_ORIGIN_Y_MM: float = SA04_TOP_Y_MM  # 111.241052 mm
SA05_ORIGIN_Z_MM: float = SA04_ORIGIN_Z_MM  # +1.489590 mm
LOWER_NECK_Y_MM: float = SA05_ORIGIN_Y_MM + 9.5 * PLATE_MM  # 141.641052 mm
LOWER_NECK_Z_MM: float = SA05_ORIGIN_Z_MM + 0.0 * STUD_MM  # +1.489590 mm

# SA-07: Level (0.0 deg), 23 plates tall (73.6 mm), mounted at Upper Neck Pin so crown is exact 249.6000 mm (78.0 plates)
SA07_PITCH_DEG: float = 0.0
TARGET_HEIGHT_MM: float = 78.0 * PLATE_MM  # 249.6 mm
SA07_HEIGHT_PLATES: int = 23
SA07_LOCAL_PIN_Y_MM: float = 1.5 * PLATE_MM  # 4.8000 mm (exact center of 3700 Technic brick at local_y = 0..3)
SA07_LOCAL_PIN_Z_MM: float = 1.0 * STUD_MM  # +8.0 mm

# SA-06: Tilted forward by ~19.7247 deg around Lower Neck Pin; pin-to-pin length = 13 plates (41.6 mm)
SA06_LEN_MM: float = 13.0 * PLATE_MM  # 41.6 mm
UPPER_NECK_Y_MM: float = TARGET_HEIGHT_MM - (SA07_HEIGHT_PLATES * PLATE_MM - SA07_LOCAL_PIN_Y_MM)  # 180.8000 mm
SA06_PITCH_DEG: float = math.degrees(math.acos((UPPER_NECK_Y_MM - LOWER_NECK_Y_MM) / SA06_LEN_MM))  # 19.724658 deg
UPPER_NECK_Z_MM: float = LOWER_NECK_Z_MM + SA06_LEN_MM * math.sin(math.radians(SA06_PITCH_DEG))  # +15.531650 mm


@dataclass(frozen=True)
class SubassemblyPose:
    """Rigid-body 3D world pose transformation for a modular sub-assembly."""

    subassembly_id: int
    pitch_deg: float
    local_pivot_mm: Tuple[float, float, float]
    world_pivot_mm: Tuple[float, float, float]
    nominal_y_offset_plates: int

    def transform_point(self, lx_mm: float, ly_mm: float, lz_mm: float) -> Tuple[float, float, float]:
        """Transform a 3D point (lx_mm, ly_mm, lz_mm) from sub-assembly local mm to world mm."""
        rad = math.radians(self.pitch_deg)
        c = math.cos(rad)
        s = math.sin(rad)
        dx = lx_mm - self.local_pivot_mm[0]
        dy = ly_mm - self.local_pivot_mm[1]
        dz = lz_mm - self.local_pivot_mm[2]
        wx = self.world_pivot_mm[0] + dx
        wy = self.world_pivot_mm[1] + dy * c - dz * s
        wz = self.world_pivot_mm[2] + dy * s + dz * c
        return (wx, wy, wz)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subassembly_id": self.subassembly_id,
            "subassembly_name": SUBASSEMBLY_NAMES[self.subassembly_id],
            "pitch_deg": round(self.pitch_deg, 3),
            "local_pivot_mm": [round(v, 4) for v in self.local_pivot_mm],
            "world_pivot_mm": [round(v, 4) for v in self.world_pivot_mm],
            "nominal_y_offset_plates": self.nominal_y_offset_plates,
        }


SUBASSEMBLY_POSES: Dict[int, SubassemblyPose] = {
    1: SubassemblyPose(
        subassembly_id=1,
        pitch_deg=0.0,
        local_pivot_mm=(0.0, ANKLE_Y_MM, ANKLE_Z_MM),
        world_pivot_mm=(0.0, ANKLE_Y_MM, ANKLE_Z_MM),
        nominal_y_offset_plates=0,
    ),
    2: SubassemblyPose(
        subassembly_id=2,
        pitch_deg=SA02_PITCH_DEG,
        local_pivot_mm=(0.0, 1.5 * PLATE_MM, -2.0 * STUD_MM),
        world_pivot_mm=(0.0, ANKLE_Y_MM, ANKLE_Z_MM),
        nominal_y_offset_plates=5,
    ),
    3: SubassemblyPose(
        subassembly_id=3,
        pitch_deg=SA03_PITCH_DEG,
        local_pivot_mm=(0.0, 1.5 * PLATE_MM, -2.0 * STUD_MM),
        world_pivot_mm=(0.0, KNEE_Y_MM, KNEE_Z_MM),
        nominal_y_offset_plates=17,
    ),
    4: SubassemblyPose(
        subassembly_id=4,
        pitch_deg=SA04_PITCH_DEG,
        local_pivot_mm=(0.0, 4.5 * PLATE_MM, -2.0 * STUD_MM),
        world_pivot_mm=(0.0, HIP_Y_MM, HIP_Z_MM),
        nominal_y_offset_plates=24,
    ),
    5: SubassemblyPose(
        subassembly_id=5,
        pitch_deg=SA05_PITCH_DEG,
        local_pivot_mm=(0.0, 0.0, 0.0),
        world_pivot_mm=(0.0, SA05_ORIGIN_Y_MM, SA05_ORIGIN_Z_MM),
        nominal_y_offset_plates=35,
    ),
    6: SubassemblyPose(
        subassembly_id=6,
        pitch_deg=SA06_PITCH_DEG,
        local_pivot_mm=(0.0, 1.5 * PLATE_MM, 0.0),
        world_pivot_mm=(0.0, LOWER_NECK_Y_MM, LOWER_NECK_Z_MM),
        nominal_y_offset_plates=43,
    ),
    7: SubassemblyPose(
        subassembly_id=7,
        pitch_deg=SA07_PITCH_DEG,
        local_pivot_mm=(0.0, SA07_LOCAL_PIN_Y_MM, SA07_LOCAL_PIN_Z_MM),
        world_pivot_mm=(0.0, UPPER_NECK_Y_MM, UPPER_NECK_Z_MM),
        nominal_y_offset_plates=55,
    ),
}


def get_coaxial_pin_joints() -> List[Dict[str, Any]]:
    """Return the 8 coaxial mechanical Technic pin joints uniting SA-01..SA-07."""
    return [
        {
            "joint_id": "left_ankle_pin",
            "name": "Left Ankle Coaxial Technic Pin Joint",
            "parent_subassembly_id": 1,
            "child_subassembly_id": 2,
            "side": "left",
            "connecting_parts": ["3700", "2780"],
            "pin_orientation": "horizontal_x",
            "axis": [1.0, 0.0, 0.0],
            "pivot_mm": [-36.0, round(ANKLE_Y_MM, 4), round(ANKLE_Z_MM, 4)],
            "parent_local_pin_mm": [-36.0, 6.5 * PLATE_MM, -2.0 * STUD_MM],
            "child_local_pin_mm": [-36.0, 1.5 * PLATE_MM, -2.0 * STUD_MM],
            "parent_pitch_deg": 0.0,
            "child_pitch_deg": SA02_PITCH_DEG,
        },
        {
            "joint_id": "right_ankle_pin",
            "name": "Right Ankle Coaxial Technic Pin Joint",
            "parent_subassembly_id": 1,
            "child_subassembly_id": 2,
            "side": "right",
            "connecting_parts": ["3700", "2780"],
            "pin_orientation": "horizontal_x",
            "axis": [1.0, 0.0, 0.0],
            "pivot_mm": [36.0, round(ANKLE_Y_MM, 4), round(ANKLE_Z_MM, 4)],
            "parent_local_pin_mm": [36.0, 6.5 * PLATE_MM, -2.0 * STUD_MM],
            "child_local_pin_mm": [36.0, 1.5 * PLATE_MM, -2.0 * STUD_MM],
            "parent_pitch_deg": 0.0,
            "child_pitch_deg": SA02_PITCH_DEG,
        },
        {
            "joint_id": "left_knee_pin",
            "name": "Left Knee Coaxial Technic Pin Joint",
            "parent_subassembly_id": 2,
            "child_subassembly_id": 3,
            "side": "left",
            "connecting_parts": ["3700", "2780"],
            "pin_orientation": "horizontal_x",
            "axis": [1.0, 0.0, 0.0],
            "pivot_mm": [-36.0, round(KNEE_Y_MM, 4), round(KNEE_Z_MM, 4)],
            "parent_local_pin_mm": [-36.0, 14.5 * PLATE_MM, -2.0 * STUD_MM],
            "child_local_pin_mm": [-36.0, 1.5 * PLATE_MM, -2.0 * STUD_MM],
            "parent_pitch_deg": SA02_PITCH_DEG,
            "child_pitch_deg": SA03_PITCH_DEG,
        },
        {
            "joint_id": "right_knee_pin",
            "name": "Right Knee Coaxial Technic Pin Joint",
            "parent_subassembly_id": 2,
            "child_subassembly_id": 3,
            "side": "right",
            "connecting_parts": ["3700", "2780"],
            "pin_orientation": "horizontal_x",
            "axis": [1.0, 0.0, 0.0],
            "pivot_mm": [36.0, round(KNEE_Y_MM, 4), round(KNEE_Z_MM, 4)],
            "parent_local_pin_mm": [36.0, 14.5 * PLATE_MM, -2.0 * STUD_MM],
            "child_local_pin_mm": [36.0, 1.5 * PLATE_MM, -2.0 * STUD_MM],
            "parent_pitch_deg": SA02_PITCH_DEG,
            "child_pitch_deg": SA03_PITCH_DEG,
        },
        {
            "joint_id": "left_hip_pin",
            "name": "Left Hip Coaxial Technic Pin & Roll Hub Joint",
            "parent_subassembly_id": 3,
            "child_subassembly_id": 4,
            "side": "left",
            "connecting_parts": ["3700", "2780", "4032"],
            "pin_orientation": "horizontal_x",
            "axis": [1.0, 0.0, 0.0],
            "pivot_mm": [-36.0, round(HIP_Y_MM, 4), round(HIP_Z_MM, 4)],
            "parent_local_pin_mm": [-36.0, 12.5 * PLATE_MM, -2.0 * STUD_MM],
            "child_local_pin_mm": [-36.0, 4.5 * PLATE_MM, -2.0 * STUD_MM],
            "parent_pitch_deg": SA03_PITCH_DEG,
            "child_pitch_deg": SA04_PITCH_DEG,
        },
        {
            "joint_id": "right_hip_pin",
            "name": "Right Hip Coaxial Technic Pin & Roll Hub Joint",
            "parent_subassembly_id": 3,
            "child_subassembly_id": 4,
            "side": "right",
            "connecting_parts": ["3700", "2780", "4032"],
            "pin_orientation": "horizontal_x",
            "axis": [1.0, 0.0, 0.0],
            "pivot_mm": [36.0, round(HIP_Y_MM, 4), round(HIP_Z_MM, 4)],
            "parent_local_pin_mm": [36.0, 12.5 * PLATE_MM, -2.0 * STUD_MM],
            "child_local_pin_mm": [36.0, 4.5 * PLATE_MM, -2.0 * STUD_MM],
            "parent_pitch_deg": SA03_PITCH_DEG,
            "child_pitch_deg": SA04_PITCH_DEG,
        },
        {
            "joint_id": "lower_neck_pin",
            "name": "Lower Neck U-Bracket Coaxial Technic Pin Joint",
            "parent_subassembly_id": 5,
            "child_subassembly_id": 6,
            "side": "center",
            "connecting_parts": ["3700", "2780"],
            "pin_orientation": "horizontal_x",
            "axis": [1.0, 0.0, 0.0],
            "pivot_mm": [0.0, round(LOWER_NECK_Y_MM, 4), round(LOWER_NECK_Z_MM, 4)],
            "parent_local_pin_mm": [0.0, 9.5 * PLATE_MM, 0.0],
            "child_local_pin_mm": [0.0, 1.5 * PLATE_MM, 0.0],
            "parent_pitch_deg": SA05_PITCH_DEG,
            "child_pitch_deg": SA06_PITCH_DEG,
        },
        {
            "joint_id": "upper_neck_turntable_pin",
            "name": "Upper Neck Coaxial Technic Pin & 4032 Turntable Joint",
            "parent_subassembly_id": 6,
            "child_subassembly_id": 7,
            "side": "center",
            "connecting_parts": ["3700", "2780", "4032"],
            "pin_orientation": "horizontal_x",
            "axis": [1.0, 0.0, 0.0],
            "pivot_mm": [0.0, round(UPPER_NECK_Y_MM, 4), round(UPPER_NECK_Z_MM, 4)],
            "parent_local_pin_mm": [0.0, 14.5 * PLATE_MM, 0.0],
            "child_local_pin_mm": [0.0, SA07_LOCAL_PIN_Y_MM, SA07_LOCAL_PIN_Z_MM],
            "parent_pitch_deg": SA06_PITCH_DEG,
            "child_pitch_deg": SA07_PITCH_DEG,
        },
    ]


def get_kinematic_joints() -> List[Dict[str, Any]]:
    """Return the 10-DoF kinematic walking & expressive joint tree at the exact coaxial pin centers."""
    return [
        {
            "joint_id": "left_ankle_pitch",
            "name": "Left Ankle Pitch Pin Joint",
            "subassembly_id": 1,
            "child_subassemblies": [1],
            "side": "left",
            "pivot_grid": {"x_studs": -4.5, "y_plates": 6.5, "z_studs": -2.0},
            "pivot_mm": [-36.0, round(ANKLE_Y_MM, 3), round(ANKLE_Z_MM, 3)],
            "rest_pitch_deg": SA02_PITCH_DEG,
            "axis": [1.0, 0.0, 0.0],
            "limits_deg": [-18.0, 18.0],
            "gait_amplitude_deg": 15.0,
        },
        {
            "joint_id": "right_ankle_pitch",
            "name": "Right Ankle Pitch Pin Joint",
            "subassembly_id": 1,
            "child_subassemblies": [1],
            "side": "right",
            "pivot_grid": {"x_studs": 4.5, "y_plates": 6.5, "z_studs": -2.0},
            "pivot_mm": [36.0, round(ANKLE_Y_MM, 3), round(ANKLE_Z_MM, 3)],
            "rest_pitch_deg": SA02_PITCH_DEG,
            "axis": [1.0, 0.0, 0.0],
            "limits_deg": [-18.0, 18.0],
            "gait_amplitude_deg": 15.0,
        },
        {
            "joint_id": "left_knee_pitch",
            "name": "Left Knee Linkage Pitch Joint",
            "subassembly_id": 2,
            "child_subassemblies": [1, 2],
            "side": "left",
            "pivot_grid": {"x_studs": -4.5, "y_plates": round(KNEE_Y_MM / PLATE_MM, 2), "z_studs": round(KNEE_Z_MM / STUD_MM, 2)},
            "pivot_mm": [-36.0, round(KNEE_Y_MM, 3), round(KNEE_Z_MM, 3)],
            "rest_pitch_deg": SA03_PITCH_DEG,
            "axis": [1.0, 0.0, 0.0],
            "limits_deg": [0.0, 28.0],
            "gait_amplitude_deg": 22.0,
        },
        {
            "joint_id": "right_knee_pitch",
            "name": "Right Knee Linkage Pitch Joint",
            "subassembly_id": 2,
            "child_subassemblies": [1, 2],
            "side": "right",
            "pivot_grid": {"x_studs": 4.5, "y_plates": round(KNEE_Y_MM / PLATE_MM, 2), "z_studs": round(KNEE_Z_MM / STUD_MM, 2)},
            "pivot_mm": [36.0, round(KNEE_Y_MM, 3), round(KNEE_Z_MM, 3)],
            "rest_pitch_deg": SA03_PITCH_DEG,
            "axis": [1.0, 0.0, 0.0],
            "limits_deg": [0.0, 28.0],
            "gait_amplitude_deg": 22.0,
        },
        {
            "joint_id": "left_hip_pitch",
            "name": "Left Hip Pitch Servo Joint",
            "subassembly_id": 3,
            "child_subassemblies": [1, 2, 3],
            "side": "left",
            "pivot_grid": {"x_studs": -4.5, "y_plates": round(HIP_Y_MM / PLATE_MM, 2), "z_studs": round(HIP_Z_MM / STUD_MM, 2)},
            "pivot_mm": [-36.0, round(HIP_Y_MM, 3), round(HIP_Z_MM, 3)],
            "rest_pitch_deg": SA03_PITCH_DEG,
            "axis": [1.0, 0.0, 0.0],
            "limits_deg": [-24.0, 24.0],
            "gait_amplitude_deg": 18.0,
        },
        {
            "joint_id": "right_hip_pitch",
            "name": "Right Hip Pitch Servo Joint",
            "subassembly_id": 3,
            "child_subassemblies": [1, 2, 3],
            "side": "right",
            "pivot_grid": {"x_studs": 4.5, "y_plates": round(HIP_Y_MM / PLATE_MM, 2), "z_studs": round(HIP_Z_MM / STUD_MM, 2)},
            "pivot_mm": [36.0, round(HIP_Y_MM, 3), round(HIP_Z_MM, 3)],
            "rest_pitch_deg": SA03_PITCH_DEG,
            "axis": [1.0, 0.0, 0.0],
            "limits_deg": [-24.0, 24.0],
            "gait_amplitude_deg": 18.0,
        },
        {
            "joint_id": "left_hip_roll",
            "name": "Left Cylindrical Hip-Roll Hub Joint",
            "subassembly_id": 4,
            "child_subassemblies": [1, 2, 3],
            "side": "left",
            "pivot_grid": {"x_studs": -2.5, "y_plates": round(HIP_Y_MM / PLATE_MM, 2), "z_studs": 2.0},
            "pivot_mm": [-20.0, round(HIP_Y_MM, 3), round(SA04_ORIGIN_Z_MM + 2.0 * STUD_MM, 3)],
            "rest_pitch_deg": 0.0,
            "axis": [0.0, 0.0, 1.0],
            "limits_deg": [-15.0, 15.0],
            "gait_amplitude_deg": 8.0,
        },
        {
            "joint_id": "right_hip_roll",
            "name": "Right Cylindrical Hip-Roll Hub Joint",
            "subassembly_id": 4,
            "child_subassemblies": [1, 2, 3],
            "side": "right",
            "pivot_grid": {"x_studs": 2.5, "y_plates": round(HIP_Y_MM / PLATE_MM, 2), "z_studs": 2.0},
            "pivot_mm": [20.0, round(HIP_Y_MM, 3), round(SA04_ORIGIN_Z_MM + 2.0 * STUD_MM, 3)],
            "rest_pitch_deg": 0.0,
            "axis": [0.0, 0.0, 1.0],
            "limits_deg": [-15.0, 15.0],
            "gait_amplitude_deg": 8.0,
        },
        {
            "joint_id": "lower_neck_pitch",
            "name": "Lower Neck Stalk Pitch Joint",
            "subassembly_id": 6,
            "child_subassemblies": [6, 7],
            "side": "center",
            "pivot_grid": {"x_studs": 0.0, "y_plates": round(LOWER_NECK_Y_MM / PLATE_MM, 2), "z_studs": round(LOWER_NECK_Z_MM / STUD_MM, 2)},
            "pivot_mm": [0.0, round(LOWER_NECK_Y_MM, 3), round(LOWER_NECK_Z_MM, 3)],
            "rest_pitch_deg": SA06_PITCH_DEG,
            "axis": [1.0, 0.0, 0.0],
            "limits_deg": [-20.0, 25.0],
            "gait_amplitude_deg": 6.0,
        },
        {
            "joint_id": "upper_neck_pitch_and_head_yaw",
            "name": "Upper Neck Pitch & Head Pan/Tilt Joint",
            "subassembly_id": 6,
            "child_subassemblies": [7],
            "side": "center",
            "pivot_grid": {"x_studs": 0.0, "y_plates": round(UPPER_NECK_Y_MM / PLATE_MM, 2), "z_studs": round(UPPER_NECK_Z_MM / STUD_MM, 2)},
            "pivot_mm": [0.0, round(UPPER_NECK_Y_MM, 3), round(UPPER_NECK_Z_MM, 3)],
            "rest_pitch_deg": SA07_PITCH_DEG,
            "axis": [0.0, 1.0, 0.0],
            "secondary_axis": [1.0, 0.0, 0.0],
            "limits_deg": [-45.0, 45.0],
            "gait_amplitude_deg": 10.0,
        },
    ]


def _compute_world_rotation_matrix(
    local_rot_y_deg: int,
    pitch_deg: float,
    pin_orientation: str = "vertical_y",
) -> List[List[float]]:
    """Compute exact 3x3 orthogonal rotation matrix R_world = R_x(pitch_deg) * R_local."""
    rot = local_rot_y_deg % 360
    if rot == 0:
        r_loc = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    elif rot == 90:
        r_loc = [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]]
    elif rot == 180:
        r_loc = [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]]
    else:
        r_loc = [[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]]

    if pin_orientation == "horizontal_x":
        # Rotate local Y shaft axis horizontally onto X axis: R_z(-90 deg)
        r_loc = [
            [0.0, 1.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
        ]

    rad = math.radians(pitch_deg)
    c = math.cos(rad)
    s = math.sin(rad)
    r_x = [
        [1.0, 0.0, 0.0],
        [0.0, c, -s],
        [0.0, s, c],
    ]

    out: List[List[float]] = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            out[i][j] = round(
                r_x[i][0] * r_loc[0][j] + r_x[i][1] * r_loc[1][j] + r_x[i][2] * r_loc[2][j],
                6,
            )
    return out


@dataclass
class PlacedBrick:
    """A single placed LEGO element in its sub-assembly's integer grid with 3D world pose."""

    brick_id: int
    part_id: str
    color_id: int
    x: int
    y: int  # local_y within subassembly_id (starts at 0 for each subassembly)
    z: int
    rotation: int
    subassembly_id: int
    step_id: int
    notes: str = ""
    pin_orientation: str = "vertical_y"
    pin_x_offset_studs: float = 0.0
    pin_z_offset_studs: float = 0.0

    @property
    def spec(self) -> PartSpec:
        return PARTS_CATALOG[self.part_id]

    @property
    def dims(self) -> Tuple[int, int, int]:
        return self.spec.oriented_dims(self.rotation)

    @property
    def dx(self) -> int:
        return self.dims[0]

    @property
    def dy(self) -> int:
        return self.dims[1]

    @property
    def dz(self) -> int:
        return self.dims[2]

    @property
    def x_max(self) -> int:
        return self.x + self.dx

    @property
    def y_top(self) -> int:
        return self.y + self.dy

    @property
    def z_max(self) -> int:
        return self.z + self.dz

    @property
    def pose(self) -> SubassemblyPose:
        return SUBASSEMBLY_POSES[self.subassembly_id]

    @property
    def world_pitch_deg(self) -> float:
        return self.pose.pitch_deg

    @property
    def world_rotation_matrix(self) -> List[List[float]]:
        return _compute_world_rotation_matrix(
            self.rotation, self.world_pitch_deg, self.pin_orientation
        )

    def occupied_cells(self) -> List[Tuple[int, int, int]]:
        """Return all unit (1 stud x 1 plate x 1 stud) local grid cells occupied."""
        if self.part_id == "2780":
            return []
        cells: List[Tuple[int, int, int]] = []
        dx, dy, dz = self.dims
        for ix in range(self.x, self.x + dx):
            for iy in range(self.y, self.y + dy):
                for iz in range(self.z, self.z + dz):
                    cells.append((ix, iy, iz))
        return cells

    def footprint_cells(self) -> Set[Tuple[int, int]]:
        """Return 2D (x, z) local stud footprint cells."""
        if self.part_id == "2780":
            return set()
        dx, _, dz = self.dims
        return {
            (ix, iz)
            for ix in range(self.x, self.x + dx)
            for iz in range(self.z, self.z + dz)
        }

    def local_center_mm(self) -> Tuple[float, float, float]:
        """Return 3D center of mass in the sub-assembly's local millimeter frame."""
        dx, dy, dz = self.dims
        lx = (self.x + 0.5 * dx + self.pin_x_offset_studs) * STUD_MM
        ly = (self.y + 0.5 * dy) * PLATE_MM
        lz = (self.z + 0.5 * dz + self.pin_z_offset_studs) * STUD_MM
        return (lx, ly, lz)

    def pin_hole_world_yz_mm(self) -> Tuple[float, float]:
        """Return world (wy, wz) of this Technic brick's coaxial pin hole center."""
        dx, dy, dz = self.dims
        lx = (self.x + 0.5 * dx) * STUD_MM
        ly = (self.y + 0.5 * dy) * PLATE_MM
        lz = (self.z + 0.5 * dz) * STUD_MM
        _, wy, wz = self.pose.transform_point(lx, ly, lz)
        return (wy, wz)

    def world_center_mm(self) -> Tuple[float, float, float]:
        """Return exact 3D world-space center of mass in millimeters after pose rotation."""
        lx, ly, lz = self.local_center_mm()
        return self.pose.transform_point(lx, ly, lz)

    def center_mm(self) -> Tuple[float, float, float]:
        """Return 3D world-space center of mass in millimeters."""
        return self.world_center_mm()

    def world_corners_mm(self) -> List[Tuple[float, float, float]]:
        """Return all 8 corners of this brick in 3D posed world space (mm)."""
        if self.part_id == "2780":
            wx, wy, wz = self.world_center_mm()
            return [
                (wx + sx * 7.88, wy + sy * 2.30, wz + sz * 2.30)
                for sx in (-1.0, 1.0)
                for sy in (-1.0, 1.0)
                for sz in (-1.0, 1.0)
            ]
        dx, dy, dz = self.dims
        x0 = self.x * STUD_MM
        x1 = (self.x + dx) * STUD_MM
        y0 = self.y * PLATE_MM
        y1 = (self.y + dy) * PLATE_MM
        z0 = (self.z + self.pin_z_offset_studs) * STUD_MM
        z1 = (self.z + dz + self.pin_z_offset_studs) * STUD_MM
        corners: List[Tuple[float, float, float]] = []
        for cx in (x0, x1):
            for cy in (y0, y1):
                for cz in (z0, z1):
                    corners.append(self.pose.transform_point(cx, cy, cz))
        return corners

    def world_aabb_mm(self) -> Tuple[float, float, float, float, float, float]:
        """Return (min_x, max_x, min_y, max_y, min_z, max_z) in 3D world space (mm)."""
        pts = self.world_corners_mm()
        return (
            min(p[0] for p in pts),
            max(p[0] for p in pts),
            min(p[1] for p in pts),
            max(p[1] for p in pts),
            min(p[2] for p in pts),
            max(p[2] for p in pts),
        )

    def to_dict(self) -> Dict[str, Any]:
        dx, dy, dz = self.dims
        lx, ly, lz = self.local_center_mm()
        wx, wy, wz = self.world_center_mm()
        return {
            "brick_id": self.brick_id,
            "part_id": self.part_id,
            "part_name": self.spec.name,
            "color_id": self.color_id,
            "color_name": COLORS[self.color_id].name,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "local_x": self.x,
            "local_y": self.y,
            "local_z": self.z,
            "local_y_top": self.y_top,
            "dx": dx,
            "dy": dy,
            "dz": dz,
            "y_top": self.y_top,
            "rotation": self.rotation,
            "subassembly_id": self.subassembly_id,
            "subassembly_name": SUBASSEMBLY_NAMES[self.subassembly_id],
            "step_id": self.step_id,
            "mass_g": self.spec.mass_g,
            "has_top_studs": self.spec.has_top_studs,
            "has_bottom_tubes": self.spec.has_bottom_tubes,
            "pin_orientation": self.pin_orientation,
            "pin_x_offset_studs": self.pin_x_offset_studs,
            "pin_z_offset_studs": self.pin_z_offset_studs,
            "local_center_mm": [round(lx, 3), round(ly, 3), round(lz, 3)],
            "world_center_mm": [round(wx, 3), round(wy, 3), round(wz, 3)],
            "center_mm": [round(wx, 3), round(wy, 3), round(wz, 3)],
            "world_pitch_deg": round(self.world_pitch_deg, 3),
            "world_rotation_matrix": self.world_rotation_matrix,
            "notes": self.notes,
        }


@dataclass
class MicroduckModel:
    """Complete parametric CAD & 10-DoF kinematic model of the Microduck LEGO robot."""

    bricks: List[PlacedBrick] = field(default_factory=list)
    kinematic_joints: List[Dict[str, Any]] = field(default_factory=get_kinematic_joints)
    coaxial_pin_joints: List[Dict[str, Any]] = field(default_factory=get_coaxial_pin_joints)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": "Hugging Face x Pollen Robotics Microduck - Life-Sized LEGO Edition (Rev 3.1 Zero-Collision Pin-Jointed)",
            "scale_height_plates": 78,
            "scale_height_mm": 249.6,
            "total_pieces": len(self.bricks),
            "total_steps": max((b.step_id for b in self.bricks), default=0),
            "subassembly_poses": [
                SUBASSEMBLY_POSES[sid].to_dict() for sid in sorted(SUBASSEMBLY_POSES.keys())
            ],
            "coaxial_pin_joints": self.coaxial_pin_joints,
            "subassemblies": [
                {
                    "subassembly_id": sid,
                    "name": sname,
                    "pitch_deg": SUBASSEMBLY_POSES[sid].pitch_deg,
                    "piece_count": sum(1 for b in self.bricks if b.subassembly_id == sid),
                    "local_y_min": min(
                        (b.y for b in self.bricks if b.subassembly_id == sid),
                        default=0,
                    ),
                    "local_y_max": max(
                        (b.y_top for b in self.bricks if b.subassembly_id == sid),
                        default=0,
                    ),
                    "world_y_min_mm": round(
                        min(
                            (b.world_aabb_mm()[2] for b in self.bricks if b.subassembly_id == sid),
                            default=0.0,
                        ),
                        2,
                    ),
                    "world_y_max_mm": round(
                        max(
                            (b.world_aabb_mm()[3] for b in self.bricks if b.subassembly_id == sid),
                            default=0.0,
                        ),
                        2,
                    ),
                }
                for sid, sname in SUBASSEMBLY_NAMES.items()
            ],
            "kinematic_joints": self.kinematic_joints,
            "bricks": [b.to_dict() for b in self.bricks],
        }

    def save_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


class MicroduckBuilder:
    """Constructs the 7 modular sub-assemblies cleanly in their local integer grids."""

    def __init__(self) -> None:
        self.raw_bricks: List[PlacedBrick] = []
        self.occupied_by_sub: Dict[int, Dict[Tuple[int, int, int], int]] = {
            sid: {} for sid in SUBASSEMBLY_NAMES
        }
        self.top_studs_by_sub: Dict[int, Set[Tuple[int, int, int]]] = {
            sid: set() for sid in SUBASSEMBLY_NAMES
        }
        self._next_id = 1

    def add(
        self,
        part_id: str,
        color_id: int,
        x: int,
        y: int,
        z: int,
        rotation: int,
        subassembly_id: int,
        notes: str = "",
        pin_orientation: str = "vertical_y",
        pin_x_offset_studs: float = 0.0,
        pin_z_offset_studs: float = 0.0,
    ) -> PlacedBrick:
        """Place a brick in subassembly_id's local grid and verify 0 local collisions & valid stud support."""
        if part_id not in PARTS_CATALOG:
            raise ValueError(f"Unknown part_id {part_id}")
        if color_id not in COLORS:
            raise ValueError(f"Unknown color_id {color_id}")
        if part_id == "2780" and pin_orientation == "vertical_y":
            pin_orientation = "horizontal_x"

        brick = PlacedBrick(
            brick_id=self._next_id,
            part_id=part_id,
            color_id=color_id,
            x=x,
            y=y,
            z=z,
            rotation=rotation,
            subassembly_id=subassembly_id,
            step_id=0,
            notes=notes,
            pin_orientation=pin_orientation,
            pin_x_offset_studs=pin_x_offset_studs,
            pin_z_offset_studs=pin_z_offset_studs,
        )
        if part_id == "2780":
            self._next_id += 1
            self.raw_bricks.append(brick)
            return brick

        occ = self.occupied_by_sub[subassembly_id]
        top_studs = self.top_studs_by_sub[subassembly_id]

        for cell in brick.occupied_cells():
            if cell in occ:
                other_id = occ[cell]
                raise RuntimeError(
                    f"Local volumetric collision in SA-{subassembly_id:02d} at cell {cell} "
                    f"between {part_id} at ({x},{y},{z}) and brick_id={other_id}"
                )
        if y > 0:
            if not brick.spec.has_bottom_tubes or not any(
                (ix, y, iz) in top_studs for (ix, iz) in brick.footprint_cells()
            ):
                raise RuntimeError(
                    f"Unsupported brick {part_id} at local ({x},{y},{z}) in SA-{subassembly_id:02d} ({notes})"
                )
        for cell in brick.occupied_cells():
            occ[cell] = brick.brick_id
        if brick.spec.has_top_studs:
            for ix, iz in brick.footprint_cells():
                top_studs.add((ix, brick.y_top, iz))

        self._next_id += 1
        self.raw_bricks.append(brick)
        return brick

    def tile_rect(
        self,
        x0: int,
        x1: int,
        y: int,
        z0: int,
        z1: int,
        height_y: int,
        color_id: int,
        subassembly_id: int,
        prefer_x_axis: bool,
        stagger_shift: int = 0,
        use_tiles: bool = False,
        notes: str = "",
    ) -> List[PlacedBrick]:
        """Tile a rectangular [x0, x1) x [y, y+height_y) x [z0, z1) region in subassembly_id's local grid."""
        placed: List[PlacedBrick] = []
        occ = self.occupied_by_sub[subassembly_id]
        top_studs = self.top_studs_by_sub[subassembly_id]

        if height_y == 1 and use_tiles:
            candidates_long = [
                ("87079", 2, 4),
                ("2431", 1, 4),
                ("3068b", 2, 2),
                ("3069b", 1, 2),
                ("3070b", 1, 1),
            ]
        elif height_y == 1:
            if stagger_shift % 2 == 1:
                candidates_long = [
                    ("3021", 2, 3),
                    ("3020", 2, 4),
                    ("3795", 2, 6),
                    ("3022", 2, 2),
                    ("3623", 1, 3),
                    ("3710", 1, 4),
                    ("3023", 1, 2),
                    ("3024", 1, 1),
                ]
            else:
                candidates_long = [
                    ("3020", 2, 4),
                    ("3795", 2, 6),
                    ("3021", 2, 3),
                    ("3022", 2, 2),
                    ("3710", 1, 4),
                    ("3623", 1, 3),
                    ("3023", 1, 2),
                    ("3024", 1, 1),
                ]
        elif height_y == 3:
            if stagger_shift % 2 == 1:
                candidates_long = [
                    ("3002", 2, 3),
                    ("3001", 2, 4),
                    ("3003", 2, 2),
                    ("3622", 1, 3),
                    ("3010", 1, 4),
                    ("3004", 1, 2),
                    ("3005", 1, 1),
                ]
            else:
                candidates_long = [
                    ("3001", 2, 4),
                    ("3002", 2, 3),
                    ("3003", 2, 2),
                    ("3010", 1, 4),
                    ("3622", 1, 3),
                    ("3004", 1, 2),
                    ("3005", 1, 1),
                ]
        else:
            raise ValueError(f"Unsupported height_y={height_y} in tile_rect")

        unfilled: Set[Tuple[int, int]] = {
            (ix, iz)
            for ix in range(x0, x1)
            for iz in range(z0, z1)
            if not any((ix, iy, iz) in occ for iy in range(y, y + height_y))
        }

        primary_rot = 90 if prefer_x_axis else 0
        rot_order = [primary_rot, 0 if primary_rot == 90 else 90]

        def _leaves_valid_remainder(cells_2d: List[Tuple[int, int]]) -> bool:
            if y == 0:
                return True
            rem = unfilled.difference(cells_2d)
            for rx, rz in rem:
                if (rx, y, rz) in top_studs:
                    continue
                has_anchor = False
                for step_dir in (-1, 1):
                    for dist in (1, 2, 3):
                        nx = rx + step_dir * dist
                        if (nx, rz) not in rem:
                            break
                        if (nx, y, rz) in top_studs:
                            has_anchor = True
                            break
                    if has_anchor:
                        break
                    for dist in (1, 2, 3):
                        nz = rz + step_dir * dist
                        if (rx, nz) not in rem:
                            break
                        if (rx, y, nz) in top_studs:
                            has_anchor = True
                            break
                    if has_anchor:
                        break
                if not has_anchor:
                    return False
            return True

        if y > 0:
            span_candidates = sorted(
                [c for c in candidates_long if not (c[1] == 1 and c[2] == 1)],
                key=lambda item: (-(item[1] * item[2]), -max(item[1], item[2])),
            )
            unsupported = sorted(
                [c for c in unfilled if (c[0], y, c[1]) not in top_studs],
                key=lambda c: -min(
                    [
                        abs(c[0] - sx) + abs(c[1] - sz)
                        for (sx, sz) in unfilled
                        if (sx, y, sz) in top_studs
                    ]
                    or [0]
                ),
            )
            for ux, uz in unsupported:
                if (ux, uz) not in unfilled:
                    continue
                anchored = False
                for rot in rot_order:
                    if anchored:
                        break
                    for part_id, w_orig, d_orig in span_candidates:
                        dx = d_orig if rot == 90 else w_orig
                        dz = w_orig if rot == 90 else d_orig
                        for ox in range(dx):
                            if anchored:
                                break
                            for oz in range(dz):
                                bx = ux - ox
                                bz = uz - oz
                                cells_2d = [
                                    (bx + ix, bz + iz)
                                    for ix in range(dx)
                                    for iz in range(dz)
                                ]
                                if (
                                    all(c in unfilled for c in cells_2d)
                                    and any((cx, y, cz) in top_studs for (cx, cz) in cells_2d)
                                    and _leaves_valid_remainder(cells_2d)
                                ):
                                    b = self.add(
                                        part_id=part_id,
                                        color_id=color_id,
                                        x=bx,
                                        y=y,
                                        z=bz,
                                        rotation=rot,
                                        subassembly_id=subassembly_id,
                                        notes=notes,
                                    )
                                    placed.append(b)
                                    for c in cells_2d:
                                        unfilled.remove(c)
                                    anchored = True
                                    break

        for iz in range(z0, z1):
            for ix in range(x0, x1):
                if (ix, iz) not in unfilled:
                    continue
                for rot in rot_order:
                    placed_here = False
                    for part_id, w_orig, d_orig in candidates_long:
                        dx = d_orig if rot == 90 else w_orig
                        dz = w_orig if rot == 90 else d_orig
                        cells_2d = [
                            (ix + ox, iz + oz)
                            for ox in range(dx)
                            for oz in range(dz)
                        ]
                        if all(c in unfilled for c in cells_2d):
                            if y > 0 and not any(
                                (cx, y, cz) in top_studs for (cx, cz) in cells_2d
                            ):
                                continue
                            b = self.add(
                                part_id=part_id,
                                color_id=color_id,
                                x=ix,
                                y=y,
                                z=iz,
                                rotation=rot,
                                subassembly_id=subassembly_id,
                                notes=notes,
                            )
                            placed.append(b)
                            for c in cells_2d:
                                unfilled.remove(c)
                            placed_here = True
                            break
                    if placed_here:
                        break

        fallback_part = (
            "3070b"
            if (height_y == 1 and use_tiles)
            else ("3024" if height_y == 1 else "3005")
        )
        for ix, iz in sorted(list(unfilled)):
            b = self.add(
                part_id=fallback_part,
                color_id=color_id,
                x=ix,
                y=y,
                z=iz,
                rotation=0,
                subassembly_id=subassembly_id,
                notes=notes,
            )
            placed.append(b)
        return placed

    # ------------------------------------------------------------------
    # SA-01: Two-Tone Orange & Yellow Robotic Bootie Feet (local_y = 0..8, pitch = 0.0 deg)
    # ------------------------------------------------------------------
    def build_sa01_bootie_feet(self) -> None:
        sid = 1
        for foot_name, x0, x1 in [("Left Bootie Foot", -7, -2), ("Right Bootie Foot", 2, 7)]:
            # local_y = 0..1: Yellow ground sole layer 1 (Z-oriented, z in [-6, 5) = 11 studs = 88.0 mm)
            self.tile_rect(
                x0, x1, 0, -6, 5, 1, COLOR_YELLOW, sid,
                prefer_x_axis=False, stagger_shift=0, notes=f"{foot_name} Yellow ground sole y=0..1"
            )
            # local_y = 1..2: Yellow upper sole layer 2 (bridge Z=3 toe seam + X-oriented stagger)
            self.add("3020", COLOR_YELLOW, x0, 1, 1, 0, sid, f"{foot_name} Yellow toe-instep bridge outer")
            self.add("3020", COLOR_YELLOW, x0 + 2, 1, 1, 0, sid, f"{foot_name} Yellow toe-instep bridge mid")
            self.add("3710", COLOR_YELLOW, x0 + 4, 1, 1, 0, sid, f"{foot_name} Yellow toe-instep bridge inner")
            self.tile_rect(
                x0, x1, 1, -6, 5, 1, COLOR_YELLOW, sid,
                prefer_x_axis=True, stagger_shift=1, notes=f"{foot_name} Yellow upper sole y=1..2"
            )
            # local_y = 2..3: Orange midsole base platform
            # Cap central 3-stud shin recess (x in [x0+1, x1-1), z in [-3, 0)) with smooth tiles (use_tiles=True)
            # and build front (z=0) & rear (z=-4) hard-stop cradle ledges for SA-02's +24 deg lower shin!
            self.tile_rect(
                x0 + 1, x1 - 1, 2, -3, 0, 1, COLOR_ORANGE, sid,
                prefer_x_axis=False, use_tiles=True, notes=f"{foot_name} smooth shin recess floor y=2..3"
            )
            self.tile_rect(
                x0, x1, 2, -6, 5, 1, COLOR_ORANGE, sid,
                prefer_x_axis=False, stagger_shift=0, notes=f"{foot_name} Orange midsole y=2..3"
            )
            # Rear ankle hard-stop cradle ledge at z = -4, x in [x0+1, x1-1) (y = 3..5)
            self.add("54200", COLOR_ORANGE, x0 + 1, 3, -4, 0, sid, f"{foot_name} rear ankle cradle left slope stop")
            self.add("3070b", COLOR_ORANGE, x0 + 2, 3, -4, 0, sid, f"{foot_name} rear ankle cradle center tile stop")
            self.add("54200", COLOR_ORANGE, x0 + 3, 3, -4, 0, sid, f"{foot_name} rear ankle cradle right slope stop")
            # Front ankle hard-stop cradle ledge at z = 0, x in [x0+1, x1-1) (y = 3..5) cradling +24 deg shin!
            self.add("3623", COLOR_ORANGE, x0 + 1, 3, 0, 90, sid, f"{foot_name} front ankle cradle base plate y=3..4")
            self.add("3069b", COLOR_ORANGE, x0 + 1, 4, 0, 90, sid, f"{foot_name} front ankle cradle smooth stop tile left y=4..5")
            self.add("3070b", COLOR_ORANGE, x0 + 3, 4, 0, 0, sid, f"{foot_name} front ankle cradle smooth stop tile right y=4..5")
            # local_y = 3..5: Front rounded toe cap at z in [3, 5) using Orange curved slopes
            self.add("15068", COLOR_ORANGE, x0, 3, 3, 0, sid, f"{foot_name} outer toe curved slope")
            self.add("11477", COLOR_ORANGE, x0 + 2, 3, 3, 0, sid, f"{foot_name} center toe curved slope")
            self.add("15068", COLOR_ORANGE, x0 + 3, 3, 3, 0, sid, f"{foot_name} inner toe curved slope")
            # Smooth tiled Orange upper toe deck at z in [1, 3) (local_y = 3..4)
            self.tile_rect(
                x0, x1, 3, 1, 3, 1, COLOR_ORANGE, sid,
                prefer_x_axis=True, use_tiles=True, notes=f"{foot_name} smooth Orange toe deck y=3..4"
            )
            # Rear heel bevel tile at z in [-6, -4) (local_y = 3..4)
            self.tile_rect(
                x0, x1, 3, -6, -4, 1, COLOR_ORANGE, sid,
                prefer_x_axis=True, use_tiles=True, notes=f"{foot_name} heel bevel tile y=3..4"
            )
            # Outer & inner ankle cheek bracket foundations at x=x0 and x=x1-1, z in [-4, 1) (local_y = 3..8)
            for cheek_side, cx in [("outer", x0), ("inner", x1 - 1)]:
                self.add("3710", COLOR_ORANGE, cx, 3, -4, 0, sid, f"{foot_name} {cheek_side} cheek foundation y=3..4")
                self.add("3070b", COLOR_ORANGE, cx, 3, 0, 0, sid, f"{foot_name} {cheek_side} instep trim tile y=3..4")
                self.add("3710", COLOR_ORANGE, cx, 4, -4, 0, sid, f"{foot_name} {cheek_side} cheek base y=4..5")
                # local_y = 5..8: Coaxial 3700 Technic Brick 1x2 with Hole at z in [-3, -1) (Ankle Pin Hole at y=6.5, z=-2.0)
                self.add("54200", COLOR_ORANGE, cx, 5, -4, 0, sid, f"{foot_name} {cheek_side} cheek rear slope")
                self.add("3700", COLOR_ORANGE, cx, 5, -3, 0, sid, f"{foot_name} {cheek_side} coaxial ankle Technic bracket")
                self.add("54200", COLOR_ORANGE, cx, 5, -1, 0, sid, f"{foot_name} {cheek_side} cheek front slope")

    # ------------------------------------------------------------------
    # SA-02: Slanted Lower Shin Servos & Angled Grey Knee Linkages (local_y = 0..16, pitch = +24.0 deg)
    # ------------------------------------------------------------------
    def build_sa02_shins_and_knees(self) -> None:
        sid = 2
        for leg_name, is_left in [("Left Slanted Shin", True), ("Right Slanted Shin", False)]:
            x0, x1 = (-6, -3) if is_left else (3, 6)
            kx0, kx1 = (-5, -3) if is_left else (3, 5)
            outer_col = -6 if is_left else 5

            # local_y = 0..3: Coaxial Ankle Pin Hub restricted to z in [-3, -1)
            self.add("3700", COLOR_DARK_BLUISH_GRAY, x0, 0, -3, 0, sid, f"{leg_name} left coaxial ankle Technic brick")
            self.add("3004", COLOR_BLACK, x0 + 1, 0, -3, 0, sid, f"{leg_name} center ankle hub brick")
            self.add("3700", COLOR_DARK_BLUISH_GRAY, x1 - 1, 0, -3, 0, sid, f"{leg_name} right coaxial ankle Technic brick")
            # Two horizontal 2780 ankle shear pins centered on the X-seams with SA-01's ankle cheeks (x=x0 and x=x1)
            self.add(
                "2780", COLOR_BLACK, x0, 1, -3, 0, sid,
                notes=f"{leg_name} left coaxial horizontal ankle pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=-0.5,
                pin_z_offset_studs=0.5,
            )
            self.add(
                "2780", COLOR_BLACK, x1 - 1, 1, -3, 0, sid,
                notes=f"{leg_name} right coaxial horizontal ankle pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=0.5,
                pin_z_offset_studs=0.5,
            )

            # local_y = 3..4: Z-oriented Black cantilever plates expanding z from [-3, -1) to [-4, 0)
            self.tile_rect(
                x0, x1, 3, -4, 0, 1, COLOR_BLACK, sid,
                prefer_x_axis=False, stagger_shift=0, notes=f"{leg_name} lower servo Z-cantilever plate y=3..4"
            )
            # local_y = 4..5: X-oriented Black locking plate across x in [x0, x1), z in [-4, 0)
            self.tile_rect(
                x0, x1, 4, -4, 0, 1, COLOR_BLACK, sid,
                prefer_x_axis=True, stagger_shift=1, notes=f"{leg_name} lower servo tie plate y=4..5"
            )
            # local_y = 5..8: Dual-Pin Triangulated Black Upper Servo Housing with 3701 1x4 Technic Bricks & secondary 2780 locking pin!
            for sx_col in range(x0, x1):
                self.add("3701", COLOR_BLACK, sx_col, 5, -4, 0, sid, f"{leg_name} triangulated 1x4 Technic strut brick x={sx_col}")
            self.add(
                "2780", COLOR_BLACK, x0 if is_left else (x0 + 1), 6, -3, 0, sid,
                notes=f"{leg_name} mid-shin secondary triangulated horizontal locking pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=0.5,
                pin_z_offset_studs=0.5,
            )
            # local_y = 8..9: Front servo grille tile at z in [-1, 0) + Dark Bluish Gray transition plate at z in [-4, -1)
            self.add("2412b", COLOR_DARK_BLUISH_GRAY, x0, 8, -1, 90, sid, f"{leg_name} front servo grille")
            self.add("3070b", COLOR_DARK_BLUISH_GRAY, x0 + 2, 8, -1, 0, sid, f"{leg_name} front servo trim tile")
            self.tile_rect(
                x0, x1, 8, -4, -1, 1, COLOR_DARK_BLUISH_GRAY, sid,
                prefer_x_axis=True, stagger_shift=1, notes=f"{leg_name} linkage base plate y=8..9"
            )
            # local_y = 9..10: Cap outer column (x=-6 Left / x=5 Right) with smooth tiles under SA-03's outer cheek
            self.add("2412b", COLOR_LIGHT_BLUISH_GRAY, outer_col, 9, -3, 0, sid, f"{leg_name} outer step-down grille tile y=9..10")
            self.add("3070b", COLOR_LIGHT_BLUISH_GRAY, outer_col, 9, -4, 0, sid, f"{leg_name} outer step-down rear tile y=9..10")
            self.tile_rect(
                kx0, kx1, 9, -4, -1, 1, COLOR_LIGHT_BLUISH_GRAY, sid,
                prefer_x_axis=False, stagger_shift=0, notes=f"{leg_name} knee tongue base plate y=9..10"
            )
            # local_y = 10..12: 2-stud Knee Linkage Tongue on kx0..kx1 (x in [-5,-3) Left, x in [3,5) Right), z in [-4, -1)
            self.tile_rect(
                kx0, kx1, 10, -4, -1, 1, COLOR_DARK_BLUISH_GRAY, sid,
                prefer_x_axis=True, stagger_shift=1, notes=f"{leg_name} knee tongue mid plate y=10..11"
            )
            self.tile_rect(
                kx0, kx1, 11, -4, -1, 1, COLOR_LIGHT_BLUISH_GRAY, sid,
                prefer_x_axis=False, stagger_shift=0, notes=f"{leg_name} knee tongue upper plate y=11..12"
            )
            # local_y = 12..14: Rear knee hard-stop cradle slope (54200) at z in [-4, -3) + knee clevis seat at z in [-3, -1)
            self.add("54200", COLOR_DARK_BLUISH_GRAY, kx0, 12, -4, 0, sid, f"{leg_name} rear knee cradle outer slope stop")
            self.add("54200", COLOR_DARK_BLUISH_GRAY, kx0 + 1, 12, -4, 0, sid, f"{leg_name} rear knee cradle inner slope stop")
            self.add("3022", COLOR_DARK_BLUISH_GRAY, kx0, 12, -3, 0, sid, f"{leg_name} upper knee seat y=12..13")
            # local_y = 13..16: Coaxial Upper Knee Pivot Block on kx0..kx1, z in [-3, -1) (Knee Pin Hole at local_y = 14.5, local_z = -2.0)
            self.add("3700", COLOR_DARK_BLUISH_GRAY, kx0, 13, -3, 0, sid, f"{leg_name} outer coaxial knee Technic brick")
            self.add("3700", COLOR_DARK_BLUISH_GRAY, kx0 + 1, 13, -3, 0, sid, f"{leg_name} inner coaxial knee Technic brick")
            # Outer & Inner Coaxial Horizontal 2780 Knee Shear Pins at X = ±40.0 mm and X = ±24.0 mm bridging SA-02 and SA-03
            self.add(
                "2780", COLOR_BLACK, kx0 if is_left else (kx0 + 1), 14, -3, 0, sid,
                notes=f"{leg_name} outer coaxial horizontal knee Technic shear pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=-0.5 if is_left else 0.5,
                pin_z_offset_studs=0.5,
            )
            self.add(
                "2780", COLOR_BLACK, (kx0 + 1) if is_left else kx0, 14, -3, 0, sid,
                notes=f"{leg_name} inner coaxial horizontal knee Technic shear pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=0.5 if is_left else -0.5,
                pin_z_offset_studs=0.5,
            )

    # ------------------------------------------------------------------
    # SA-03: Slanted Upper Thigh Servos & Diagonal White Outer Thigh Armor Shields (local_y = 0..16, pitch = -26.0 deg)
    # ------------------------------------------------------------------
    def build_sa03_thighs_and_white_shields(self) -> None:
        sid = 3
        for side_name, is_left in [("Left Thigh & Diagonal White Shield", True), ("Right Thigh & Diagonal White Shield", False)]:
            # True Double-Shear Clevis Forks at BOTH Knee (local_y = 0..6) and Hip (local_y = 6..15)!
            # Outer Cheek at clevis_outer_col (x = -6 Left / x = 5 Right) + Inner Cheek at clevis_inner_col (x = -3 Left / x = 2 Right),
            # bracketing the 2-stud Knee Tongue (SA-02) and 2-stud Hip Tongue (SA-04) at x in [-5, -3) Left / [3, 5) Right!
            sx0, sx1 = (-8, -6) if is_left else (6, 8)
            lx0, lx1 = (-8, -5) if is_left else (5, 8)
            clevis_outer_col = -6 if is_left else 5
            clevis_inner_col = -3 if is_left else 2

            # local_y = 0..3: Double-Shear Lower Knee Clevis Fork bracketing SA-02's 2-stud knee tongue ([-5,-3) Left / [3,5) Right)
            # 1) Outer Knee Cheek on lx0..lx1 (x in [-8, -5) Left, x in [5, 8) Right), z in [-3, 0)
            self.add("3700", COLOR_DARK_BLUISH_GRAY, clevis_outer_col, 0, -3, 0, sid, f"{side_name} outer coaxial knee Technic brick")
            self.add("3700", COLOR_WHITE, sx0, 0, -3, 0, sid, f"{side_name} outer shield lower Technic brick")
            self.add("3700", COLOR_WHITE, sx0 + 1, 0, -3, 0, sid, f"{side_name} mid shield lower Technic brick")
            self.add(
                "2780", COLOR_BLACK, sx0, 1, -3, 0, sid,
                notes=f"{side_name} outer shield lower horizontal Technic pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=0.5,
                pin_z_offset_studs=0.5,
            )
            self.tile_rect(
                lx0, lx1, 0, -1, 0, 3, COLOR_WHITE, sid,
                prefer_x_axis=True, notes=f"{side_name} lower front shield edge y=0..3"
            )
            # 2) Inner Knee Cheek on clevis_inner_col (x = -3 Left, x = 2 Right), z in [-3, -1)
            self.add("3700", COLOR_DARK_BLUISH_GRAY, clevis_inner_col, 0, -3, 0, sid, f"{side_name} inner coaxial knee Technic brick")

            # local_y = 3..5: Expand Z to [-4, 1) across lx0..lx1 + stack inner clevis column at clevis_inner_col (z in [-3, -1))
            self.tile_rect(
                lx0, lx1, 3, -4, 1, 1, COLOR_WHITE, sid,
                prefer_x_axis=False, stagger_shift=0, notes=f"{side_name} lower thigh Z-expansion plate y=3..4"
            )
            self.add("3023", COLOR_DARK_BLUISH_GRAY, clevis_inner_col, 3, -3, 0, sid, f"{side_name} inner knee cheek plate y=3..4")
            self.tile_rect(
                lx0, lx1, 4, -4, 1, 1, COLOR_DARK_BLUISH_GRAY, sid,
                prefer_x_axis=True, stagger_shift=1, notes=f"{side_name} lower thigh lock plate y=4..5"
            )
            self.add("3023", COLOR_DARK_BLUISH_GRAY, clevis_inner_col, 4, -3, 0, sid, f"{side_name} inner knee cheek plate y=4..5")

            # local_y = 5..8:
            # 1) Double-Shear Clevis Cross-Bridge at y = 5..6 across x in [-6, -2) Left / [2, 6) Right, z in [-3, -1)
            k_bridge_x = -6 if is_left else 2
            self.add("3710", COLOR_DARK_BLUISH_GRAY, k_bridge_x, 5, -3, 90, sid, f"{side_name} clevis fork rear bridge plate y=5..6")
            self.add("2431", COLOR_DARK_BLUISH_GRAY, k_bridge_x, 5, -2, 90, sid, f"{side_name} clevis fork front smooth bridge tile y=5..6")
            # Cap 2-stud clevis pocket floor (x in [-5, -3) Left / [3, 5) Right) at y = 6..7, z = -3 with smooth 3069b tile
            self.add("3069b", COLOR_DARK_BLUISH_GRAY, -5 if is_left else 3, 6, -3, 90, sid, f"{side_name} clevis bridge smooth cradle stop tile y=6..7")
            # Continue Inner Clevis Column upward at clevis_inner_col (x = -3 Left / x = 2 Right), y = 6..9, z in [-3, -1)
            self.add("3004", COLOR_DARK_BLUISH_GRAY, clevis_inner_col, 6, -3, 0, sid, f"{side_name} inner clevis vertical column brick y=6..9")

            # 2) Dual-Pin Triangulated White Outer Thigh Shield (sx0..sx1) with 3701 1x4 Technic bricks & secondary 2780 locking pin!
            self.add("3701", COLOR_WHITE, sx0, 5, -4, 0, sid, f"{side_name} outer shield mid 1x4 Technic brick")
            self.add("3701", COLOR_WHITE, sx0 + 1, 5, -4, 0, sid, f"{side_name} inner shield mid 1x4 Technic brick")
            self.add(
                "2780", COLOR_BLACK, sx0, 6, -3, 0, sid,
                notes=f"{side_name} mid-shield secondary triangulated horizontal Technic pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=0.5,
                pin_z_offset_studs=0.5,
            )
            self.add("3004", COLOR_WHITE, sx0, 5, 0, 90, sid, f"{side_name} White shield mid front brick y=5..8")

            # 3) Black Thigh Servo Column at clevis_outer_col (x = -6 Left / x = 5 Right) around the y = 5..6 bridge
            self.add("3005", COLOR_BLACK, clevis_outer_col, 5, -4, 0, sid, f"{side_name} Black thigh servo rear column y=5..8")
            self.add("3004", COLOR_BLACK, clevis_outer_col, 5, -1, 0, sid, f"{side_name} Black thigh servo front column y=5..8")
            self.add("3024", COLOR_BLACK, clevis_outer_col, 6, -3, 0, sid, f"{side_name} Black thigh servo mid plate y=6..7")
            self.add("3024", COLOR_BLACK, clevis_outer_col, 7, -3, 0, sid, f"{side_name} Black thigh servo upper plate y=7..8")

            # local_y = 8..11: Reinforcing plate stack on outer thigh (lx0..lx1) + Inner Clevis Column (clevis_inner_col)
            self.tile_rect(
                lx0, lx1, 8, -4, 1, 1, COLOR_DARK_BLUISH_GRAY, sid,
                prefer_x_axis=True, stagger_shift=0, notes=f"{side_name} mid thigh tie plate y=8..9"
            )
            self.tile_rect(
                lx0, lx1, 9, -4, 1, 1, COLOR_DARK_BLUISH_GRAY, sid,
                prefer_x_axis=False, stagger_shift=1, notes=f"{side_name} upper thigh tie plate y=9..10"
            )
            self.add("3023", COLOR_DARK_BLUISH_GRAY, clevis_inner_col, 9, -3, 0, sid, f"{side_name} inner hip cheek lower seat plate y=9..10")
            self.add("3023", COLOR_DARK_BLUISH_GRAY, clevis_inner_col, 10, -3, 0, sid, f"{side_name} inner hip cheek upper seat plate y=10..11")
            self.tile_rect(
                sx0, sx1, 10, -4, 1, 1, COLOR_WHITE, sid,
                prefer_x_axis=False, stagger_shift=1, notes=f"{side_name} White shield upper seat plate y=10..11"
            )
            self.tile_rect(
                clevis_outer_col, clevis_outer_col + 1, 10, -4, 1, 1, COLOR_BLACK, sid,
                prefer_x_axis=False, stagger_shift=1, notes=f"{side_name} Black servo upper seat plate y=10..11"
            )

            # local_y = 11..14: Double-Shear Upper Hip Coaxial Pin Joint Layer (Hip Pin Hole at local_y = 12.5, local_z = -2.0)
            # 1) Outer White Thigh Shield upper pin block (sx0..sx1)
            self.add("3700", COLOR_WHITE, sx0, 11, -3, 0, sid, f"{side_name} shield upper outer Technic brick")
            self.add("3700", COLOR_WHITE, sx0 + 1, 11, -3, 0, sid, f"{side_name} shield upper inner Technic brick")
            self.add(
                "2780", COLOR_BLACK, sx0, 12, -3, 0, sid,
                notes=f"{side_name} shield upper horizontal Technic pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=0.5,
                pin_z_offset_studs=0.5,
            )
            self.add("3004", COLOR_WHITE, sx0, 11, -4, 90, sid, f"{side_name} shield upper rear brick")
            self.add("3003", COLOR_WHITE, sx0, 11, -1, 0, sid, f"{side_name} shield upper front brick")

            # 2) Outer Hip Clevis Cheek at clevis_outer_col (x = -6 Left / x = 5 Right), z in [-3, -1)
            self.add("3700", COLOR_DARK_BLUISH_GRAY, clevis_outer_col, 11, -3, 0, sid, f"{side_name} outer coaxial hip clevis Technic brick")
            self.add("3005", COLOR_BLACK, clevis_outer_col, 11, -4, 0, sid, f"{side_name} servo upper rear brick")
            self.add("3004", COLOR_BLACK, clevis_outer_col, 11, -1, 0, sid, f"{side_name} servo upper front brick")

            # 3) Inner Hip Clevis Cheek at clevis_inner_col (x = -3 Left / x = 2 Right), z in [-3, -1)
            self.add("3700", COLOR_DARK_BLUISH_GRAY, clevis_inner_col, 11, -3, 0, sid, f"{side_name} inner coaxial hip clevis Technic brick")
            self.add("3069b", COLOR_DARK_BLUISH_GRAY, clevis_inner_col, 14, -3, 0, sid, f"{side_name} inner hip clevis smooth cap tile y=14..15")

            # local_y = 14..16: Curved White armor slopes & smooth tiles crowning the diagonal White Outer Thigh Shield
            self.add("15068", COLOR_WHITE, sx0, 14, -4, 0, sid, f"{side_name} shield top rear curved slope")
            self.add("15068", COLOR_WHITE, sx0, 14, -1, 0, sid, f"{side_name} shield top front curved slope")
            self.add("3069b", COLOR_WHITE, sx0, 14, -2, 90, sid, f"{side_name} shield top center smooth tile")
            self.add("2431", COLOR_DARK_BLUISH_GRAY, clevis_outer_col, 14, -4, 0, sid, f"{side_name} outer hip cheek top smooth cap tile")
            self.add("3070b", COLOR_DARK_BLUISH_GRAY, clevis_outer_col, 14, 0, 0, sid, f"{side_name} outer hip cheek front smooth cap tile")

    # ------------------------------------------------------------------
    # SA-04: Level Exposed Black Hip Servo Cluster & Cylindrical Grey Hip-Roll Hubs (local_y = 0..11, pitch = 0.0 deg)
    # ------------------------------------------------------------------
    def build_sa04_hip_servo_and_roll_hubs(self) -> None:
        sid = 4
        # Keep SA-04's first step (local_y = 0..1, Step 40) strictly within local_x in [-3, 3) (6 studs = 48.0 mm wide)
        # so there is a full 1-stud (8.0 mm) horizontal air gap between SA-04 and the tilted SA-03 thighs at Step 40!
        # Leave x = -3 (Left) and x = 2 (Right) at z in [-4, 0) open below y = 8 for SA-03's Inner Hip Clevis Cheeks!
        # local_y = 0..1: Black lower hip servo base plate
        self.tile_rect(
            -3, 3, 0, 0, 3, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=0, notes="Hip servo cluster front lower base y=0..1"
        )
        self.tile_rect(
            -2, 2, 0, -4, 0, 1, COLOR_BLACK, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Hip servo cluster center spine lower base y=0..1"
        )
        # local_y = 1..2: Cantilever along front z in [0, 2) out to x in [-5, -3) (Left) and x in [3, 5) (Right)
        self.add("3020", COLOR_BLACK, -5, 1, 0, 90, sid, "Left hip front X-cantilever plate y=1..2")
        self.add("3023", COLOR_BLACK, -1, 1, 0, 0, sid, "Center-left hip front tie plate y=1..2")
        self.add("3023", COLOR_BLACK, 0, 1, 0, 0, sid, "Center-right hip front tie plate y=1..2")
        self.add("3020", COLOR_BLACK, 1, 1, 0, 90, sid, "Right hip front X-cantilever plate y=1..2")
        self.tile_rect(
            -3, 3, 1, 2, 3, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=1, notes="Hip servo front lip plate y=1..2"
        )
        self.tile_rect(
            -2, 2, 1, -4, 0, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=1, notes="Hip servo center spine lower plate y=1..2"
        )

        # local_y = 2..3: Support Left (-5..-3), Center (-2..2), and Right (3..5) coaxial hip bosses on z in [-3, 1)
        # while keeping x = -3 and x = 2 open on z in [-4, 0) for SA-03's Inner Hip Clevis Cheeks!
        self.add("3020", COLOR_DARK_BLUISH_GRAY, -5, 2, -3, 0, sid, "Left hip boss Z-bridge support plate y=2..3")
        self.add("3020", COLOR_DARK_BLUISH_GRAY, 3, 2, -3, 0, sid, "Right hip boss Z-bridge support plate y=2..3")
        self.add("3024", COLOR_DARK_BLUISH_GRAY, -3, 2, 0, 0, sid, "Left inner clevis front tie plate y=2..3")
        self.add("3024", COLOR_DARK_BLUISH_GRAY, 2, 2, 0, 0, sid, "Right inner clevis front tie plate y=2..3")
        self.tile_rect(
            -2, 2, 2, -4, 1, 1, COLOR_DARK_BLUISH_GRAY, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Center pelvic seat plate y=2..3"
        )
        self.tile_rect(
            -3, 3, 2, 1, 3, 1, COLOR_DARK_BLUISH_GRAY, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Hip roll-hub front support plate y=2..3"
        )

        # local_y = 3..6: Double-Shear Coaxial Hip Pin Joint Layer (Hip Pin Hole at local_y = 4.5, local_z = -2.0)
        # SA-04's Left Hip Boss (x=-5,-4) is bracketed by SA-03's Outer Cheek (x=-6, pin at X=-40.0 mm) & Inner Cheek (x=-3, pin at X=-24.0 mm)!
        # SA-04's Right Hip Boss (x=3,4) is bracketed by SA-03's Inner Cheek (x=2, pin at X=+24.0 mm) & Outer Cheek (x=5, pin at X=+40.0 mm)!
        for side_label, hx_outer, hx_inner, outer_pin_x, outer_off, inner_pin_x, inner_off in [
            ("Left", -5, -4, -5, -0.5, -4, 0.5),
            ("Right", 4, 3, 4, 0.5, 3, -0.5),
        ]:
            self.add("3700", COLOR_DARK_BLUISH_GRAY, hx_outer, 3, -3, 0, sid, f"{side_label} hip coaxial outer Technic brick")
            self.add("3700", COLOR_DARK_BLUISH_GRAY, hx_inner, 3, -3, 0, sid, f"{side_label} hip coaxial inner Technic brick")
            self.add(
                "2780", COLOR_BLACK, outer_pin_x, 4, -3, 0, sid,
                notes=f"{side_label} hip outer coaxial horizontal Technic shear pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=outer_off,
                pin_z_offset_studs=0.5,
            )
            self.add(
                "2780", COLOR_BLACK, inner_pin_x, 4, -3, 0, sid,
                notes=f"{side_label} hip inner coaxial horizontal Technic shear pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=inner_off,
                pin_z_offset_studs=0.5,
            )
            # Smooth hard-stop cap tiles on front (y=3..4, z in [-1,1)) and top (y=6..7, z in [-3,-1)) of the 2-stud hip boss
            self.add("3068b", COLOR_DARK_BLUISH_GRAY, min(hx_outer, hx_inner), 3, -1, 0, sid, f"{side_label} hip boss front smooth cradle tile y=3..4")
            self.add("3068b", COLOR_DARK_BLUISH_GRAY, min(hx_outer, hx_inner), 6, -3, 0, sid, f"{side_label} hip boss top smooth cap tile y=6..7")

        # Center pelvic coaxial 3700 Technic core at x = -1, 0, z in [-3, -1) + center 2780 pin
        self.add("3700", COLOR_DARK_BLUISH_GRAY, -1, 3, -3, 0, sid, "Center pelvic coaxial left Technic brick")
        self.add("3700", COLOR_DARK_BLUISH_GRAY, 0, 3, -3, 0, sid, "Center pelvic coaxial right Technic brick")
        self.add(
            "2780", COLOR_BLACK, -1, 4, -3, 0, sid,
            notes="Center pelvic coaxial horizontal Technic pin",
            pin_orientation="horizontal_x",
            pin_x_offset_studs=0.5,
            pin_z_offset_studs=0.5,
        )
        self.add("3004", COLOR_BLACK, -2, 3, -3, 0, sid, "Center-left pelvic core brick y=3..6")
        self.add("3004", COLOR_BLACK, 1, 3, -3, 0, sid, "Center-right pelvic core brick y=3..6")

        # Fill remaining Black hip servo body at local_y = 3..6 and front Light Bluish Gray roll-hub housings at z in [1, 3)
        self.tile_rect(
            -2, 2, 3, -4, -3, 3, COLOR_BLACK, sid,
            prefer_x_axis=True, notes="Center hip servo rear wall y=3..6"
        )
        self.tile_rect(
            -2, 2, 3, -1, 0, 3, COLOR_BLACK, sid,
            prefer_x_axis=True, notes="Center hip servo mid wall y=3..6"
        )
        self.tile_rect(
            -3, 3, 3, 0, 1, 3, COLOR_BLACK, sid,
            prefer_x_axis=True, notes="Hip servo front wall y=3..6"
        )
        self.tile_rect(
            -3, -1, 3, 1, 3, 3, COLOR_LIGHT_BLUISH_GRAY, sid,
            prefer_x_axis=True, notes="Left front hip-roll hub housing y=3..6"
        )
        self.tile_rect(
            1, 3, 3, 1, 3, 3, COLOR_LIGHT_BLUISH_GRAY, sid,
            prefer_x_axis=True, notes="Right front hip-roll hub housing y=3..6"
        )
        self.tile_rect(
            -1, 1, 3, 1, 2, 3, COLOR_DARK_BLUISH_GRAY, sid,
            prefer_x_axis=True, notes="Center pelvic bridge strut y=3..6"
        )

        # local_y = 6..8: Keep x=-3 and x=2 at z in [-4, 0) open up to y=8 above SA-03's inner hip cheek, and build Cylindrical Grey Hip-Roll Hubs!
        for hub_side, rx0 in [("Left", -3), ("Right", 1)]:
            self.add("4032", COLOR_LIGHT_BLUISH_GRAY, rx0, 6, 1, 0, sid, f"{hub_side} cylindrical hip-roll hub base")
            self.add("4032", COLOR_DARK_BLUISH_GRAY, rx0, 7, 1, 0, sid, f"{hub_side} cylindrical hip-roll hub ring")
            self.add("3068b", COLOR_LIGHT_BLUISH_GRAY, rx0, 8, 1, 0, sid, f"{hub_side} cylindrical hip-roll hub cap")
        self.add("3004", COLOR_DARK_BLUISH_GRAY, -1, 6, 1, 90, sid, "Center roll hub divider y=6..9")
        for py_hip in (6, 7):
            self.tile_rect(
                -2, 2, py_hip, -4, 0, 1, COLOR_BLACK, sid,
                prefer_x_axis=(py_hip % 2 == 0), stagger_shift=py_hip, notes=f"Center pelvic spine plate y={py_hip}"
            )
            self.tile_rect(
                -3, 3, py_hip, 0, 1, 1, COLOR_BLACK, sid,
                prefer_x_axis=(py_hip % 2 == 1), stagger_shift=py_hip, notes=f"Upper hip servo front wall y={py_hip}"
            )

        # local_y = 8..11: Bridge across full x in [-3, 3), z in [-4, 1) above SA-03's inner hip cheeks!
        self.tile_rect(
            -3, 3, 8, -4, 1, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=0, notes="Upper hip clevis locking bridge plate y=8..9"
        )
        self.add("54200", COLOR_LIGHT_BLUISH_GRAY, -1, 9, 1, 0, sid, "Left roll hub top slope")
        self.add("54200", COLOR_LIGHT_BLUISH_GRAY, 0, 9, 1, 0, sid, "Right roll hub top slope")
        self.tile_rect(
            -3, 3, 9, -4, 1, 1, COLOR_DARK_BLUISH_GRAY, sid,
            prefer_x_axis=False, stagger_shift=1, notes="Pelvic bridge plate y=9..10"
        )
        self.tile_rect(
            -3, 3, 10, -4, 1, 1, COLOR_DARK_BLUISH_GRAY, sid,
            prefer_x_axis=True, stagger_shift=0, notes="Pelvic top mounting deck y=10..11"
        )

    # ------------------------------------------------------------------
    # SA-05: Level Compact Rounded White Torso Pod & Flush Rear Black Battery Column (local_y = 0..11, pitch = 0.0 deg)
    # ------------------------------------------------------------------
    def build_sa05_torso_and_battery_spine(self) -> None:
        sid = 5
        # Stacks directly on SA-04's top deck (x in [-3, 3) at y=0..1, expanding to x in [-5, 5) at y>=1 well above SA-03!)
        # local_y = 0..2: Rounded White torso base (z in [-2, 3)) + Flush Rear Black Battery Column (z in [-4, -2))
        self.tile_rect(
            -3, 3, 0, -2, 3, 1, COLOR_WHITE, sid,
            prefer_x_axis=False, stagger_shift=0, notes="White torso pod lower base y=0..1"
        )
        self.tile_rect(
            -3, 3, 0, -4, -2, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=0, notes="Rear Black battery column base y=0..1"
        )
        self.add("3020", COLOR_BLACK, -2, 1, -3, 0, sid, "Torso-to-battery left-center Z-bridge plate y=1..2")
        self.add("3020", COLOR_BLACK, 0, 1, -3, 0, sid, "Torso-to-battery right-center Z-bridge plate y=1..2")
        self.tile_rect(
            -5, 5, 1, -2, 3, 1, COLOR_WHITE, sid,
            prefer_x_axis=True, stagger_shift=0, notes="White torso pod tie plate y=1..2"
        )
        self.tile_rect(
            -4, 4, 1, -4, -2, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=1, notes="Rear Black battery tie plate y=1..2"
        )

        # local_y = 2..5: Main White torso shell + Rear Black battery pack
        self.tile_rect(
            -5, 5, 2, -2, 3, 3, COLOR_WHITE, sid,
            prefer_x_axis=True, stagger_shift=0, notes="White torso pod body y=2..5"
        )
        self.tile_rect(
            -4, 4, 2, -4, -2, 3, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=0, notes="Rear Black battery body y=2..5"
        )

        # local_y = 5..9: Central 4x4 neck recess floor at x in [-2, 2), z in [-1, 1)
        # + Front (z=1, y=5..9) & Rear (z=-2, y=5..7) Flush Hard-Stop Neck Cradle Ledges for SA-06 (+19.725 deg)!
        # + Trans-Light Blue status LEDs at z=2!
        self.add("3070b", COLOR_TRANS_LIGHT_BLUE, -1, 5, 2, 0, sid, "Torso front telemetry indicator LED Left")
        self.add("3070b", COLOR_TRANS_LIGHT_BLUE, 0, 5, 2, 0, sid, "Torso front telemetry indicator LED Right")
        self.add("54200", COLOR_WHITE, -2, 5, 2, 0, sid, "Torso front neck cradle left slope trim")
        self.add("54200", COLOR_WHITE, 1, 5, 2, 0, sid, "Torso front neck cradle right slope trim")
        # Smooth neck slot floor at z in [-1, 1), y = 5..6
        self.tile_rect(
            -2, 2, 5, -1, 1, 1, COLOR_DARK_BLUISH_GRAY, sid,
            prefer_x_axis=True, use_tiles=True, notes="Recessed 4x2 neck slot smooth floor y=5..6"
        )
        # Rear neck hard-stop cradle ledge at z in [-2, -1), x in [-2, 2) (y = 5..7)
        self.add("3710", COLOR_DARK_BLUISH_GRAY, -2, 5, -2, 90, sid, "Rear neck cradle base plate y=5..6")
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, -2, 6, -2, 90, sid, "Rear neck cradle smooth left stop tile y=6..7")
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, 0, 6, -2, 90, sid, "Rear neck cradle smooth right stop tile y=6..7")
        # Front neck hard-stop cradle ledge at z in [1, 2), x in [-2, 2) (y = 5..9) directly supporting +19.725 deg neck!
        self.add("3710", COLOR_DARK_BLUISH_GRAY, -2, 5, 1, 90, sid, "Front neck cradle base plate y=5..6")
        self.add("3710", COLOR_DARK_BLUISH_GRAY, -2, 6, 1, 90, sid, "Front neck cradle mid plate y=6..7")
        self.add("3710", COLOR_DARK_BLUISH_GRAY, -2, 7, 1, 90, sid, "Front neck cradle upper plate y=7..8")
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, -2, 8, 1, 90, sid, "Front neck cradle smooth left stop tile y=8..9")
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, 0, 8, 1, 90, sid, "Front neck cradle smooth right stop tile y=8..9")
        self.tile_rect(
            -5, -2, 5, -2, 3, 1, COLOR_WHITE, sid,
            prefer_x_axis=False, stagger_shift=1, notes="Left White torso lobe plate y=5..6"
        )
        self.tile_rect(
            2, 5, 5, -2, 3, 1, COLOR_WHITE, sid,
            prefer_x_axis=False, stagger_shift=1, notes="Right White torso lobe plate y=5..6"
        )
        self.tile_rect(
            -4, 4, 5, -4, -2, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=1, notes="Rear Black battery plate y=5..6"
        )

        # local_y = 6..8: Left (-5..-2) & Right (2..5) White torso saddle walls + Rear Black battery column (-4..-2),
        # leaving central neck slot x in [-2, 2), z in [-2, 3) open above y=6 for slanted neck stalk!
        for lobe_side, lx0, lx1 in [("Left", -5, -2), ("Right", 2, 5)]:
            self.tile_rect(
                lx0, lx1, 6, -2, 3, 1, COLOR_WHITE, sid,
                prefer_x_axis=True, stagger_shift=0, notes=f"{lobe_side} torso saddle wall y=6..7"
            )
            self.tile_rect(
                lx0, lx1, 7, -2, 3, 1, COLOR_WHITE, sid,
                prefer_x_axis=False, stagger_shift=1, notes=f"{lobe_side} torso saddle wall y=7..8"
            )
        self.tile_rect(
            -4, 4, 6, -4, -2, 1, COLOR_BLACK, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Rear battery wall y=6..7"
        )
        self.tile_rect(
            -4, 4, 7, -4, -2, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=1, notes="Rear battery wall y=7..8"
        )

        # local_y = 8..11: Coaxial Lower Neck Pin Joint Layer (Lower Neck Pin Hole at local_y = 9.5, local_z = 0.0)
        # Pins centered at X = -16.0 mm (bridging SA-05 x=-3 & SA-06 x=-2) and X = +16.0 mm (bridging SA-06 x=1 & SA-05 x=2)
        for neck_side, hx_inner, hx_mid, pin_x, pin_x_off, outer_x in [
            ("Left", -3, -4, -3, 0.5, -5),
            ("Right", 2, 3, 2, -0.5, 4),
        ]:
            self.add("3700", COLOR_WHITE, hx_inner, 8, -1, 0, sid, f"{neck_side} torso coaxial lower-neck inner Technic brick")
            self.add("3700", COLOR_WHITE, hx_mid, 8, -1, 0, sid, f"{neck_side} torso coaxial lower-neck mid Technic brick")
            self.add(
                "2780", COLOR_BLACK, pin_x, 9, -1, 0, sid,
                notes=f"{neck_side} torso horizontal lower-neck Technic pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=pin_x_off,
                pin_z_offset_studs=0.5,
            )
            self.add("3004", COLOR_WHITE, outer_x, 8, -1, 0, sid, f"{neck_side} torso outer shoulder brick")

        # Curved White front & rear slopes on Left (-5..-2) and Right (2..5) lobes + Rear Black battery top (z in [-4, -2))
        for lobe_side, lx0, lx1 in [("Left", -5, -2), ("Right", 2, 5)]:
            self.tile_rect(
                lx0, lx1, 8, -2, -1, 3, COLOR_WHITE, sid,
                prefer_x_axis=True, notes=f"{lobe_side} torso rear shoulder y=8..11"
            )
            self.tile_rect(
                lx0, lx1, 8, 1, 2, 1, COLOR_WHITE, sid,
                prefer_x_axis=True, notes=f"{lobe_side} torso front shoulder base y=8..9"
            )
            self.add("15068", COLOR_WHITE, lx0, 9, 1, 0, sid, f"{lobe_side} torso front curved slope outer")
            self.add("11477", COLOR_WHITE, lx0 + 2, 9, 1, 0, sid, f"{lobe_side} torso front curved slope inner")
            self.add("3069b", COLOR_WHITE, lx0, 8, 2, 90, sid, f"{lobe_side} torso front lip tile")
            self.add("3070b", COLOR_WHITE, lx0 + 2, 8, 2, 0, sid, f"{lobe_side} torso front corner tile")

        # Build rear battery y=8..10 as 2 plate layers + y=10..11 radiator grilles
        self.tile_rect(
            -4, 4, 8, -4, -2, 1, COLOR_BLACK, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Rear battery pack plate y=8..9"
        )
        self.tile_rect(
            -4, 4, 9, -4, -2, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=1, notes="Rear battery pack plate y=9..10"
        )
        for gx in range(-4, 4, 2):
            self.add("2412b", COLOR_DARK_BLUISH_GRAY, gx, 10, -4, 90, sid, "Rear battery heatsink grille rear")
            self.add("2412b", COLOR_BLACK, gx, 10, -3, 90, sid, "Rear battery heatsink grille front")

    # ------------------------------------------------------------------
    # SA-06: Slanted Slender 4x4 Multi-Servo Neck Stalk (local_y = 0..16, pitch = +19.725 deg)
    # ------------------------------------------------------------------
    def build_sa06_slender_neck_stalk(self) -> None:
        sid = 6
        # Slender 4x4 column (x in [-2, 2)) tilted forward around Lower Neck Pin so Upper Neck Pin is at exact 180.8000 mm
        # local_y = 0..3: Coaxial Lower Neck Pin Base in z in [-1, 1) (clears SA-05 rear battery wall by >6.9 mm)
        for tx in (-2, -1, 0, 1):
            self.add("3700", COLOR_LIGHT_BLUISH_GRAY, tx, 0, -1, 0, sid, f"Lower neck coaxial Technic brick x={tx}")
        self.add(
            "2780", COLOR_BLACK, 0, 1, -1, 0, sid,
            notes="Lower neck center coaxial horizontal Technic pin",
            pin_orientation="horizontal_x",
            pin_x_offset_studs=-0.5,
            pin_z_offset_studs=0.5,
        )

        # local_y = 3..4: Locking 2x4 plate across z in [-1, 1)
        self.add("3020", COLOR_DARK_BLUISH_GRAY, -2, 3, -1, 90, sid, "Neck stalk lower 2x4 locking plate y=3..4")

        # local_y = 4..5: Expand to full 4x4 neck stalk (x in [-2, 2), z in [-2, 2)) above SA-05
        self.add("3031", COLOR_DARK_BLUISH_GRAY, -2, 4, -2, 0, sid, "Neck stalk 4x4 expansion plate y=4..5")

        # local_y = 5..7: Black Mid-Neck Servo Housing (4x4)
        self.tile_rect(
            -2, 2, 5, -2, 2, 1, COLOR_BLACK, sid,
            prefer_x_axis=True, stagger_shift=0, notes="Mid neck Black servo block y=5..6"
        )
        self.tile_rect(
            -2, 2, 6, -2, 2, 1, COLOR_BLACK, sid,
            prefer_x_axis=False, stagger_shift=1, notes="Mid neck Black servo block y=6..7"
        )

        # local_y = 7..9: Light & Dark Bluish Gray mid-neck bracket plates
        self.tile_rect(
            -2, 2, 7, -2, 2, 1, COLOR_LIGHT_BLUISH_GRAY, sid,
            prefer_x_axis=False, stagger_shift=1, notes="Mid neck bracket plate y=7..8"
        )
        self.tile_rect(
            -2, 2, 8, -2, 2, 1, COLOR_DARK_BLUISH_GRAY, sid,
            prefer_x_axis=True, stagger_shift=0, notes="Mid neck bracket plate y=8..9"
        )

        # local_y = 9..12: Upper-Mid Black Servo Block
        self.tile_rect(
            -2, 2, 9, -2, 2, 3, COLOR_BLACK, sid,
            prefer_x_axis=False, stagger_shift=1, notes="Upper neck servo block y=9..12"
        )

        # local_y = 12..13: Dark Bluish Gray upper neck collar plate (smooth 1x2 tiles on z=-2 and z=1, 2x4 plate on z in [-1, 1))
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, -2, 12, -2, 90, sid, "Upper neck rear left smooth collar tile")
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, 0, 12, -2, 90, sid, "Upper neck rear right smooth collar tile")
        self.add("3020", COLOR_DARK_BLUISH_GRAY, -2, 12, -1, 90, sid, "Upper neck 2x4 support plate y=12..13")
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, -2, 12, 1, 90, sid, "Upper neck front left smooth collar tile")
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, 0, 12, 1, 90, sid, "Upper neck front right smooth collar tile")

        # local_y = 13..16: Coaxial Upper Neck Pin Clevis Cheeks at x = -2 and x = 1, z in [-1, 1)
        # with recessed smooth 2x2 tile (3068b) in center x in [-1, 1) so no center studs stick up under SA-07's bridge!
        self.add("3700", COLOR_DARK_BLUISH_GRAY, -2, 13, -1, 0, sid, "Upper neck coaxial left Technic brick x=-2")
        self.add("3068b", COLOR_DARK_BLUISH_GRAY, -1, 13, -1, 0, sid, "Upper neck center smooth saddle tile y=13..14")
        self.add("3700", COLOR_DARK_BLUISH_GRAY, 1, 13, -1, 0, sid, "Upper neck coaxial right Technic brick x=1")

    # ------------------------------------------------------------------
    # SA-07: Wide Curved White Visor Hood, Orange Base Rim & Cyclops Camera Head (local_y = 0..23, pitch = 0.0 deg)
    # ------------------------------------------------------------------
    def build_sa07_visor_head(self) -> None:
        sid = 7
        # local_y = 0..3: Under-Chin Coaxial Neck Clevis Cheeks at x in [-4, -2) and x in [2, 4), z in [0, 2)
        # Leaves central neck slot x in [-2, 2) 100% open for SA-06!
        # Hole centers are at exact local_y = 1.5 plates = 4.8000 mm -> world_y = 180.8000 mm!
        # Coaxial 2780 pins centered at X = -16.0 mm (bridging SA-07 x=-3 & SA-06 x=-2) and X = +16.0 mm (bridging SA-06 x=1 & SA-07 x=2)
        for clevis_side, hx_inner, hx_outer, pin_x, pin_x_off in [
            ("Left", -3, -4, -3, 0.5),
            ("Right", 2, 3, 2, -0.5),
        ]:
            self.add(
                "3700", COLOR_DARK_BLUISH_GRAY, hx_inner, 0, 0, 0, sid,
                notes=f"{clevis_side} under-chin coaxial inner Technic brick",
            )
            self.add(
                "3700", COLOR_DARK_BLUISH_GRAY, hx_outer, 0, 0, 0, sid,
                notes=f"{clevis_side} under-chin coaxial outer Technic brick",
            )
            self.add(
                "2780", COLOR_BLACK, pin_x, 1, 0, 0, sid,
                notes=f"{clevis_side} under-chin horizontal upper-neck Technic pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=pin_x_off,
                pin_z_offset_studs=0.5,
            )

        # local_y = 3..4 (Step 83): Cap inner under-chin 3700 bricks (x=-3 and x=2, z in [0, 2)) with smooth Grey tiles
        # (using 3069b rot=90 on z=0 to bond x=-4&-3 and x=2&3, plus 3070b on x=-3,z=1 and x=2,z=1),
        # and keep the Orange cantilever plates strictly within x in [-7, -3) (Left) and x in [3, 7) (Right), z in [1, 5)
        # (anchored on outer under-chin 3700 bricks at x=-4,z=1 and x=3,z=1), creating a full 1-stud (8.0 mm) horizontal air gap
        # between the Orange plates (|X| >= 24.0 mm) and the tilted Grey SA-06 neck (|X| <= 16.0 mm)!
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, -4, 3, 0, 90, sid, "Left under-chin clevis bonding smooth cap tile y=3..4")
        self.add("3069b", COLOR_DARK_BLUISH_GRAY, 2, 3, 0, 90, sid, "Right under-chin clevis bonding smooth cap tile y=3..4")
        self.add("3070b", COLOR_DARK_BLUISH_GRAY, -3, 3, 1, 0, sid, "Left inner under-chin clevis front smooth cap tile y=3..4")
        self.add("3070b", COLOR_DARK_BLUISH_GRAY, 2, 3, 1, 0, sid, "Right inner under-chin clevis front smooth cap tile y=3..4")
        self.add("3031", COLOR_ORANGE, -7, 3, 1, 0, sid, "Head base left 4x4 Orange cantilever plate y=3..4")
        self.add("3031", COLOR_ORANGE, 3, 3, 1, 0, sid, "Head base right 4x4 Orange cantilever plate y=3..4")

        # local_y = 4..5 (Step 84): Expand Left (x in [-8, -3)) and Right (x in [3, 8)) trays to z in [-5, 5),
        # keeping the entire 6-stud center channel x in [-3, 3) open for SA-06!
        self.add("3035", COLOR_ORANGE, -8, 4, -5, 0, sid, "Left head base 4x8 outer Z-bridge y=4..5")
        self.add("3460", COLOR_ORANGE, -4, 4, -5, 0, sid, "Left head base 1x8 inner Z-bridge y=4..5")
        self.add("3020", COLOR_ORANGE, -8, 4, 3, 90, sid, "Left head base 2x4 outer front plate y=4..5")
        self.add("3023", COLOR_ORANGE, -4, 4, 3, 0, sid, "Left head base 1x2 inner front plate y=4..5")
        self.add("3460", COLOR_ORANGE, 3, 4, -5, 0, sid, "Right head base 1x8 inner Z-bridge y=4..5")
        self.add("3035", COLOR_ORANGE, 4, 4, -5, 0, sid, "Right head base 4x8 outer Z-bridge y=4..5")
        self.add("3023", COLOR_ORANGE, 3, 4, 3, 0, sid, "Right head base 1x2 inner front plate y=4..5")
        self.add("3020", COLOR_ORANGE, 4, 4, 3, 90, sid, "Right head base 2x4 outer front plate y=4..5")

        # local_y = 5..6 (Step 85, world_y = 192.0..195.2 mm > 189.62 mm top of SA-06): Bridge across full x in [-8, 8), z in [-5, 5)!
        for bx in (-8, 0):
            self.add("3035", COLOR_ORANGE, bx, 5, -5, 90, sid, f"Head base 4x8 X-bridge rear x={bx} y=5..6")
            self.add("3035", COLOR_ORANGE, bx, 5, -1, 90, sid, f"Head base 4x8 X-bridge mid x={bx} y=5..6")
            self.add("3034", COLOR_ORANGE, bx, 5, 3, 90, sid, f"Head base 2x8 X-bridge front x={bx} y=5..6")

        # local_y = 6..7: Full 16x11 Orange lower rim plate (expanding rear to z = -6) + smooth tiled front chin lip at z in [3, 5)
        self.tile_rect(
            -8, 8, 6, 3, 5, 1, COLOR_ORANGE, sid,
            prefer_x_axis=True, use_tiles=True, notes="Smooth Orange front chin lip under camera faceplate y=6..7"
        )
        # Leave central acoustic chamber x in [-5, 5), z in [-4, 1) capped at y=6..7 with tiles so upper head is lightweight hollow shell!
        self.tile_rect(
            -5, 5, 6, -4, 1, 1, COLOR_ORANGE, sid,
            prefer_x_axis=True, use_tiles=True, notes="Hollow projector acoustic chamber smooth floor y=6..7"
        )
        self.tile_rect(
            -8, 8, 6, -6, 3, 1, COLOR_ORANGE, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Orange head lower rim perimeter deck y=6..7"
        )

        # local_y = 7..13 (6 plates):
        # - Orange Side Pivot Ear Brackets on x in [-8, -6) and x in [6, 8) (coaxial 3700 Technic bricks + horizontal 2780 Black pin!)
        # - Recessed Flat Light Bluish Gray Camera Faceplate at z in [2, 3), x in [-6, 6)
        # - Single Circular Yellow/Bright-Light-Orange Camera Ring (y = 9..15, x in [-3, 3), z in [3, 4)) around 2x2 Black Lens (x in [-1, 1), y = 11..13)
        # - Offset Black Pill Sensor Slot (x in [3, 5), y = 11..13, z in [3, 4))
        # - Hollow acoustic chamber in x in [-5, 5), z in [-4, 1) for optimal low Center of Gravity!
        for ear_side, ex_outer, ex_inner, pin_x, pin_x_off in [
            ("Left", -8, -7, -7, -0.5),
            ("Right", 7, 6, 6, 0.5),
        ]:
            self.add("3700", COLOR_ORANGE, ex_outer, 7, -1, 0, sid, f"{ear_side} Orange ear outer Technic brick")
            self.add("3700", COLOR_ORANGE, ex_inner, 7, -1, 0, sid, f"{ear_side} Orange ear inner Technic brick")
            self.add(
                "2780", COLOR_BLACK, pin_x, 8, -1, 0, sid,
                notes=f"{ear_side} Orange ear horizontal Technic pin",
                pin_orientation="horizontal_x",
                pin_x_offset_studs=pin_x_off,
                pin_z_offset_studs=0.5,
            )

        # Fill perimeter walls at y = 7..9 (Side walls x in [-8,-5) & [5,8), Rear wall z in [-6,-4), Front faceplate backing z in [1,3))
        for py in (7, 8):
            w_col = COLOR_ORANGE if py == 7 else COLOR_WHITE
            self.tile_rect(-8, -5, py, -6, 3, 1, w_col, sid, prefer_x_axis=(py % 2 == 0), stagger_shift=py, notes=f"Left head perimeter wall y={py}")
            self.tile_rect(5, 8, py, -6, 3, 1, w_col, sid, prefer_x_axis=(py % 2 == 0), stagger_shift=py, notes=f"Right head perimeter wall y={py}")
            self.tile_rect(-5, 5, py, -6, -4, 1, w_col, sid, prefer_x_axis=True, stagger_shift=py, notes=f"Rear head perimeter wall y={py}")
            self.tile_rect(-5, 5, py, 1, 3, 1, COLOR_LIGHT_BLUISH_GRAY if py == 8 else COLOR_ORANGE, sid, prefer_x_axis=True, stagger_shift=py, notes=f"Front faceplate backing y={py}")

        # local_y = 9..15: Sculpt the Cyclops Yellow Camera Ring + 2x2 Black Lens + Offset Black Pill Sensor on z in [2, 4)
        for py in range(9, 15):
            if py in (9, 14):
                self.add("3022", COLOR_YELLOW, -2, py, 2, 0, sid, f"Cyclops camera ring arc left y={py}")
                self.add("3022", COLOR_YELLOW, 0, py, 2, 0, sid, f"Cyclops camera ring arc right y={py}")
            elif py in (10, 13):
                self.add("3023", COLOR_YELLOW, -3, py, 2, 0, sid, f"Cyclops camera ring outer left y={py}")
                self.add("3022", COLOR_BRIGHT_LIGHT_ORANGE, -2, py, 2, 0, sid, f"Cyclops camera inner bezel left y={py}")
                self.add("3022", COLOR_BRIGHT_LIGHT_ORANGE, 0, py, 2, 0, sid, f"Cyclops camera inner bezel right y={py}")
                self.add("3023", COLOR_YELLOW, 2, py, 2, 0, sid, f"Cyclops camera ring outer right y={py}")
            else:
                self.add("3022", COLOR_YELLOW, -3, py, 2, 0, sid, f"Cyclops camera ring mid left y={py}")
                self.add("3022", COLOR_BLACK, -1, py, 2, 0, sid, f"Cyclops 2x2 Black central camera lens y={py}")
                self.add("3022", COLOR_YELLOW, 1, py, 2, 0, sid, f"Cyclops camera ring mid right y={py}")
                self.add("3022", COLOR_BLACK, 3, py, 2, 0, sid, f"Offset Black pill sensor slot y={py}")

            # Fill remaining Recessed Light Bluish Gray faceplate at z in [1, 3), x in [-6, 6)
            self.tile_rect(
                -6, 6, py, 1, 3, 1, COLOR_LIGHT_BLUISH_GRAY, sid,
                prefer_x_axis=True, stagger_shift=py, notes=f"Recessed Light Bluish Gray faceplate y={py}"
            )
            # Overhanging White side visor walls at x in [-8, -5) and x in [5, 8) extending forward to z = 5!
            for side_w, wx0, wx1 in [("Left", -8, -5), ("Right", 5, 8)]:
                wall_color = COLOR_ORANGE if py < 11 else COLOR_WHITE
                self.tile_rect(
                    wx0, wx1, py, -6, 3, 1, wall_color, sid,
                    prefer_x_axis=(py % 2 == 0), stagger_shift=py, notes=f"{side_w} visor hood cheek wall y={py}"
                )
            # Rear heatsink grille at z in [-6, -4), x in [-5, 5)
            rear_col = COLOR_DARK_BLUISH_GRAY if py in (10, 11, 12, 13) else COLOR_WHITE
            self.tile_rect(
                -5, 5, py, -6, -4, 1, rear_col, sid,
                prefer_x_axis=True, stagger_shift=py, notes=f"Rear head wall & heatsink grille y={py}"
            )

        # local_y = 15..18 (3 plates): Upper Recessed Faceplate & Hollow Visor Perimeter Walls
        self.tile_rect(
            -6, 6, 15, 1, 3, 3, COLOR_LIGHT_BLUISH_GRAY, sid,
            prefer_x_axis=True, stagger_shift=0, notes="Upper recessed Light Bluish Gray faceplate y=15..18"
        )
        self.tile_rect(
            -8, -5, 15, -6, 3, 3, COLOR_WHITE, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Left White visor side hood wall y=15..18"
        )
        self.tile_rect(
            5, 8, 15, -6, 3, 3, COLOR_WHITE, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Right White visor side hood wall y=15..18"
        )
        self.tile_rect(
            -5, 5, 15, -6, -4, 3, COLOR_WHITE, sid,
            prefer_x_axis=True, stagger_shift=1, notes="Upper White rear head wall y=15..18"
        )

        # local_y = 18..21 (3 plates): Overhanging White Projector Visor Hood Roof bridging full x in [-8, 8), z in [-6, 5)!
        # At y = 18..19: Bridge across the hollow chamber z in [-4, 1) using four Z-oriented 4x8 plates (3035) at z in [-6, 2) + front brow z in [2, 5)!
        for bx in (-8, -4, 0, 4):
            self.add("3035", COLOR_WHITE, bx, 18, -6, 0, sid, f"Visor hood 4x8 roof bridge plate x={bx} y=18..19")
        self.tile_rect(
            -8, 8, 18, 1, 5, 1, COLOR_WHITE, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Overhanging White visor hood front brow y=18..19"
        )
        self.tile_rect(
            -8, 8, 19, -6, 5, 1, COLOR_WHITE, sid,
            prefer_x_axis=True, stagger_shift=1, notes="Overhanging White visor hood mid deck y=19..20"
        )
        self.tile_rect(
            -8, 8, 20, -6, 5, 1, COLOR_WHITE, sid,
            prefer_x_axis=False, stagger_shift=0, notes="Overhanging White visor hood upper deck y=20..21"
        )

        # local_y = 21..23 (2 plates): Sculpted Curved White Visor Hood Crown (world_y_max_mm == 249.60 mm = 78.0 plates!)
        # Front overhanging brow curved slopes at z in [3, 5) and rear curved crown at z in [-6, -4)
        for cx in range(-8, 8, 2):
            self.add("15068", COLOR_WHITE, cx, 21, 3, 0, sid, "Visor hood front overhanging curved slope")
            self.add("15068", COLOR_WHITE, cx, 21, -6, 0, sid, "Visor hood rear curved crown slope")
        # Side shoulder curved slopes at x in [-8, -6) and x in [6, 8), z in [-4, 3)
        for side_s, sx in [("Left", -8), ("Right", 6)]:
            self.add("15068", COLOR_WHITE, sx, 21, -4, 90, sid, f"{side_s} visor hood shoulder curved slope rear")
            self.add("15068", COLOR_WHITE, sx, 21, -2, 90, sid, f"{side_s} visor hood shoulder curved slope mid")
            self.add("15068", COLOR_WHITE, sx, 21, 0, 90, sid, f"{side_s} visor hood shoulder curved slope front")
            self.add("11477", COLOR_WHITE, sx, 21, 2, 90, sid, f"{side_s} visor hood shoulder curved slope brow")

        # Central crown foundation at y = 21..22 (x in [-6, 6), z in [-4, 3))
        self.tile_rect(
            -6, 6, 21, -4, 3, 1, COLOR_WHITE, sid,
            prefer_x_axis=True, stagger_shift=1, notes="Visor hood crown plate y=21..22"
        )
        # Smooth White top crown tiles at y = 22..23 (local_y_top = 23 -> world_y_max_mm == 249.60 mm!)
        self.tile_rect(
            -6, 6, 22, -4, 3, 1, COLOR_WHITE, sid,
            prefer_x_axis=True, use_tiles=True, notes="Visor hood smooth top crown tiles y=22..23 (249.6 mm)"
        )

    # ------------------------------------------------------------------
    # Sequential Step Partitioner (129 Steps: 1..12, 13..24, 25..39, 40..53, 54..67, 68..79, 80..129)
    # ------------------------------------------------------------------
    def assign_sequential_steps(self) -> List[PlacedBrick]:
        """Sort bricks by (subassembly_id, local_y, z, x) and group into exact 129 buildable steps."""
        ordered: List[PlacedBrick] = sorted(
            self.raw_bricks,
            key=lambda b: (b.subassembly_id, b.y, b.z, b.x, b.brick_id),
        )

        target_steps_by_sub: Dict[int, int] = {
            1: 12,  # Steps 1..12
            2: 13,  # Steps 13..25
            3: 14,  # Steps 26..39 (Step 39 -> 40 is SA-03 -> SA-04!)
            4: 14,  # Steps 40..53
            5: 14,  # Steps 54..67
            6: 12,  # Steps 68..79
            7: 50,  # Steps 80..129 (Steps 80..82 under-chin clevis & pins -> Step 83 Orange head base!)
        }

        def _partition_layers(layers: List[List[PlacedBrick]], target_steps: int, fixed_first: Optional[Dict[int, int]] = None) -> List[List[PlacedBrick]]:
            fixed = fixed_first or {}
            counts = [
                fixed[i] if i in fixed else max(1, math.ceil(len(layer) / 14))
                for i, layer in enumerate(layers)
            ]
            while sum(counts) < target_steps:
                best_i = -1
                best_ratio = -1.0
                for i, layer in enumerate(layers):
                    if i in fixed or counts[i] >= len(layer):
                        continue
                    ratio = len(layer) / counts[i]
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_i = i
                if best_i < 0:
                    break
                counts[best_i] += 1

            while sum(counts) > target_steps:
                best_i = -1
                best_ratio = 999999.0
                for i, layer in enumerate(layers):
                    if i in fixed or counts[i] <= 1:
                        continue
                    if math.ceil(len(layer) / (counts[i] - 1)) > 14:
                        continue
                    ratio = len(layer) / counts[i]
                    if ratio < best_ratio:
                        best_ratio = ratio
                        best_i = i
                if best_i < 0:
                    break
                counts[best_i] -= 1

            result_steps: List[List[PlacedBrick]] = []
            for layer, k in zip(layers, counts):
                m = len(layer)
                for ci in range(k):
                    s_idx = (ci * m) // k
                    e_idx = ((ci + 1) * m) // k
                    result_steps.append(layer[s_idx:e_idx])
            return result_steps

        step_id = 0
        for sid in sorted(SUBASSEMBLY_NAMES.keys()):
            sub_bricks = [b for b in ordered if b.subassembly_id == sid]
            layers: List[List[PlacedBrick]] = []
            idx = 0
            n_sub = len(sub_bricks)
            while idx < n_sub:
                cur_y = sub_bricks[idx].y
                layer: List[PlacedBrick] = []
                while idx < n_sub and sub_bricks[idx].y == cur_y:
                    layer.append(sub_bricks[idx])
                    idx += 1
                layers.append(layer)

            # In SA-07, fix layer 0 (y=0, 4 clevis bricks) -> 2 steps (Steps 80, 81),
            # layer 1 (y=1, 2 coaxial pins) -> 1 step (Step 82), and layer 2 (y=3, 2 Orange plates) -> 1 step (Step 83)
            fixed_map = {0: 2, 1: 1, 2: 1} if sid == 7 else None
            sub_steps = _partition_layers(layers, target_steps_by_sub[sid], fixed_map)
            for chunk in sub_steps:
                step_id += 1
                for b in chunk:
                    b.step_id = step_id

        for new_id, b in enumerate(ordered, start=1):
            b.brick_id = new_id
        return ordered

    def build(self) -> MicroduckModel:
        self.build_sa01_bootie_feet()
        self.build_sa02_shins_and_knees()
        self.build_sa03_thighs_and_white_shields()
        self.build_sa04_hip_servo_and_roll_hubs()
        self.build_sa05_torso_and_battery_spine()
        self.build_sa06_slender_neck_stalk()
        self.build_sa07_visor_head()
        bricks = self.assign_sequential_steps()
        return MicroduckModel(bricks=bricks)


def generate_microduck_model(output_json_path: Optional[Path] = None) -> MicroduckModel:
    """Build the complete Rev 3.0 Microduck CAD model and optionally write JSON."""
    builder = MicroduckBuilder()
    model = builder.build()
    if output_json_path is not None:
        model.save_json(output_json_path)
    return model


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    out_json = root / "output" / "microduck_model.json"
    mdl = generate_microduck_model(out_json)
    print(
        f"Generated Rev 3.0 Microduck Model: {len(mdl.bricks)} pieces, "
        f"{max(b.step_id for b in mdl.bricks)} steps -> {out_json}"
    )
