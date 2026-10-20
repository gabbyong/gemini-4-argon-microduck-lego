"""BrickLink Wanted List XML and Bill of Materials (BOM) CSV Exporter.

Aggregates all placed LEGO bricks by (part_id, color_id) lot and exports:
  1. output/microduck_bricklink_wanted_list.xml (BrickLink Mass Upload XML)
  2. output/microduck_bom.csv (Detailed procurement BOM with mass and dimensions)
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom

from cad.microduck_builder import MicroduckModel
from cad.parts_catalog import COLORS, PARTS_CATALOG


def aggregate_bom_lots(model: MicroduckModel) -> List[Dict[str, Any]]:
    """Aggregate placed bricks into unique (part_id, color_id) procurement lots."""
    counts: Dict[Tuple[str, int], int] = {}
    subassemblies_used: Dict[Tuple[str, int], set] = {}

    for b in model.bricks:
        key = (b.part_id, b.color_id)
        counts[key] = counts.get(key, 0) + 1
        subassemblies_used.setdefault(key, set()).add(b.subassembly_id)

    lots: List[Dict[str, Any]] = []
    for (part_id, color_id), qty in sorted(
        counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1])
    ):
        spec = PARTS_CATALOG[part_id]
        color = COLORS[color_id]
        lots.append(
            {
                "part_id": part_id,
                "part_name": spec.name,
                "category": spec.category,
                "color_id": color_id,
                "color_name": color.name,
                "ldraw_color_id": color.ldraw_id,
                "hex_rgb": color.hex_rgb,
                "quantity": qty,
                "unit_mass_g": spec.mass_g,
                "total_mass_g": round(qty * spec.mass_g, 2),
                "dimensions_studs_plates": f"{spec.width_x}x{spec.depth_z} ({spec.height_y}p)",
                "subassemblies": ",".join(
                    str(s) for s in sorted(subassemblies_used[(part_id, color_id)])
                ),
            }
        )
    return lots


def export_bricklink_xml(model: MicroduckModel, output_path: Path) -> None:
    """Export standard BrickLink Wanted List XML (<INVENTORY><ITEM>...)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lots = aggregate_bom_lots(model)

    root = ET.Element("INVENTORY")
    for lot in lots:
        item = ET.SubElement(root, "ITEM")
        item_type = ET.SubElement(item, "ITEMTYPE")
        item_type.text = "P"
        item_id = ET.SubElement(item, "ITEMID")
        item_id.text = str(lot["part_id"])
        color = ET.SubElement(item, "COLOR")
        color.text = str(lot["color_id"])
        min_qty = ET.SubElement(item, "MINQTY")
        min_qty.text = str(lot["quantity"])
        condition = ET.SubElement(item, "CONDITION")
        condition.text = "N"
        remarks = ET.SubElement(item, "REMARKS")
        remarks.text = f"{lot['color_name']} {lot['part_name']} (Sub-Assemblies: {lot['subassemblies']})"

    raw_xml = ET.tostring(root, encoding="utf-8")
    pretty_xml = minidom.parseString(raw_xml).toprettyxml(indent="  ")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)


def export_bom_csv(model: MicroduckModel, output_path: Path) -> None:
    """Export detailed Bill of Materials CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lots = aggregate_bom_lots(model)
    fieldnames = [
        "part_id",
        "part_name",
        "category",
        "color_id",
        "color_name",
        "ldraw_color_id",
        "hex_rgb",
        "quantity",
        "unit_mass_g",
        "total_mass_g",
        "dimensions_studs_plates",
        "subassemblies",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lot in lots:
            writer.writerow(lot)
