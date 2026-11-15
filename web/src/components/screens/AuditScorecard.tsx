"use client";

import React, { useState } from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info, ChevronDown, ChevronUp } from "lucide-react";
import { AuditScorecard as AuditType } from "@/types/api";
import { Lang } from "@/utils/i18n";

interface AuditScorecardProps {
  auditResults: AuditType[];
  allPassed: boolean;
  failureReason?: string | null;
  lang: Lang;
}

export function AuditScorecard({
  auditResults,
  allPassed,
  failureReason,
  lang,
}: AuditScorecardProps) {
  const [expandedCode, setExpandedCode] = useState<string | null>(null);

  const toggleExpand = (code: string) => {
    setExpandedCode(expandedCode === code ? null : code);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "green":
        return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
      case "amber":
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case "red":
        return <XCircle className="h-4 w-4 text-rose-600" />;
      default:
        return <Info className="h-4 w-4 text-court-400" />;
    }
  };

  const getTagBadge = (basis: string) => {
    switch (basis) {
      case "statutory":
        return (
          <span className="rounded bg-sky-100 px-1.5 py-0.5 text-[10px] font-bold uppercase text-sky-800">
            {lang === "hi" ? "वैधानिक" : "Statutory"}
          </span>
        );
      case "case-law":
        return (
          <span className="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-bold uppercase text-purple-800">
            {lang === "hi" ? "नज़ीर" : "Case-Law"}
          </span>
        );
      case "heuristic":
      default:
        return (
          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700">
            {lang === "hi" ? "मानक" : "Heuristic"}
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Overall Status Banner */}
      <div
        className={`flex items-center justify-between rounded-xl border p-4 ${
          allPassed
            ? "border-emerald-200 bg-emerald-50/70 text-emerald-950"
            : "border-rose-200 bg-rose-50/70 text-rose-950"
        }`}
      >
        <div className="flex items-center gap-3">
          {allPassed ? (
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-sm shrink-0">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          ) : (
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-600 text-white shadow-sm shrink-0">
              <XCircle className="h-5 w-5" />
            </div>
          )}
          <div>
            <h4 className="text-sm font-bold">
              {allPassed
                ? (lang === "hi" ? "नियम 109(5) त्रिस्तरीय विधिक ऑडिट: पूर्ण स्वीकृत" : "Rule 109(5) Three-Tier Audit: Fully Compliant")
                : (lang === "hi" ? "नियम 109(5) विधिक ऑडिट: अपूर्ण / संशोधन आवश्यक" : "Rule 109(5) Audit: Amendments Required")}
            </h4>
            <p className="text-xs text-court-600 mt-0.5">
              {allPassed
                ? (lang === "hi"
                    ? "प्रस्तावित सभी कुर्रे राजस्व संहिता नियमावली के वैधानिक व तकनीकी मानकों के अनुकूल हैं।"
                    : "All proposed lots comply strictly with UP Revenue Code statutory and heuristic standards.")
                : failureReason || (lang === "hi"
                    ? "कुछ कुर्रे विधिक न्यूनतम सीमा या सड़क अग्रभाग मानक का उल्लंघन करते हैं।"
                    : "Certain lots violate minimum width or road frontage criteria.")}
            </p>
          </div>
        </div>
      </div>

      {/* Audit Checklist Table */}
      <div className="rounded-xl border border-court-200 bg-white shadow-sm overflow-hidden">
        <div className="border-b border-court-100 bg-court-50/60 px-5 py-3">
          <h5 className="text-xs font-bold uppercase tracking-wider text-court-700">
            {lang === "hi"
              ? "नियम 109(5) क्रमबद्ध टियर अनुपालन सूची"
              : "Rule 109(5) Ordered Tier Compliance Checklist"}
          </h5>
        </div>

        <div className="divide-y divide-court-100">
          {auditResults.map((item) => {
            const isExpanded = expandedCode === item.code;
            return (
              <div key={item.code} className="p-4 hover:bg-court-50/40 transition">
                <div
                  onClick={() => toggleExpand(item.code)}
                  className="flex items-start justify-between cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">{getStatusIcon(item.status)}</div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-court-900">
                          {item.clause_ref}
                        </span>
                        {getTagBadge(item.legal_basis)}
                        <span className="text-xs font-bold text-court-800">
                          {lang === "hi" ? item.name_hi : item.name_en}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-court-600 leading-relaxed">
                        {item.detail}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0 ml-4">
                    <span className="font-mono text-xs font-bold text-court-700">
                      {item.metric}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-court-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-court-400" />
                    )}
                  </div>
                </div>

                {isExpanded && item.statutory_citation && (
                  <div className="mt-3 ml-7 rounded-md bg-court-50 p-3 text-[11px] text-court-700 border border-court-200">
                    <span className="font-bold text-court-900 block mb-0.5">
                      {lang === "hi" ? "विधिक संदर्भ व स्रोत:" : "Statutory Authority:"}
                    </span>
                    {item.statutory_citation}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
