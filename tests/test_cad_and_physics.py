"""Comprehensive Unit Tests for the Hugging Face x Pollen Robotics Microduck LEGO CAD & Physics Model."""

import csv
import json
from pathlib import Path
import unittest

from cad.microduck_builder import SUBASSEMBLY_NAMES, generate_microduck_model
from cad.parts_catalog import (
    COLOR_BLACK,
    COLOR_BRIGHT_LIGHT_ORANGE,
    COLOR_DARK_BLUISH_GRAY,
    COLOR_LIGHT_BLUISH_GRAY,
    COLOR_ORANGE,
    COLOR_TRANS_LIGHT_BLUE,
    COLOR_WHITE,
    COLOR_YELLOW,
)
from cad.verifier import (
    audit_1_scale_and_specs,
    audit_2_volumetric_collisions,
    audit_3_connectivity_graph,
    audit_4_step_buildability,
    audit_5_center_of_gravity_and_balance,
    audit_6_bricklink_procurement,
    audit_7_bipedal_walking_gait_and_kinematics,
    run_full_verification,
)


class TestMicroduckCadAndPhysics(unittest.TestCase):
    """End-to-end CAD geometry, connectivity, buildability, physics, and walking gait tests."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.output_dir = cls.root_dir / "output"
        cls.report = run_full_verification(cls.output_dir)
        cls.model = generate_microduck_model()

    def test_audit_1_exact_scale_and_piece_counts(self) -> None:
        """Verify exact 78-plate (249.6 mm) height, piece count, and step bounds."""
        a1 = audit_1_scale_and_specs(self.model)
        self.assertTrue(a1["passed"])
        self.assertEqual(a1["min_y_plates"], 0)
        self.assertEqual(a1["max_y_plates"], 78)
        self.assertEqual(a1["height_plates"], 78)
        self.assertAlmostEqual(a1["height_mm"], 249.6, places=2)
        self.assertAlmostEqual(a1["height_cm"], 24.96, places=1)
        self.assertGreaterEqual(a1["total_pieces"], 700)
        self.assertLessEqual(a1["total_pieces"], 1150)
        self.assertGreaterEqual(a1["total_steps"], 85)
        self.assertLessEqual(a1["total_steps"], 140)
        self.assertGreaterEqual(a1["min_bricks_per_step"], 1)
        self.assertLessEqual(a1["max_bricks_per_step"], 14)

    def test_all_7_modular_subassemblies_and_y_ranges(self) -> None:
        """Verify all 7 modular sub-assemblies match their local plate height spans and 3D pitch angles."""
        a1 = audit_1_scale_and_specs(self.model)
        subs = a1["subassemblies"]
        self.assertEqual(set(subs.keys()), {1, 2, 3, 4, 5, 6, 7})

        expected_local_y_ranges = {
            1: (0, 8),
            2: (0, 16),
            3: (0, 16),
            4: (0, 11),
            5: (0, 11),
            6: (0, 16),
            7: (0, 23),
        }
        expected_pitch_deg = {
            1: 0.0,
            2: 24.0,
            3: -26.0,
            4: 0.0,
            5: 0.0,
            6: 19.7247,
            7: 0.0,
        }
        for sid, (y0, y1) in expected_local_y_ranges.items():
            self.assertEqual(subs[sid]["y_min"], y0, f"Sub-Assembly {sid} local y_min mismatch")
            self.assertEqual(subs[sid]["y_max"], y1, f"Sub-Assembly {sid} local y_max mismatch")
            self.assertAlmostEqual(subs[sid]["pitch_deg"], expected_pitch_deg[sid], places=2)
            self.assertGreater(subs[sid]["piece_count"], 15)

    def test_signature_colorway_and_authentic_features(self) -> None:
        """Verify all 8 authentic Microduck robot colors and key mechanical/sculpted parts are present."""
        used_colors = {b.color_id for b in self.model.bricks}
        expected_colors = {
            COLOR_WHITE,
            COLOR_ORANGE,
            COLOR_YELLOW,
            COLOR_BRIGHT_LIGHT_ORANGE,
            COLOR_DARK_BLUISH_GRAY,
            COLOR_LIGHT_BLUISH_GRAY,
            COLOR_BLACK,
            COLOR_TRANS_LIGHT_BLUE,
        }
        self.assertEqual(used_colors, expected_colors)

        used_parts = {b.part_id for b in self.model.bricks}
        # Verify Technic pin blocks, friction pins, round hubs, curved visor slopes, and grille tiles
        for required_part in (
            "3700",
            "3701",
            "2780",
            "4032",
            "11477",
            "15068",
            "2412b",
            "3068b",
            "3070b",
            "54200",
            "3035",
        ):
            self.assertIn(required_part, used_parts)

        # Verify every 2780 Technic pin is oriented horizontally along the X-axis
        pins = [b for b in self.model.bricks if b.part_id == "2780"]
        self.assertGreaterEqual(len(pins), 16)
        for p in pins:
            self.assertEqual(p.pin_orientation, "horizontal_x")

    def test_audit_2_zero_volumetric_collisions(self) -> None:
        """Verify 0 overlapping local cells, 0 3D OBB collisions across all sub-assembly pairs, and 0 pin collisions."""
        a2 = audit_2_volumetric_collisions(self.model)
        self.assertTrue(a2["passed"])
        self.assertEqual(a2["collision_count"], 0)
        self.assertEqual(a2["obb_world_collisions"], 0)
        self.assertEqual(a2["same_sub_obb_collisions"], 0)
        self.assertEqual(a2["adjacent_sub_collisions"], 0)
        self.assertEqual(a2["non_mating_world_penetrations"], 0)
        self.assertEqual(a2["pin_collisions"], 0)

    def test_audit_3_full_connectivity_graph_and_coaxial_pin_joints(self) -> None:
        """Verify 1 single connected component, 0 floating bricks, 100% ground path, and 8 coaxial pin joints."""
        a3 = audit_3_connectivity_graph(self.model)
        self.assertTrue(a3["passed"])
        self.assertEqual(a3["connected_components"], 1)
        self.assertEqual(a3["floating_bricks"], 0)
        self.assertEqual(a3["grounded_bricks"], len(self.model.bricks))
        self.assertGreater(a3["total_stud_connections"], 2500)
        self.assertEqual(a3["verified_coaxial_pin_joints"], 8)
        self.assertEqual(a3["verified_double_shear_joints"], 8)
        self.assertGreaterEqual(a3["total_joint_shear_pins"], 16)
        self.assertEqual(len(a3["coaxial_pin_joints"]), 8)
        for j in a3["coaxial_pin_joints"]:
            self.assertTrue(j["passed"], f"Coaxial joint {j['joint_id']} failed")
            self.assertTrue(j["double_shear"], f"Coaxial joint {j['joint_id']} is not double-shear")
            self.assertGreaterEqual(len(j["shear_pin_brick_ids"]), 2, f"Coaxial joint {j['joint_id']} has fewer than 2 shear pins")
        self.assertLess(a3["max_coaxial_pin_error_mm"], 0.05)
        self.assertGreaterEqual(a3["horizontal_technic_pins_count"], 20)

    def test_audit_4_every_step_buildability_and_insertion_access(self) -> None:
        """Verify 0 unbuildable steps, 0 floating bricks at any step, and 0 trapped insertions."""
        a4 = audit_4_step_buildability(self.model)
        self.assertTrue(a4["passed"])
        self.assertEqual(a4["unbuildable_steps"], 0)
        self.assertEqual(a4["step_floating_bricks"], 0)
        self.assertEqual(a4["trapped_insertions"], 0)
        self.assertEqual(a4["trapped_insertions_within_subassembly"], 0)
        self.assertEqual(a4["trapped_insertions_global"], 0)
        for sid in SUBASSEMBLY_NAMES:
            self.assertTrue(a4["subassembly_merge_milestones_passed"][sid])

    def test_audit_5_center_of_gravity_and_static_balance(self) -> None:
        """Verify CoG lies strictly inside support polygon with >=25mm margin and >=15 deg tipping."""
        a5 = audit_5_center_of_gravity_and_balance(self.model)
        self.assertTrue(a5["passed"])
        self.assertTrue(a5["is_balanced"])
        self.assertGreaterEqual(a5["edge_margins_mm"]["min_edge_margin_mm"], 25.0)
        self.assertGreaterEqual(a5["edge_margins_mm"]["front_margin_mm"], 25.0)
        self.assertGreaterEqual(a5["edge_margins_mm"]["back_margin_mm"], 25.0)
        self.assertGreaterEqual(a5["edge_margins_mm"]["left_margin_mm"], 25.0)
        self.assertGreaterEqual(a5["edge_margins_mm"]["right_margin_mm"], 25.0)
        self.assertGreaterEqual(a5["tipping_angles_deg"]["min_tipping_angle_deg"], 15.0)
        self.assertGreaterEqual(a5["tipping_angles_deg"]["front_deg"], 15.0)
        self.assertGreaterEqual(a5["tipping_angles_deg"]["back_deg"], 15.0)
        self.assertGreaterEqual(a5["tipping_angles_deg"]["left_deg"], 15.0)
        self.assertGreaterEqual(a5["tipping_angles_deg"]["right_deg"], 15.0)

    def test_audit_6_bricklink_xml_and_all_exported_artifacts(self) -> None:
        """Verify BrickLink XML, BOM CSV, LDraw MPD/LDR, and JSON model artifacts."""
        xml_path = self.output_dir / "microduck_bricklink_wanted_list.xml"
        csv_path = self.output_dir / "microduck_bom.csv"
        mpd_path = self.output_dir / "microduck.mpd"
        ldr_path = self.output_dir / "microduck.ldr"
        json_path = self.output_dir / "microduck_model.json"
        report_path = self.output_dir / "verification_report.json"

        for p in (xml_path, csv_path, mpd_path, ldr_path, json_path, report_path):
            self.assertTrue(p.exists(), f"Missing artifact {p}")
            self.assertGreater(p.stat().st_size, 100)

        a6 = audit_6_bricklink_procurement(self.model, xml_path, csv_path)
        self.assertTrue(a6["passed"])
        self.assertEqual(a6["invalid_parts"], 0)
        self.assertEqual(a6["xml_total_quantity"], len(self.model.bricks))

        # Check LDraw MPD contains 0 FILE for main and all 7 sub-assemblies plus 0 STEP markers
        mpd_text = mpd_path.read_text(encoding="utf-8")
        self.assertIn("0 FILE microduck_main.ldr", mpd_text)
        for sid in range(1, 8):
            self.assertIn(f"0 FILE subassembly_{sid}.ldr", mpd_text)
        self.assertGreaterEqual(mpd_text.count("0 STEP"), 90)

        # Check BOM CSV quantities sum to total pieces
        with open(csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(sum(int(r["quantity"]) for r in rows), len(self.model.bricks))

        # Check JSON model contains kinematic_joints, subassembly_poses, coaxial_pin_joints, and per-brick 3D pose fields
        model_data = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(len(model_data["kinematic_joints"]), 10)
        self.assertEqual(len(model_data["subassembly_poses"]), 7)
        self.assertEqual(len(model_data["coaxial_pin_joints"]), 8)
        sample_tilted = next(b for b in model_data["bricks"] if b["subassembly_id"] == 2)
        self.assertIn("world_center_mm", sample_tilted)
        self.assertIn("world_pitch_deg", sample_tilted)
        self.assertIn("world_rotation_matrix", sample_tilted)
        self.assertAlmostEqual(sample_tilted["world_pitch_deg"], 24.0, places=2)
        self.assertEqual(len(sample_tilted["world_rotation_matrix"]), 3)
        for row in sample_tilted["world_rotation_matrix"]:
            self.assertEqual(len(row), 3)

    def test_audit_7_bipedal_walking_gait_and_kinematics(self) -> None:
        """Verify 10 DoF kinematic joints and 8-phase bipedal walking gait stability & leg clearance."""
        a7 = audit_7_bipedal_walking_gait_and_kinematics(self.model)
        self.assertTrue(a7["passed"])
        self.assertEqual(a7["total_kinematic_joints"], 10)
        self.assertTrue(a7["all_10_joints_present"])
        self.assertEqual(a7["stride_phases_evaluated"], 8)
        self.assertEqual(a7["inter_leg_collisions"], 0)
        self.assertGreaterEqual(a7["min_inter_leg_clearance_mm"], 24.0)
        self.assertTrue(a7["all_phases_dynamically_stable"])
        for phase_data in a7["stride_phases"]:
            self.assertTrue(phase_data["phase_stable"])


if __name__ == "__main__":
    unittest.main()
