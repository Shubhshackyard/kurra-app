"""Interactive, scalable cadastral map of Village 151769 for UP Bhunaksha inspection.

Renders all 303 surveyed plots of गाँव 151769 इखलाशपुरा च0क्षे0 (तहसील: 00854 उरई, जिला: 165 जालौन)
with interactive pan/zoom, plot search, land classification colors, satellite imagery overlay,
and official ROR property inspector cards.
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA_DIR = HERE.parent / "data" / "jalaun_151769"
GEOJSON_WGS84 = DATA_DIR / "all_plots_151769_wgs84.geojson"


def generate_village_map_html(selected_plot: str = "12", height: int = 680) -> str:
    """Generate a high-performance Leaflet cadastral map HTML string for Village 151769."""
    geojson_data = {}
    if GEOJSON_WGS84.exists():
        with open(GEOJSON_WGS84, encoding="utf-8") as f:
            geojson_data = json.load(f)

    # Filter out bigger overlapping geometries without owner details
    if "features" in geojson_data:
        filtered = []
        for feat in geojson_data["features"]:
            props = feat.get("properties", {})
            owners = str(props.get("owners") or "").strip()
            khata = str(props.get("khata_no") or "").strip()
            has_owner = owners not in ["—", "-", "None", "", "null"]
            has_khata = khata not in ["N/A", "-", "None", "", "null"]

            # If feature has owner or khata, keep verified cadastral parcel
            if has_owner or has_khata:
                filtered.append(feat)
                continue

            # If without owner details, filter out bigger/overlapping bounding box geometries
            area = props.get("area_sqm") or (props.get("area_ha", 0) * 10000)
            is_exact = props.get("is_exact_polygon", True)
            if area > 2000 or not is_exact:
                continue
            filtered.append(feat)
        geojson_data["features"] = filtered

    geojson_str = json.dumps(geojson_data, ensure_ascii=False)


    html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ग्राम 151769 इखलाशपुरा च0क्षे0 - भू-नक्शा</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      height: 100%;
      width: 100%;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #f8fafc;
      overflow: hidden;
    }}
    #map {{
      height: {height}px;
      width: 100%;
      background: #ffffff;
    }}
    /* Top Bar Controls */
    .top-controls {{
      position: absolute;
      top: 12px;
      left: 60px;
      z-index: 1000;
      display: flex;
      gap: 8px;
      align-items: center;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(8px);
      padding: 6px 12px;
      border-radius: 8px;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.15);
      border: 1px solid #cbd5e1;
    }}
    .search-input {{
      padding: 6px 10px;
      border: 1px solid #94a3b8;
      border-radius: 6px;
      font-size: 13px;
      width: 130px;
      outline: none;
      font-weight: 500;
    }}
    .search-input:focus {{
      border-color: #2563eb;
      box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
    }}
    .btn {{
      padding: 6px 12px;
      background: #2563eb;
      color: #ffffff;
      border: none;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: background 0.15s ease;
    }}
    .btn:hover {{
      background: #1d4ed8;
    }}
    .btn-secondary {{
      background: #f1f5f9;
      color: #334155;
      border: 1px solid #cbd5e1;
    }}
    .btn-secondary:hover {{
      background: #e2e8f0;
    }}
    /* Plot Centroid Labels */
    .plot-label {{
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid #94a3b8;
      border-radius: 3px;
      padding: 1px 4px;
      font-size: 10px;
      font-weight: 700;
      color: #1e293b;
      white-space: nowrap;
      box-shadow: 0 1px 2px rgba(0,0,0,0.1);
      pointer-events: none;
      text-align: center;
    }}
    .plot-label-selected {{
      background: #facc15;
      color: #0f172a;
      border: 1.5px solid #1e3a8a;
      font-size: 11px;
      font-weight: 800;
      box-shadow: 0 2px 4px rgba(0,0,0,0.25);
    }}
    /* HUD Info Card */
    .info-hud {{
      position: absolute;
      bottom: 20px;
      right: 20px;
      z-index: 1000;
      width: 320px;
      background: rgba(255, 255, 255, 0.98);
      backdrop-filter: blur(10px);
      border-radius: 10px;
      padding: 14px 16px;
      box-shadow: 0 10px 25px rgba(15, 23, 42, 0.2);
      border: 1px solid #cbd5e1;
      font-size: 12px;
      line-height: 1.45;
      color: #1e293b;
    }}
    .info-hud h4 {{
      margin: 0 0 8px 0;
      font-size: 15px;
      font-weight: 700;
      color: #1e3a8a;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 6px;
    }}
    .hud-badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
    }}
    .hud-row {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 5px;
    }}
    .hud-label {{
      color: #64748b;
      font-weight: 500;
    }}
    .hud-value {{
      font-weight: 600;
      color: #0f172a;
      text-align: right;
    }}
    .legend-box {{
      position: absolute;
      bottom: 20px;
      left: 20px;
      z-index: 1000;
      background: rgba(255, 255, 255, 0.95);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 11px;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
      border: 1px solid #cbd5e1;
      line-height: 1.5;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 3px;
    }}
    .legend-swatch {{
      width: 14px;
      height: 10px;
      border-radius: 2px;
      border: 1px solid rgba(0,0,0,0.2);
    }}
    /* Pulse animation for selected parcel */
    @keyframes pulse-border {{
      0% {{ stroke-opacity: 1; stroke-width: 3.5; }}
      50% {{ stroke-opacity: 0.5; stroke-width: 5; }}
      100% {{ stroke-opacity: 1; stroke-width: 3.5; }}
    }}
    .active-parcel-pulse {{
      animation: pulse-border 2s infinite ease-in-out;
    }}
  </style>
</head>
<body>
  <div id="map"></div>

  <!-- Top Search & Zoom Controls -->
  <div class="top-controls">
    <span style="font-weight: 700; color: #1e3a8a; font-size: 13px;">गाँव: 151769</span>
    <input type="text" id="plotSearchInput" class="search-input" placeholder="गाटा संख्या (उदा. 12)" value="{selected_plot}" />
    <button class="btn" onclick="searchPlot()">🔍 खोजें</button>
    <button class="btn btn-secondary" onclick="fitVillage()">🏠 पूरा गाँव</button>
    <label style="font-size: 12px; color: #475569; display: flex; align-items: center; gap: 4px; margin-left: 6px; cursor: pointer;">
      <input type="checkbox" id="toggleLabels" checked onchange="togglePlotLabels(this.checked)" /> गाटा सं.
    </label>
  </div>

  <!-- Legend -->
  <div class="legend-box">
    <div style="font-weight: 700; margin-bottom: 5px; color: #0f172a;">भूमि वर्गीकरण (संकेतिका)</div>
    <div class="legend-item"><div class="legend-swatch" style="background: #facc15; border-color: #1e3a8a;"></div><b>चयनित गाटा (Active)</b></div>
    <div class="legend-item"><div class="legend-swatch" style="background: #ea580c;"></div>चक मार्ग (Field Path)</div>
    <div class="legend-item"><div class="legend-swatch" style="background: #dc2626;"></div>रास्ता / सड़क (Road)</div>
    <div class="legend-item"><div class="legend-swatch" style="background: #0284c7;"></div>नाली (Drainage Channel)</div>
    <div class="legend-item"><div class="legend-swatch" style="background: #2563eb;"></div>तालाब (Water Reservoir)</div>
    <div class="legend-item"><div class="legend-swatch" style="background: #9333ea;"></div>बंजर / नवीन परती (Govt)</div>
    <div class="legend-item"><div class="legend-swatch" style="background: #16a34a;"></div>कृषि (Agricultural)</div>
  </div>

  <!-- HUD Property Inspector -->
  <div class="info-hud" id="infoHud">
    <h4>
      <span>गाटा संख्या: <span id="hudPlotNo">{selected_plot}</span></span>
      <span class="hud-badge" id="hudBadge" style="background: #fef08a; color: #854d0e;">चयनित</span>
    </h4>
    <div class="hud-row"><span class="hud-label">भूमि श्रेणी:</span><span class="hud-value" id="hudClass">—</span></div>
    <div class="hud-row"><span class="hud-label">अभिलेखीय क्षेत्रफल:</span><span class="hud-value" id="hudAreaHa">—</span></div>
    <div class="hud-row"><span class="hud-label">नक्शा क्षेत्रफल:</span><span class="hud-value" id="hudAreaSqm">—</span></div>
    <div class="hud-row"><span class="hud-label">खाता संख्या:</span><span class="hud-value" id="hudKhata">—</span></div>
    <div class="hud-row" style="flex-direction: column; gap: 2px;">
      <span class="hud-label">खातेदार:</span>
      <span class="hud-value" id="hudOwners" style="text-align: left; font-size: 11px; color: #334155; line-height: 1.3;">—</span>
    </div>
    <div style="margin-top: 8px; font-size: 10px; color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 4px;">
      जिला: 165 जालौन · तहसील: 00854 उरई · गाँव: 151769 इखलाशपुरा
    </div>
  </div>

  <script>
    const villageData = {geojson_str};
    let currentSelectedPlot = "{selected_plot}";
    let plotLayers = {{}};
    let labelMarkers = [];
    let labelsGroup = L.layerGroup();

    // 1. Initialize Map centered on Village 151769
    const map = L.map('map', {{
      center: [25.992202, 79.474945],
      zoom: 15,
      zoomControl: true,
      maxZoom: 21,
      minZoom: 13
    }});

    // 2. Basemaps
    const cadastralSheet = L.tileLayer('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=', {{
      attribution: 'UP Bhunaksha Cadastral Survey Sheet'
    }});

    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }});

    const osm = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }});

    // Default to clean Cadastral sheet with white background
    cadastralSheet.addTo(map);

    const baseMaps = {{
      "सफेद राजस्व नक्शा (Cadastre)": cadastralSheet,
      "उपग्रह चित्र (Satellite)": satellite,
      "सड़क नक्शा (OSM)": osm
    }};

    L.control.layers(baseMaps, {{ "गाटा संख्या लेबल्स": labelsGroup }}, {{ position: 'topright' }}).addTo(map);
    labelsGroup.addTo(map);

    // 3. Cadastral Styling Function
    function getPlotStyle(feature) {{
      const pNo = String(feature.properties.plot_no || "");
      const isSelected = (pNo === currentSelectedPlot);
      const lc = feature.properties.land_class || "";

      if (isSelected) {{
        return {{
          fillColor: "#facc15",
          fillOpacity: 0.85,
          color: "#1e3a8a",
          weight: 3.5,
          opacity: 1.0,
          className: "active-parcel-pulse"
        }};
      }}

      if (lc.includes("चक मार्ग")) {{
        return {{ fillColor: "#ea580c", fillOpacity: 0.35, color: "#ea580c", weight: 1.8, opacity: 0.95 }};
      }} else if (lc.includes("रास्ता") || lc.includes("सड़क")) {{
        return {{ fillColor: "#dc2626", fillOpacity: 0.35, color: "#dc2626", weight: 2.0, opacity: 0.95 }};
      }} else if (lc.includes("नाली")) {{
        return {{ fillColor: "#0284c7", fillOpacity: 0.35, color: "#0284c7", weight: 1.8, opacity: 0.95 }};
      }} else if (lc.includes("तालाब")) {{
        return {{ fillColor: "#2563eb", fillOpacity: 0.40, color: "#1d4ed8", weight: 1.8, opacity: 0.95 }};
      }} else if (lc.includes("बंजर") || lc.includes("परती")) {{
        return {{ fillColor: "#9333ea", fillOpacity: 0.25, color: "#7e22ce", weight: 1.4, opacity: 0.85 }};
      }} else if (lc.includes("आबादी")) {{
        return {{ fillColor: "#b45309", fillOpacity: 0.30, color: "#92400e", weight: 1.4, opacity: 0.85 }};
      }} else {{
        return {{ fillColor: "#22c55e", fillOpacity: 0.12, color: "#475569", weight: 1.2, opacity: 0.8 }};
      }}
    }}

    // 4. Update HUD Card
    function updateHud(props) {{
      document.getElementById('hudPlotNo').innerText = props.plot_no || "—";
      document.getElementById('hudClass').innerText = props.land_class || "कृषि";
      document.getElementById('hudAreaHa').innerText = (props.area_ha ? props.area_ha.toFixed(4) + " हे. (" + Math.round(props.area_sqm || props.area_ha*10000) + " मी²)" : "—");
      document.getElementById('hudAreaSqm').innerText = (props.map_area_sqm ? props.map_area_sqm.toLocaleString() + " वर्ग मीटर" : "—");
      document.getElementById('hudKhata').innerText = props.khata_no || "N/A";
      document.getElementById('hudOwners').innerText = props.owners || "—";

      const badge = document.getElementById('hudBadge');
      if (String(props.plot_no) === currentSelectedPlot) {{
        badge.innerText = "चयनित (Active)";
        badge.style.background = "#fef08a";
        badge.style.color = "#854d0e";
      }} else {{
        badge.innerText = props.is_exact_polygon ? "सत्यापित" : "सीमा बॉक्स";
        badge.style.background = "#e2e8f0";
        badge.style.color = "#475569";
      }}
    }}

    // 5. Select Plot
    function selectPlot(pNo, zoomTo = true) {{
      const oldPlot = currentSelectedPlot;
      currentSelectedPlot = String(pNo);

      if (oldPlot && plotLayers[oldPlot]) {{
        plotLayers[oldPlot].setStyle(getPlotStyle(plotLayers[oldPlot].feature));
      }}

      if (plotLayers[currentSelectedPlot]) {{
        const targetLayer = plotLayers[currentSelectedPlot];
        targetLayer.setStyle(getPlotStyle(targetLayer.feature));
        targetLayer.bringToFront();
        updateHud(targetLayer.feature.properties);

        if (zoomTo) {{
          map.fitBounds(targetLayer.getBounds(), {{ padding: [60, 60], maxZoom: 18, animate: true }});
        }}
      }}
      document.getElementById('plotSearchInput').value = currentSelectedPlot;
    }}

    // 6. Add Cadastral Features
    let geojsonLayer = L.geoJSON(villageData, {{
      style: getPlotStyle,
      onEachFeature: function(feature, layer) {{
        const pNo = String(feature.properties.plot_no || "");
        plotLayers[pNo] = layer;

        // Tooltip
        layer.bindTooltip(
          `<b>गाटा ${{pNo}}</b><br>${{feature.properties.land_class}}<br>${{feature.properties.area_sqm || ''}} m²`,
          {{ sticky: true, opacity: 0.95 }}
        );

        // Click Handler
        layer.on('click', function(e) {{
          selectPlot(pNo, false);
        }});

        layer.on('mouseover', function(e) {{
          if (pNo !== currentSelectedPlot) {{
            layer.setStyle({{ weight: 2.5, color: "#1e3a8a", fillOpacity: 0.4 }});
          }}
          updateHud(feature.properties);
        }});

        layer.on('mouseout', function(e) {{
          if (pNo !== currentSelectedPlot) {{
            geojsonLayer.resetStyle(layer);
          }}
          if (plotLayers[currentSelectedPlot]) {{
            updateHud(plotLayers[currentSelectedPlot].feature.properties);
          }}
        }});

        // Centroid Label Marker
        if (layer.getBounds) {{
          const center = layer.getBounds().getCenter();
          const isSel = (pNo === currentSelectedPlot);
          const icon = L.divIcon({{
            className: isSel ? 'plot-label plot-label-selected' : 'plot-label',
            html: pNo,
            iconSize: [26, 16],
            iconAnchor: [13, 8]
          }});
          const marker = L.marker(center, {{ icon: icon, interactive: false }});
          labelsGroup.addLayer(marker);
          labelMarkers.push({{ plotNo: pNo, marker: marker }});
        }}
      }}
    }}).addTo(map);

    // Initial Zoom to selected plot or village
    if (currentSelectedPlot && plotLayers[currentSelectedPlot]) {{
      selectPlot(currentSelectedPlot, true);
    }} else if (geojsonLayer.getLayers().length > 0) {{
      map.fitBounds(geojsonLayer.getBounds(), {{ padding: [20, 20] }});
    }}

    // 7. Search Handler
    function searchPlot() {{
      const val = document.getElementById('plotSearchInput').value.trim();
      if (!val) return;
      if (plotLayers[val]) {{
        selectPlot(val, true);
      }} else {{
        alert("गाटा संख्या " + val + " गाँव 151769 के वैध भू-अभिलेख में उपलब्ध नहीं है (अमान्य / बिना खातेदार का अतिव्यापी गाटा प्रदर्शित नहीं किया गया है)।");
      }}
    }}

    document.getElementById('plotSearchInput').addEventListener('keydown', function(e) {{
      if (e.key === 'Enter') {{
        searchPlot();
      }}
    }});

    function fitVillage() {{
      map.fitBounds(geojsonLayer.getBounds(), {{ padding: [20, 20], animate: true }});
    }}

    function togglePlotLabels(show) {{
      if (show) {{
        map.addLayer(labelsGroup);
      }} else {{
        map.removeLayer(labelsGroup);
      }}
    }}
  </script>
</body>
</html>
"""
    return html
