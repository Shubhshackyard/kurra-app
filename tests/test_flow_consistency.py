"""Automated Flow Consistency & Statutory Integrity Tests.

Validates end-to-end data integrity across all stages of the SDM Kurra Dashboard:
1. Plot 57 (private co-sharers partitionable under Section 116 / Rule 109(5)).
2. Plot 7 (public utility 'तालाब' under Section 77 UP Revenue Code).
3. Plot 123 (large multi-sharer village parcel with cadastre adjacencies).
4. Custom Cut / Pencil Demarcation endpoint (/api/plans/custom-cut).
"""
import unittest
from shapely.geometry import Polygon

from kurra.ingest.store import CadastreStore
from kurra.fractions import validate_shares
from kurra.rules import evaluate
from kurra.optimizer import Party


class TestFlowConsistency(unittest.TestCase):
    def setUp(self):
        self.store = CadastreStore("165", "00854", "151769")

    def test_plot_57_private_partition_integrity(self):
        """Plot 57: ensure accurate co-sharers and non-empty adjacencies."""
        rep = self.store.get_plot("57")
        self.assertIsNotNone(rep)
        self.assertEqual(rep.khasra_no, "57")
        self.assertEqual(rep.total_area_ha, 0.373)
        self.assertEqual(rep.total_area_sqm, 3730.0)

        # Co-sharers in Khata 00087
        sp1 = next(sp for sp in rep.sub_plots if sp.khata_no == "00087")
        names = [o.name for o in sp1.owners]
        self.assertIn("जगदीश प्रसाद", names)
        self.assertIn("राजेश कुमार", names)
        self.assertIn("सत्यबीर सिंह", names)

        # Adjacencies must be populated
        self.assertTrue(len(rep.adjacencies) >= 4)
        adj_plots = [a.plot_no for a in rep.adjacencies]
        self.assertIn("56", adj_plots)
        self.assertIn("48", adj_plots)

    def test_plot_7_public_utility_no_cross_plot_leak(self):
        """Plot 7: public utility pond must NOT leak Plot 57 private owners."""
        rep = self.store.get_plot("7")
        self.assertIsNotNone(rep)
        self.assertEqual(rep.khasra_no, "7")
        self.assertEqual(rep.total_area_ha, 0.886)
        self.assertEqual(rep.total_area_sqm, 8860.0)

        # Owner must strictly be 'तालाब'
        all_owners = [o.name for sp in rep.sub_plots for o in sp.owners]
        self.assertIn("तालाब", all_owners)
        self.assertNotIn("जगदीश प्रसाद", all_owners)
        self.assertNotIn("राजेश कुमार", all_owners)

        # Adjacencies dynamically resolved from village cadastre
        self.assertTrue(len(rep.adjacencies) >= 3)
        adj_plots = [a.plot_no for a in rep.adjacencies]
        self.assertTrue("6" in adj_plots or "8" in adj_plots or "9" in adj_plots)

    def test_plot_123_cadastre_resolution(self):
        """Plot 123: multi-khata parcel with dynamic boundary adjacencies."""
        rep = self.store.get_plot("123")
        self.assertIsNotNone(rep)
        self.assertEqual(rep.khasra_no, "123")
        self.assertTrue(len(rep.adjacencies) >= 4)

    def test_custom_cut_evaluation_logic(self):
        """Verify rule evaluation logic on custom bisected geometries."""
        # Simple rectangular plot 100m x 40m = 4000 m²
        plot_poly = Polygon([(0, 0), (100, 0), (100, 40), (0, 40), (0, 0)])
        lot1 = Polygon([(0, 0), (50, 0), (50, 40), (0, 40), (0, 0)])
        lot2 = Polygon([(50, 0), (100, 0), (100, 40), (50, 40), (50, 0)])

        parties = [
            Party(id="P1", name="सह-खातेदार 1", share=0.5),
            Party(id="P2", name="सह-खातेदार 2", share=0.5),
        ]
        lots = {"P1": lot1, "P2": lot2}

        # Road along southern boundary (y=0)
        from shapely.geometry import LineString
        road_poly = LineString([(0, 0), (100, 0)]).buffer(2.0)

        results = evaluate(lots, parties, plot_poly, roads=road_poly)
        self.assertTrue(len(results) >= 7)

        # Check Rule 109(5)(a) proportion check
        t3_share = next(r for r in results if r.code == "a")
        self.assertEqual(t3_share.status, "green")

        # Check Rule 109(5)(f) road access check
        t3_road = next(r for r in results if r.code == "f")
        self.assertEqual(t3_road.status, "green")


if __name__ == "__main__":
    unittest.main()
