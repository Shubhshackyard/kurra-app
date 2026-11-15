"use client";

import React, { useMemo } from "react";
import { Users, Plus, Trash2, CheckCircle2, AlertCircle, Equal, ShieldAlert } from "lucide-react";
import { CoSharerInput, ColorSwatch } from "@/types/api";
import { translations, Lang } from "@/utils/i18n";

interface CoSharersProps {
  sharers: CoSharerInput[];
  onUpdateSharers: (sharers: CoSharerInput[]) => void;
  availableColors: ColorSwatch[];
  lang: Lang;
}

export function CoSharers({ sharers, onUpdateSharers, availableColors, lang }: CoSharersProps) {
  const t = translations;

  // Parse fractions to compute sum
  const totalNominal = useMemo(() => {
    return sharers.reduce((acc, s) => {
      let val = 0;
      const str = (s.share || "").trim();
      if (str.includes("/")) {
        const parts = str.split("/");
        const num = parseFloat(parts[0]);
        const den = parseFloat(parts[1]);
        if (den && !isNaN(num) && !isNaN(den)) val = num / den;
      } else if (str.endsWith("%")) {
        val = parseFloat(str.replace("%", "")) / 100.0;
      } else {
        val = parseFloat(str) || 0;
      }
      return acc + (isNaN(val) ? 0 : val);
    }, 0);
  }, [sharers]);

  const isValid = Math.abs(totalNominal - 1.0) < 0.001;

  const isPublicUtility = useMemo(() => {
    return sharers.some(
      (s) =>
        (s.name || "").includes("सार्वजनिक") ||
        (s.name || "").includes("तालाब") ||
        (s.name || "").includes("बंजर") ||
        (s.name || "").includes("नाली") ||
        (s.name || "").includes("चकरोड")
    );
  }, [sharers]);

  const handleAdd = () => {
    const nextIdx = sharers.length;
    const defaultColor = availableColors[nextIdx % availableColors.length] || {
      name_hi: "सुर्ख (लाल)",
      name_en: "Red",
      hex: "#dc2626",
    };
    onUpdateSharers([
      ...sharers,
      {
        id: `P${nextIdx + 1}`,
        name: lang === "hi" ? `सह-खातेदार ${nextIdx + 1}` : `Co-Sharer ${nextIdx + 1}`,
        share: `1/${nextIdx + 1}`,
        color_hex: defaultColor.hex,
        color_name_hi: defaultColor.name_hi,
      },
    ]);
  };

  const handleEqualize = () => {
    const n = sharers.length;
    if (n === 0) return;
    const frac = `1/${n}`;
    onUpdateSharers(sharers.map((s) => ({ ...s, share: frac })));
  };

  const handleRemove = (id: string) => {
    if (sharers.length <= 1) return;
    onUpdateSharers(sharers.filter((s) => s.id !== id));
  };

  const handleUpdate = (id: string, updates: Partial<CoSharerInput>) => {
    onUpdateSharers(
      sharers.map((s) => (s.id === id ? { ...s, ...updates } : s))
    );
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-court-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-court-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-court-700" />
              <h3 className="text-base font-bold text-court-900">
                {t.sharersTitle[lang]}
              </h3>
            </div>
            <p className="mt-1 text-xs text-court-500">
              {t.sharersSub[lang]}
            </p>
          </div>

          {/* Sum Validation Badge */}
          <div
            className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-bold ${
              isValid
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-rose-200 bg-rose-50 text-rose-800"
            }`}
          >
            {isValid ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-rose-600" />
            )}
            <span>
              {t.totalShareSum[lang]}: <strong className="font-mono">{totalNominal.toFixed(4)}</strong> (
              {(totalNominal * 100).toFixed(1)}%) — {isValid ? t.fullyValid[lang] : t.invalidSum[lang]}
            </span>
          </div>
        </div>

        {/* Section 77 Statutory Notice for Public Utility Land */}
        {isPublicUtility && (
          <div className="mt-4 flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50/90 p-4">
            <ShieldAlert className="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-amber-900">
                {lang === "hi"
                  ? "उ०प्र० राजस्व संहिता धारा 77 — गैर-विभाज्य सार्वजनिक भूमि"
                  : "UP Revenue Code Section 77 — Non-Partitionable Public Parcel"}
              </h4>
              <p className="text-xs text-amber-800 leading-relaxed">
                {lang === "hi"
                  ? "यह गाटा सार्वजनिक उपयोगिता (तालाब/बंजर/ग्राम सभा) के रूप में दर्ज है। धारा 116 के अंतर्गत इसका निजी कुर्रा बटवारा विधिक रूप से वर्जित है। अभिलेखों की यथार्थता हेतु इसे 100% (1/1) एकल सार्वजनिक स्वामित्व के रूप में दर्शाया गया है।"
                  : "This parcel is recorded as public utility (Pond / Gaon Sabha land). Partition under Section 116 is statutorily barred. In accordance with land records, it is reflected under 100% (1/1) public title."}
              </p>
            </div>
          </div>
        )}

        {/* Sharers Table */}
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-court-100 text-court-500">
                <th className="pb-2 font-semibold">{t.lotOrder[lang]}</th>
                <th className="pb-2 font-semibold">{t.partyNameCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.shareCol[lang]}</th>
                <th className="pb-2 font-semibold">{t.colorCol[lang]}</th>
                <th className="pb-2 text-center font-semibold">{t.possessionClaim[lang]}</th>
                <th className="pb-2 text-right font-semibold">{t.removeLot[lang]}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-court-50">
              {sharers.map((s, idx) => (
                <tr key={s.id} className="hover:bg-court-50/50">
                  <td className="py-3 font-mono font-bold text-court-700">
                    {lang === "hi" ? `कुर्रा ${idx + 1}` : `Lot ${idx + 1}`}
                  </td>
                  <td className="py-3">
                    <input
                      type="text"
                      value={s.name || ""}
                      onChange={(e) => handleUpdate(s.id, { name: e.target.value })}
                      className="w-full rounded-md border border-court-200 bg-white px-2.5 py-1.5 font-semibold text-court-900 focus:border-court-900 focus:outline-none"
                    />
                  </td>
                  <td className="py-3">
                    <input
                      type="text"
                      value={s.share || ""}
                      onChange={(e) => handleUpdate(s.id, { share: e.target.value })}
                      className="w-28 rounded-md border border-court-200 bg-white px-2.5 py-1.5 font-mono font-bold text-court-900 focus:border-court-900 focus:outline-none"
                      placeholder="1/3"
                    />
                  </td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-5 w-5 rounded-full border border-court-300 shadow-sm shrink-0"
                        style={{ backgroundColor: s.color_hex || "#3b82f6" }}
                      />
                      <select
                        value={s.color_hex || ""}
                        onChange={(e) => {
                          const chosen = availableColors.find((c) => c.hex === e.target.value);
                          handleUpdate(s.id, {
                            color_hex: e.target.value,
                            color_name_hi: chosen ? chosen.name_hi : s.color_name_hi,
                          });
                        }}
                        className="rounded-md border border-court-200 bg-white px-2 py-1 text-xs text-court-800 focus:border-court-900 focus:outline-none"
                      >
                        {availableColors.map((col) => (
                          <option key={col.hex} value={col.hex}>
                            {lang === "hi" ? col.name_hi : col.name_en}
                          </option>
                        ))}
                      </select>
                    </div>
                  </td>
                  <td className="py-3 text-center">
                    <label className="inline-flex cursor-pointer items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={Boolean(s.possession_wkt)}
                        onChange={(e) =>
                          handleUpdate(s.id, {
                            possession_wkt: e.target.checked ? "CLAIMED_EXISTING" : undefined,
                          })
                        }
                        className="h-4 w-4 rounded border-court-300 text-court-900 focus:ring-0"
                      />
                      <span className="text-[11px] text-court-600">
                        {lang === "hi" ? "दखल दावा" : "Claimed"}
                      </span>
                    </label>
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => handleRemove(s.id)}
                      disabled={sharers.length <= 1}
                      className="rounded-md p-1.5 text-court-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-30"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex flex-wrap gap-2 justify-between border-t border-court-100 pt-4">
          <button
            onClick={handleAdd}
            className="inline-flex items-center gap-1.5 rounded-lg border border-court-200 bg-white px-3 py-2 text-xs font-semibold text-court-700 shadow-sm transition hover:bg-court-50"
          >
            <Plus className="h-4 w-4 text-court-600" />
            <span>{t.addSharerBtn[lang]}</span>
          </button>

          <button
            onClick={handleEqualize}
            className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700 transition hover:bg-indigo-100"
          >
            <Equal className="h-4 w-4 text-indigo-600" />
            <span>{t.equalizeSharesBtn[lang]}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
