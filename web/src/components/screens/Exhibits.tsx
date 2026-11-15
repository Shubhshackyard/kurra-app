"use client";

import React, { useState } from "react";
import { Printer, FileText } from "lucide-react";
import { CaseMetadata, PartitionScheme, PlotResponse } from "@/types/api";
import { PlotCanvas } from "../PlotCanvas";
import { translations, Lang } from "@/utils/i18n";

interface ExhibitsProps {
  caseMeta: CaseMetadata;
  scheme: PartitionScheme | null;
  plotData: PlotResponse | null;
  lang: Lang;
}

export function Exhibits({ caseMeta, scheme, plotData, lang }: ExhibitsProps) {
  const [activeDoc, setActiveDoc] = useState<"naksha" | "lekhpal_report" | "decree">("naksha");
  const t = translations;

  if (!scheme || !plotData) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-court-300 p-12 text-center">
        <FileText className="h-10 w-10 text-court-400" />
        <h3 className="mt-3 text-base font-bold text-court-800">
          {t.noSchemeSelected[lang]}
        </h3>
        <p className="mt-1 text-xs text-court-500">
          {t.selectSchemePrompt[lang]}
        </p>
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  const report = plotData.report;

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-col gap-4 rounded-xl border border-court-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between print:hidden">
        <div>
          <h3 className="text-base font-bold text-court-900">
            {t.exhibitsTitle[lang]}
          </h3>
          <p className="text-xs text-court-500">
            {t.exhibitsSub[lang]}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Document Switcher */}
          <div className="inline-flex rounded-lg border border-court-200 bg-court-50 p-1">
            <button
              onClick={() => setActiveDoc("naksha")}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
                activeDoc === "naksha" ? "bg-white text-court-900 shadow-sm" : "text-court-600 hover:text-court-900"
              }`}
            >
              {t.tabNaksha[lang]}
            </button>
            <button
              onClick={() => setActiveDoc("lekhpal_report")}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
                activeDoc === "lekhpal_report" ? "bg-white text-court-900 shadow-sm" : "text-court-600 hover:text-court-900"
              }`}
            >
              {t.tabLekhpalReport[lang]}
            </button>
            <button
              onClick={() => setActiveDoc("decree")}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
                activeDoc === "decree" ? "bg-white text-court-900 shadow-sm" : "text-court-600 hover:text-court-900"
              }`}
            >
              {t.tabDecree[lang]}
            </button>
          </div>

          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 rounded-lg bg-court-900 px-4 py-2 text-xs font-bold text-white shadow-sm transition hover:bg-court-800"
          >
            <Printer className="h-4 w-4" />
            <span>{t.printBtn[lang]}</span>
          </button>
        </div>
      </div>

      {/* Printable A4 Canvas Container */}
      <div className="mx-auto max-w-[850px] rounded-2xl border border-court-200 bg-white p-8 sm:p-12 shadow-md print:border-none print:shadow-none print:p-0">
        {/* Court Header */}
        <div className="text-center border-b-2 border-court-900 pb-5">
          <span className="text-xs font-bold uppercase tracking-widest text-court-600">
            {t.courtSubtitle[lang]}
          </span>
          <h2 className="mt-1 text-xl font-bold text-court-900 sm:text-2xl">
            {caseMeta.court_name || (lang === "hi" ? "न्यायालय उपजिलाधिकारी / सहायक कलेक्टर प्रथम श्रेणी, उरई, जालौन" : "Court of SDM / Assistant Collector 1st Class, Orai, Jalaun")}
          </h2>
          <div className="mt-2 inline-flex items-center gap-2 rounded-full border border-court-300 bg-court-50 px-3 py-0.5 text-xs font-semibold text-court-800">
            <span>
              {lang === "hi"
                ? "अन्तर्गत धारा 116 / नियम 109(5) उ०प्र० राजस्व संहिता 2006"
                : "Under Section 116 / Rule 109(5) UP Revenue Code 2006"}
            </span>
          </div>
        </div>

        {/* Suit Meta Subheader */}
        <div className="mt-4 grid grid-cols-2 gap-4 border-b border-court-200 pb-4 text-xs">
          <div>
            <div>
              <span className="font-semibold text-court-600">{t.caseNoCol[lang]}:</span>{" "}
              <strong className="font-mono text-court-900">{caseMeta.case_no}</strong>
            </div>
            <div className="mt-1">
              <span className="font-semibold text-court-600">{t.plaintiffLabel[lang]}:</span>{" "}
              <strong className="text-court-900">{caseMeta.plaintiff}</strong>
            </div>
            <div className="mt-1">
              <span className="font-semibold text-court-600">{t.defendantLabel[lang]}:</span>{" "}
              <strong className="text-court-900">{caseMeta.defendant}</strong>
            </div>
          </div>
          <div className="text-right">
            <div>
              <span className="font-semibold text-court-600">{lang === "hi" ? "मौजा:" : "Village:"}</span>{" "}
              <strong className="text-court-900">{report.village_name} ({report.village_code})</strong>
            </div>
            <div className="mt-1">
              <span className="font-semibold text-court-600">{lang === "hi" ? "तहसील व जिला:" : "Tehsil & District:"}</span>{" "}
              <strong className="text-court-900">{report.tehsil_name}, {report.district_name}</strong>
            </div>
            <div className="mt-1">
              <span className="font-semibold text-court-600">{lang === "hi" ? "गाटा संख्या व रकबा:" : "Plot No & Area:"}</span>{" "}
              <strong className="text-court-900">
                {lang === "hi" ? `गाटा ${report.khasra_no} (${report.total_area_ha} हे०)` : `Plot ${report.khasra_no} (${report.total_area_ha} Ha)`}
              </strong>
            </div>
          </div>
        </div>

        {/* 1. NAKSHA EXHIBIT */}
        {activeDoc === "naksha" && (
          <div className="mt-6 space-y-6">
            <div className="text-center">
              <h3 className="text-base font-bold text-court-900">
                {lang === "hi"
                  ? `प्रस्तावित कुर्रा फांट व नजरी नक्शा (योजना: ${scheme.scheme_name_hi})`
                  : `Proposed Demarcation Map Sheet (${scheme.scheme_name_en})`}
              </h3>
              <span className="text-xs text-court-500">
                {lang === "hi"
                  ? `पैमाना: ${report.scale || "1:1698"} (प्रक्षेपण: EPSG:32644 UTM Zone 44N)`
                  : `Scale: ${report.scale || "1:1698"} (CRS: EPSG:32644 UTM Zone 44N)`}
              </span>
            </div>

            {/* Cadastral Map View */}
            <div className="overflow-hidden rounded-xl border border-court-300">
              <PlotCanvas
                basePolygon={plotData.polygon_geojson}
                lots={scheme.lots}
                scaleStr={report.scale || "1:1698"}
                height={420}
                lang={lang}
              />
            </div>

            {/* Sanket Suchi (Legend & Lot Specifications) Table */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-court-800">
                {t.sanketSuchi[lang]}
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border border-court-200">
                  <thead className="bg-court-100 text-court-800">
                    <tr>
                      <th className="p-2 border-r border-court-200">{t.lotNoHeader[lang]}</th>
                      <th className="p-2 border-r border-court-200">{t.colorHeader[lang]}</th>
                      <th className="p-2 border-r border-court-200">{t.sharerNameHeader[lang]}</th>
                      <th className="p-2 border-r border-court-200">{t.shareHeader[lang]}</th>
                      <th className="p-2 border-r border-court-200">{t.areaSqmHeader[lang]}</th>
                      <th className="p-2 border-r border-court-200">{t.areaHaHeader[lang]}</th>
                      <th className="p-2">{t.frontageHeader[lang]}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-court-200">
                    {scheme.lots.map((l, i) => (
                      <tr key={l.party_id}>
                        <td className="p-2 font-bold border-r border-court-200">
                          {lang === "hi" ? `कुर्रा ${i + 1}` : `Lot ${i + 1}`}
                        </td>
                        <td className="p-2 border-r border-court-200">
                          <span
                            className="inline-block h-3.5 w-3.5 rounded-sm mr-1.5 align-middle border border-court-300"
                            style={{ backgroundColor: l.color_hex }}
                          />
                          {lang === "hi" ? l.color_hi : l.color_hex}
                        </td>
                        <td className="p-2 font-semibold border-r border-court-200">{l.party_name}</td>
                        <td className="p-2 font-mono border-r border-court-200">{l.share_str}</td>
                        <td className="p-2 font-mono font-bold border-r border-court-200">{l.area_sqm.toFixed(1)}</td>
                        <td className="p-2 font-mono border-r border-court-200">{l.area_ha.toFixed(4)}</td>
                        <td className="p-2 font-mono">{l.road_frontage_m.toFixed(1)} m</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Field Stake-Out Measurement Tape Sheet */}
            <div className="rounded-lg border border-court-200 bg-court-50 p-4 text-xs">
              <h5 className="font-bold text-court-900 mb-2">
                {t.tapeMeasureSheet[lang]}
              </h5>
              <p className="text-court-600 leading-relaxed text-[11px]">
                {t.tapeDesc[lang]}
              </p>
            </div>

            {/* Signatures */}
            <div className="mt-12 grid grid-cols-3 gap-4 text-center text-xs pt-8 border-t border-court-200">
              <div>
                <span className="block font-bold text-court-800">{t.sigLekhpal[lang]}</span>
                <span className="mt-1 block text-[11px] text-court-500">
                  {lang === "hi" ? `मौजा ${report.village_name}` : `Village ${report.village_name}`}
                </span>
              </div>
              <div>
                <span className="block font-bold text-court-800">{t.sigRI[lang]}</span>
                <span className="mt-1 block text-[11px] text-court-500">
                  {lang === "hi" ? `वृत्त ${report.tehsil_name}` : `Circle ${report.tehsil_name}`}
                </span>
              </div>
              <div>
                <span className="block font-bold text-court-800">{t.sigSDM[lang]}</span>
                <span className="mt-1 block text-[11px] text-court-500">
                  {lang === "hi" ? `तहसील ${report.tehsil_name}` : `Tehsil ${report.tehsil_name}`}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* 2. LEKHPAL REPORT */}
        {activeDoc === "lekhpal_report" && (
          <div className="mt-6 space-y-5 text-xs text-court-800 leading-relaxed">
            <h3 className="text-sm font-bold text-center text-court-900 border-b pb-2">
              {lang === "hi" ? "आख्या राजस्व लेखपाल बाबत कुर्रा बटवारा" : "Field Verification Report of Revenue Lekhpal"}
            </h3>
            <p>
              {lang === "hi"
                ? `महोदय, उपर्युक्त वाद में न्यायालय के आदेशानुसार मौजा ${report.village_name}, गाटा संख्या ${report.khasra_no}, कुल रकबा ${report.total_area_ha} हेक्टेयर का मौका मुआयना किया गया। पक्षकारों के डिक्रीत अंशों एवं मौके पर उनके वर्तमान काश्तकारी कब्जे की जांच की गई।`
                : `Sir, in compliance with the orders of the Court, on-ground inspection of Plot No ${report.khasra_no}, Village ${report.village_name}, area ${report.total_area_ha} Ha was conducted. The decreed shares and ground possession were verified.`}
            </p>
            <p>
              {lang === "hi"
                ? `उ०प्र० राजस्व संहिता नियमावली 2016 के नियम 109(5) के समस्त उपबंधों के अनुपालन में कुर्रा निर्धारण किया गया है। मुख्य चकमार्ग (गाटा संख्या 50) पर प्रत्येक खातेदार को समतुल्य एवं सुगम निकास दिया गया है तथा सभी कुर्रे संहत व सुगठित चतुर्भुजाकार निर्मित किए गए हैं।`
                : `Partition scheme has been formulated in strict adherence to Rule 109(5) of UP Revenue Code Rules 2016. Every co-sharer is allotted proportionate road frontage on the chakroad (Plot 50), and all lots form compact quad parcels.`}
            </p>
            <div className="pt-8 text-right font-bold">
              <span>{t.sigLekhpal[lang]}</span>
            </div>
          </div>
        )}

        {/* 3. PRELIMINARY DECREE */}
        {activeDoc === "decree" && (
          <div className="mt-6 space-y-5 text-xs text-court-800 leading-relaxed">
            <h3 className="text-sm font-bold text-center text-court-900 border-b pb-2">
              {lang === "hi" ? "प्रारंभिक डिक्री (धारा 116 उ०प्र० राजस्व संहिता 2006)" : "Preliminary Decree (Section 116 UP Revenue Code 2006)"}
            </h3>
            <p>
              {lang === "hi"
                ? `यह वाद वादी द्वारा प्रतिवादीगण के विरुद्ध गाटा संख्या ${report.khasra_no} के विभाजन हेतु प्रस्तुत किया गया। पत्रावली पर उपलब्ध अभिलेखों एवं साक्ष्यों के आधार पर पक्षकारों के अंश निम्नानुसार तय किए जाते हैं:`
                : `This suit was instituted for partition of Plot No ${report.khasra_no}. Based on the cadastral records and evidence on record, the respective shares of the parties are decreed as follows:`}
            </p>
            <ul className="list-disc pl-5 space-y-1">
              {scheme.lots.map((l) => (
                <li key={l.party_id}>
                  <strong>{l.party_name}:</strong> {l.share_str} {lang === "hi" ? "अंश" : "share"} ({l.area_ha.toFixed(4)} Ha)
                </li>
              ))}
            </ul>
            <div className="pt-8 text-right font-bold">
              <span>{t.sigSDM[lang]}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
