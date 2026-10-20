"""Authentic LEGO Parts & Color Catalog for the Life-Sized Microduck Robot.

All dimensions use standard LEGO geometry:
  - 1 stud (X, Z) = 8.0 mm = 20 LDU
  - 1 plate (Y)   = 3.2 mm = 8 LDU
  - 1 brick (Y)   = 3 plates = 9.6 mm = 24 LDU

Every part ID and color ID corresponds to a real, high-availability BrickLink
catalog item and its matching LDraw part number / color code.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

STUD_MM: float = 8.0
PLATE_MM: float = 3.2
BRICK_MM: float = 9.6

STUD_LDU: float = 20.0
PLATE_LDU: float = 8.0


@dataclass(frozen=True)
class LegoColor:
    """Represents an official LEGO color with BrickLink and LDraw mappings."""

    bricklink_id: int
    ldraw_id: int
    name: str
    hex_rgb: str


@dataclass(frozen=True)
class PartSpec:
    """Physical and CAD specification for a real LEGO element.

    Dimensions (width_x, height_y, depth_z) are given in (studs, plates, studs)
    at canonical rotation = 0.
    """

    part_id: str
    name: str
    category: str
    width_x: int
    height_y: int  # in plates (1 plate = 3.2mm, 1 brick = 3 plates = 9.6mm)
    depth_z: int
    mass_g: float
    has_top_studs: bool
    has_bottom_tubes: bool
    ldraw_dat: str
    is_hinge_base: bool = False
    is_hinge_top: bool = False

    def oriented_dims(self, rotation: int) -> Tuple[int, int, int]:
        """Return (dx, dy, dz) in (studs, plates, studs) for a 90-deg rotation."""
        rot = rotation % 360
        if rot in (0, 180):
            return (self.width_x, self.height_y, self.depth_z)
        elif rot in (90, 270):
            return (self.depth_z, self.height_y, self.width_x)
        raise ValueError(f"Unsupported rotation {rotation}; must be 0, 90, 180, or 270.")


# Official Hugging Face x Pollen Robotics Microduck Colorway
COLORS: Dict[int, LegoColor] = {
    1: LegoColor(
        bricklink_id=1,
        ldraw_id=15,
        name="White",
        hex_rgb="#F4F4F4",
    ),
    2: LegoColor(
        bricklink_id=2,
        ldraw_id=19,
        name="Tan",
        hex_rgb="#E4CD9E",
    ),
    3: LegoColor(
        bricklink_id=3,
        ldraw_id=14,
        name="Yellow",
        hex_rgb="#F2CD37",
    ),
    4: LegoColor(
        bricklink_id=4,
        ldraw_id=25,
        name="Orange",
        hex_rgb="#FE8A18",
    ),
    110: LegoColor(
        bricklink_id=110,
        ldraw_id=191,
        name="Bright Light Orange",
        hex_rgb="#F8BB3D",
    ),
    85: LegoColor(
        bricklink_id=85,
        ldraw_id=72,
        name="Dark Bluish Gray",
        hex_rgb="#6C6E68",
    ),
    86: LegoColor(
        bricklink_id=86,
        ldraw_id=71,
        name="Light Bluish Gray",
        hex_rgb="#A0A5A9",
    ),
    11: LegoColor(
        bricklink_id=11,
        ldraw_id=0,
        name="Black",
        hex_rgb="#1B2A34",
    ),
    15: LegoColor(
        bricklink_id=15,
        ldraw_id=43,
        name="Trans-Light Blue",
        hex_rgb="#AEEFEC",
    ),
}

# Symbolic color constants (BrickLink Color IDs)
COLOR_WHITE = 1
COLOR_TAN = 2
COLOR_YELLOW = 3
COLOR_ORANGE = 4
COLOR_BRIGHT_LIGHT_ORANGE = 110
COLOR_DARK_BLUISH_GRAY = 85
COLOR_LIGHT_BLUISH_GRAY = 86
COLOR_BLACK = 11
COLOR_TRANS_LIGHT_BLUE = 15


# Catalog of real, high-availability BrickLink parts
PARTS_CATALOG: Dict[str, PartSpec] = {
    # Standard Bricks (height_y = 3 plates)
    "3005": PartSpec(
        part_id="3005",
        name="Brick 1 x 1",
        category="Brick",
        width_x=1,
        height_y=3,
        depth_z=1,
        mass_g=0.45,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3005.dat",
    ),
    "3004": PartSpec(
        part_id="3004",
        name="Brick 1 x 2",
        category="Brick",
        width_x=1,
        height_y=3,
        depth_z=2,
        mass_g=0.82,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3004.dat",
    ),
    "3622": PartSpec(
        part_id="3622",
        name="Brick 1 x 3",
        category="Brick",
        width_x=1,
        height_y=3,
        depth_z=3,
        mass_g=1.18,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3622.dat",
    ),
    "3010": PartSpec(
        part_id="3010",
        name="Brick 1 x 4",
        category="Brick",
        width_x=1,
        height_y=3,
        depth_z=4,
        mass_g=1.52,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3010.dat",
    ),
    "3009": PartSpec(
        part_id="3009",
        name="Brick 1 x 6",
        category="Brick",
        width_x=1,
        height_y=3,
        depth_z=6,
        mass_g=2.24,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3009.dat",
    ),
    "3003": PartSpec(
        part_id="3003",
        name="Brick 2 x 2",
        category="Brick",
        width_x=2,
        height_y=3,
        depth_z=2,
        mass_g=1.15,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3003.dat",
    ),
    "3002": PartSpec(
        part_id="3002",
        name="Brick 2 x 3",
        category="Brick",
        width_x=2,
        height_y=3,
        depth_z=3,
        mass_g=1.70,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3002.dat",
    ),
    "3001": PartSpec(
        part_id="3001",
        name="Brick 2 x 4",
        category="Brick",
        width_x=2,
        height_y=3,
        depth_z=4,
        mass_g=2.25,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3001.dat",
    ),
    "2456": PartSpec(
        part_id="2456",
        name="Brick 2 x 6",
        category="Brick",
        width_x=2,
        height_y=3,
        depth_z=6,
        mass_g=3.35,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="2456.dat",
    ),
    # Technic Bricks & Pins
    "3700": PartSpec(
        part_id="3700",
        name="Technic, Brick 1 x 2 with Hole",
        category="Technic Brick",
        width_x=1,
        height_y=3,
        depth_z=2,
        mass_g=0.80,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3700.dat",
    ),
    "3701": PartSpec(
        part_id="3701",
        name="Technic, Brick 1 x 4 with Holes",
        category="Technic Brick",
        width_x=1,
        height_y=3,
        depth_z=4,
        mass_g=1.48,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3701.dat",
    ),
    "3894": PartSpec(
        part_id="3894",
        name="Technic, Brick 1 x 6 with Holes",
        category="Technic Brick",
        width_x=1,
        height_y=3,
        depth_z=6,
        mass_g=2.18,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3894.dat",
    ),
    "2780": PartSpec(
        part_id="2780",
        name="Technic, Pin with Short Friction Ridges",
        category="Technic Pin",
        width_x=1,
        height_y=1,
        depth_z=1,
        mass_g=0.16,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="2780.dat",
    ),
    # Standard & Rotational Plates (height_y = 1 plate)
    "3024": PartSpec(
        part_id="3024",
        name="Plate 1 x 1",
        category="Plate",
        width_x=1,
        height_y=1,
        depth_z=1,
        mass_g=0.18,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3024.dat",
    ),
    "3023": PartSpec(
        part_id="3023",
        name="Plate 1 x 2",
        category="Plate",
        width_x=1,
        height_y=1,
        depth_z=2,
        mass_g=0.34,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3023.dat",
    ),
    "3623": PartSpec(
        part_id="3623",
        name="Plate 1 x 3",
        category="Plate",
        width_x=1,
        height_y=1,
        depth_z=3,
        mass_g=0.49,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3623.dat",
    ),
    "3710": PartSpec(
        part_id="3710",
        name="Plate 1 x 4",
        category="Plate",
        width_x=1,
        height_y=1,
        depth_z=4,
        mass_g=0.65,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3710.dat",
    ),
    "3666": PartSpec(
        part_id="3666",
        name="Plate 1 x 6",
        category="Plate",
        width_x=1,
        height_y=1,
        depth_z=6,
        mass_g=0.96,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3666.dat",
    ),
    "3460": PartSpec(
        part_id="3460",
        name="Plate 1 x 8",
        category="Plate",
        width_x=1,
        height_y=1,
        depth_z=8,
        mass_g=1.28,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3460.dat",
    ),
    "3022": PartSpec(
        part_id="3022",
        name="Plate 2 x 2",
        category="Plate",
        width_x=2,
        height_y=1,
        depth_z=2,
        mass_g=0.62,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3022.dat",
    ),
    "3021": PartSpec(
        part_id="3021",
        name="Plate 2 x 3",
        category="Plate",
        width_x=2,
        height_y=1,
        depth_z=3,
        mass_g=0.92,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3021.dat",
    ),
    "3020": PartSpec(
        part_id="3020",
        name="Plate 2 x 4",
        category="Plate",
        width_x=2,
        height_y=1,
        depth_z=4,
        mass_g=1.22,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3020.dat",
    ),
    "3795": PartSpec(
        part_id="3795",
        name="Plate 2 x 6",
        category="Plate",
        width_x=2,
        height_y=1,
        depth_z=6,
        mass_g=1.82,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3795.dat",
    ),
    "3034": PartSpec(
        part_id="3034",
        name="Plate 2 x 8",
        category="Plate",
        width_x=2,
        height_y=1,
        depth_z=8,
        mass_g=2.42,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3034.dat",
    ),
    "4032": PartSpec(
        part_id="4032",
        name="Plate, Round 2 x 2 with Axle Hole",
        category="Plate, Round",
        width_x=2,
        height_y=1,
        depth_z=2,
        mass_g=0.55,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="4032.dat",
    ),
    "3031": PartSpec(
        part_id="3031",
        name="Plate 4 x 4",
        category="Plate",
        width_x=4,
        height_y=1,
        depth_z=4,
        mass_g=2.40,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3031.dat",
    ),
    "3032": PartSpec(
        part_id="3032",
        name="Plate 4 x 6",
        category="Plate",
        width_x=4,
        height_y=1,
        depth_z=6,
        mass_g=3.60,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3032.dat",
    ),
    "3035": PartSpec(
        part_id="3035",
        name="Plate 4 x 8",
        category="Plate",
        width_x=4,
        height_y=1,
        depth_z=8,
        mass_g=4.80,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3035.dat",
    ),
    # Hinges (3937 Base = 2 plates + 3938 Top = 1 plate -> 3 plates combined)
    "3937": PartSpec(
        part_id="3937",
        name="Hinge Brick 1 x 2 Base",
        category="Hinge",
        width_x=1,
        height_y=2,
        depth_z=2,
        mass_g=0.65,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3937.dat",
        is_hinge_base=True,
    ),
    "3938": PartSpec(
        part_id="3938",
        name="Hinge Brick 1 x 2 Top",
        category="Hinge",
        width_x=1,
        height_y=1,
        depth_z=2,
        mass_g=0.40,
        has_top_studs=True,
        has_bottom_tubes=True,
        ldraw_dat="3938.dat",
        is_hinge_top=True,
    ),
    # Tiles & Grille Tiles (height_y = 1 plate, no top studs)
    "3070b": PartSpec(
        part_id="3070b",
        name="Tile 1 x 1 with Groove",
        category="Tile",
        width_x=1,
        height_y=1,
        depth_z=1,
        mass_g=0.15,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="3070b.dat",
    ),
    "3069b": PartSpec(
        part_id="3069b",
        name="Tile 1 x 2 with Groove",
        category="Tile",
        width_x=1,
        height_y=1,
        depth_z=2,
        mass_g=0.30,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="3069b.dat",
    ),
    "3068b": PartSpec(
        part_id="3068b",
        name="Tile 2 x 2 with Groove",
        category="Tile",
        width_x=2,
        height_y=1,
        depth_z=2,
        mass_g=0.58,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="3068b.dat",
    ),
    "2412b": PartSpec(
        part_id="2412b",
        name="Tile, Modified 1 x 2 Grille with Bottom Groove",
        category="Tile, Modified",
        width_x=1,
        height_y=1,
        depth_z=2,
        mass_g=0.28,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="2412b.dat",
    ),
    "2431": PartSpec(
        part_id="2431",
        name="Tile 1 x 4 with Groove",
        category="Tile",
        width_x=1,
        height_y=1,
        depth_z=4,
        mass_g=0.60,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="2431.dat",
    ),
    "87079": PartSpec(
        part_id="87079",
        name="Tile 2 x 4 with Groove",
        category="Tile",
        width_x=2,
        height_y=1,
        depth_z=4,
        mass_g=1.15,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="87079.dat",
    ),
    # Slopes & Curved Slopes (no top studs on sloped profile; used as top/edge finishing)
    "54200": PartSpec(
        part_id="54200",
        name="Slope 30 1 x 1 x 2/3",
        category="Slope",
        width_x=1,
        height_y=2,
        depth_z=1,
        mass_g=0.22,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="54200.dat",
    ),
    "85984": PartSpec(
        part_id="85984",
        name="Slope 30 1 x 2 x 2/3",
        category="Slope",
        width_x=1,
        height_y=2,
        depth_z=2,
        mass_g=0.44,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="85984.dat",
    ),
    "11477": PartSpec(
        part_id="11477",
        name="Slope, Curved 2 x 1 x 2/3",
        category="Slope, Curved",
        width_x=1,
        height_y=2,
        depth_z=2,
        mass_g=0.42,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="11477.dat",
    ),
    "15068": PartSpec(
        part_id="15068",
        name="Slope, Curved 2 x 2 x 2/3",
        category="Slope, Curved",
        width_x=2,
        height_y=2,
        depth_z=2,
        mass_g=0.82,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="15068.dat",
    ),
    "3040": PartSpec(
        part_id="3040",
        name="Slope 45 2 x 1",
        category="Slope",
        width_x=1,
        height_y=3,
        depth_z=2,
        mass_g=0.68,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="3040.dat",
    ),
    "3039": PartSpec(
        part_id="3039",
        name="Slope 45 2 x 2",
        category="Slope",
        width_x=2,
        height_y=3,
        depth_z=2,
        mass_g=1.05,
        has_top_studs=False,
        has_bottom_tubes=True,
        ldraw_dat="3039.dat",
    ),
}
