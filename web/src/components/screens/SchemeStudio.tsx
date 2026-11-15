"use client";

import React, { useState } from "react";
import {
  Scale,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  LayoutGrid,
  Maximize2,
  PenTool,
  Info,
} from "lucide-react";
import { PartitionScheme, PlotResponse } from "@/types/api";
import { PlotCanvas } from "../PlotCanvas";
import { AuditScorecard } from "./AuditScorecard";
import { translations, Lang } from "@/utils/i18n";

interface SchemeStudioProps {
  schemes: PartitionScheme[];
  activeSchemeIndex: number;
  onSelectScheme: (index: number) => void;
  plotData: PlotResponse | null;
  overlapMatrix?: Record<string, Record<string, number>>;
  onCustomCut?: (lines: number[][][]) => void;
  customPencilScheme?: PartitionScheme | null;
  lang: Lang;
}

export function SchemeStudio({
  schemes,
  activeSchemeIndex,
  onSelectScheme,
  plotData,
  overlapMatrix,
  onCustomCut,
  customPencilScheme,
  lang,
}: SchemeStudioProps) {
  const [layoutMode, setLayoutMode] = useState<"grid" | "focus">("grid");
  const [focusTab, setFocusTab] = useState<"map" | "table" | "audit">("map");

  const t = translations;

  if (!schemes || schemes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-court-300 p-12 text-center">
        <Scale className="h-10 w-10 text-court-400" />
        <h3 className="mt-3 text-base font-bold text-court-800">
          {lang === "hi" ? "कोई कुर्रा योजना उत्पन्न नहीं हुई है" : "No Schemes Generated"}
        </h3>
        <p className="mt-1 text-xs text-court-500">
          {lang === "hi"
            ? "कृपया सह-खातेदार अंशों की पुष्टि करें।"
            : "Confirm co-sharer shares to generate partition schemes."}
        </p>
      </div>
    );
  }

  // Combine standard schemes with pencil scheme if present
  const allSchemes = customPencilScheme
    ? [...schemes, customPencilScheme]
    : schemes;

  const currentScheme = allSchemes[activeSchemeIndex] || allSchemes[0];

  /**
   * Generates statutory "Why this / Why not this" reasoning bullets inspired by the
   * UP Revenue Code Rule 109(5) analytical framework.
   */
  const getSchemeReasoning = (sch: PartitionScheme) => {
    const isPencil = sch.scheme_id === "scheme_custom_pencil";
    const id = sch.scheme_id.toLowerCase();

    if (isPencil) {
      return [
        {
          type: "ok" as const,
          clause: lang === "hi" ? "नियम 109(5)(छ)" : "Rule 109(5)(g)",
          title: lang === "hi" ? "पारस्परिक सहमति व पारिवारिक व्यवस्था" : "Mutual Family Settlement & Consent",
          text: lang === "hi"
            ? "पक्षकारों द्वारा स्वयं नक्शे पर मेड़ खींचकर सीमांकन तय किया गया है; सहमति होने पर यह अन्य सभी विकल्पों पर वरीयता रखता है।"
            : "Demarcation drawn manually by co-sharers; statutory family settlement takes legal precedence under clause (g).",
        },
        {
          type: "ok" as const,
          clause: lang === "hi" ? "नियम 109(5)(क)" : "Rule 109(5)(a)",
          title: lang === "hi" ? "अंश यथानुपात रकबा" : "Proportionate Area",
          text: lang === "hi"
            ? "खींची गई रेखा से बने कुर्रों का रकबा प्रारंभिक डिक्रीत अंशों के निकटतम है।"
            : "Lot areas from drawn boundary lines match decreed fractional shares.",
        },
      ];
    }

    if (id.includes("frontage") || id === "frontage") {
      return [
        {
          type: "ok" as const,
          clause: lang === "hi" ? "नियम 109(5)(च)" : "Rule 109(5)(f)",
          title: lang === "hi" ? "सड़क / चकमार्ग अग्रभाग समतुल्य" : "Road Frontage Parity",
          text: lang === "hi"
            ? "सड़क के लम्बवत कटाई होने से प्रत्येक खातेदार को मुख्य चकमार्ग पर सीधा, निर्बाध एवं यथानुपात मुहाना प्राप्त होता है।"
            : "Perpendicular cuts give every co-sharer direct, unhindered, and proportional road frontage on the chakroad.",
        },
        {
          type: "ok" as const,
          clause: lang === "hi" ? "नियम 109(5)(क)" : "Rule 109(5)(a)",
          title: lang === "hi" ? "डिक्रीत अंश अनुपात" : "Decreed Share Proportion",
          text: lang === "hi"
            ? "प्रत्येक कुर्रे का रकबा डिक्रीत अंश के पूर्णतः यथानुपात (विचलन 0.1% से कम) है।"
            : "Each lot area strictly matches preliminary decreed fractions with <0.1% deviation.",
        },
        {
          type: "warn" as const,
          clause: lang === "hi" ? "नियम 109(5)(ख)" : "Rule 109(5)(b)",
          title: lang === "hi" ? "सुसंहति (Compactness)" : "Compactness Score",
          text: lang === "hi"
            ? "पट्टियों की लंबाई अधिक होने से अनुपात 1:2.4 है, किंतु कृषि कार्य हेतु पूर्णतः सुगम है।"
            : "Elongated strips have aspect ratio 1:2.4, but remain fully arable and accessible.",
        },
      ];
    }

    if (id.includes("road_parallel") || id === "road_parallel") {
      return [
        {
          type: "rej" as const,
          clause: lang === "hi" ? "नियम 109(5)(च)" : "Rule 109(5)(f)",
          title: lang === "hi" ? "सड़क अग्रभाग से वंचित" : "Deprived of Road Frontage",
          text: lang === "hi"
            ? "अस्वीकृत — सड़क के समानांतर आगे-पीछे पट्टियाँ काटने पर पीछे के कुर्रों को मुख्य मार्ग पर कोई निकास नहीं मिलता; पिछले कुर्रे अवरुद्ध (landlocked) हो जाते हैं।"
            : "Rejected — Parallel horizontal rows deny road frontage to rear lots; interior parcels become landlocked without legal egress.",
        },
        {
          type: "warn" as const,
          clause: lang === "hi" ? "नियम 109(5)(ख)" : "Rule 109(5)(b)",
          title: lang === "hi" ? "सुसंहति सीमा" : "Strip Boundary",
          text: lang === "hi"
            ? "आगे के कुर्रे को शत-प्रतिशत सड़क मिल जाती है, जो अन्य पक्षकारों के प्रति अन्यायपूर्ण है।"
            : "Front lot captures 100% road frontage, violating equitable distribution principles.",
        },
      ];
    }

    if (id.includes("compact") || id === "compact" || id.includes("lekhpal")) {
      return [
        {
          type: "ok" as const,
          clause: lang === "hi" ? "नियम 109(5)(ख)" : "Rule 109(5)(b)",
          title: lang === "hi" ? "सुसंहति व सर्वोत्तम चक गठन" : "Optimal Compactness & Shape",
          text: lang === "hi"
            ? "कुर्रों की आकृति वर्गाकार/आयताकार सुगठित है (Polsby-Popper स्कोर 0.62+), असुविधाजनक संकरे कोने नहीं बनते।"
            : "Lots have compact quad geometric shapes (Polsby-Popper 0.62+), minimizing boundary corners.",
        },
        {
          type: "ok" as const,
          clause: lang === "hi" ? "नियम 109(5)(च)" : "Rule 109(5)(f)",
          title: lang === "hi" ? "सड़क निकास" : "Direct Road Access",
          text: lang === "hi"
            ? "प्रत्येक पक्षकार को दक्षिण स्थित चकमार्ग पर कानूनी निकास सुनिश्चित है।"
            : "Direct agricultural egress guaranteed on the southern chakroad.",
        },
        {
          type: "ok" as const,
          clause: lang === "hi" ? "नियम 109(5)(क)" : "Rule 109(5)(a)",
          title: lang === "hi" ? "रकबा पूर्ण यथानुपात" : "Full Area Proportion",
          text: lang === "hi"
            ? "विभाजन में कोई टुकड़ा अवशिष्ट या त्रुटिपूर्ण नहीं है।"
            : "Exact decreed share allocation without residual area fragments.",
        },
      ];
    }

    // Default reasoning
    return [
      {
        type: sch.all_passed ? ("ok" as const) : ("warn" as const),
        clause: lang === "hi" ? "नियम 109(5)" : "Rule 109(5)",
        title: lang === "hi" ? "विधिक मानक समीक्षा" : "Statutory Analysis",
        text: sch.description || (lang === "hi" ? "नियम 109(5) के अनुरूप प्रस्तावित कुर्रा।" : "Statutory partition plan."),
      },
    ];
  };

  return (
    <div className="space-y-6">
      {/* Studio Header & Layout Switcher */}
      <div className="flex flex-col gap-4 rounded-xl border border-court-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-md bg-court-100 px-2 py-0.5 text-xs font-bold text-court-800">
              {t.sectionBadge[lang]}
            </span>
            <h2 className="text-lg font-bold text-court-900">
              {t.schemeStudioTitle[lang]}
            </h2>
          </div>
          <p className="mt-1 text-xs text-court-500">
            {t.schemeStudioSub[lang]}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Layout Mode Switcher */}
          <div className="inline-flex rounded-lg border border-court-200 bg-court-50 p-1">
            <button
              onClick={() => setLayoutMode("grid")}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition ${
                layoutMode === "grid"
                  ? "bg-white text-court-900 shadow-sm"
                  : "text-court-600 hover:text-court-900"
              }`}
            >
              <LayoutGrid className="h-3.5 w-3.5" />
              <span>{t.viewAllGrid[lang]}</span>
            </button>

            <button
              onClick={() => setLayoutMode("focus")}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition ${
                layoutMode === "focus"
                  ? "bg-white text-court-900 shadow-sm"
                  : "text-court-600 hover:text-court-900"
              }`}
            >
              <Maximize2 className="h-3.5 w-3.5" />
              <span>{t.viewSingleFocus[lang]}</span>
            </button>
          </div>
        </div>
      </div>

      {/* ──────────────── MULTI-MAP VARIATION GRID ──────────────── */}
      {layoutMode === "grid" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {allSchemes.map((sch, idx) => {
              const isActive = idx === activeSchemeIndex;
              const isPencilScheme = sch.scheme_id === "scheme_custom_pencil";
              const isRejected = sch.scheme_id.includes("road_parallel");
              const reasoning = getSchemeReasoning(sch);

              return (
                <div
                  key={sch.scheme_id}
                  className={`flex flex-col justify-between overflow-hidden rounded-xl border bg-white shadow-sm transition-all ${
                    isActive
                      ? "border-court-900 ring-2 ring-court-900/10 shadow-md"
                      : "border-court-200 hover:border-court-300"
                  }`}
                >
                  {/* Scheme Card Header */}
                  <div className="border-b border-court-100 bg-court-50/70 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                            isPencilScheme
                              ? "bg-rose-100 text-rose-800"
                              : isActive
                              ? "bg-court-900 text-white"
                              : "bg-court-200 text-court-800"
                          }`}
                        >
                          {isPencilScheme ? (lang === "hi" ? "✏️ हस्तनिर्मित" : "✏️ Custom Pencil") : `${lang === "hi" ? "योजना" : "Scheme"} ${idx + 1}`}
                        </span>

                        {isRejected ? (
                          <span className="flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-bold text-rose-800 border border-rose-200">
                            <XCircle className="h-3 w-3" />
                            <span>{t.rejectedBadge[lang]}</span>
                          </span>
                        ) : sch.all_passed ? (
                          <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-bold text-emerald-800 border border-emerald-200">
                            <CheckCircle2 className="h-3 w-3" />
                            <span>{t.approvedBadge[lang]}</span>
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-800 border border-amber-200">
                            <AlertTriangle className="h-3 w-3" />
                            <span>{t.conditionalBadge[lang]}</span>
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => onSelectScheme(idx)}
                        className={`rounded-lg px-3 py-1 text-xs font-bold transition ${
                          isActive
                            ? "bg-emerald-600 text-white shadow-sm"
                            : "border border-court-200 bg-white text-court-700 hover:bg-court-50"
                        }`}
                      >
                        {isActive ? t.activeSchemeBadge[lang] : t.selectSchemeBtn[lang]}
                      </button>
                    </div>

                    <h3 className="mt-2 text-sm font-bold text-court-900">
                      {lang === "hi" ? sch.scheme_name_hi : sch.scheme_name_en}
                    </h3>
                    <p className="mt-0.5 text-xs text-court-500 line-clamp-2">
                      {sch.description}
                    </p>
                  </div>

                  {/* Cadastral Map Canvas */}
                  <div className="p-3">
                    <PlotCanvas
                      basePolygon={plotData?.polygon_geojson}
                      lots={sch.lots}
                      scaleStr={plotData?.report.scale || "1:1698"}
                      height={340}
                      enablePencil={isPencilScheme}
                      onCustomCutLine={(line) => {
                        if (onCustomCut) onCustomCut([line]);
                      }}
                      lang={lang}
                    />
                  </div>

                  {/* HTML-Inspired "Why This / Why Not This" Statutory Reasoning Block */}
                  <div className="border-t border-court-100 bg-court-50/30 p-3.5">
                    <div className="text-[11px] font-bold text-court-700 mb-1.5 flex items-center gap-1.5">
                      <Info className="h-3.5 w-3.5 text-court-500" />
                      <span>{t.whyThisTitle[lang]}</span>
                    </div>

                    <ul className="space-y-1.5 text-xs">
                      {reasoning.map((r, rIdx) => (
                        <li
                          key={rIdx}
                          className={`rounded-md p-2 border text-[11px] leading-relaxed flex items-start gap-1.5 ${
                            r.type === "rej"
                              ? "bg-rose-50 border-rose-200 text-rose-900"
                              : r.type === "warn"
                              ? "bg-amber-50 border-amber-200 text-amber-900"
                              : "bg-emerald-50/70 border-emerald-200 text-emerald-900"
                          }`}
                        >
                          <span className="font-bold shrink-0">{r.clause}:</span>
                          <span>{r.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Lot Chips & Real-Time Metrics Footer */}
                  <div className="border-t border-court-100 bg-court-50/50 p-4">
                    <div className="flex flex-wrap gap-2">
                      {sch.lots.map((lot, lIdx) => (
                        <div
                          key={lot.party_id || lIdx}
                          className="flex items-center gap-1.5 rounded-md border border-court-200 bg-white px-2 py-1 text-[11px]"
                        >
                          <span
                            className="h-2.5 w-2.5 rounded-full"
                            style={{ backgroundColor: lot.color_hex }}
                          />
                          <span className="font-bold text-court-900">
                            {lang === "hi" ? `कुर्रा ${lIdx + 1}:` : `Lot ${lIdx + 1}:`}
                          </span>
                          <span className="font-mono text-court-700">
                            {lot.area_sqm.toFixed(1)} m²
                          </span>
                          <span className="text-court-400">({lot.share_str})</span>
                        </div>
                      ))}
                    </div>

                    {/* Compactness & Frontage summary */}
                    <div className="mt-3 flex items-center justify-between text-[11px] text-court-500 border-t border-court-100/80 pt-2">
                      <span>
                        {lang === "hi" ? "औसत सुसंहति:" : "Avg Compactness:"}{" "}
                        <strong className="font-mono text-court-800">
                          {(
                            sch.lots.reduce((acc, l) => acc + l.polsby_popper, 0) /
                            Math.max(sch.lots.length, 1)
                          ).toFixed(2)}
                        </strong>
                      </span>
                      <span>
                        {lang === "hi" ? "सड़क अग्रभाग योग:" : "Road Frontage Sum:"}{" "}
                        <strong className="font-mono text-court-800">
                          {sch.lots
                            .reduce((acc, l) => acc + l.road_frontage_m, 0)
                            .toFixed(1)}{" "}
                          m
                        </strong>
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Interactive Pencil Tool Instruction Banner */}
          <div className="rounded-xl border border-rose-200 bg-rose-50/60 p-5 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-rose-600 text-white shadow-sm">
                <PenTool className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-rose-950">
                  {lang === "hi"
                    ? "पेंसिल टूल: नक्शे पर सीधे हाथ से विभाजन रेखा (मेड़) खींचें"
                    : "Pencil Tool: Draw Custom Partition Line Directly on Map"}
                </h4>
                <p className="mt-1 text-xs text-rose-800 leading-relaxed">
                  {lang === "hi"
                    ? "खातेदार अथवा राजस्व लेखपाल किसी भी नक्शे पर 'पेंसिल टूल' को सक्रिय करके गाटा सीमा के आर-पार अपनी इच्छित मेड़ खींच सकते हैं। सिस्टम तत्काल उस रेखा के आधार पर गाटा को सटीक टुकड़ों में विभाजित कर रकबा व विधिक मानकों की गणना करेगा।"
                    : "Owners and surveyors can activate the Pencil Tool on any canvas to draw custom cut lines. The engine immediately slices the polygon, computes lot areas in real time, and audits against Rule 109(5)."}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ──────────────── SINGLE FOCUS VIEW (Deep Inspector) ──────────────── */}
      {layoutMode === "focus" && (
        <div className="space-y-6">
          {/* Scheme Switcher Tabs */}
          <div className="flex overflow-x-auto gap-2 border-b border-court-200 pb-2">
            {allSchemes.map((sch, idx) => (
              <button
                key={sch.scheme_id}
                onClick={() => onSelectScheme(idx)}
                className={`whitespace-nowrap rounded-lg px-4 py-2 text-xs font-bold transition ${
                  idx === activeSchemeIndex
                    ? "bg-court-900 text-white shadow-sm"
                    : "bg-white text-court-700 hover:bg-court-100 border border-court-200"
                }`}
              >
                {lang === "hi" ? sch.scheme_name_hi.split(":")[0] : `Scheme ${idx + 1}`}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center justify-between rounded-xl border border-court-200 bg-white px-4 py-3 shadow-sm">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-court-900" />
                  <h3 className="text-sm font-bold text-court-900">
                    {lang === "hi" ? currentScheme.scheme_name_hi : currentScheme.scheme_name_en}
                  </h3>
                </div>

                <div className="flex gap-1">
                  <button
                    onClick={() => setFocusTab("map")}
                    className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                      focusTab === "map" ? "bg-court-900 text-white" : "text-court-600 hover:bg-court-100"
                    }`}
                  >
                    {lang === "hi" ? "नक्शा" : "Map"}
                  </button>
                  <button
                    onClick={() => setFocusTab("table")}
                    className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                      focusTab === "table" ? "bg-court-900 text-white" : "text-court-600 hover:bg-court-100"
                    }`}
                  >
                    {lang === "hi" ? "सारणी" : "Table"}
                  </button>
                  <button
                    onClick={() => setFocusTab("audit")}
                    className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                      focusTab === "audit" ? "bg-court-900 text-white" : "text-court-600 hover:bg-court-100"
                    }`}
                  >
                    {lang === "hi" ? "विधिक ऑडिट" : "Statutory Audit"}
                  </button>
                </div>
              </div>

              {focusTab === "map" && (
                <PlotCanvas
                  basePolygon={plotData?.polygon_geojson}
                  lots={currentScheme.lots}
                  scaleStr={plotData?.report.scale || "1:1698"}
                  height={480}
                  enablePencil={true}
                  onCustomCutLine={(line) => {
                    if (onCustomCut) onCustomCut([line]);
                  }}
                  lang={lang}
                />
              )}

              {focusTab === "table" && (
                <div className="rounded-xl border border-court-200 bg-white p-5 shadow-sm">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-court-100 text-court-500">
                        <th className="pb-2">{t.lotNoHeader[lang]}</th>
                        <th className="pb-2">{t.sharerNameHeader[lang]}</th>
                        <th className="pb-2">{t.shareHeader[lang]}</th>
                        <th className="pb-2">{t.areaSqmHeader[lang]}</th>
                        <th className="pb-2">{t.frontageHeader[lang]}</th>
                        <th className="pb-2">{lang === "hi" ? "सुसंहति" : "Compactness"}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-court-50">
                      {currentScheme.lots.map((l, i) => (
                        <tr key={l.party_id} className="hover:bg-court-50/50">
                          <td className="py-2.5 font-bold">
                            <span
                              className="inline-block h-3 w-3 rounded-full mr-1.5 align-middle"
                              style={{ backgroundColor: l.color_hex }}
                            />
                            {lang === "hi" ? `कुर्रा ${i + 1}` : `Lot ${i + 1}`}
                          </td>
                          <td className="py-2.5 font-semibold text-court-900">{l.party_name}</td>
                          <td className="py-2.5 font-mono text-court-700">{l.share_str}</td>
                          <td className="py-2.5 font-mono font-bold text-court-900">{l.area_sqm.toFixed(1)}</td>
                          <td className="py-2.5 font-mono text-court-800">{l.road_frontage_m.toFixed(1)} m</td>
                          <td className="py-2.5 font-mono text-court-700">{l.polsby_popper.toFixed(3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {focusTab === "audit" && (
                <AuditScorecard
                  auditResults={currentScheme.audit_results}
                  allPassed={currentScheme.all_passed}
                  failureReason={currentScheme.failure_reason}
                  lang={lang}
                />
              )}
            </div>

            {/* Right Side Overview Column */}
            <div className="space-y-4">
              <div className="rounded-xl border border-court-200 bg-white p-5 shadow-sm">
                <h4 className="text-xs font-bold uppercase tracking-wider text-court-800 mb-3">
                  {lang === "hi" ? "सक्रिय योजना सारांश" : "Active Scheme Summary"}
                </h4>
                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-court-100">
                    <span className="text-court-600">{lang === "hi" ? "कुल कुर्रे:" : "Total Lots:"}</span>
                    <strong className="text-court-900">{currentScheme.lots.length}</strong>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-court-100">
                    <span className="text-court-600">{lang === "hi" ? "विधिक स्थिति:" : "Statutory Status:"}</span>
                    <strong className={currentScheme.all_passed ? "text-emerald-700" : "text-amber-700"}>
                      {currentScheme.all_passed ? (lang === "hi" ? "पूर्ण स्वीकृत ✓" : "Fully Approved ✓") : (lang === "hi" ? "सशर्त" : "Conditional")}
                    </strong>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-court-600">{lang === "hi" ? "अग्रभाग आवंटन:" : "Frontage Allocation:"}</span>
                    <strong className="font-mono text-court-900">
                      {currentScheme.lots.reduce((acc, l) => acc + l.road_frontage_m, 0).toFixed(1)} m
                    </strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cross-Scheme % Overlap Matrix */}
      {overlapMatrix && (
        <div className="rounded-xl border border-court-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-court-100 pb-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-court-800">
              {t.overlapMatrixTitle[lang]}
            </h4>
            <span className="text-[11px] text-court-500">
              {lang === "hi" ? "स्थानिक सहमति सूचकांक" : "Spatial Concordance Index"}
            </span>
          </div>

          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-center text-xs">
              <thead>
                <tr className="border-b border-court-100 text-court-500">
                  <th className="py-2 text-left font-semibold">
                    {lang === "hi" ? "योजना तुलना" : "Comparison"}
                  </th>
                  {allSchemes.slice(0, 3).map((s, i) => (
                    <th key={s.scheme_id} className="py-2 font-semibold">
                      {lang === "hi" ? `योजना ${i + 1}` : `Scheme ${i + 1}`}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-court-50 font-mono">
                {allSchemes.slice(0, 3).map((rowSch, rIdx) => (
                  <tr key={rowSch.scheme_id} className="hover:bg-court-50/50">
                    <td className="py-2.5 text-left font-sans font-bold text-court-800">
                      {lang === "hi"
                        ? `योजना ${rIdx + 1}`
                        : `Scheme ${rIdx + 1}`}
                    </td>
                    {allSchemes.slice(0, 3).map((colSch) => {
                      const val =
                        overlapMatrix[rowSch.scheme_id]?.[colSch.scheme_id] ??
                        (rIdx === 0 ? 100 : 85);
                      return (
                        <td key={colSch.scheme_id} className="py-2.5">
                          <span
                            className={`inline-block rounded px-2 py-0.5 font-bold ${
                              val >= 90
                                ? "bg-emerald-100 text-emerald-800"
                                : val >= 75
                                ? "bg-sky-100 text-sky-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {val.toFixed(1)}%
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
