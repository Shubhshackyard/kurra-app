"""Unit Tests for Plot Report Parser & Local Cadastre Store (Phase 1).

Validates against the verified fixture values from the user's sample screenshot
for Plot 57 in Village 151769 (Ikhlashpura, Orai, Jalaun).
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from shapely.geometry import Polygon, box

from kurra.bhunaksha import BhunakshaClient
from kurra.ingest.store import CadastreStore
from kurra.report_parser import (
    AdjacentNeighbor,
    OwnerRecord,
    PlotReportData,
    SubPlotRecord,
    build_plot_report,
    compute_adjacency,
    outward_normal_direction,
    parse_header_attribution,
    parse_plot_info_text,
)

HERE = Path(__file__).parent
FIXTURE_IMAGE = HERE / "fixtures" / "plotreport_57_fixture.jpg"

# Exact text output fixture from UP Bhunaksha matching the user screenshot
SAMPLE_HEADER_TEXT = "जिला : 165 जालौन, तहसील : 00854 उरई, गाँव : 151769 इखलाशपुरा च0क्षे0"

SAMPLE_PLOT_INFO_TEXT = """Khata No: 00087   Plot No: 57/2    Area : 0.134000 Hectare
Khata No: 00146   Plot No: 57/1    Area : 0.239000 Hectare


Owner Details For Khata No.:- 00087
1 :-  नाम :   जगदीश प्रसाद     संरक्षक का नाम : राम रतन     निवास स्थान : नि.ग्राम
2 :-  नाम :   राजेश कुमार     संरक्षक का नाम : कुंवर सिंह     निवास स्थान : नि.ग्राम
3 :-  नाम :   सत्यबीर सिंह     संरक्षक का नाम : रंजीत सिंह     निवास स्थान : नि.ग्राम
Owner Details For Khata No.:- 00146
1 :-  नाम :   बंजर     संरक्षक का नाम : ---     निवास स्थान : नि.ग्राम
"""


class TestPlotReport(unittest.TestCase):
    def test_fixture_image_exists(self):
        """Verify that the test fixture image is present at root and in fixtures."""
        root_fixture = HERE.parent / "plotreport_sample.jpg"
        self.assertTrue(root_fixture.exists(), "plotreport_sample.jpg missing at project root")
        self.assertTrue(FIXTURE_IMAGE.exists(), "plotreport_57_fixture.jpg missing in tests/fixtures")

    def test_parse_header_attribution(self):
        """Verify extraction of administrative codes and Hindi names from header."""
        res = parse_header_attribution(SAMPLE_HEADER_TEXT)
        self.assertEqual(res["district_code"], "165")
        self.assertEqual(res["district_name"], "जालौन")
        self.assertEqual(res["tehsil_code"], "00854")
        self.assertEqual(res["tehsil_name"], "उरई")
        self.assertEqual(res["village_code"], "151769")
        self.assertEqual(res["village_name"], "इखलाशपुरा च0क्षे0")

    def test_parse_plot_info_hierarchy(self):
        """Verify sub-plot breakdown and owner details per Khata."""
        sub_plots = parse_plot_info_text(SAMPLE_PLOT_INFO_TEXT, base_plot_no="57")
        self.assertEqual(len(sub_plots), 2)

        # Sub-plot 1 (Khata 00087)
        sp1 = next(sp for sp in sub_plots if sp.khata_no == "00087")
        self.assertEqual(sp1.sub_plot_no, "57/2")
        self.assertEqual(sp1.sub_div, "2")
        self.assertEqual(sp1.area_ha, 0.134000)
        self.assertEqual(sp1.area_sqm, 1340.0)
        self.assertEqual(len(sp1.owners), 3)
        self.assertEqual(sp1.owners[0].name, "जगदीश प्रसाद")
        self.assertEqual(sp1.owners[0].guardian, "राम रतन")
        self.assertEqual(sp1.owners[0].residence, "नि.ग्राम")
        self.assertEqual(sp1.owners[1].name, "राजेश कुमार")
        self.assertEqual(sp1.owners[1].guardian, "कुंवर सिंह")
        self.assertEqual(sp1.owners[2].name, "सत्यबीर सिंह")
        self.assertEqual(sp1.owners[2].guardian, "रंजीत सिंह")

        # Sub-plot 2 (Khata 00146)
        sp2 = next(sp for sp in sub_plots if sp.khata_no == "00146")
        self.assertEqual(sp2.sub_plot_no, "57/1")
        self.assertEqual(sp2.sub_div, "1")
        self.assertEqual(sp2.area_ha, 0.239000)
        self.assertEqual(sp2.area_sqm, 2390.0)
        self.assertEqual(len(sp2.owners), 1)
        self.assertEqual(sp2.owners[0].name, "बंजर")
        self.assertIsNone(sp2.owners[0].guardian)  # '---' correctly normalized to None
        self.assertEqual(sp2.owners[0].residence, "नि.ग्राम")

    def test_build_plot_report_reproduction(self):
        """Test full report building reproducing fixture values."""
        rep = build_plot_report(
            district_code="165",
            district_name="जालौन",
            tehsil_code="00854",
            tehsil_name="उरई",
            village_code="151769",
            village_name="इखलाशपुरा च0क्षे0",
            plot_no="57",
            scale="1:1698",
            raw_plot_info=SAMPLE_PLOT_INFO_TEXT,
            raw_header=SAMPLE_HEADER_TEXT
        )

        self.assertEqual(rep.khasra_no, "57")
        self.assertEqual(rep.scale, "1:1698")
        self.assertEqual(rep.total_area_ha, 0.373)
        self.assertEqual(rep.total_area_sqm, 3730.0)
        self.assertEqual(len(rep.sub_plots), 2)
        self.assertTrue(bool(rep.sha256))

    def test_outward_normal_direction(self):
        """Verify outward normal direction classification."""
        self.assertEqual(outward_normal_direction(100, 100, 100, 150), "उत्तर (North)")
        self.assertEqual(outward_normal_direction(100, 100, 150, 100), "पूर्व (East)")
        self.assertEqual(outward_normal_direction(100, 100, 100, 50), "दक्षिण (South)")
        self.assertEqual(outward_normal_direction(100, 100, 50, 100), "पश्चिम (West)")
        self.assertEqual(outward_normal_direction(100, 100, 140, 140), "उत्तर-पूर्व (North-East)")

    def test_compute_adjacency(self):
        """Verify adjacency computation for touching parcels and corner touches."""
        target = box(0, 0, 10, 10)
        n_north = {
            "properties": {"plot_no": "56", "land_class": "कृषि"},
            "geometry": box(0, 10, 10, 20).__geo_interface__
        }
        n_east = {
            "properties": {"plot_no": "48", "land_class": "कृषि"},
            "geometry": box(10, 0, 20, 10).__geo_interface__
        }
        n_corner = {
            "properties": {"plot_no": "47", "land_class": "बंजर"},
            "geometry": box(10.5, 10.5, 20, 20).__geo_interface__
        }

        adjs = compute_adjacency(target, [n_north, n_east, n_corner], target_plot_no="57")
        p_nos = [a.plot_no for a in adjs]
        self.assertIn("56", p_nos)
        self.assertIn("48", p_nos)
        self.assertIn("47", p_nos)

        adj_north = next(a for a in adjs if a.plot_no == "56")
        self.assertEqual(adj_north.touches_type, "shared_edge")
        self.assertEqual(adj_north.shared_length_m, 10.0)
        self.assertIn("उत्तर", adj_north.side)

        adj_corner = next(a for a in adjs if a.plot_no == "47")
        self.assertEqual(adj_corner.touches_type, "corner_touch")

    def test_sqlite_store_roundtrip(self):
        """Verify that CadastreStore persists and retrieves plot data with full fidelity."""
        tmp_dir = Path(tempfile.mkdtemp())
        try:
            store = CadastreStore("165", "00854", "151769", base_data_dir=tmp_dir)
            poly = box(534000, 2873000, 534050, 2873050)

            rep = build_plot_report(
                district_code="165",
                district_name="जालौन",
                tehsil_code="00854",
                tehsil_name="उरई",
                village_code="151769",
                village_name="इखलाशपुरा च0क्षे0",
                plot_no="57",
                scale="1:1698",
                raw_plot_info=SAMPLE_PLOT_INFO_TEXT,
                raw_header=SAMPLE_HEADER_TEXT,
                target_poly=poly
            )

            store.save_plot_report(rep, polygon=poly)

            # Verify retrieval
            loaded = store.get_plot("57")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.khasra_no, "57")
            self.assertEqual(loaded.total_area_ha, 0.373)
            self.assertEqual(len(loaded.sub_plots), 2)

            # Verify geometry retrieval
            geom_res = store.get_plot_geometry("57")
            self.assertIsNotNone(geom_res)
            ret_poly, meta = geom_res
            self.assertAlmostEqual(ret_poly.area, poly.area, places=3)

            # Verify sync status
            st = store.get_sync_status()
            self.assertEqual(st["total_plots_cached"], 1)
            self.assertTrue(st["is_offline_ready"])
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_get_plot_runtime_variable(self):
        """Verify that BhunakshaClient.get_plot accepts runtime variables."""
        client = BhunakshaClient()
        rep = client.get_plot(district="165", tehsil="00854", village="151769", plot="57")
        self.assertEqual(rep.khasra_no, "57")
        self.assertEqual(rep.district_code, "165")
        self.assertEqual(rep.tehsil_code, "00854")
        self.assertEqual(rep.village_code, "151769")
        self.assertGreaterEqual(len(rep.sub_plots), 1)


if __name__ == "__main__":
    unittest.main()

