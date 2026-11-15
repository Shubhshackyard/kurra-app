"""CLI interface for Cadastral Ingestion.

Usage:
  python -m kurra.ingest pull --district 165 --tehsil 00854 --village 151769 --plot 57
  python -m kurra.ingest pull --district 165 --tehsil 00854 --village 151769 --all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .crawler import IngestBlockedError, VillageCrawler
from .store import CadastreStore


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m kurra.ingest",
        description="Local-First Cadastral Data Store Ingestion CLI (Section 116 / Rule 109(5))"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: pull
    pull_parser = subparsers.add_parser("pull", help="Pull plot reports, vector geometry, and WMS tiles")
    pull_parser.add_argument("--district", "-d", default="165", help="LGD District Code (e.g. 165 for Jalaun)")
    pull_parser.add_argument("--tehsil", "-t", default="00854", help="LGD Tehsil Code (e.g. 00854 for Orai)")
    pull_parser.add_argument("--village", "-v", default="151769", help="LGD Village Code (e.g. 151769 for Ikhlashpura)")
    pull_parser.add_argument("--plot", "-p", help="Single plot number to pull (e.g. 57)")
    pull_parser.add_argument("--all", action="store_true", help="Pull all enumerated plots in the village")
    pull_parser.add_argument("--rate-limit", type=float, default=1.0, help="Base rate limit in seconds (default: 1.0)")
    pull_parser.add_argument("--force", action="store_true", help="Force re-download even if already in local store")

    # Subcommand: status
    status_parser = subparsers.add_parser("status", help="Inspect local SQLite database sync status")
    status_parser.add_argument("--district", "-d", default="165")
    status_parser.add_argument("--tehsil", "-t", default="00854")
    status_parser.add_argument("--village", "-v", default="151769")

    args = parser.parse_args(argv)

    if args.command == "status":
        store = CadastreStore(args.district, args.tehsil, args.village)
        st = store.get_sync_status()
        print("\n🏛️  LOCAL CADASTRE STORE STATUS")
        print("─────────────────────────────────────────────")
        print(f"GIS Code:           {st['gis_code']}")
        print(f"District/Tehsil:    {st['district']} / {st['tehsil']}")
        print(f"Village:            {st['village']}")
        print(f"Plots Cached:       {st['total_plots_cached']}")
        print(f"Last Sync Date:     {st['last_sync'] or 'Never'}")
        print(f"Offline Ready:      {'✅ YES' if st['is_offline_ready'] else '❌ NO'}")
        print("─────────────────────────────────────────────\n")
        return 0

    if args.command == "pull":
        if not args.plot and not args.all:
            print("Error: Specify either --plot <plot_no> or --all to crawl the village.", file=sys.stderr)
            return 1

        crawler = VillageCrawler(
            district=args.district,
            tehsil=args.tehsil,
            village=args.village,
            rate_limit_s=args.rate_limit
        )

        if args.plot:
            print(f"📡 Fetching Plot {args.plot} for Village {args.village} (Dist: {args.district}, Teh: {args.tehsil})...")
            try:
                rep = crawler.ingest_plot(args.plot, force=args.force)
                print("\n✅ PLOT INGESTION SUCCESSFUL")
                print("─────────────────────────────────────────────")
                print(f"गाटा / खसरा:        {rep.khasra_no}")
                print(f"स्थान:             {rep.district_name} > {rep.tehsil_name} > {rep.village_name}")
                print(f"कुल क्षेत्रफल:       {rep.total_area_ha} Ha ({rep.total_area_sqm} sq m)")
                print(f"मानचित्र पैमाना:    {rep.scale}")
                print(f"उप-गाटा (SubPlots): {len(rep.sub_plots)}")
                for sp in rep.sub_plots:
                    owner_names = ", ".join(o.name for o in sp.owners)
                    print(f"  • गाटा {sp.sub_plot_no} (खाता {sp.khata_no}): {sp.area_ha} Ha [{owner_names}]")
                print(f"चौहद्दी स्पर्श गाटा:  {len(rep.adjacencies)} adjacent parcels")
                for a in rep.adjacencies[:4]:
                    print(f"  • {a.side}: गाटा {a.plot_no} (स्पर्श लंबाई: {a.shared_length_m}m)")
                print(f"स्थानीय डेटाबेस:    {crawler.store.db_path}")
                print("─────────────────────────────────────────────\n")
            except IngestBlockedError as e:
                print(f"\n⚠️  INGESTION HALTED: Government portal blocked request ({e})", file=sys.stderr)
                return 2
            except Exception as e:
                print(f"\n❌ Error ingesting plot {args.plot}: {e}", file=sys.stderr)
                return 1

        elif args.all:
            plots = crawler.enumerate_village_plots()
            print(f"🌐 Commencing full sync for Village {args.village} ({len(plots)} plots discovered)...")

            def progress_cb(current, total, plot_no):
                pct = (current / total) * 100
                sys.stdout.write(f"\r[{current:3d}/{total:3d}] ({pct:5.1f}%) Processing Plot {plot_no:<6s} ... ")
                sys.stdout.flush()

            try:
                res = crawler.crawl_all(progress_cb=progress_cb, force=args.force)
                print("\n\n🎉 VILLAGE SYNC COMPLETE")
                print("─────────────────────────────────────────────")
                print(f"Total plots:        {res['total_plots']}")
                print(f"Newly ingested:     {res['success_count']}")
                print(f"Already cached:     {res['skipped_count']}")
                print(f"Failures:           {res['failure_count']}")
                if res['failure_count'] > 0:
                    print(f"Log of failures:    {crawler.failure_log_path}")
                print("─────────────────────────────────────────────\n")
            except IngestBlockedError as e:
                print(f"\n\n🛑 CRAWL STOPPED: {e}", file=sys.stderr)
                return 2
            except Exception as e:
                print(f"\n\n❌ Crawl interrupted: {e}", file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
