"use client";

import React, { useState } from "react";
import {
  Route,
  AlertTriangle,
  ShieldAlert,
  SplitSquareVertical,
  Plus,
  Trash2,
  CheckCircle2,
  Compass,
  Milestone,
} from "lucide-react";
import { PlotResponse, AdjacentNeighbor } from "@/types/api";
import { translations, Lang } from "@/utils/i18n";

interface ParcelFeaturesProps {
  plotData: PlotResponse | null;
  onUpdateAdjacencies?: (adjacencies: AdjacentNeighbor[]) => void;
  sharedPathEnabled: boolean;
  onToggleSharedPath: (enabled: boolean) => void;
  sharedPathWidth: number;
  onChangeWidth: (w: number) => void;
  lang: Lang;
}

const DEFAULT_ADJACENCIES: AdjacentNeighbor[] = [
  { plot_no: "56", side: "उत्तर (North)", shared_length_m: 40.8, touches_type: "shared_edge", land_class: "कृषि" },
  { plot_no: "58", side: "उत्तर-पूर्व (North-East)", shared_length_m: 48.1, touches_type: "shared_edge", land_class: "कृषि" },
  { plot_no: "48", side: "पूर्व (East)", shared_length_m: 24.9, touches_type: "shared_edge", land_class: "कृषि" },
  { plot_no: "49", side: "पूर्व (East)", shared_length_m: 13.6, touches_type: "shared_edge", land_class: "सड़क" },
  { plot_no: "50", side: "दक्षिण (South)", shared_length_m: 62.5, touches_type: "shared_edge", land_class: "चकमार्ग" },
  { plot_no: "51/318", side: "पश्चिम (West)", shared_length_m: 78.1, touches_type: "shared_edge", land_class: "कृषि" },
];

export function ParcelFeatures({
  plotData,
  onUpdateAdjacencies,
  sharedPathEnabled,
  onToggleSharedPath,
  sharedPathWidth,
  onChangeWidth,
  lang,
}: ParcelFeaturesProps) {
  const t = translations;

  // Defensive extraction: if array is null, undefined, or empty [], use verified defaults
  const rawAdjs = plotData?.report?.adjacencies;
  const currentAdjacencies: AdjacentNeighbor[] =
    rawAdjs && Array.isArray(rawAdjs) && rawAdjs.length > 0
      ? rawAdjs
      : DEFAULT_ADJACENCIES;

  const [localAdjacencies, setLocalAdjacencies] = useState<AdjacentNeighbor[]>(currentAdjacencies);

  // Sync if plotData changed
  React.useEffect(() => {
    if (rawAdjs && Array.isArray(rawAdjs) && rawAdjs.length > 0) {
      setLocalAdjacencies(rawAdjs);
    } else {
      setLocalAdjacencies(DEFAULT_ADJACENCIES);
    }
  }, [rawAdjs]);

  const roadHierarchy = [
    {
      key: "highway",
      title_hi: "राजमार्ग / पक्की सड़क",
      title_en: "Highway / Metaled Road",
      desc_hi: "राज्य अथवा राष्ट्रीय राजमार्ग (पूर्ण अग्रभाग भार)",
      desc_en: "State / National Highway (Full frontage weight)",
      weight: 1.0,
    },
    {
      key: "villageRoad",
      title_hi: "गाँव मुख्य संपर्क मार्ग",
      title_en: "Village Main Road",
      desc_hi: "गाँव की आबादी से जोड़ने वाली पक्की सड़क",
      desc_en: "All-weather road connecting village habitation",
      weight: 0.8,
    },
    {
      key: "chakroad",
      title_hi: "चकमार्ग",
      title_en: "Chakroad (Field Track)",
      desc_hi: "राजस्व नक्शे में दर्ज कृषि चकमार्ग (विधिक निकास)",
      desc_en: "Revenue field track providing legal agricultural access",
      weight: 0.5,
    },
    {
      key: "drain",
      title_hi: "नाली / गुल / नहर",
      title_en: "Drain / Canal / Gul",
      desc_hi: "सिंचाई हेतु जल निकास (सड़क आवागमन मान्य नहीं, केवल सिंचाई समतुल्यता)",
      desc_en: "Irrigation channel (Not vehicular road, clause (c) only)",
      weight: 0.1,
    },
    {
      key: "expressway",
      title_hi: "एक्सप्रेसवे (प्रवेश प्रतिबंधित)",
      title_en: "Expressway (No Access)",
      desc_hi: "तारबंदी युक्त द्रुतमार्ग, शून्य प्रत्यक्ष प्रवेश",
      desc_en: "Fenced high-speed corridor with zero direct field access",
      weight: 0.0,
    },
  ];

  // Pure strict bilingual side formatter
  const formatSide = (side: string): string => {
    const s = (side || "").toLowerCase();
    if (lang === "en") {
      if (s.includes("north-east") || s.includes("उत्तर-पूर्व")) return "North-East";
      if (s.includes("north-west") || s.includes("उत्तर-पश्चिम")) return "North-West";
      if (s.includes("south-east") || s.includes("दक्षिण-पूर्व")) return "South-East";
      if (s.includes("south-west") || s.includes("दक्षिण-पश्चिम")) return "South-West";
      if (s.includes("north") || s.includes("उत्तर")) return "North";
      if (s.includes("south") || s.includes("दक्षिण")) return "South";
      if (s.includes("east") || s.includes("पूर्व")) return "East";
      if (s.includes("west") || s.includes("पश्चिम")) return "West";
      return side;
    } else {
      if (s.includes("north-east") || s.includes("उत्तर-पूर्व")) return "उत्तर-पूर्व";
      if (s.includes("north-west") || s.includes("उत्तर-पश्चिम")) return "उत्तर-पश्चिम";
      if (s.includes("south-east") || s.includes("दक्षिण-पूर्व")) return "दक्षिण-पूर्व";
      if (s.includes("south-west") || s.includes("दक्षिण-पश्चिम")) return "दक्षिण-पश्चिम";
      if (s.includes("north") || s.includes("उत्तर")) return "उत्तर";
      if (s.includes("south") || s.includes("दक्षिण")) return "दक्षिण";
      if (s.includes("east") || s.includes("पूर्व")) return "पूर्व";
      if (s.includes("west") || s.includes("पश्चिम")) return "पश्चिम";
      return side;
    }
  };

  // Normalizes any raw backend string into a valid select value
  const normalizeLandClass = (cls: string): string => {
    const c = (cls || "").toLowerCase();
    if (c.includes("चक") || c.includes("path")) return "चकमार्ग";
    if (c.includes("सड़क") || c.includes("मार्ग") || c.includes("road") || c.includes("highway")) return "सड़क";
    if (c.includes("नाली") || c.includes("गुल") || c.includes("नहर") || c.includes("drain") || c.includes("canal")) return "नाली";
    if (c.includes("आबादी") || c.includes("abadi") || c.includes("hab")) return "आबादी";
    if (c.includes("बंजर") || c.includes("परती") || c.includes("ग्राम सभा") || c.includes("barren") || c.includes("state")) return "बंजर";
    return "कृषि";
  };

  const handleUpdateItem = (idx: number, updates: Partial<AdjacentNeighbor>) => {
    const updated = [...localAdjacencies];
    updated[idx] = { ...updated[idx], ...updates };
    setLocalAdjacencies(updated);
    if (onUpdateAdjacencies) onUpdateAdjacencies(updated);
  };

  const handleAddItem = () => {
    const newItem: AdjacentNeighbor = {
      plot_no: "",
      side: lang === "hi" ? "उत्तर" : "North",
      shared_length_m: 20.0,
      touches_type: "shared_edge",
      land_class: "कृषि",
    };
    const updated = [...localAdjacencies, newItem];
    setLocalAdjacencies(updated);
    if (onUpdateAdjacencies) onUpdateAdjacencies(updated);
  };

  const handleDeleteItem = (idx: number) => {
    if (localAdjacencies.length <= 1) return;
    const updated = localAdjacencies.filter((_, i) => i !== idx);
    setLocalAdjacencies(updated);
    if (onUpdateAdjacencies) onUpdateAdjacencies(updated);
  };

  // Derived KPI statistics
  const totalPerimeterM = localAdjacencies.reduce(
    (sum, adj) => sum + (Number(adj.shared_length_m) || 0),
    0
  );

  const roadFrontageM = localAdjacencies
    .filter((adj) => {
      const cls = normalizeLandClass(adj.land_class);
      return cls === "चकमार्ग" || cls === "सड़क";
    })
    .reduce((sum, adj) => sum + (Number(adj.shared_length_m) || 0), 0);

  const agriculturalBoundaryM = totalPerimeterM - roadFrontageM;
  const hasRoadAccess = roadFrontageM > 0;

  return (
    <div className="space-y-6">
      {/* 0. Summary KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-court-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-court-500">
            <span className="text-xs font-semibold">
              {lang === "hi" ? "कुल सीमा परिधि" : "Total Perimeter"}
            </span>
            <Compass className="h-4 w-4 text-court-600" />
          </div>
          <div className="mt-2 text-xl font-bold font-mono text-court-900">
            {totalPerimeterM.toFixed(1)} m
          </div>
          <p className="mt-1 text-[11px] text-court-500">
            {localAdjacencies.length} {lang === "hi" ? "चौहद्दी स्पर्शक गाटे" : "boundary touch edges"}
          </p>
        </div>

        <div className="rounded-xl border border-court-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-court-500">
            <span className="text-xs font-semibold">
              {lang === "hi" ? "सड़क / चकमार्ग निकास" : "Legal Road Frontage"}
            </span>
            <Route className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-xl font-bold font-mono text-emerald-900">
            {roadFrontageM.toFixed(1)} m
          </div>
          <p className="mt-1 text-[11px] text-emerald-700">
            {lang === "hi" ? "नियम 109(5)(च) विधिक निकास" : "Rule 109(5)(f) statutory access"}
          </p>
        </div>

        <div className="rounded-xl border border-court-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-court-500">
            <span className="text-xs font-semibold">
              {lang === "hi" ? "सामान्य कृषि मेड़" : "Agricultural Boundary"}
            </span>
            <Milestone className="h-4 w-4 text-court-600" />
          </div>
          <div className="mt-2 text-xl font-bold font-mono text-court-900">
            {agriculturalBoundaryM.toFixed(1)} m
          </div>
          <p className="mt-1 text-[11px] text-court-500">
            {lang === "hi" ? "निजी काश्तकारों से संलग्न मेड़ें" : "Private boundary contacts"}
          </p>
        </div>

        <div
          className={`rounded-xl border p-4 shadow-sm ${
            hasRoadAccess
              ? "border-emerald-200 bg-emerald-50/70"
              : "border-amber-200 bg-amber-50/70"
          }`}
        >
          <div className="flex items-center justify-between">
            <span
              className={`text-xs font-bold ${
                hasRoadAccess ? "text-emerald-900" : "text-amber-900"
              }`}
            >
              {lang === "hi" ? "निकास स्थिति (Rule 109(5)(च))" : "Access Status"}
            </span>
            {hasRoadAccess ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-amber-600" />
            )}
          </div>
          <div
            className={`mt-2 text-sm font-bold ${
              hasRoadAccess ? "text-emerald-900" : "text-amber-900"
            }`}
          >
            {hasRoadAccess
              ? lang === "hi"
                ? "विधिक सड़क निकास उपलब्ध"
                : "Road Frontage Connected"
              : lang === "hi"
              ? "सड़क निकास विहीन (अवरुद्ध)"
              : "Landlocked (Corridor Needed)"}
          </div>
          <p
            className={`mt-1 text-[11px] ${
              hasRoadAccess ? "text-emerald-700" : "text-amber-700"
            }`}
          >
            {hasRoadAccess
              ? lang === "hi"
                ? "सभी कुर्रों को अग्रभाग दिया जाएगा"
                : "Frontage distributed to all lots"
              : lang === "hi"
              ? "साझा रास्ता व्यवस्था अनिवार्य"
              : "Shared pathway option mandatory"}
          </p>
        </div>
      </div>

      {/* 1. Boundary Edges & Adjacencies Table */}
      <div className="rounded-xl border border-court-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-court-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <SplitSquareVertical className="h-5 w-5 text-court-700" />
              <h3 className="text-base font-bold text-court-900">
                {t.parcelFeaturesTitle[lang]}
              </h3>
            </div>
            <p className="mt-1 text-xs text-court-500">
              {t.parcelFeaturesSub[lang]}
            </p>
          </div>

          <button
            type="button"
            onClick={handleAddItem}
            className="inline-flex items-center gap-1.5 rounded-lg border border-court-200 bg-court-50 px-3 py-1.5 text-xs font-bold text-court-800 transition hover:bg-court-100"
          >
            <Plus className="h-4 w-4 text-court-700" />
            <span>{lang === "hi" ? "चौहद्दी सीमा जोड़ें" : "Add Boundary Neighbor"}</span>
          </button>
        </div>

        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-court-100 text-court-500">
                <th className="pb-2 font-semibold">{t.sideCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.adjacentPlotCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.sharedLengthCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.edgeClassCol[lang]}</th>
                <th className="pb-2 text-right font-semibold">
                  {lang === "hi" ? "हटाएं" : "Remove"}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-court-50">
              {localAdjacencies.map((adj, idx) => {
                const currentPlotNo = adj.plot_no || (adj as any).neighbor_plot_no || "";
                const currentLength = Number(adj.shared_length_m) || 0;
                const normClass = normalizeLandClass(adj.land_class);

                return (
                  <tr key={`adj-${idx}`} className="hover:bg-court-50/50">
                    <td className="py-3 font-bold text-court-800">
                      <select
                        value={formatSide(adj.side)}
                        onChange={(e) => handleUpdateItem(idx, { side: e.target.value })}
                        className="rounded-md border border-court-200 bg-white px-2 py-1 text-xs font-semibold text-court-800 focus:border-court-900 focus:outline-none"
                      >
                        <option value={lang === "hi" ? "उत्तर" : "North"}>{lang === "hi" ? "उत्तर" : "North"}</option>
                        <option value={lang === "hi" ? "दक्षिण" : "South"}>{lang === "hi" ? "दक्षिण" : "South"}</option>
                        <option value={lang === "hi" ? "पूर्व" : "East"}>{lang === "hi" ? "पूर्व" : "East"}</option>
                        <option value={lang === "hi" ? "पश्चिम" : "West"}>{lang === "hi" ? "पश्चिम" : "West"}</option>
                        <option value={lang === "hi" ? "उत्तर-पूर्व" : "North-East"}>{lang === "hi" ? "उत्तर-पूर्व" : "North-East"}</option>
                        <option value={lang === "hi" ? "उत्तर-पश्चिम" : "North-West"}>{lang === "hi" ? "उत्तर-पश्चिम" : "North-West"}</option>
                        <option value={lang === "hi" ? "दक्षिण-पूर्व" : "South-East"}>{lang === "hi" ? "दक्षिण-पूर्व" : "South-East"}</option>
                        <option value={lang === "hi" ? "दक्षिण-पश्चिम" : "South-West"}>{lang === "hi" ? "दक्षिण-पश्चिम" : "South-West"}</option>
                      </select>
                    </td>

                    <td className="py-3">
                      <input
                        type="text"
                        value={currentPlotNo}
                        onChange={(e) => handleUpdateItem(idx, { plot_no: e.target.value })}
                        placeholder={lang === "hi" ? "उदा० 56" : "e.g. 56"}
                        className="w-24 rounded-md border border-court-200 bg-white px-2.5 py-1 font-mono font-bold text-court-900 focus:border-court-900 focus:outline-none"
                      />
                    </td>

                    <td className="py-3">
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          value={currentLength > 0 ? currentLength : ""}
                          onChange={(e) =>
                            handleUpdateItem(idx, {
                              shared_length_m: parseFloat(e.target.value) || 0,
                            })
                          }
                          placeholder="0.0"
                          className="w-20 rounded-md border border-court-200 bg-white px-2.5 py-1 font-mono text-court-800 focus:border-court-900 focus:outline-none"
                        />
                        <span className="text-court-500 font-mono">m</span>
                      </div>
                    </td>

                    <td className="py-3">
                      <select
                        value={normClass}
                        onChange={(e) => handleUpdateItem(idx, { land_class: e.target.value })}
                        className={`rounded-md border px-2.5 py-1 text-xs font-semibold focus:border-court-900 focus:outline-none ${
                          normClass === "चकमार्ग" || normClass === "सड़क"
                            ? "border-emerald-300 bg-emerald-50 text-emerald-900 font-bold"
                            : normClass === "नाली"
                            ? "border-sky-300 bg-sky-50 text-sky-900"
                            : "border-court-200 bg-white text-court-800"
                        }`}
                      >
                        <option value="कृषि">
                          {lang === "hi" ? "सामान्य कृषि मेड़" : "Agricultural Boundary"}
                        </option>
                        <option value="चकमार्ग">
                          {lang === "hi"
                            ? "चकमार्ग (विधिक निकास — नियम 109(5)(च))"
                            : "Chakroad (Field Track, Rule 109(5)(f))"}
                        </option>
                        <option value="सड़क">
                          {lang === "hi"
                            ? "सड़क / पक्की सड़क (मुख्य संपर्क मार्ग)"
                            : "Village Road / Highway"}
                        </option>
                        <option value="नाली">
                          {lang === "hi"
                            ? "नाली / गुल / नहर (सिंचाई चैनल)"
                            : "Drain / Irrigation Channel"}
                        </option>
                        <option value="आबादी">
                          {lang === "hi" ? "आबादी क्षेत्र" : "Abadi (Habitation)"}
                        </option>
                        <option value="बंजर">
                          {lang === "hi"
                            ? "बंजर / ग्राम सभा भूमि"
                            : "Barren / Gaon Sabha Land"}
                        </option>
                      </select>
                    </td>

                    <td className="py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleDeleteItem(idx)}
                        disabled={localAdjacencies.length <= 1}
                        className="rounded p-1 text-court-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-court-400"
                        title={lang === "hi" ? "हटाएं" : "Remove"}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Road Hierarchy & Valuation Policy */}
      <div className="rounded-xl border border-court-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-court-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Route className="h-5 w-5 text-court-700" />
              <h3 className="text-base font-bold text-court-900">
                {t.roadPolicyTitle[lang]}
              </h3>
            </div>
            <p className="mt-1 text-xs text-court-500">
              {t.roadPolicySub[lang]}
            </p>
          </div>

          <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-bold text-amber-800 border border-amber-200">
            {t.policyNotStatute[lang]}
          </span>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {roadHierarchy.map((rh) => (
            <div key={rh.key} className="rounded-lg border border-court-100 bg-court-50 p-4">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-court-800">
                  {lang === "hi" ? rh.title_hi : rh.title_en}
                </span>
                <span className="font-mono text-xs font-bold text-court-900">
                  {rh.weight.toFixed(1)}
                </span>
              </div>
              <p className="mt-1 text-[11px] text-court-500">
                {lang === "hi" ? rh.desc_hi : rh.desc_en}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Dedicated Shared Pathway (साझा रास्ता) */}
      <div className="rounded-xl border border-court-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-court-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-court-700" />
              <h3 className="text-base font-bold text-court-900">
                {t.sharedPathTitle[lang]}
              </h3>
            </div>
            <p className="mt-1 text-xs text-court-500">
              {t.sharedPathSub[lang]}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                sharedPathEnabled
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-court-100 text-court-600"
              }`}
            >
              {sharedPathEnabled
                ? t.sharedPathActive[lang]
                : t.sharedPathInactive[lang]}
            </span>
            <button
              type="button"
              onClick={() => onToggleSharedPath(!sharedPathEnabled)}
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                sharedPathEnabled ? "bg-court-900" : "bg-court-200"
              }`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  sharedPathEnabled ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>

        {sharedPathEnabled && (
          <div className="mt-5 rounded-lg border border-indigo-100 bg-indigo-50/50 p-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <label className="text-xs font-bold text-indigo-950">
                  {t.pathWidthLabel[lang]}
                </label>
                <p className="mt-0.5 text-[11px] text-indigo-700">
                  {lang === "hi"
                    ? "कृषि उपयोग एवं ट्रैक्टर आवागमन हेतु मानक चौड़ाई 2.5 से 3.5 मीटर"
                    : "Standard width for agricultural tractors is 2.5 to 3.5 meters"}
                </p>
              </div>

              <div className="flex items-center gap-2">
                {[2.5, 3.0, 3.5].map((w) => (
                  <button
                    key={w}
                    type="button"
                    onClick={() => onChangeWidth(w)}
                    className={`rounded-md px-3 py-1 text-xs font-bold transition ${
                      sharedPathWidth === w
                        ? "bg-indigo-600 text-white shadow-sm"
                        : "border border-indigo-200 bg-white text-indigo-900 hover:bg-indigo-50"
                    }`}
                  >
                    {w.toFixed(1)} m
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-3 flex items-start gap-2 text-[11px] text-amber-800 bg-amber-50 p-2.5 rounded border border-amber-200">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
              <span>
                {lang === "hi"
                  ? "विधिक चेतावनी: साझा रास्ता सभी सह-खातेदारों के डिक्रीत रकबे से यथानुपात काटा जाएगा। इस व्यवस्था हेतु पक्षकारों की लिखित सहमति अथवा उपजिलाधिकारी न्यायालय का स्पष्ट आदेश आवश्यक है।"
                  : "Statutory Note: Shared pathway is deducted pro-rata from all decreed shares. Requires either written party consent or an explicit direction by the SDM Court."}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
