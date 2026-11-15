import csv
from concurrent.futures import ThreadPoolExecutor
import requests

GIS_CODE = "16500854151769"
API_URL = "https://upbhunaksha.gov.in/bhunakshaserver/MapInfo/getPlotByPlotNo"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://upbhunaksha.gov.in/home"
}

def fetch_plot_uuid(plot_no: int):
    try:
        resp = requests.post(
            API_URL,
            data={"giscode": GIS_CODE, "plotno": str(plot_no)},
            headers=HEADERS,
            timeout=8
        )
        if resp.status_code == 200 and resp.text != "{}":
            d = resp.json()
            return {
                "plot_no": str(plot_no),
                "plot_id": d.get("id"),
                "minx": d.get("minx"),
                "miny": d.get("miny"),
                "maxx": d.get("maxx"),
                "maxy": d.get("maxy")
            }
    except Exception:
        pass
    return None

# Fetch all plots 1 through 310 concurrently
print("Fetching Plot UUIDs for Village 16500854151769...")
plots_to_check = range(1, 311)
results = []

with ThreadPoolExecutor(max_workers=10) as executor:
    for res in executor.map(fetch_plot_uuid, plots_to_check):
        if res and res["plot_id"]:
            results.append(res)

results.sort(key=lambda r: int(r["plot_no"]))

# Save to CSV
with open("data/jalaun_151769_plot_uuids.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["plot_no", "plot_id", "minx", "miny", "maxx", "maxy"])
    writer.writeheader()
    writer.writerows(results)

print(f"✅ Successfully exported {len(results)} plot UUIDs to data/jalaun_151769_plot_uuids.csv")