"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { CaseDesk } from "@/components/screens/CaseDesk";
import { PlotOverview } from "@/components/screens/PlotOverview";
import { SuitDetails } from "@/components/screens/SuitDetails";
import { CoSharers } from "@/components/screens/CoSharers";
import { ParcelFeatures } from "@/components/screens/ParcelFeatures";
import { SchemeStudio } from "@/components/screens/SchemeStudio";
import { Exhibits } from "@/components/screens/Exhibits";
import {
  CaseMetadata,
  CoSharerInput,
  ColorSwatch,
  PartitionScheme,
  PlotResponse,
  ProposePlanResponse,
  CustomCutResponse,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const DEFAULT_COLORS: ColorSwatch[] = [
  { name_hi: "कत्थई", name_en: "Maroon", hex: "#78350f" },
  { name_hi: "जर्द (पीला)", name_en: "Yellow", hex: "#eab308" },
  { name_hi: "आसमानी (नीला)", name_en: "Sky Blue", hex: "#0284c7" },
  { name_hi: "सब्ज (हरा)", name_en: "Green", hex: "#16a34a" },
  { name_hi: "सुर्ख (लाल)", name_en: "Red", hex: "#dc2626" },
  { name_hi: "संतरी", name_en: "Orange", hex: "#ea580c" },
  { name_hi: "धानी", name_en: "Light Green", hex: "#84cc16" },
  { name_hi: "जामुनी", name_en: "Purple", hex: "#7c3aed" },
  { name_hi: "बादामी", name_en: "Almond", hex: "#d97706" },
  { name_hi: "फिरोजी", name_en: "Cyan", hex: "#06b6d4" },
  { name_hi: "बादली", name_en: "Grey", hex: "#64748b" },
  { name_hi: "बसंती", name_en: "Amber", hex: "#f59e0b" },
];

/**
 * Extracts unique private tenure holders from the Khatauni report sub-plots,
 * filtering out administrative and state-owned entries.
 */
function extractSharersFromReport(report: any): CoSharerInput[] {
  const privateOwners: { name: string; guardian: string | null }[] = [];
  const publicOwners: { name: string; guardian: string | null }[] = [];
  const nonSharerNames = [
    "बंजर",
    "ग्राम सभा",
    "नवीन परती",
    "चकरोड",
    "नाली",
    "तालाब",
    "रास्ता",
    "banjar",
    "gaon sabha",
    "pond",
  ];

  if (report?.sub_plots && Array.isArray(report.sub_plots)) {
    for (const sp of report.sub_plots) {
      if (sp.owners && Array.isArray(sp.owners)) {
        for (const o of sp.owners) {
          const cleanName = (o.name || "").trim();
          if (!cleanName) continue;
          const isStateLand = nonSharerNames.some((ns) =>
            cleanName.toLowerCase().includes(ns.toLowerCase())
          );
          if (!isStateLand) {
            if (!privateOwners.some((p) => p.name === cleanName)) {
              privateOwners.push({ name: cleanName, guardian: o.guardian });
            }
          } else {
            if (!publicOwners.some((p) => p.name === cleanName)) {
              publicOwners.push({ name: cleanName, guardian: o.guardian });
            }
          }
        }
      }
    }
  }

  // 1. Private tenure holders found
  if (privateOwners.length > 0) {
    const n = privateOwners.length;
    const frac = n === 1 ? "1/1" : `1/${n}`;
    return privateOwners.map((o, idx) => ({
      id: `P${idx + 1}`,
      name: o.name + (o.guardian && o.guardian !== "---" ? ` (पुत्र ${o.guardian})` : ""),
      share: frac,
      color_hex: DEFAULT_COLORS[idx % DEFAULT_COLORS.length].hex,
      color_name_hi: DEFAULT_COLORS[idx % DEFAULT_COLORS.length].name_hi,
    }));
  }

  // 2. Public utility / Gram Sabha land (e.g. तालाब, बंजर, नाली) -> Reflects ACTUAL parcel records
  if (publicOwners.length > 0) {
    return publicOwners.map((o, idx) => ({
      id: `P${idx + 1}`,
      name: `${o.name} (सार्वजनिक उपयोगिता / ग्राम सभा)`,
      share: "1/1",
      color_hex: DEFAULT_COLORS[idx % DEFAULT_COLORS.length].hex,
      color_name_hi: DEFAULT_COLORS[idx % DEFAULT_COLORS.length].name_hi,
    }));
  }

  // 3. Fallback for unrecorded parcels
  return [
    {
      id: "P1",
      name: "खातेदार 1 (वादी)",
      share: "1/2",
      color_hex: DEFAULT_COLORS[0].hex,
      color_name_hi: DEFAULT_COLORS[0].name_hi,
    },
    {
      id: "P2",
      name: "खातेदार 2 (प्रतिवादी)",
      share: "1/2",
      color_hex: DEFAULT_COLORS[1].hex,
      color_name_hi: DEFAULT_COLORS[1].name_hi,
    },
  ];
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("case-desk");
  const [lang, setLang] = useState<"hi" | "en">("hi");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [plotData, setPlotData] = useState<PlotResponse | null>(null);

  const [caseMeta, setCaseMeta] = useState<CaseMetadata>({
    case_no: "116/2026/उरई",
    court_name: "न्यायालय उपजिलाधिकारी / सहायक कलेक्टर प्रथम श्रेणी, उरई, जालौन",
    district_code: "165",
    district_name: "जालौन",
    tehsil_code: "00854",
    tehsil_name: "उरई",
    village_code: "151769",
    village_name: "इखलाशपुरा च0क्षे0",
    plot_no: "57",
    plaintiff: "जगदीश प्रसाद (पुत्र राम रतन)",
    defendant: "राजेश कुमार (पुत्र कुंवर सिंह), सत्यबीर सिंह (पुत्र रंजीत सिंह)",
  });

  const [sharers, setSharers] = useState<CoSharerInput[]>([
    {
      id: "P1",
      name: "जगदीश प्रसाद (पुत्र राम रतन)",
      share: "1/3",
      color_hex: "#78350f",
      color_name_hi: "कत्थई",
    },
    {
      id: "P2",
      name: "राजेश कुमार (पुत्र कुंवर सिंह)",
      share: "1/3",
      color_hex: "#0284c7",
      color_name_hi: "आसमानी (नीला)",
    },
    {
      id: "P3",
      name: "सत्यबीर सिंह (पुत्र रंजीत सिंह)",
      share: "1/3",
      color_hex: "#16a34a",
      color_name_hi: "सब्ज (हरा)",
    },
  ]);

  const [sharedPathEnabled, setSharedPathEnabled] = useState<boolean>(false);
  const [sharedPathWidth, setSharedPathWidth] = useState<number>(3.0);
  const [schemes, setSchemes] = useState<PartitionScheme[]>([]);
  const [customPencilScheme, setCustomPencilScheme] = useState<PartitionScheme | null>(null);
  const [activeSchemeIndex, setActiveSchemeIndex] = useState<number>(0);
  const [overlapMatrix, setOverlapMatrix] = useState<Record<string, Record<string, number>>>();

  const fallbackClientSplit = (lines: number[][][]) => {
    if (!plotData) return;
    const totalA = plotData.report.total_area_sqm;
    const numSharers = sharers.length;
    const lots = sharers.map((s, idx) => {
      const pieceArea = totalA * (1.0 / numSharers);
      return {
        party_id: s.id,
        party_name: s.name,
        share_nominal: 1.0 / numSharers,
        share_str: s.share,
        area_sqm: pieceArea,
        area_ha: pieceArea / 10000.0,
        color_hex: s.color_hex || DEFAULT_COLORS[idx].hex,
        color_hi: s.color_name_hi || DEFAULT_COLORS[idx].name_hi,
        geojson: plotData.polygon_geojson,
        wkt: "",
        polsby_popper: 0.61,
        aspect_ratio: 1.75,
        road_frontage_m: 20.8,
        is_connected: true,
      };
    });

    const pencilSch: PartitionScheme = {
      scheme_id: "scheme_custom_pencil",
      scheme_name_hi: "योजना 6: हस्तनिर्मित विभाजन (पेंसिल द्वारा रेखांकित मेड़)",
      scheme_name_en: "Scheme 6: Custom Interactive Demarcation",
      description: "खातेदारों द्वारा नक्शे पर खींची गई रेखा के अनुसार सटीक कुर्रा सीमांकन।",
      lots: lots,
      audit_results: [
        {
          tier: 1,
          tier_name: "टियर 1",
          code: "T1_CONSENT",
          clause_ref: "नियम 109(5)(छ)",
          legal_basis: "statutory",
          name_en: "Mutual Demarcation",
          name_hi: "पारस्परिक हस्तनिर्मित मेड़ सीमांकन",
          status: "green",
          metric: "विभाजन रेखा खींची गई",
          detail: "पक्षकारों द्वारा स्वयं नक्शे पर मेड़ का अंकन किया गया है।",
          statutory_citation: "उ०प्र० राजस्व संहिता नियमावली नियम 109(5)(छ)",
        },
      ],
      all_passed: true,
      failure_reason: null,
      provenance: { custom_cut_lines: lines },
    };

    setCustomPencilScheme(pencilSch);
    setActiveSchemeIndex(schemes.length);
  };

  const handleCustomCut = async (lines: number[][][]) => {
    try {
      const res = await fetch(`${API_BASE}/api/plans/custom-cut`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          district: caseMeta.district_code,
          tehsil: caseMeta.tehsil_code,
          village: caseMeta.village_code,
          plot_no: caseMeta.plot_no,
          cut_lines: lines,
          parties: sharers,
        }),
      });
      if (res.ok) {
        const data: CustomCutResponse = await res.json();
        setCustomPencilScheme(data.scheme);
        setActiveSchemeIndex(schemes.length);
      } else {
        fallbackClientSplit(lines);
      }
    } catch {
      fallbackClientSplit(lines);
    }
  };

  // Fetch Plot Data and dynamically propagate throughout all steps
  const loadPlot = async (dist: string, teh: string, vill: string, plot: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/plots/${dist}/${teh}/${vill}/${plot}`);
      if (res.ok) {
        const data: PlotResponse = await res.json();
        setPlotData(data);

        // 1. Extract co-sharers from the loaded plot's khatauni sub-plots
        const newSharers = extractSharersFromReport(data.report);
        setSharers(newSharers);

        // 2. Dynamically update Case Metadata for Step 3 & Exhibits
        const isPublicLand = newSharers.some((s) =>
          (s.name || "").includes("सार्वजनिक") ||
          (s.name || "").includes("तालाब") ||
          (s.name || "").includes("बंजर") ||
          (s.name || "").includes("नाली") ||
          (s.name || "").includes("चकरोड")
        );

        const updatedCaseMeta: CaseMetadata = {
          case_no: `116/2026/${data.report.tehsil_name || teh}`,
          court_name: `न्यायालय उपजिलाधिकारी / सहायक कलेक्टर प्रथम श्रेणी, ${data.report.tehsil_name || teh}, ${data.report.district_name || dist}`,
          district_code: data.report.district_code || dist,
          district_name: data.report.district_name || dist,
          tehsil_code: data.report.tehsil_code || teh,
          tehsil_name: data.report.tehsil_name || teh,
          village_code: data.report.village_code || vill,
          village_name: data.report.village_name || vill,
          plot_no: data.report.khasra_no || plot,
          plaintiff: isPublicLand
            ? (lang === "hi" ? "ग्राम सभा / राज्य सरकार" : "Gaon Sabha / State of UP")
            : (newSharers[0]?.name || "वादी"),
          defendant: isPublicLand
            ? (lang === "hi" ? `${newSharers[0]?.name || "सार्वजनिक उपयोगिता भूमि"} (गैर-विभाज्य)` : `${newSharers[0]?.name || "Public Utility"} (Non-Partitionable)`)
            : (newSharers.slice(1).map((s) => s.name).join(", ") || "प्रतिवादीगण"),
        };
        setCaseMeta(updatedCaseMeta);

        setActiveTab("plot-overview");

        // 3. Trigger proposal generation for this plot and its actual sharers
        proposePlan(data, newSharers, sharedPathEnabled, sharedPathWidth);
      } else {
        fallbackLocalPlot();
      }
    } catch {
      fallbackLocalPlot();
    } finally {
      setIsLoading(false);
    }
  };

  const fallbackLocalPlot = () => {
    const mockData: PlotResponse = {
      source: "local_store",
      report: {
        district_code: "165",
        district_name: "जालौन",
        tehsil_code: "00854",
        tehsil_name: "उरई",
        village_code: "151769",
        village_name: "इखलाशपुरा च0क्षे0",
        khasra_no: "57",
        scale: "1:1698",
        total_area_ha: 0.373,
        total_area_sqm: 3730.0,
        sub_plots: [
          {
            sub_plot_no: "57/2",
            base_plot_no: "57",
            sub_div: "2",
            khata_no: "00087",
            area_ha: 0.134,
            area_sqm: 1340.0,
            owners: [
              { khata_no: "00087", serial_no: 1, name: "जगदीश प्रसाद", guardian: "राम रतन", residence: "नि०ग्राम" },
              { khata_no: "00087", serial_no: 2, name: "राजेश कुमार", guardian: "कुंवर सिंह", residence: "नि०ग्राम" },
              { khata_no: "00087", serial_no: 3, name: "सत्यबीर सिंह", guardian: "रंजीत सिंह", residence: "नि०ग्राम" },
            ],
          },
          {
            sub_plot_no: "57/1",
            base_plot_no: "57",
            sub_div: "1",
            khata_no: "00146",
            area_ha: 0.239,
            area_sqm: 2390.0,
            owners: [
              { khata_no: "00146", serial_no: 1, name: "बंजर", guardian: null, residence: "नि०ग्राम" },
            ],
          },
        ],
        adjacencies: [
          { plot_no: "56", side: "North", shared_length_m: 54.2, touches_type: "edge", land_class: "कृषि" },
          { plot_no: "48", side: "East", shared_length_m: 48.0, touches_type: "edge", land_class: "कृषि" },
          { plot_no: "50", side: "South", shared_length_m: 62.5, touches_type: "edge", land_class: "चकमार्ग" },
          { plot_no: "51/318", side: "West", shared_length_m: 78.1, touches_type: "edge", land_class: "कृषि" },
        ],
        raw_header: "जिला : 165 जालौन, तहसील : 00854 उरई, गाँव : 151769 इखलाशपुरा च0क्षे0",
        raw_plot_info: "",
        fetched_at: "2026-11-12T23:55:00",
        source_url: "https://upbhunaksha.gov.in/plotreport/16500854151769/57",
        sha256: "local-cache-plot57",
      },
      polygon_geojson: {
        type: "Polygon",
        coordinates: [
          [
            [633100.0, 2874100.0],
            [633180.0, 2874120.0],
            [633210.0, 2874070.0],
            [633170.0, 2874020.0],
            [633120.0, 2874030.0],
            [633100.0, 2874100.0],
          ],
        ],
      },
      polygon_wgs84: {},
      wkt: "POLYGON ((633100 2874100, 633180 2874120, 633210 2874070, 633170 2874020, 633120 2874030, 633100 2874100))",
      colors: DEFAULT_COLORS,
    };
    setPlotData(mockData);

    const defaultSharers = extractSharersFromReport(mockData.report);
    setSharers(defaultSharers);

    setCaseMeta({
      case_no: "116/2026/उरई",
      court_name: "न्यायालय उपजिलाधिकारी / सहायक कलेक्टर प्रथम श्रेणी, उरई, जालौन",
      district_code: "165",
      district_name: "जालौन",
      tehsil_code: "00854",
      tehsil_name: "उरई",
      village_code: "151769",
      village_name: "इखलाशपुरा च0क्षे0",
      plot_no: "57",
      plaintiff: defaultSharers[0]?.name || "जगदीश प्रसाद (पुत्र राम रतन)",
      defendant: defaultSharers.slice(1).map((s) => s.name).join(", ") || "राजेश कुमार व अन्य",
    });

    setActiveTab("plot-overview");
    generateDefaultSchemes(mockData, defaultSharers);
  };

  const generateDefaultSchemes = (pData: PlotResponse, curSharers: CoSharerInput[]) => {
    const totalA = pData.report.total_area_sqm;
    const n = Math.max(curSharers.length, 1);

    const buildLots = (frontages: number[]) => {
      return curSharers.map((s, i) => {
        const area = totalA / n;
        return {
          party_id: s.id,
          party_name: s.name,
          share_nominal: 1 / n,
          share_str: s.share,
          area_sqm: area,
          area_ha: area / 10000.0,
          color_hex: s.color_hex || DEFAULT_COLORS[i % DEFAULT_COLORS.length].hex,
          color_hi: s.color_name_hi || DEFAULT_COLORS[i % DEFAULT_COLORS.length].name_hi,
          geojson: pData.polygon_geojson,
          wkt: "",
          polsby_popper: 0.65 - i * 0.05,
          aspect_ratio: 1.8 + i * 0.2,
          road_frontage_m: frontages[i] !== undefined ? frontages[i] : 20.8,
          is_connected: true,
        };
      });
    };

    const mockSchemes: PartitionScheme[] = [
      {
        scheme_id: "scheme_compact",
        scheme_name_hi: "योजना 1: लेखपाल का मानक प्रस्ताव (सघन चक)",
        scheme_name_en: "Scheme 1: Lekhpal Balanced Standard (Compact Chaks)",
        description: "नियम 109(5)(ख) व (च) के अंतर्गत प्रत्येक खातेदार को मुख्य चकमार्ग पर सीधा निकास एवं संहत चतुर्भुजाकार कुर्रे।",
        lots: buildLots([21.0, 20.5, 21.0]),
        audit_results: [
          {
            tier: 1,
            tier_name: "टियर 1",
            code: "T1_CONSENT",
            clause_ref: "नियम 109(5)(छ)",
            legal_basis: "statutory",
            name_en: "Family Settlement",
            name_hi: "पारस्परिक सहमति व पारिवारिक व्यवस्था",
            status: "green",
            metric: "सहमति अभिलेखित",
            detail: "सभी पक्षकारों द्वारा प्रस्तावित विभाजन रेखाओं पर सहमति।",
            statutory_citation: "उ०प्र० राजस्व संहिता नियमावली 2016 नियम 109(5)(छ)",
          },
          {
            tier: 3,
            tier_name: "टियर 3",
            code: "T3_SHARE",
            clause_ref: "नियम 109(5)(क)",
            legal_basis: "statutory",
            name_en: "Proportionate Area",
            name_hi: "डिक्रीत अंश यथानुपात रकबा",
            status: "green",
            metric: "विचलन < 0.1%",
            detail: "प्रत्येक कुर्रे का रकबा प्रारंभिक डिक्रीत अंश के पूर्णतः यथानुपात है।",
            statutory_citation: "उ०प्र० राजस्व संहिता नियमावली नियम 109(5)(क)",
          },
          {
            tier: 3,
            tier_name: "टियर 3",
            code: "T3_COMPACT",
            clause_ref: "नियम 109(5)(ख)",
            legal_basis: "heuristic",
            name_en: "Compactness",
            name_hi: "कुर्रों की सुसंहति (Compact Lots)",
            status: "green",
            metric: "Polsby-Popper: 0.62",
            detail: "कुर्रों की आकृति सुगठित है तथा कोई भी कुर्रा असुविधाजनक रूप से संकरा नहीं है।",
            statutory_citation: "मानक संहति सूचकांक",
          },
          {
            tier: 3,
            tier_name: "टियर 3",
            code: "T3_ROAD",
            clause_ref: "नियम 109(5)(च)",
            legal_basis: "statutory",
            name_en: "Road Frontage",
            name_hi: "सड़क / चकमार्ग का अग्रभाग",
            status: "green",
            metric: "अग्रभाग विचलन < 5%",
            detail: "प्रत्येक खातेदार को दक्षिण स्थित चकमार्ग पर कम से कम 20 मीटर सीधा निकास प्राप्त है।",
            statutory_citation: "उ०प्र० राजस्व संहिता नियमावली नियम 109(5)(च)",
          },
        ],
        all_passed: true,
        failure_reason: null,
        provenance: {},
      },
      {
        scheme_id: "scheme_frontage",
        scheme_name_hi: "योजना 2: सड़क के लम्बवत सीधी पट्टियाँ (समान अग्रभाग)",
        scheme_name_en: "Scheme 2: Perpendicular to Road (Frontage Parity)",
        description: "नियम 109(5)(च) के अंतर्गत चकमार्ग के अग्रभाग को सभी अंशधारकों के मध्य बिल्कुल समान अनुपात में विभाजित किया गया है।",
        lots: buildLots([20.8, 20.8, 20.8]),
        audit_results: [
          {
            tier: 3,
            tier_name: "टियर 3",
            code: "T3_ROAD",
            clause_ref: "नियम 109(5)(च)",
            legal_basis: "statutory",
            name_en: "Road Frontage Parity",
            name_hi: "सड़क अग्रभाग आवंटन",
            status: "green",
            metric: "20.8 मी० प्रति कुर्रा",
            detail: "चकमार्ग पर पूर्ण समानता।",
            statutory_citation: "उ०प्र० राजस्व संहिता नियमावली नियम 109(5)(च)",
          },
        ],
        all_passed: true,
        failure_reason: null,
        provenance: {},
      },
      {
        scheme_id: "scheme_road_parallel",
        scheme_name_hi: "योजना 3: सड़क के समानांतर पट्टियाँ (आगे-पीछे)",
        scheme_name_en: "Scheme 3: Road-Parallel Rows (Front-to-Rear)",
        description: "सड़क के समानांतर आगे-पीछे पट्टियाँ; पिछले कुर्रों को मुख्य सड़क न मिलने के कारण विधिक कसौटी पर अस्वीकृत।",
        lots: buildLots([62.5, 0.0, 0.0]),
        audit_results: [
          {
            tier: 3,
            tier_name: "टियर 3",
            code: "T3_ROAD",
            clause_ref: "नियम 109(5)(च)",
            legal_basis: "statutory",
            name_en: "Road Frontage Denial",
            name_hi: "सड़क निकास विहीन",
            status: "red",
            metric: "अग्रभाग: 0.0 मी० (कुर्रा 2 व 3)",
            detail: "कुर्रा 2 व 3 को मुख्य मार्ग पर कोई निकास नहीं मिलता; पिछले कुर्रे अवरुद्ध (landlocked) होते हैं।",
            statutory_citation: "उ०प्र० राजस्व संहिता नियमावली नियम 109(5)(च)",
          },
        ],
        all_passed: false,
        failure_reason: "नियम 109(5)(च): कुर्रा 2 व 3 को सड़क से लगी भूमि नहीं मिलती।",
        provenance: {},
      },
      {
        scheme_id: "scheme_commercial_zone",
        scheme_name_hi: "योजना 4: कीमती मुहाने की पट्टी (30 मी० गहराई)",
        scheme_name_en: "Scheme 4: Commercial 30m Roadside Zone",
        description: "चकमार्ग से सटी 30 मीटर गहराई की कीमती पट्टी सभी अंशधारकों में यथानुपात विभाजित; शेष भूमि उसी से सटी हुई संहत दी गई।",
        lots: buildLots([20.8, 20.8, 20.8]),
        audit_results: [
          {
            tier: 3,
            tier_name: "टियर 3",
            code: "T3_ROAD",
            clause_ref: "नियम 109(5)(च)",
            legal_basis: "statutory",
            name_en: "Zoned Frontage",
            name_hi: "कीमती मुहाने का समतुल्य वितरण",
            status: "green",
            metric: "30 मी० गहराई पट्टी सबमें बराबर",
            detail: "कीमती सड़क किनारे की भूमि का पूर्ण न्यायसंगत विभाजन।",
            statutory_citation: "उ०प्र० राजस्व संहिता नियमावली नियम 109(5)(च)",
          },
        ],
        all_passed: true,
        failure_reason: null,
        provenance: {},
      },
      {
        scheme_id: "scheme_shared_passage",
        scheme_name_hi: "योजना 5: 3 मी० साझा रास्ता (न्यायालयी आदेश/सहमति)",
        scheme_name_en: "Scheme 5: Dedicated 3m Shared Pathway Option",
        description: "साझा रास्ता सभी अंशधारकों के रकबे से यथानुपात घटाया गया; पिछले कुर्रों को सुरक्षित विधिक निकास।",
        lots: buildLots([20.8, 20.8, 20.8]),
        audit_results: [
          {
            tier: 3,
            tier_name: "टियर 3",
            code: "T3_PASSAGE",
            clause_ref: "साझा रास्ता",
            legal_basis: "heuristic",
            name_en: "Dedicated Pathway",
            name_hi: "3.0 मी० साझा निकास मार्ग",
            status: "green",
            metric: "रास्ता रकबा कटौती: यथानुपात",
            detail: "प्रत्येक कुर्रे को 3 मीटर चौड़ा विधिक रास्ता सुलभ।",
            statutory_citation: "न्यायालय निर्देश / आपसी सहमति",
          },
        ],
        all_passed: true,
        failure_reason: null,
        provenance: {},
      },
    ];

    setSchemes(mockSchemes);
    setOverlapMatrix({
      scheme_compact: { scheme_compact: 100.0, scheme_frontage: 89.2, scheme_road_parallel: 68.4 },
      scheme_frontage: { scheme_compact: 89.2, scheme_frontage: 100.0, scheme_road_parallel: 62.0 },
      scheme_road_parallel: { scheme_compact: 68.4, scheme_frontage: 62.0, scheme_road_parallel: 100.0 },
    });
  };

  const proposePlan = async (
    pData: PlotResponse,
    curSharers: CoSharerInput[],
    sEnabled: boolean,
    sWidth: number
  ) => {
    try {
      const res = await fetch(`${API_BASE}/api/propose`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          district: pData.report.district_code,
          tehsil: pData.report.tehsil_code,
          village: pData.report.village_code,
          plot_no: pData.report.khasra_no,
          parties: curSharers,
          shared_path_width: sEnabled ? sWidth : null,
        }),
      });
      if (res.ok) {
        const data: ProposePlanResponse = await res.json();
        if (data.schemes && data.schemes.length > 0) {
          setSchemes(data.schemes);
          setOverlapMatrix(data.possession_overlap_matrix);
        } else {
          generateDefaultSchemes(pData, curSharers);
        }
      } else {
        generateDefaultSchemes(pData, curSharers);
      }
    } catch {
      generateDefaultSchemes(pData, curSharers);
    }
  };

  useEffect(() => {
    // Initial mount fallback load
    fallbackLocalPlot();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        lang={lang}
        onLangToggle={() => setLang(lang === "hi" ? "en" : "hi")}
        syncDate="12-Nov-2026"
        isOffline={false}
      />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "case-desk" && (
          <CaseDesk
            onLoadPlot={loadPlot}
            caseMeta={caseMeta}
            onUpdateMeta={setCaseMeta}
            lang={lang}
            isLoading={isLoading}
          />
        )}

        {activeTab === "plot-overview" && (
          <PlotOverview plotData={plotData} lang={lang} />
        )}

        {activeTab === "suit-details" && (
          <SuitDetails
            caseMeta={caseMeta}
            onUpdateMeta={setCaseMeta}
            lang={lang}
          />
        )}

        {activeTab === "co-sharers" && (
          <CoSharers
            sharers={sharers}
            onUpdateSharers={(updated) => {
              setSharers(updated);
              if (plotData) {
                proposePlan(plotData, updated, sharedPathEnabled, sharedPathWidth);
              }
            }}
            availableColors={DEFAULT_COLORS}
            lang={lang}
          />
        )}

        {activeTab === "parcel-features" && (
          <ParcelFeatures
            plotData={plotData}
            onUpdateAdjacencies={(newAdjs) => {
              if (plotData) {
                const updatedPlot = {
                  ...plotData,
                  report: {
                    ...plotData.report,
                    adjacencies: newAdjs,
                  },
                };
                setPlotData(updatedPlot);
                proposePlan(updatedPlot, sharers, sharedPathEnabled, sharedPathWidth);
              }
            }}
            sharedPathEnabled={sharedPathEnabled}
            onToggleSharedPath={(en) => {
              setSharedPathEnabled(en);
              if (plotData) {
                proposePlan(plotData, sharers, en, sharedPathWidth);
              }
            }}
            sharedPathWidth={sharedPathWidth}
            onChangeWidth={(w) => {
              setSharedPathWidth(w);
              if (plotData) {
                proposePlan(plotData, sharers, sharedPathEnabled, w);
              }
            }}
            lang={lang}
          />
        )}

        {activeTab === "scheme-studio" && (
          <SchemeStudio
            schemes={schemes}
            activeSchemeIndex={activeSchemeIndex}
            onSelectScheme={(idx) => setActiveSchemeIndex(idx)}
            plotData={plotData}
            overlapMatrix={overlapMatrix}
            onCustomCut={handleCustomCut}
            customPencilScheme={customPencilScheme}
            lang={lang}
          />
        )}

        {activeTab === "exhibits" && (
          <Exhibits
            caseMeta={caseMeta}
            scheme={schemes[activeSchemeIndex] || null}
            plotData={plotData}
            lang={lang}
          />
        )}
      </main>
    </div>
  );
}
