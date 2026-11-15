"use client";

import React from "react";
import {
  Landmark,
  Layers,
  MapPin,
  Scale,
  Users,
  FileText,
  SlidersHorizontal,
  Wifi,
  Database,
  Languages,
} from "lucide-react";
import { translations, Lang } from "@/utils/i18n";

interface NavbarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  lang: Lang;
  onLangToggle: () => void;
  syncDate?: string;
  isOffline?: boolean;
}

export function Navbar({
  activeTab,
  onTabChange,
  lang,
  onLangToggle,
  syncDate = "12-Nov-2026",
  isOffline = false,
}: NavbarProps) {
  const t = translations;

  const tabs = [
    { id: "case-desk", label: t.tabCaseDesk[lang], icon: Landmark },
    { id: "plot-overview", label: t.tabPlotOverview[lang], icon: MapPin },
    { id: "suit-details", label: t.tabSuitDetails[lang], icon: FileText },
    { id: "co-sharers", label: t.tabCoSharers[lang], icon: Users },
    { id: "parcel-features", label: t.tabFeatures[lang], icon: SlidersHorizontal },
    { id: "scheme-studio", label: t.tabSchemeStudio[lang], icon: Scale },
    { id: "exhibits", label: t.tabExhibits[lang], icon: Layers },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-court-200 bg-white/95 backdrop-blur-md">
      {/* Top utility row */}
      <div className="flex h-14 items-center justify-between border-b border-court-100 px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-court-900 text-white shadow-sm">
            <Scale className="h-4.5 w-4.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-court-500">
                {t.courtSubtitle[lang]}
              </span>
              <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                {t.sectionBadge[lang]}
              </span>
            </div>
            <h1 className="text-sm font-bold text-court-900">
              {t.appTitle[lang]}
            </h1>
          </div>
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          {/* Data freshness badge */}
          <div className="flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50/70 px-2.5 py-1 text-xs text-emerald-800">
            <Database className="h-3.5 w-3.5 text-emerald-600" />
            <span>
              {t.dataDate[lang]}: <strong className="font-mono">{syncDate}</strong>
            </span>
          </div>

          <div className="flex items-center gap-1.5 rounded-md border border-court-200 bg-court-50 px-2.5 py-1 text-xs text-court-700">
            <Wifi className="h-3.5 w-3.5 text-emerald-600" />
            <span>{isOffline ? t.offlineMode[lang] : t.localFirstBadge[lang]}</span>
          </div>

          {/* Universal Language Switcher */}
          <div className="flex items-center rounded-lg border border-court-200 bg-court-50 p-0.5 shadow-sm">
            <button
              onClick={() => {
                if (lang !== "hi") onLangToggle();
              }}
              className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-bold transition ${
                lang === "hi"
                  ? "bg-court-900 text-white shadow-sm"
                  : "text-court-600 hover:text-court-900"
              }`}
            >
              <Languages className="h-3.5 w-3.5" />
              <span>हिंदी</span>
            </button>
            <button
              onClick={() => {
                if (lang !== "en") onLangToggle();
              }}
              className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-bold transition ${
                lang === "en"
                  ? "bg-court-900 text-white shadow-sm"
                  : "text-court-600 hover:text-court-900"
              }`}
            >
              <span>English</span>
            </button>
          </div>
        </div>
      </div>

      {/* Navigation tabs row */}
      <nav className="flex space-x-1 overflow-x-auto px-6 py-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-3.5 py-2 text-xs font-semibold transition ${
                isActive
                  ? "bg-court-900 text-white shadow-sm"
                  : "text-court-600 hover:bg-court-100 hover:text-court-900"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
}
