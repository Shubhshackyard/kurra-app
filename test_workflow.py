"""Command-line runner for the 3-Step Intelligent Cadastral Workflow.

Usage:
    python3 test_workflow.py <GIS_CODE> <PLOT_NO>
Example:
    python3 test_workflow.py 16500854151769 181
    python3 test_workflow.py 16500854151769 2
"""
import sys
import json
from kurra.workflow import CadastralWorkflow

def run_workflow(gis_code: str = "16500854151769", plot_no: str = "181"):
    print("=" * 80)
    print(f"🚀 INITIATING INTELLIGENT CADASTRAL WORKFLOW (GIS: {gis_code} | गाटा: {plot_no})")
    print("=" * 80)

    wf = CadastralWorkflow(gis_code=gis_code, plot_no=plot_no)

    # -------------------------------------------------------------------------
    # STEP 1: Ingestion (WMS PNGs + Plot Owner Details)
    # -------------------------------------------------------------------------
    print("\n[STEP 1/3] 📥 Ingestion: Fetching Ultra-HD WMS Tiles & Owner ROR...")
    assets = wf.fetch_plot_assets(dpi=300)
    print(f"  • Plot Number:        {assets['plot_no']}")
    print(f"  • Village GIS Code:   {assets['gis_code']}")
    print(f"  • Official Plot UUID: {assets['plot_id']}")
    print(f"  • Khata Number:       {assets['khata_no']}")
    print(f"  • Khatauni Area:      {assets['record_area_ha']} Ha ({assets['record_area_sqm']:,.1f} m²)")
    print(f"  • Co-Sharers ({len(assets['owners'])}):   {', '.join(assets['owners'])}")
    print(f"  • Isolated Plot WMS:  {assets['isolated_wms_image']}")
    print(f"  • Bird's Eye WMS:     {assets['birdseye_wms_image']}")

    # -------------------------------------------------------------------------
    # STEP 2: Directional Dimensions, Area Reconciliation & Surroundings
    # -------------------------------------------------------------------------
    print("\n[STEP 2/3] 📐 Cadastral Analysis: Directional Dimensions & Surroundings...")
    analysis = wf.analyze_plot()
    dims = analysis["directional_dimensions"]
    print("  • Directional Boundary Lengths:")
    print(f"      ⬆️  उत्तर सीमा (North):  {dims['north_boundary_length_meters']:>8.2f} m")
    print(f"      ⬇️  दक्षिण सीमा (South):  {dims['south_boundary_length_meters']:>8.2f} m")
    print(f"      ➡️  पूर्व सीमा (East):   {dims['east_boundary_length_meters']:>8.2f} m")
    print(f"      ⬅️  पश्चिम सीमा (West):   {dims['west_boundary_length_meters']:>8.2f} m")
    print(f"  • Bounding Dimensions:      {dims['bbox_width_ew_meters']} m (E-W) × {dims['bbox_height_ns_meters']} m (N-S)")
    print(f"  • Aspect Ratio:             {dims['aspect_ratio']} : 1 ({dims['orientation']})")

    recon = analysis["area_reconciliation"]
    print("  • Area Reconciliation:")
    print(f"      - Khatauni Record Area: {recon['khatauni_record_area_sqm']:,.1f} m²")
    print(f"      - Surveyed Map Area:    {recon['surveyed_map_area_sqm']:,.1f} m²")
    print(f"      - Variance:             {recon['area_difference_sqm']:+,.1f} m² ({recon['area_difference_percent']:+.2f}%)")
    print(f"      - Reconciliation Status: {recon['status']}")

    surr = analysis["surroundings"]
    print("  • Surroundings & Adjacent Parcels:")
    print(f"      - North: {', '.join(surr['North']) if surr['North'] else 'खुला क्षेत्र'}")
    print(f"      - South: {', '.join(surr['South']) if surr['South'] else 'खुला क्षेत्र'}")
    print(f"      - East:  {', '.join(surr['East']) if surr['East'] else 'खुला क्षेत्र'}")
    print(f"      - West:  {', '.join(surr['West']) if surr['West'] else 'खुला क्षेत्र'}")
    if analysis["touching_pathways"]:
        print(f"  • Touching Pathways/Roads:  {', '.join(analysis['touching_pathways'])}")

    # -------------------------------------------------------------------------
    # STEP 3: Statutory Partition Proposals (UP Revenue Code Rule 109(5))
    # -------------------------------------------------------------------------
    print("\n[STEP 3/3] ⚖️ Statutory Partition: Generating Rule 109(5) Options...")
    options = wf.suggest_partition_options()
    for idx, opt in enumerate(options, 1):
        print(f"\n  --- {opt['title']} ---")
        print(f"  विवरण: {opt['description']}")
        print("  Allotments:")
        for a in opt["allotments"]:
            print(f"    • {a['owner_name']:<22} | Share: {a['share_percent']:>6} | Area: {a['allotted_area_sqm']:>10,.1f} m² | Road Access: {a['touches_road']}")
        
        passed_rules = [r['rule_code'] for r in opt['statutory_compliance_audit'] if r['status'] == 'GREEN']
        flagged_rules = [f"{r['rule_code']} ({r['status']})" for r in opt['statutory_compliance_audit'] if r['status'] != 'GREEN' and r['status'] != 'NA']
        print(f"  Audit Scorecard: Passed Rules ({len(passed_rules)}): {', '.join(passed_rules)}")
        if flagged_rules:
            print(f"  Flagged Constraints: {', '.join(flagged_rules)}")

    print("\n" + "=" * 80)
    print("✅ CADASTRAL WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    g_code = sys.argv[1] if len(sys.argv) > 1 else "16500854151769"
    p_no = sys.argv[2] if len(sys.argv) > 2 else "181"
    run_workflow(g_code, p_no)
