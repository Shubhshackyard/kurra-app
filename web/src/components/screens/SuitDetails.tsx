"use client";

import React from "react";
import { FileText, Landmark, User, ShieldCheck } from "lucide-react";
import { CaseMetadata } from "@/types/api";
import { translations, Lang } from "@/utils/i18n";

interface SuitDetailsProps {
  caseMeta: CaseMetadata;
  onUpdateMeta: (meta: CaseMetadata) => void;
  lang: Lang;
}

export function SuitDetails({ caseMeta, onUpdateMeta, lang }: SuitDetailsProps) {
  const t = translations;

  const handleChange = (key: keyof CaseMetadata, val: string) => {
    onUpdateMeta({
      ...caseMeta,
      [key]: val,
    });
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-court-200 bg-white p-6 shadow-sm">
        <div className="border-b border-court-100 pb-4">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-court-700" />
            <h3 className="text-base font-bold text-court-900">
              {t.suitDetailsTitle[lang]}
            </h3>
          </div>
          <p className="mt-1 text-xs text-court-500">
            {t.suitDetailsSub[lang]}
          </p>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <label className="block text-xs font-semibold text-court-700">
              {t.caseNoCol[lang]}
            </label>
            <div className="mt-1 flex items-center rounded-lg border border-court-200 bg-court-50 px-3 py-2 focus-within:border-court-900 focus-within:bg-white">
              <input
                type="text"
                value={caseMeta.case_no || ""}
                onChange={(e) => handleChange("case_no", e.target.value)}
                className="w-full bg-transparent text-sm font-bold font-mono text-court-900 outline-none"
                placeholder={lang === "hi" ? "116/2026/उरई" : "116/2026/Orai"}
              />
            </div>
            <span className="mt-1 block text-[11px] text-court-400">
              {lang === "hi" ? "उदा० 116/2026" : "e.g. 116/2026"}
            </span>
          </div>

          <div className="lg:col-span-2">
            <label className="block text-xs font-semibold text-court-700">
              {t.competentCourt[lang]}
            </label>
            <div className="mt-1 flex items-center gap-2 rounded-lg border border-court-200 bg-court-50 px-3 py-2 focus-within:border-court-900 focus-within:bg-white">
              <Landmark className="h-4 w-4 text-court-500 shrink-0" />
              <input
                type="text"
                value={caseMeta.court_name || ""}
                onChange={(e) => handleChange("court_name", e.target.value)}
                className="w-full bg-transparent text-sm font-semibold text-court-900 outline-none"
                placeholder={lang === "hi" ? "न्यायालय उपजिलाधिकारी / सहायक कलेक्टर प्रथम श्रेणी, उरई, जालौन" : "Court of SDM / Assistant Collector 1st Class, Orai, Jalaun"}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-court-700">
              {t.plaintiffLabel[lang]}
            </label>
            <div className="mt-1 flex items-center gap-2 rounded-lg border border-court-200 bg-court-50 px-3 py-2 focus-within:border-court-900 focus-within:bg-white">
              <User className="h-4 w-4 text-court-500 shrink-0" />
              <input
                type="text"
                value={caseMeta.plaintiff || ""}
                onChange={(e) => handleChange("plaintiff", e.target.value)}
                className="w-full bg-transparent text-sm font-semibold text-court-900 outline-none"
                placeholder={lang === "hi" ? "जगदीश प्रसाद पुत्र राम रतन" : "Jagdish Prasad s/o Ram Ratan"}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-court-700">
              {t.defendantLabel[lang]}
            </label>
            <div className="mt-1 flex items-center gap-2 rounded-lg border border-court-200 bg-court-50 px-3 py-2 focus-within:border-court-900 focus-within:bg-white">
              <User className="h-4 w-4 text-court-500 shrink-0" />
              <input
                type="text"
                value={caseMeta.defendant || ""}
                onChange={(e) => handleChange("defendant", e.target.value)}
                className="w-full bg-transparent text-sm font-semibold text-court-900 outline-none"
                placeholder={lang === "hi" ? "राजेश कुमार व अन्य" : "Rajesh Kumar and others"}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-court-700">
              {t.plotNoCol[lang]}
            </label>
            <div className="mt-1 flex items-center rounded-lg border border-court-200 bg-court-100/60 px-3 py-2">
              <span className="font-mono text-sm font-bold text-court-900">
                {caseMeta.plot_no}
              </span>
              <span className="ml-2 text-xs text-court-500">
                ({caseMeta.village_name})
              </span>
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-lg border border-court-100 bg-court-50 p-4">
          <div className="flex items-start gap-3">
            <ShieldCheck className="h-5 w-5 text-court-700 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold text-court-900">
                {t.statuteReference[lang]}
              </h4>
              <p className="mt-1 text-xs text-court-600 leading-relaxed">
                {t.statuteDesc[lang]}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
