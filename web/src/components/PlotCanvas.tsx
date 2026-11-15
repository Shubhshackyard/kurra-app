"use client";

import React, { useMemo, useState, useRef } from "react";
import { ProposedLot } from "@/types/api";
import { PenTool, RotateCcw, Crosshair } from "lucide-react";

interface PlotCanvasProps {
  basePolygon?: any; // GeoJSON Polygon
  lots?: ProposedLot[];
  neighborFeatures?: any[];
  scaleStr?: string;
  width?: number | string;
  height?: number | string;
  showNeighbors?: boolean;
  enablePencil?: boolean;
  onCustomCutLine?: (line: number[][]) => void;
  lang?: "hi" | "en";
}

export function PlotCanvas({
  basePolygon,
  lots = [],
  neighborFeatures = [],
  scaleStr = "1:1698",
  height = 480,
  showNeighbors = true,
  enablePencil = false,
  onCustomCutLine,
  lang = "hi",
}: PlotCanvasProps) {
  const [pencilActive, setPencilActive] = useState<boolean>(enablePencil);
  const [dragStart, setDragStart] = useState<[number, number] | null>(null);
  const [dragCurrent, setDragCurrent] = useState<[number, number] | null>(null);
  const [drawnLine, setDrawnLine] = useState<[number, number][] | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  // Extract bounding box
  const { minX, maxY, widthM, heightM } = useMemo(() => {
    let coords: number[][] = [];
    if (basePolygon && basePolygon.coordinates) {
      coords = basePolygon.coordinates[0];
    } else if (lots.length > 0 && lots[0].geojson?.coordinates) {
      lots.forEach((l) => {
        if (l.geojson?.coordinates) {
          coords.push(...l.geojson.coordinates[0]);
        }
      });
    }

    if (coords.length === 0) {
      return { minX: 0, maxY: 100, widthM: 100, heightM: 100 };
    }

    const xs = coords.map((c) => c[0]);
    const ys = coords.map((c) => c[1]);
    const min_x = Math.min(...xs);
    const max_x = Math.max(...xs);
    const min_y = Math.min(...ys);
    const max_y = Math.max(...ys);

    const w = max_x - min_x || 50;
    const h = max_y - min_y || 50;
    const pad = Math.max(Math.max(w, h) * 0.25, 20);

    return {
      minX: min_x - pad,
      maxY: max_y + pad,
      widthM: max_x - min_x + 2 * pad,
      heightM: max_y - min_y + 2 * pad,
    };
  }, [basePolygon, lots]);

  // Convert UTM (x, y) to SVG (sx, sy)
  const toSvg = (x: number, y: number) => {
    const sx = ((x - minX) / widthM) * 800;
    const sy = ((maxY - y) / heightM) * 600; // Invert y for standard cartographic North up
    return [sx, sy];
  };

  // Convert SVG (sx, sy) back to UTM (x, y)
  const toUtm = (sx: number, sy: number) => {
    const x = minX + (sx / 800) * widthM;
    const y = maxY - (sy / 600) * heightM;
    return [x, y];
  };

  const coordsToSvgPath = (ring: number[][]) => {
    if (!ring || ring.length === 0) return "";
    return (
      ring
        .map((pt, i) => {
          const [sx, sy] = toSvg(pt[0], pt[1]);
          return `${i === 0 ? "M" : "L"} ${sx.toFixed(1)} ${sy.toFixed(1)}`;
        })
        .join(" ") + " Z"
    );
  };

  // Handle Mouse Events for Pencil Cut Line
  const getSvgCoordinates = (e: React.MouseEvent<SVGSVGElement>): [number, number] | null => {
    if (!svgRef.current) return null;
    const rect = svgRef.current.getBoundingClientRect();
    const sx = ((e.clientX - rect.left) / rect.width) * 800;
    const sy = ((e.clientY - rect.top) / rect.height) * 600;
    return [sx, sy];
  };

  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!pencilActive) return;
    const coords = getSvgCoordinates(e);
    if (coords) {
      setDragStart(coords);
      setDragCurrent(coords);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!pencilActive || !dragStart) return;
    const coords = getSvgCoordinates(e);
    if (coords) {
      setDragCurrent(coords);
    }
  };

  const handleMouseUp = () => {
    if (!pencilActive || !dragStart || !dragCurrent) return;
    const dist = Math.hypot(dragCurrent[0] - dragStart[0], dragCurrent[1] - dragStart[1]);
    if (dist > 15) {
      // Valid line drawn
      const utm1 = toUtm(dragStart[0], dragStart[1]);
      const utm2 = toUtm(dragCurrent[0], dragCurrent[1]);
      setDrawnLine([dragStart, dragCurrent]);
      if (onCustomCutLine) {
        onCustomCutLine([utm1, utm2]);
      }
    }
    setDragStart(null);
    setDragCurrent(null);
  };

  const handleClearLine = () => {
    setDrawnLine(null);
    setDragStart(null);
    setDragCurrent(null);
  };

  // Base polygon vertex markers
  const baseVertices = useMemo(() => {
    if (!basePolygon || !basePolygon.coordinates) return [];
    return basePolygon.coordinates[0].slice(0, -1);
  }, [basePolygon]);

  return (
    <div className="relative w-full overflow-hidden rounded-xl border border-court-200 bg-court-50 shadow-inner">
      {/* North Arrow & Scale Badge */}
      <div className="absolute left-3 top-3 z-10 flex flex-col items-center rounded-lg border border-court-200/80 bg-white/90 p-2 shadow-sm backdrop-blur-sm">
        <svg width="22" height="26" viewBox="0 0 24 28" className="text-slate-800">
          <path d="M12 2 L19 24 L12 19 L5 24 Z" fill="currentColor" />
          <path d="M12 2 L12 19 L5 24 Z" fill="#64748b" />
        </svg>
        <span className="mt-0.5 text-[9px] font-bold tracking-wider text-slate-700">
          {lang === "hi" ? "उ० (N)" : "N"}
        </span>
      </div>

      {/* Floating Toolbar: Pencil Tool & Reset */}
      <div className="absolute right-3 top-3 z-10 flex items-center gap-1.5 rounded-lg border border-court-200 bg-white/95 p-1 shadow-sm backdrop-blur-sm">
        <button
          onClick={() => setPencilActive(!pencilActive)}
          className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-bold transition ${
            pencilActive
              ? "bg-rose-600 text-white shadow-sm"
              : "text-court-700 hover:bg-court-100"
          }`}
          title={lang === "hi" ? "विभाजन रेखा खींचने हेतु पेंसिल सक्रिय करें" : "Toggle Pencil Cut Line Tool"}
        >
          <PenTool className="h-3.5 w-3.5" />
          <span>{pencilActive ? (lang === "hi" ? "पेंसिल सक्रिय" : "Pencil Active") : (lang === "hi" ? "पेंसिल टूल" : "Pencil Tool")}</span>
        </button>

        {drawnLine && (
          <button
            onClick={handleClearLine}
            className="inline-flex items-center rounded-md p-1 text-court-500 hover:bg-court-100 hover:text-court-900"
            title={lang === "hi" ? "खींची गई रेखा हटाएं" : "Clear Drawn Line"}
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Scale & Help Badge */}
      <div className="absolute bottom-3 left-3 z-10 flex items-center gap-2">
        <div className="rounded-md border border-court-200/80 bg-white/90 px-2.5 py-1 text-[11px] font-medium text-slate-700 shadow-sm backdrop-blur-sm">
          {lang === "hi" ? "पैमाना:" : "Scale:"} <span className="font-mono font-bold text-slate-900">{scaleStr}</span>
        </div>

        {pencilActive && (
          <div className="animate-pulse flex items-center gap-1.5 rounded-md border border-rose-300 bg-rose-50 px-2.5 py-1 text-[11px] font-semibold text-rose-800 shadow-sm">
            <Crosshair className="h-3 w-3 text-rose-600" />
            <span>
              {lang === "hi"
                ? "गाटा सीमा के आर-पार क्लिक करके विभाजन रेखा खींचें"
                : "Click and drag across parcel boundary to draw cut line"}
            </span>
          </div>
        )}
      </div>

      <svg
        ref={svgRef}
        viewBox="0 0 800 600"
        className={`w-full select-none ${pencilActive ? "cursor-crosshair" : "cursor-default"}`}
        style={{ height }}
        preserveAspectRatio="xMidYMid meet"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e2e8f0" strokeWidth="0.75" />
          </pattern>
        </defs>

        <rect width="800" height="600" fill="url(#grid)" />

        {/* 1. Surrounding Neighbor Parcels */}
        {showNeighbors &&
          neighborFeatures.map((ft, idx) => {
            if (!ft.geometry?.coordinates) return null;
            const pNo = ft.properties?.plot_no || "";
            const landClass = ft.properties?.land_class || "";
            const isPath = landClass.includes("मार्ग") || landClass.includes("रास्ता");
            const isWater = landClass.includes("तालाब") || landClass.includes("नाली");

            const fillColor = isPath
              ? "rgba(234, 88, 12, 0.12)"
              : isWater
              ? "rgba(2, 132, 199, 0.12)"
              : "rgba(148, 163, 184, 0.08)";
            const strokeColor = isPath ? "#ea580c" : isWater ? "#0284c7" : "#cbd5e1";

            const pathD = coordsToSvgPath(ft.geometry.coordinates[0]);

            return (
              <g key={`neigh-${idx}`} className="transition-opacity hover:opacity-80">
                <path d={pathD} fill={fillColor} stroke={strokeColor} strokeWidth="1.2" strokeDasharray={isPath ? "4 2" : undefined} />
                {ft.properties?.centroid && (
                  <text
                    x={toSvg(ft.properties.centroid[0], ft.properties.centroid[1])[0]}
                    y={toSvg(ft.properties.centroid[0], ft.properties.centroid[1])[1]}
                    fill={isPath ? "#c2410c" : "#64748b"}
                    fontSize="11"
                    fontWeight="500"
                    textAnchor="middle"
                    dominantBaseline="central"
                  >
                    {pNo}
                  </text>
                )}
              </g>
            );
          })}

        {/* 2. Base Surveyed Parcel (if no partition lots yet) */}
        {lots.length === 0 && basePolygon?.coordinates && (
          <g>
            <path
              d={coordsToSvgPath(basePolygon.coordinates[0])}
              fill="#fef08a"
              stroke="#ca8a04"
              strokeWidth="2.5"
              className="filter drop-shadow-sm"
            />
            {/* Auto-constructed boundary vertices */}
            {baseVertices.map((v: number[], vi: number) => {
              const [vx, vy] = toSvg(v[0], v[1]);
              return (
                <circle
                  key={`vtx-${vi}`}
                  cx={vx}
                  cy={vy}
                  r="4"
                  fill="#ffffff"
                  stroke="#854d0e"
                  strokeWidth="2"
                />
              );
            })}
          </g>
        )}

        {/* 3. Partition Lots */}
        {lots.map((lot, idx) => {
          if (!lot.geojson?.coordinates) return null;
          const pathD = coordsToSvgPath(lot.geojson.coordinates[0]);

          // Center for label
          const ring = lot.geojson.coordinates[0];
          const avgX = ring.reduce((acc: number, p: number[]) => acc + p[0], 0) / ring.length;
          const avgY = ring.reduce((acc: number, p: number[]) => acc + p[1], 0) / ring.length;
          const [lx, ly] = toSvg(avgX, avgY);

          return (
            <g key={`lot-${lot.party_id || idx}`} className="cursor-pointer transition-all hover:brightness-105">
              <path
                d={pathD}
                fill={lot.color_hex}
                fillOpacity="0.45"
                stroke={lot.color_hex}
                strokeWidth="2.5"
                className="filter drop-shadow-sm"
              />
              <circle cx={lx} cy={ly - 14} r="14" fill="#ffffff" stroke={lot.color_hex} strokeWidth="2" />
              <text x={lx} y={ly - 14} fill={lot.color_hex} fontSize="11" fontWeight="bold" textAnchor="middle" dominantBaseline="central">
                {idx + 1}
              </text>
              <text x={lx} y={ly + 8} fill="#0f172a" fontSize="11" fontWeight="bold" textAnchor="middle">
                {lot.party_name}
              </text>
              <text x={lx} y={ly + 22} fill="#334155" fontSize="10" fontFamily="monospace" textAnchor="middle">
                {lot.area_sqm} m² ({lot.share_str})
              </text>
            </g>
          );
        })}

        {/* 4. Active Drawn Cut Line (Live Mouse Dragging) */}
        {dragStart && dragCurrent && (
          <g>
            <line
              x1={dragStart[0]}
              y1={dragStart[1]}
              x2={dragCurrent[0]}
              y2={dragCurrent[1]}
              stroke="#e11d48"
              strokeWidth="3.5"
              strokeDasharray="6 4"
            />
            <circle cx={dragStart[0]} cy={dragStart[1]} r="6" fill="#e11d48" stroke="#ffffff" strokeWidth="2" />
            <circle cx={dragCurrent[0]} cy={dragCurrent[1]} r="6" fill="#e11d48" stroke="#ffffff" strokeWidth="2" />
          </g>
        )}

        {/* 5. Finished Custom Pencil Cut Line */}
        {drawnLine && (
          <g className="filter drop-shadow-md">
            <line
              x1={drawnLine[0][0]}
              y1={drawnLine[0][1]}
              x2={drawnLine[1][0]}
              y2={drawnLine[1][1]}
              stroke="#dc2626"
              strokeWidth="3.5"
              strokeDasharray="6 4"
            />
            <circle cx={drawnLine[0][0]} cy={drawnLine[0][1]} r="6" fill="#dc2626" stroke="#ffffff" strokeWidth="2" />
            <circle cx={drawnLine[1][0]} cy={drawnLine[1][1]} r="6" fill="#dc2626" stroke="#ffffff" strokeWidth="2" />
            <text
              x={(drawnLine[0][0] + drawnLine[1][0]) / 2}
              y={(drawnLine[0][1] + drawnLine[1][1]) / 2 - 8}
              fill="#991b1b"
              fontSize="11"
              fontWeight="bold"
              textAnchor="middle"
              className="bg-white px-1"
            >
              {lang === "hi" ? "हस्तनिर्मित विभाजन रेखा" : "Custom Cut Line"}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}
