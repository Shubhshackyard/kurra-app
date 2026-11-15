"use client";

import React, { useState } from "react";
import { Landmark, Search, Database, Clock, ArrowRight, CheckCircle2 } from "lucide-react";
import { CaseMetadata } from "@/types/api";
import { translations, Lang } from "@/utils/i18n";

interface CaseDeskProps {
  onLoadPlot: (dist: string, teh: string, vill: string, plot: string) => void;
  caseMeta: CaseMetadata;
  onUpdateMeta: (meta: CaseMetadata) => void;
  lang: Lang;
  isLoading?: boolean;
}

export function CaseDesk({ onLoadPlot, caseMeta, onUpdateMeta, lang, isLoading = false }: CaseDeskProps) {
  const [district, setDistrict] = useState(caseMeta.district_code || "165");
  const [tehsil, setTehsil] = useState(caseMeta.tehsil_code || "00854");
  const [village, setVillage] = useState(caseMeta.village_code || "151769");
  const [plot, setPlot] = useState(caseMeta.plot_no || "57");

  const t = translations;

  const recentCases = [
    {
      caseNo: "116/2026/उरई",
      caseNoEn: "116/2026/Orai",
      village: "इखलाशपुरा च0क्षे0",
      villageEn: "Ikhlashpura",
      plotNo: "57",
      parties: "जगदीश प्रसाद बनाम राजेश कुमार आदि",
      partiesEn: "Jagdish Prasad vs Rajesh Kumar & others",
      area: "0.3730 हे०",
      areaEn: "0.3730 Ha",
      status: "कुर्रा विचाराधीन",
      statusEn: "Partition Pending",
      district: "165",
      tehsil: "00854",
      villageCode: "151769",
    },
    {
      caseNo: "84/2025/उरई",
      caseNoEn: "84/2025/Orai",
      village: "इखलाशपुरा च0क्षे0",
      villageEn: "Ikhlashpura",
      plotNo: "48",
      parties: "राम कुमार बनाम संतराम",
      partiesEn: "Ram Kumar vs Santram",
      area: "0.2150 हे०",
      areaEn: "0.2150 Ha",
      status: "प्रारंभिक डिक्री पारित",
      statusEn: "Preliminary Decree",
      district: "165",
      tehsil: "00854",
      villageCode: "151769",
    },
    {
      caseNo: "19/2026/उरई",
      caseNoEn: "19/2026/Orai",
      village: "इखलाशपुरा च0क्षे0",
      villageEn: "Ikhlashpura",
      plotNo: "56",
      parties: "छोटेलाल बनाम हरिश्चंद्र",
      partiesEn: "Chhotelal vs Harishchandra",
      area: "0.1800 हे०",
      areaEn: "0.1800 Ha",
      status: "आख्या प्रतीक्षित",
      statusEn: "Report Awaited",
      district: "165",
      tehsil: "00854",
      villageCode: "151769",
    },
  ];

  const handleApplyPreset = () => {
    setDistrict("165");
    setTehsil("00854");
    setVillage("151769");
    setPlot("57");
    onUpdateMeta({
      ...caseMeta,
      district_code: "165",
      district_name: lang === "hi" ? "जालौन" : "Jalaun",
      tehsil_code: "00854",
      tehsil_name: lang === "hi" ? "उरई" : "Orai",
      village_code: "151769",
      village_name: lang === "hi" ? "इखलाशपुरा च0क्षे0" : "Ikhlashpura",
      plot_no: "57",
    });
    onLoadPlot("165", "00854", "151769", "57");
  };

  const handleSelectRecent = (c: typeof recentCases[0]) => {
    setDistrict(c.district);
    setTehsil(c.tehsil);
    setVillage(c.villageCode);
    setPlot(c.plotNo);
    onLoadPlot(c.district, c.tehsil, c.villageCode, c.plotNo);
  };

  return (
    <div className="space-y-6">
      {/* Court Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-court-200 bg-gradient-to-r from-court-900 via-court-800 to-slate-900 p-8 text-white shadow-md">
        <div className="relative z-10 max-w-2xl">
          <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur-md">
            <Landmark className="h-3.5 w-3.5 text-amber-300" />
            <span>{lang === "hi" ? "उत्तर प्रदेश राजस्व संहिता 2006 — धारा 116 वाद डेस्क" : "UP Revenue Code 2006 — Section 116 Judicial Desk"}</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t.bannerTitle[lang]}
          </h2>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed">
            {t.bannerDesc[lang]}
          </p>
        </div>
      </div>

      {/* Cadastral Search & Preset */}
      <div className="rounded-xl border border-court-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-court-100 pb-4">
          <div>
            <h3 className="text-base font-bold text-court-900">
              {t.parcelLookup[lang]}
            </h3>
            <p className="text-xs text-court-500">
              {t.parcelLookupSub[lang]}
            </p>
          </div>
          <button
            onClick={handleApplyPreset}
            disabled={isLoading}
            className="inline-flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700 transition hover:bg-indigo-100"
          >
            <CheckCircle2 className="h-4 w-4 text-indigo-600" />
            <span>{t.loadDefaultPreset[lang]}</span>
          </button>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-xs font-semibold text-court-700">{t.districtLabel[lang]}</label>
            <input
              type="text"
              value={district || ""}
              onChange={(e) => setDistrict(e.target.value)}
              className="mt-1 w-full rounded-lg border border-court-200 bg-court-50 px-3 py-2 text-sm font-medium text-court-900 focus:border-court-900 focus:bg-white focus:outline-none"
              placeholder="165"
            />
            <span className="mt-1 block text-[11px] text-court-400">
              {lang === "hi" ? "165 — जालौन" : "165 — Jalaun"}
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-court-700">{t.tehsilLabel[lang]}</label>
            <input
              type="text"
              value={tehsil || ""}
              onChange={(e) => setTehsil(e.target.value)}
              className="mt-1 w-full rounded-lg border border-court-200 bg-court-50 px-3 py-2 text-sm font-medium text-court-900 focus:border-court-900 focus:bg-white focus:outline-none"
              placeholder="00854"
            />
            <span className="mt-1 block text-[11px] text-court-400">
              {lang === "hi" ? "00854 — उरई" : "00854 — Orai"}
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-court-700">{t.villageLabel[lang]}</label>
            <input
              type="text"
              value={village || ""}
              onChange={(e) => setVillage(e.target.value)}
              className="mt-1 w-full rounded-lg border border-court-200 bg-court-50 px-3 py-2 text-sm font-medium text-court-900 focus:border-court-900 focus:bg-white focus:outline-none"
              placeholder="151769"
            />
            <span className="mt-1 block text-[11px] text-court-400">
              {lang === "hi" ? "151769 — इखलाशपुरा च0क्षे0" : "151769 — Ikhlashpura"}
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-court-700">{t.plotLabel[lang]}</label>
            <div className="mt-1 flex gap-2">
              <input
                type="text"
                value={plot || ""}
                onChange={(e) => setPlot(e.target.value)}
                className="w-full rounded-lg border border-court-200 bg-court-50 px-3 py-2 text-sm font-bold text-court-900 focus:border-court-900 focus:bg-white focus:outline-none"
                placeholder="57"
              />
              <button
                onClick={() => onLoadPlot(district, tehsil, village, plot)}
                disabled={isLoading}
                className="inline-flex items-center gap-1.5 rounded-lg bg-court-900 px-4 py-2 text-xs font-bold text-white shadow-sm transition hover:bg-court-800 disabled:opacity-50"
              >
                <Search className="h-4 w-4" />
                <span>{isLoading ? t.searchingBtn[lang] : t.searchBtn[lang]}</span>
              </button>
            </div>
            <span className="mt-1 block text-[11px] text-court-400">
              {lang === "hi" ? "उदा० 57 या 57/2" : "e.g. 57 or 57/2"}
            </span>
          </div>
        </div>

        {/* Local store status banner */}
        <div className="mt-6 flex items-center justify-between rounded-lg border border-court-100 bg-court-50 px-4 py-3 text-xs text-court-700">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-emerald-600" />
            <span>{t.localStoreStatus[lang]}</span>
          </div>
          <span className="font-mono text-court-500">data/{district}/{tehsil}/{village}/cadastre.db</span>
        </div>
      </div>

      {/* Recent Cases Table */}
      <div className="rounded-xl border border-court-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-court-100 pb-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-court-600" />
            <h3 className="text-sm font-bold text-court-900">
              {t.recentCasesTitle[lang]}
            </h3>
          </div>
          <span className="text-xs text-court-500">
            {t.totalCasesBadge[lang]}: {recentCases.length}
          </span>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-court-100 text-court-500">
                <th className="pb-2 font-semibold">{t.caseNoCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.plotNoCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.partiesCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.areaCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.statusCol[lang]}</th>
                <th className="pb-2 text-right font-semibold">{t.actionCol[lang]}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-court-50">
              {recentCases.map((c, i) => (
                <tr key={i} className="hover:bg-court-50/60 transition">
                  <td className="py-3 font-mono font-bold text-court-900">
                    {lang === "hi" ? c.caseNo : c.caseNoEn}
                  </td>
                  <td className="py-3 font-semibold text-court-800">{c.plotNo}</td>
                  <td className="py-3 text-court-700">
                    {lang === "hi" ? c.parties : c.partiesEn}
                  </td>
                  <td className="py-3 font-mono text-court-600">
                    {lang === "hi" ? c.area : c.areaEn}
                  </td>
                  <td className="py-3">
                    <span className="inline-flex rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-700 border border-amber-200">
                      {lang === "hi" ? c.status : c.statusEn}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => handleSelectRecent(c)}
                      className="inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-semibold text-court-700 hover:bg-court-100 hover:text-court-900"
                    >
                      <span>{t.openBtn[lang]}</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
