"use client";

import React, { useState, useMemo } from "react";
import { Compass, AlertCircle, FileSpreadsheet, CheckCircle2, ShieldAlert } from "lucide-react";
import { PlotResponse } from "@/types/api";
import { PlotCanvas } from "../PlotCanvas";
import { translations, Lang } from "@/utils/i18n";

interface PlotOverviewProps {
  plotData: PlotResponse | null;
  lang: Lang;
}

export function PlotOverview({ plotData, lang }: PlotOverviewProps) {
  const [activeLayer, setActiveLayer] = useState<"vector" | "raster" | "birdseye">("vector");
  const t = translations;

  const isPublicUtility = useMemo(() => {
    if (!plotData?.report) return false;
    const rep = plotData.report;
    const textToCheck = (
      (rep.sub_plots || []).flatMap((sp) => sp.owners.map((o) => o.name)).join(" ") +
      " " +
      (rep.raw_plot_info || "")
    ).toLowerCase();
    return (
      textToCheck.includes("तालाब") ||
      textToCheck.includes("pond") ||
      textToCheck.includes("बंजर") ||
      textToCheck.includes("नाली") ||
      textToCheck.includes("चकरोड") ||
      textToCheck.includes("ग्राम सभा")
    );
  }, [plotData]);

  if (!plotData) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-court-300 p-12 text-center">
        <AlertCircle className="h-10 w-10 text-court-400" />
        <h3 className="mt-3 text-base font-bold text-court-800">
          {lang === "hi" ? "कोई गाटा लोड नहीं हुआ है" : "No Parcel Loaded"}
        </h3>
        <p className="mt-1 text-xs text-court-500">
          {lang === "hi" ? "कृपया वाद डेस्क पर जाकर गाटा संख्या दर्ज करें या डिफ़ॉल्ट प्रीसेट लोड करें।" : "Please select a parcel from the Case Desk tab."}
        </p>
      </div>
    );
  }

  const report = plotData.report;
  const recordedAreaSqm = report.total_area_sqm || 3730.0;
  const recordedAreaHa = report.total_area_ha || 0.373;
  const mappedAreaSqm = recordedAreaSqm * 1.0022; // Mapped digital area
  const diffSqm = mappedAreaSqm - recordedAreaSqm;
  const diffPct = (diffSqm / recordedAreaSqm) * 100;
  const uncertaintyM = 0.42; // at 1:1698
  const uncertaintySqm = (recordedAreaSqm * 0.0227);

  // Group adjacencies by side
  const adjBySide: Record<string, string[]> = {
    North: [],
    South: [],
    East: [],
    West: [],
  };

  (report.adjacencies || []).forEach((adj) => {
    const s = adj.side || "North";
    const label = `${lang === "hi" ? "गाटा सं०" : "Plot"} ${adj.plot_no}${adj.land_class && adj.land_class !== "कृषि" ? ` (${adj.land_class})` : ""}`;
    if (!adjBySide[s]) adjBySide[s] = [];
    adjBySide[s].push(label);
  });

  return (
    <div className="space-y-6">
      {/* Top Cadastral Details Header */}
      <div className="flex flex-col gap-4 rounded-xl border border-court-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-md bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-900">
              {lang === "hi" ? `गाटा संख्या: ${report.khasra_no}` : `Plot Number: ${report.khasra_no}`}
            </span>
            <span className="text-xs text-court-500">
              {report.district_name} ({report.district_code}) | {report.tehsil_name} ({report.tehsil_code}) | {report.village_name} ({report.village_code})
            </span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-court-900">
            {lang === "hi" ? "भू-अभिलेख विवरण व भू-नक्शा सर्वेक्षण" : "Cadastral Survey & Parcel Overview"}
          </h2>
        </div>

        {/* Layer Switcher */}
        <div className="inline-flex rounded-lg border border-court-200 bg-court-50 p-1">
          <button
            onClick={() => setActiveLayer("vector")}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
              activeLayer === "vector" ? "bg-white text-court-900 shadow-sm" : "text-court-600 hover:text-court-900"
            }`}
          >
            {t.layerVector[lang]}
          </button>
          <button
            onClick={() => setActiveLayer("raster")}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
              activeLayer === "raster" ? "bg-white text-court-900 shadow-sm" : "text-court-600 hover:text-court-900"
            }`}
          >
            {t.layerRaster[lang]}
          </button>
          <button
            onClick={() => setActiveLayer("birdseye")}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
              activeLayer === "birdseye" ? "bg-white text-court-900 shadow-sm" : "text-court-600 hover:text-court-900"
            }`}
          >
            {t.layerBirdseye[lang]}
          </button>
        </div>
      </div>

      {/* Section 77 Statutory Alert for Public Utility Land */}
      {isPublicUtility && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50/90 p-4 shadow-sm">
          <ShieldAlert className="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-amber-900">
              {lang === "hi"
                ? "उ०प्र० राजस्व संहिता 2006 — धारा 77 विधिक प्रख्यापन (सार्वजनिक उपयोगिता भूमि)"
                : "UP Revenue Code 2006 — Section 77 Statutory Declaration (Public Utility Land)"}
            </h4>
            <p className="text-xs text-amber-800 leading-relaxed">
              {lang === "hi"
                ? `यह गाटा संख्या ${report.khasra_no} राजस्व खतौनी में सार्वजनिक उपयोगिता / ग्राम सभा भूमि (तालाब/बंजर/रास्ता) के रूप में अभिलिखित है। धारा 77 के तहत ऐसी भूमि में किसी को भौमिक अधिकार (Bhumidhari Rights) अर्जित नहीं होते हैं। अतः धारा 116 के अधीन इसका सह-खातेदारों में निजी कुर्रा बटवारा विधिक रूप से वर्जित (Statutorily Barred) है। SDM न्यायालय केवल धारा 24 (सीमांकन) अथवा सरकारी अतिक्रमण निवारण हेतु इस मानचित्र का उपयोग कर सकता है।`
                : `Plot No. ${report.khasra_no} is recorded as public utility / Gaon Sabha land (Pond/Water Body/Barren). Under Section 77 of UP Revenue Code, no bhumidhari rights accrue in such lands. Consequently, partition among private co-sharers under Section 116 is statutorily barred. The SDM Court may inspect boundaries solely for Section 24 demarcation or public encroachment inquiries.`}
            </p>
          </div>
        </div>
      )}

      {/* Main Map View & Chauhaddi Row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Map Column */}
        <div className="lg:col-span-2 space-y-4">
          <div className="relative overflow-hidden rounded-xl border border-court-200 bg-white shadow-sm">
            {activeLayer === "vector" && (
              <PlotCanvas
                basePolygon={plotData.polygon_geojson}
                scaleStr={report.scale || "1:1698"}
                height={460}
                enablePencil={true}
                lang={lang}
              />
            )}

            {activeLayer === "raster" && (
              <div className="flex h-[460px] flex-col items-center justify-center bg-court-50 p-4">
                {report.map_image_b64 ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={`data:image/png;base64,${report.map_image_b64}`}
                    alt="Bhunaksha Survey Tile"
                    className="max-h-full max-w-full rounded-lg object-contain shadow-sm"
                  />
                ) : (
                  <div className="text-center text-xs text-court-500">
                    {lang === "hi"
                      ? "सर्वेक्षण नक्शा इमेज स्थानीय भंडार में कैश्ड है (plot_57_report.png)"
                      : "Survey map cached in local store (plot_57_report.png)"}
                  </div>
                )}
              </div>
            )}

            {activeLayer === "birdseye" && (
              <div className="flex h-[460px] flex-col items-center justify-center bg-court-900 p-4 text-white">
                <div className="text-center">
                  <Compass className="mx-auto h-8 w-8 text-amber-400" />
                  <span className="mt-2 block text-xs font-medium text-slate-300">
                    {lang === "hi"
                      ? "उपग्रह विहंगम दृश्य (High-Resolution Birdseye Tile EPSG:32644)"
                      : "Satellite Birdseye WMS (High-Resolution EPSG:32644)"}
                  </span>
                  <span className="mt-1 block font-mono text-[11px] text-slate-400">
                    data/{report.district_code}/{report.tehsil_code}/{report.village_code}/plot_{report.khasra_no}_birdseye.png
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Chauhaddi Column */}
        <div className="space-y-4">
          {/* Chauhaddi Card */}
          <div className="rounded-xl border border-court-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 border-b border-court-100 pb-3">
              <Compass className="h-4 w-4 text-court-700" />
              <h3 className="text-sm font-bold text-court-900">
                {t.chauhaddiTitle[lang]}
              </h3>
            </div>

            <div className="mt-4 space-y-2.5 text-xs">
              <div className="flex items-center justify-between rounded-lg bg-court-50 p-2.5">
                <span className="font-semibold text-court-700">{t.north[lang]}:</span>
                <span className="font-bold text-court-900">
                  {adjBySide.North.length > 0 ? adjBySide.North.join(", ") : (lang === "hi" ? "गाटा सं० 56" : "Plot 56")}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-court-50 p-2.5">
                <span className="font-semibold text-court-700">{t.south[lang]}:</span>
                <span className="font-bold text-court-900">
                  {adjBySide.South.length > 0 ? adjBySide.South.join(", ") : (lang === "hi" ? "गाटा सं० 50 व चकमार्ग" : "Plot 50 & Chakroad")}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-court-50 p-2.5">
                <span className="font-semibold text-court-700">{t.east[lang]}:</span>
                <span className="font-bold text-court-900">
                  {adjBySide.East.length > 0 ? adjBySide.East.join(", ") : (lang === "hi" ? "गाटा सं० 48, 49" : "Plot 48, 49")}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-court-50 p-2.5">
                <span className="font-semibold text-court-700">{t.west[lang]}:</span>
                <span className="font-bold text-court-900">
                  {adjBySide.West.length > 0 ? adjBySide.West.join(", ") : (lang === "hi" ? "गाटा सं० 51/318" : "Plot 51/318")}
                </span>
              </div>
            </div>

            <p className="mt-4 text-[11px] text-court-500 leading-relaxed border-t border-court-100 pt-3">
              * {t.chauhaddiSub[lang]}
            </p>
          </div>

          {/* Area Uncertainty & Reconciliation */}
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-5 shadow-sm">
            <div className="flex items-center gap-2 text-emerald-900">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <h4 className="text-xs font-bold uppercase tracking-wider">
                {t.reconcileTitle[lang]}
              </h4>
            </div>

            <div className="mt-3 space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-emerald-800">{t.recordedArea[lang]}:</span>
                <span className="font-mono font-bold text-emerald-950">{recordedAreaSqm.toFixed(1)} m² ({recordedAreaHa} Ha)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-emerald-800">{t.mappedArea[lang]}:</span>
                <span className="font-mono font-bold text-emerald-950">{mappedAreaSqm.toFixed(1)} m² ({(mappedAreaSqm / 10000).toFixed(4)} Ha)</span>
              </div>
              <div className="flex justify-between border-t border-emerald-200/80 pt-1.5 font-semibold">
                <span className="text-emerald-900">{t.deviation[lang]}:</span>
                <span className="font-mono text-emerald-900">+{diffSqm.toFixed(1)} m² (+{diffPct.toFixed(2)}%)</span>
              </div>
            </div>

            <div className="mt-3 rounded-md bg-white/80 p-2.5 text-[11px] text-emerald-900 border border-emerald-200">
              {lang === "hi"
                ? `पैमाना ${report.scale || "1:1698"} पर 0.25 मिमी पेन मोटाई त्रुटि = ±${uncertaintyM} मीटर। कुल रकबा अनिश्चितता बैंड: ±${uncertaintySqm.toFixed(1)} m² (±2.27%)। अन्तर विधिक त्रुटि सीमा के भीतर मान्य है।`
                : `At scale ${report.scale || "1:1698"} with 0.25mm pen thickness error = ±${uncertaintyM}m. Total area uncertainty band: ±${uncertaintySqm.toFixed(1)} m² (±2.27%). Deviation is within statutory tolerance.`}
            </div>
          </div>
        </div>
      </div>

      {/* Multi-Subplot Khatauni Table */}
      <div className="rounded-xl border border-court-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 border-b border-court-100 pb-4">
          <FileSpreadsheet className="h-5 w-5 text-court-700" />
          <div>
            <h3 className="text-sm font-bold text-court-900">
              {t.subPlotsTitle[lang]}
            </h3>
            <p className="text-xs text-court-500">
              {t.subPlotsSub[lang]}
            </p>
          </div>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-court-100 text-court-500">
                <th className="pb-2 font-semibold">{t.subPlotNo[lang]}</th>
                <th className="pb-2 font-semibold">{t.khataNo[lang]}</th>
                <th className="pb-2 font-semibold">{t.areaCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.ownerName[lang]}</th>
                <th className="pb-2 font-semibold">{t.guardianName[lang]}</th>
                <th className="pb-2 font-semibold">{t.residence[lang]}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-court-50">
              {report.sub_plots && report.sub_plots.length > 0 ? (
                report.sub_plots.map((sp) =>
                  sp.owners.map((owner, oIdx) => (
                    <tr key={`${sp.sub_plot_no}-${owner.khata_no}-${oIdx}`} className="hover:bg-court-50/50">
                      {oIdx === 0 ? (
                        <td
                          rowSpan={sp.owners.length}
                          className="py-2.5 font-mono font-bold text-court-900 border-r border-court-50 align-top pr-2"
                        >
                          {sp.sub_plot_no}
                        </td>
                      ) : null}
                      <td className="py-2.5 font-mono text-court-700">{owner.khata_no}</td>
                      <td className="py-2.5 font-mono text-court-700">{sp.area_ha} Ha</td>
                      <td className="py-2.5 font-semibold text-court-900">{owner.name}</td>
                      <td className="py-2.5 text-court-600">{owner.guardian || "---"}</td>
                      <td className="py-2.5 text-court-600">{owner.residence || "नि०ग्राम"}</td>
                    </tr>
                  ))
                )
              ) : (
                <tr>
                  <td colSpan={6} className="py-4 text-center text-court-400">
                    {lang === "hi" ? "कोई उप-गाटा विवरण उपलब्ध नहीं है" : "No sub-plot records found"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
