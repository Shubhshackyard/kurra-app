/**
 * Universal bilingual dictionary for SDM Kurra Dashboard.
 * 100% Strict English & 100% Strict Hindi localization.
 */

export type Lang = "hi" | "en";

export const translations = {
  // Navigation & Header
  appTitle: {
    hi: "एसडीएम कुर्रा डैशबोर्ड — विधिक बटवारा व सीमांकन",
    en: "SDM Kurra Dashboard — Cadastral Partition & Demarcation",
  },
  courtSubtitle: {
    hi: "राजस्व न्यायालय उत्तर प्रदेश",
    en: "Revenue Court of Uttar Pradesh",
  },
  sectionBadge: {
    hi: "धारा 116 / नियम 109(5)",
    en: "Section 116 / Rule 109(5)",
  },
  dataDate: {
    hi: "डेटा दिनांक",
    en: "Data as of",
  },
  localFirstBadge: {
    hi: "स्थानीय भंडार",
    en: "Local Cadastre Store",
  },
  offlineMode: {
    hi: "ऑफ़लाइन मोड",
    en: "Offline Mode",
  },

  // Tabs
  tabCaseDesk: {
    hi: "1 · वाद डेस्क",
    en: "1 · Case Desk",
  },
  tabPlotOverview: {
    hi: "2 · भू-सर्वेक्षण अवलोकन",
    en: "2 · Plot Overview",
  },
  tabSuitDetails: {
    hi: "3 · वाद विवरण",
    en: "3 · Suit Details",
  },
  tabCoSharers: {
    hi: "4 · कुर्राधारक व अंश",
    en: "4 · Co-Sharers & Shares",
  },
  tabFeatures: {
    hi: "5 · गाटा सीमांकन व मार्ग",
    en: "5 · Boundaries & Roads",
  },
  tabSchemeStudio: {
    hi: "6 · योजना स्टूडियो व तुलना",
    en: "6 · Scheme Studio & Variations",
  },
  tabExhibits: {
    hi: "7 · विधिक कुर्रा नक्शा व आख्या",
    en: "7 · Statutory Exhibits",
  },

  // Case Desk
  bannerTitle: {
    hi: "गाटा कुर्रा बटवारा व विधिक सीमांकन प्रणाली",
    en: "Cadastral Partition & Boundary Demarcation System",
  },
  bannerDesc: {
    hi: "स्थानीय भू-नक्शा रिकॉर्ड, खतौनी खातेदारों के अंश, एवं नियम 109(5) के त्रिस्तरीय वैधानिक मानकों के आधार पर त्वरित एवं पारदर्शी कुर्रा निर्धारण।",
    en: "Instant, transparent partition based on UP Revenue Code Rule 109(5) three-tier statutory checks, local cadastre records, and decreetal shares.",
  },
  parcelLookup: {
    hi: "मौजा व गाटा चयन",
    en: "Cadastral Parcel Lookup",
  },
  parcelLookupSub: {
    hi: "अभिलेख व नक्शा लोड करने हेतु जनपद, तहसील, ग्राम एवं गाटा संख्या दर्ज करें",
    en: "Enter district, tehsil, village code, and plot number to load records",
  },
  loadDefaultPreset: {
    hi: "डिफ़ॉल्ट प्रीसेट लोड करें (गाटा 57, इखलाशपुरा)",
    en: "Load Default Preset (Plot 57, Ikhlashpura)",
  },
  districtLabel: {
    hi: "जनपद कोड",
    en: "District Code",
  },
  tehsilLabel: {
    hi: "तहसील कोड",
    en: "Tehsil Code",
  },
  villageLabel: {
    hi: "ग्राम कोड",
    en: "Village Code",
  },
  plotLabel: {
    hi: "खसरा / गाटा संख्या",
    en: "Khasra / Plot Number",
  },
  searchBtn: {
    hi: "खोजें",
    en: "Search",
  },
  searchingBtn: {
    hi: "लोड हो रहा है...",
    en: "Loading...",
  },
  recentCasesTitle: {
    hi: "हालिया राजस्व वाद",
    en: "Recent Partition Cases",
  },
  totalCasesBadge: {
    hi: "कुल वाद",
    en: "Total Cases",
  },
  caseNoCol: {
    hi: "वाद संख्या",
    en: "Case Number",
  },
  plotNoCol: {
    hi: "गाटा संख्या",
    en: "Plot Number",
  },
  partiesCol: {
    hi: "पक्षकार",
    en: "Parties",
  },
  areaCol: {
    hi: "कुल रकबा",
    en: "Total Area",
  },
  statusCol: {
    hi: "स्थिति",
    en: "Status",
  },
  actionCol: {
    hi: "कार्यवाही",
    en: "Action",
  },
  openBtn: {
    hi: "खोलें",
    en: "Open",
  },
  localStoreStatus: {
    hi: "स्थानीय भंडार स्थिति: सक्रिय (ऑफ़लाइन SQLite)",
    en: "Local Store Status: Active (Offline SQLite)",
  },

  // Plot Overview
  layerVector: {
    hi: "वेक्टर भू-नक्शा",
    en: "Vector Map (HD)",
  },
  layerRaster: {
    hi: "पोर्टल टाइल",
    en: "Bhunaksha Tile",
  },
  layerBirdseye: {
    hi: "उपग्रह विहंगम दृश्य",
    en: "Bird's-Eye Satellite View",
  },
  chauhaddiTitle: {
    hi: "गाटा चौहद्दी (सीमावर्ती गाटे)",
    en: "Boundary Neighbors (Chauhaddi)",
  },
  chauhaddiSub: {
    hi: "भू-नक्शा के स्पर्शक रेखाओं (Outward Normal Vectors) द्वारा स्वचालित गणना",
    en: "Computed via cadastral outward normal vectors",
  },
  north: {
    hi: "उत्तर",
    en: "North",
  },
  south: {
    hi: "दक्षिण",
    en: "South",
  },
  east: {
    hi: "पूर्व",
    en: "East",
  },
  west: {
    hi: "पश्चिम",
    en: "West",
  },
  reconcileTitle: {
    hi: "रकबा मिलान व विधिक त्रुटि सीमा",
    en: "Area Reconciliation & Cartographic Tolerance",
  },
  recordedArea: {
    hi: "अभिलेखीय रकबा (खतौनी)",
    en: "Recorded Area (Khatauni)",
  },
  mappedArea: {
    hi: "नक्शा रकबा (डिजिटल बहुभुज)",
    en: "Mapped Area (Digital Polygon)",
  },
  deviation: {
    hi: "अन्तर",
    en: "Deviation",
  },
  toleranceNotice: {
    hi: "पैमाना 1:1698 पर 0.25 मिमी पेन मोटाई त्रुटि = ±0.42 मीटर। कुल रकबा अनिश्चितता बैंड: ±84.9 m² (±2.27%)। अन्तर विधिक त्रुटि सीमा के भीतर मान्य है।",
    en: "At scale 1:1698 with 0.25mm line width error = ±0.42m. Total area uncertainty band: ±84.9 m² (±2.27%). Deviation is strictly within legal tolerance.",
  },
  subPlotsTitle: {
    hi: "उप-गाटा व खतौनी खातेदार विवरण",
    en: "Sub-Plots & Khatauni Co-Sharers",
  },
  subPlotsSub: {
    hi: "एक ही गाटे में विभिन्न खातों के अंतर्गत दर्ज रकबा व खातेदारों के नाम",
    en: "Khata records and recorded tenure holders per cadastral sub-division",
  },
  subPlotNo: {
    hi: "उप-गाटा",
    en: "Sub-Plot",
  },
  khataNo: {
    hi: "खाता संख्या",
    en: "Khata Number",
  },
  ownerName: {
    hi: "दर्ज खातेदार",
    en: "Recorded Owner",
  },
  guardianName: {
    hi: "संरक्षक / पिता का नाम",
    en: "Guardian / Father's Name",
  },
  residence: {
    hi: "निवास स्थान",
    en: "Residence",
  },

  // Suit Details
  suitDetailsTitle: {
    hi: "राजस्व वाद विधिक विवरण",
    en: "Suit & Judicial Metadata",
  },
  suitDetailsSub: {
    hi: "उत्तर प्रदेश राजस्व संहिता 2006 की धारा 116 के अंतर्गत पंजीकृत वाद की न्यायालयी प्रविष्टियां",
    en: "Judicial case registry entries under Section 116 of UP Revenue Code 2006",
  },
  competentCourt: {
    hi: "सक्षम राजस्व न्यायालय",
    en: "Competent Revenue Court of SDM",
  },
  plaintiffLabel: {
    hi: "वादी का नाम",
    en: "Plaintiff / Sharer 1",
  },
  defendantLabel: {
    hi: "प्रतिवादीगण",
    en: "Defendants / Other Co-Sharers",
  },
  statuteReference: {
    hi: "संबद्ध अधिनियम व नियमावली",
    en: "Statutory Reference",
  },
  statuteDesc: {
    hi: "उत्तर प्रदेश राजस्व संहिता 2006 की धारा 116 एवं उ०प्र० राजस्व संहिता नियमावली 2016 के नियम 109 के प्रावधानों के अंतर्गत कुर्रा निर्धारण की कार्यवाही।",
    en: "Kurra partition proceedings governed by Section 116 of UP Revenue Code 2006 and Rule 109 of UP Revenue Code Rules 2016.",
  },

  // Co-Sharers
  sharersTitle: {
    hi: "सह-खातेदार व अंश निर्धारण",
    en: "Co-Sharers & Decreed Fractions",
  },
  sharersSub: {
    hi: "प्रारंभिक डिक्री के अनुसार घोषित अंश (उदा० 1/2, 1/4+1/4, 25%) एवं आधिकारिक 12 कुर्रा रंग",
    en: "Decreed shares (e.g. 1/2, 1/4+1/4, 25%) and official 12 partition swatches",
  },
  totalShareSum: {
    hi: "कुल अंश योग",
    en: "Total Share Sum",
  },
  fullyValid: {
    hi: "पूर्ण वैध",
    en: "Fully Valid",
  },
  invalidSum: {
    hi: "अमान्य (योग 1.000 अनिवार्य)",
    en: "Invalid (Must sum to 1.000)",
  },
  lotOrder: {
    hi: "कुर्रा क्रम",
    en: "Lot Order",
  },
  partyNameCol: {
    hi: "खातेदार / पक्षकार का नाम",
    en: "Co-Sharer / Party Name",
  },
  shareCol: {
    hi: "घोषित विधिक अंश",
    en: "Decreed Share Fraction",
  },
  colorCol: {
    hi: "आधिकारिक कुर्रा रंग",
    en: "Official Lot Swatch",
  },
  possessionClaim: {
    hi: "मौके पर पृथक काश्तकारी कब्जा",
    en: "Separate Ground Possession",
  },
  removeLot: {
    hi: "हटाएं",
    en: "Remove",
  },
  addSharerBtn: {
    hi: "सह-खातेदार जोड़ें",
    en: "Add Co-Sharer",
  },
  equalizeSharesBtn: {
    hi: "बराबर अंश करें (1/N)",
    en: "Equalize Shares (1/N)",
  },

  // Parcel Features & Roads
  parcelFeaturesTitle: {
    hi: "गाटा सीमांकन, चौहद्दी व मार्ग विवरण",
    en: "Boundary Edges, Roads & Adjacency",
  },
  parcelFeaturesSub: {
    hi: "गाटा के चारों ओर स्थित मार्गों के अग्रभाग एवं चौहद्दी के स्पर्शक किनारों का वर्गीकरण",
    en: "Classification of boundary touches, road frontage, and neighbor plots",
  },
  boundaryEdgesTitle: {
    hi: "गाटा के चारों ओर स्थित किनारे व स्पर्शक मार्ग",
    en: "Boundary Edges & Adjacent Road Touches",
  },
  sideCol: {
    hi: "दिशा / सीमा",
    en: "Side / Direction",
  },
  adjacentPlotCol: {
    hi: "पड़ोसी गाटा संख्या",
    en: "Adjacent Plot No",
  },
  sharedLengthCol: {
    hi: "साझा सीमा लंबाई (मी०)",
    en: "Shared Length (m)",
  },
  edgeClassCol: {
    hi: "किनारा / मार्ग वर्गीकरण",
    en: "Boundary Classification",
  },
  roadPolicyTitle: {
    hi: "मार्ग वरीयता व मूल्य नीति गुणक",
    en: "Road Hierarchy & Policy Weights",
  },
  policyNotStatute: {
    hi: "नीतिगत मानक, विधिक बाध्यता नहीं",
    en: "Policy Standard, Not Statutory Mandate",
  },
  roadPolicySub: {
    hi: "विभिन्न श्रेणियों के मार्गों पर स्थित अग्रभाग का मूल्य भार",
    en: "Frontage weights applied during optimizer lot allocation",
  },
  sharedPathTitle: {
    hi: "साझा रास्ता व्यवस्था (साझा निकास गलियारा)",
    en: "Dedicated Shared Pathway Option",
  },
  sharedPathSub: {
    hi: "अग्रभाग विहीन पिछले कुर्रों हेतु साझा रास्ता (डिफ़ॉल्ट रूप से बंद, न्यायालय निर्देश या पक्षों की सहमति पर सक्षम)",
    en: "Pro-rata deducted corridor for landlocked interior lots (default off, requires court order or consent)",
  },
  sharedPathActive: {
    hi: "साझा रास्ता सक्रिय",
    en: "Shared Pathway Active",
  },
  sharedPathInactive: {
    hi: "साझा रास्ता निष्क्रिय",
    en: "Shared Pathway Inactive",
  },
  pathWidthLabel: {
    hi: "रास्ते की चौड़ाई (मीटर)",
    en: "Pathway Width (Meters)",
  },

  // Scheme Studio & Variations
  schemeStudioTitle: {
    hi: "कुर्रा विभाजन योजनाएं व वास्तविक-समय तुलना",
    en: "Partition Schemes & Real-Time Variations",
  },
  schemeStudioSub: {
    hi: "नियम 109(5) के तहत विभिन्न रणनीतियों पर आधारित विभाजन विकल्प एवं पेंसिल द्वारा हस्तनिर्मित सीमांकन",
    en: "Rule 109(5) compliant partition schemes and custom interactive boundary marking",
  },
  viewAllGrid: {
    hi: "समस्त योजना नक्शे",
    en: "Multi-Map Grid",
  },
  viewSingleFocus: {
    hi: "विस्तृत एकल दृश्य",
    en: "Single Focus View",
  },
  approvedBadge: {
    hi: "नियमानुसार स्वीकृत",
    en: "Rule 109(5) Approved",
  },
  conditionalBadge: {
    hi: "आपत्ति योग्य / शर्तयुक्त",
    en: "Conditional / Warning",
  },
  rejectedBadge: {
    hi: "अस्वीकृत",
    en: "Rejected",
  },
  whyThisTitle: {
    hi: "नियम 109(5) विधिक कसौटी व कारण (Why this / Why not this):",
    en: "Rule 109(5) Statutory Analysis (Why this / Why not this):",
  },
  activeSchemeBadge: {
    hi: "लागू योजना ✓",
    en: "Active Scheme ✓",
  },
  selectSchemeBtn: {
    hi: "यह योजना चुनें",
    en: "Select Scheme",
  },
  pencilToolBtn: {
    hi: "✏️ पेंसिल टूल (हाथ से विभाजन रेखा खींचें)",
    en: "✏️ Pencil Tool (Draw Custom Cut Line)",
  },
  pencilActiveMsg: {
    hi: "पेंसिल टूल सक्रिय: गाटा सीमा के आर-पार क्लिक करके विभाजन रेखा खींचें",
    en: "Pencil Active: Click and drag across parcel boundary to draw cut lines",
  },
  recalcBtn: {
    hi: "पुनर्गणना करें",
    en: "Recalculate",
  },
  overlapMatrixTitle: {
    hi: "योजनाओं के मध्य कब्जा सामंजस्य मैट्रिक्स (% Overlap)",
    en: "Cross-Scheme Spatial Overlap Matrix (% Alignment)",
  },

  // Exhibits & Print
  exhibitsTitle: {
    hi: "विधिक कुर्रा अभिलेख व नक्शा फांट",
    en: "Statutory Kurra Exhibits & Demarcation Maps",
  },
  exhibitsSub: {
    hi: "धारा 116 / नियम 109(5) अंतर्गत न्यायालयी प्रस्तुति हेतु ए-4 प्रिंटेबल नजरी नक्शा व आख्या",
    en: "Court-ready printable A4 Naksha Kurra Bant and statutory legal notices",
  },
  tabNaksha: {
    hi: "नजरी नक्शा फांट",
    en: "Demarcation Map Sheet",
  },
  tabLekhpalReport: {
    hi: "लेखपाल आख्या",
    en: "Lekhpal Field Report",
  },
  tabDecree: {
    hi: "प्रारंभिक डिक्री",
    en: "Preliminary Decree",
  },
  printBtn: {
    hi: "प्रिंट (A4 PDF)",
    en: "Print (A4 PDF)",
  },
  sanketSuchi: {
    hi: "संकेत सूची (कुर्रा विवरण)",
    en: "Legend & Lot Specifications",
  },
  lotNoHeader: {
    hi: "कुर्रा संख्या",
    en: "Lot No",
  },
  colorHeader: {
    hi: "आधिकारिक रंग",
    en: "Official Swatch",
  },
  sharerNameHeader: {
    hi: "कुर्राधारक का नाम",
    en: "Co-Sharer Name",
  },
  shareHeader: {
    hi: "विधिक अंश",
    en: "Decreed Share",
  },
  areaSqmHeader: {
    hi: "रकबा (वर्ग मीटर)",
    en: "Area (m²)",
  },
  areaHaHeader: {
    hi: "रकबा (हेक्टेयर)",
    en: "Area (Hectare)",
  },
  frontageHeader: {
    hi: "सड़क अग्रभाग (मीटर)",
    en: "Road Frontage (m)",
  },
  tapeMeasureSheet: {
    hi: "मौका पैमाइश व जरीब नाप तालिका",
    en: "Field Tape Coordinates & Offset Table",
  },
  tapeDesc: {
    hi: "प्रत्येक कुर्रे की सीमाएं उत्तर-पश्चिम कोने से आरम्भ कर दक्षिणावर्त दिशा में निर्धारित हैं। विभाजन रेखाओं के सीमांकन हेतु जरीब/फीता नाप राजस्व नक्शे के संदर्भ बिंदुओं से ली जाएगी।",
    en: "Boundary lines measured clockwise from the northwest corner. Field offsets and boundary stake-out coordinates taken directly from cadastral benchmarks.",
  },
  sigLekhpal: {
    hi: "हस्ताक्षर राजस्व लेखपाल",
    en: "Signature of Lekhpal",
  },
  sigRI: {
    hi: "हस्ताक्षर राजस्व निरीक्षक",
    en: "Signature of Revenue Inspector",
  },
  sigSDM: {
    hi: "हस्ताक्षर उपजिलाधिकारी / सहायक कलेक्टर",
    en: "Signature of Sub-Divisional Magistrate",
  },
  noSchemeSelected: {
    hi: "कोई कुर्रा योजना चयनित नहीं है",
    en: "No Partition Scheme Selected",
  },
  selectSchemePrompt: {
    hi: "कृपया पहले योजना स्टूडियो में जाकर एक वैध कुर्रा योजना चुनें।",
    en: "Please select a scheme first from the Scheme Studio tab.",
  },
};
