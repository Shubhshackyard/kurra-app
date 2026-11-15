"""Unit Tests for Engine Upgrades (Phase 2).

Validates:
1. Decreed fraction parser & sum=1 validator
2. Outward normal direction
3. Hard connectivity check (is_connected)
4. CP-SAT reproducibility (same seed -> same plan)
5. Possession overlap percentage
6. Tiered Rule 109(5) audit with statutory tags
7. Area uncertainty band calculation
"""
from fractions import Fraction
import unittest
from shapely.geometry import MultiPolygon, Polygon, box

from kurra.fractions import ShareValidationError, parse_fraction, validate_shares
from kurra.geometry import is_connected, overlap_percentage, polsby_popper
from kurra.optimizer import Party, assign_units, generate_plan
from kurra.report_parser import outward_normal_direction
from kurra.rules import evaluate, explain_failure
from kurra.uncertainty import compute_area_uncertainty, reconcile_record_vs_mapped


class TestEngineUpgrades(unittest.TestCase):
    def test_fraction_parser_formats(self):
        """Test parsing various decreed fraction formats."""
        self.assertEqual(parse_fraction("1/2"), Fraction(1, 2))
        self.assertEqual(parse_fraction("3/8"), Fraction(3, 8))
        self.assertEqual(parse_fraction("1/4 + 1/4"), Fraction(1, 2))
        self.assertEqual(parse_fraction("50%"), Fraction(1, 2))
        self.assertEqual(parse_fraction("0.25"), Fraction(1, 4))
        self.assertEqual(parse_fraction(0.125), Fraction(1, 8))

        with self.assertRaises(ShareValidationError):
            parse_fraction("invalid")

    def test_shares_validation_sum_to_one(self):
        """Verify strict sum = 1 validation."""
        # Valid: 1/2 + 1/4 + 1/4 = 1
        valid, float_map, str_map, msg = validate_shares({"p1": "1/2", "p2": "1/4", "p3": "1/4"})
        self.assertTrue(valid)
        self.assertEqual(float_map["p1"], 0.5)
        self.assertEqual(float_map["p2"], 0.25)

        # Invalid under-allocated: 1/3 + 1/3 = 2/3
        invalid_under, _, _, msg_under = validate_shares({"p1": "1/3", "p2": "1/3"})
        self.assertFalse(invalid_under)
        self.assertIn("कम है", msg_under)

        # Invalid over-allocated: 1/2 + 1/2 + 1/4 = 5/4
        invalid_over, _, _, msg_over = validate_shares({"p1": "1/2", "p2": "1/2", "p3": "1/4"})
        self.assertFalse(invalid_over)
        self.assertIn("अधिक है", msg_over)

    def test_hard_connectivity_check(self):
        """Verify is_connected detects single vs fragmented polygons."""
        single_poly = box(0, 0, 10, 10)
        self.assertTrue(is_connected(single_poly))

        # Disjoint multipolygon with 2 significant pieces
        multi_poly = MultiPolygon([box(0, 0, 5, 5), box(10, 10, 15, 15)])
        self.assertFalse(is_connected(multi_poly))

    def test_outward_normal_directions(self):
        """Verify outward normal calculation from centroid."""
        c_x, c_y = 50.0, 50.0
        self.assertEqual(outward_normal_direction(c_x, c_y, 50.0, 100.0), "उत्तर (North)")
        self.assertEqual(outward_normal_direction(c_x, c_y, 100.0, 50.0), "पूर्व (East)")
        self.assertEqual(outward_normal_direction(c_x, c_y, 50.0, 0.0), "दक्षिण (South)")
        self.assertEqual(outward_normal_direction(c_x, c_y, 0.0, 50.0), "पश्चिम (West)")

    def test_cpsat_reproducibility(self):
        """Verify that fixed seed produces identical deterministic partition plans."""
        plot = box(0, 0, 100, 100)
        parties = [
            Party("1", "राम", 0.5),
            Party("2", "श्याम", 0.5)
        ]

        lots1, meta1 = generate_plan(plot, parties, strategy="compact", seed=42)
        lots2, meta2 = generate_plan(plot, parties, strategy="compact", seed=42)

        self.assertAlmostEqual(lots1["1"].area, lots2["1"].area, places=4)
        self.assertAlmostEqual(lots1["2"].area, lots2["2"].area, places=4)
        self.assertEqual(lots1["1"].wkt, lots2["1"].wkt)
        self.assertEqual(meta1["seed"], meta2["seed"])

    def test_possession_overlap_percentage(self):
        """Verify overlap percentage calculation."""
        p1 = box(0, 0, 10, 10) # 100 sq m
        p2 = box(0, 0, 5, 10)  # 50 sq m, exact 100% of p2 inside p1
        self.assertEqual(overlap_percentage(p1, p2), 100.0)

        p3 = box(5, 0, 15, 10) # 100 sq m, 50 sq m overlap with p1
        self.assertEqual(overlap_percentage(p1, p3), 50.0)

        p4 = box(20, 20, 30, 30) # Disjoint
        self.assertEqual(overlap_percentage(p1, p4), 0.0)

    def test_tiered_audit_with_statutory_tags(self):
        """Verify Rule 109(5) evaluation across ordered tiers."""
        plot = box(0, 0, 100, 100)
        parties = [Party("1", "अमित", 0.5), Party("2", "सुमित", 0.5)]
        lots = {"1": box(0, 0, 50, 100), "2": box(50, 0, 100, 100)}

        results = evaluate(lots, parties, plot)
        self.assertTrue(len(results) >= 6)

        # Check tiers are represented
        tiers = {r.tier for r in results}
        self.assertIn(1, tiers)
        self.assertIn(2, tiers)
        self.assertIn(3, tiers)

        # Check statutory tags
        r_a = next(r for r in results if r.code == "a")
        self.assertEqual(r_a.legal_basis, "[statutory]")
        self.assertEqual(r_a.status, "green")
        self.assertIn("109(5)(क)", r_a.statutory_citation)

        r_g1 = next(r for r in results if r.code == "G1")
        self.assertIn("[heuristic", r_g1.legal_basis)
        self.assertEqual(r_g1.status, "green")

    def test_area_uncertainty_band(self):
        """Verify cartographic uncertainty band computation for 1:1698 scale."""
        poly = box(0, 0, 100, 100) # 10,000 sq m, perimeter 400 m
        u = compute_area_uncertainty(poly, scale_str="1:1698", paper_line_thickness_mm=0.25)

        # Linear ground error = (0.25 / 1000) * 1698 = 0.4245 m
        self.assertAlmostEqual(u.ground_linear_error_m, 0.425, places=2)
        # Delta area = 0.5 * 400 * 0.4245 ≈ 84.9 sq m
        self.assertAlmostEqual(u.delta_area_sqm, 84.9, delta=1.0)
        self.assertTrue(u.area_min_sqm < 10000.0 < u.area_max_sqm)


if __name__ == "__main__":
    unittest.main()
