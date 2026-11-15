/**
 * TypeScript types for SDM Kurra Dashboard.
 * Synchronized with kurra/api/schemas.py.
 */

export interface CoSharerInput {
  id: string;
  name: string;
  share: string; // e.g. "1/2", "25%", "0.33"
  color_hex?: string;
  color_name_hi?: string;
  possession_wkt?: string;
}

export interface CaseMetadata {
  case_no: string;
  court_name: string;
  district_code: string;
  district_name: string;
  tehsil_code: string;
  tehsil_name: string;
  village_code: string;
  village_name: string;
  plot_no: string;
  plaintiff: string;
  defendant: string;
}

export interface AuditScorecard {
  tier: number;
  tier_name: string;
  code: string;
  clause_ref: string;
  legal_basis: string;
  name_en: string;
  name_hi: string;
  status: 'green' | 'amber' | 'red' | 'na';
  metric: string;
  detail: string;
  statutory_citation: string;
}

export interface ProposedLot {
  party_id: string;
  party_name: string;
  share_nominal: number;
  share_str: string;
  area_sqm: number;
  area_ha: number;
  color_hex: string;
  color_hi: string;
  geojson: any;
  wkt: string;
  polsby_popper: number;
  aspect_ratio: number;
  road_frontage_m: number;
  is_connected: boolean;
}

export interface PartitionScheme {
  scheme_id: string;
  scheme_name_hi: string;
  scheme_name_en: string;
  description: string;
  lots: ProposedLot[];
  audit_results: AuditScorecard[];
  all_passed: boolean;
  failure_reason?: string | null;
  provenance: Record<string, any>;
}

export interface OwnerRecord {
  khata_no: string;
  serial_no: number;
  name: string;
  guardian: string | null;
  residence: string;
}

export interface SubPlotRecord {
  sub_plot_no: string;
  base_plot_no: string;
  sub_div: string | null;
  khata_no: string;
  area_ha: number;
  area_sqm: number;
  owners: OwnerRecord[];
}

export interface AdjacentNeighbor {
  plot_no: string;
  side: string;
  shared_length_m: number;
  touches_type: string;
  land_class: string;
}

export interface PlotReportData {
  district_code: string;
  district_name: string;
  tehsil_code: string;
  tehsil_name: string;
  village_code: string;
  village_name: string;
  khasra_no: string;
  scale: string;
  total_area_ha: number;
  total_area_sqm: number;
  sub_plots: SubPlotRecord[];
  adjacencies: AdjacentNeighbor[];
  raw_header: string;
  raw_plot_info: string;
  map_image_b64?: string;
  map_image_path?: string;
  fetched_at: string;
  source_url: string;
  sha256: string;
}

export interface ColorSwatch {
  name_hi: string;
  name_en: string;
  hex: string;
}

export interface PlotResponse {
  source: 'local_store' | 'live_bhunaksha';
  report: PlotReportData;
  polygon_geojson: any;
  polygon_wgs84: any;
  wkt: string;
  colors: ColorSwatch[];
}

export interface ProposePlanResponse {
  plot_no: string;
  schemes: PartitionScheme[];
  shares_valid: boolean;
  shares_message: string;
  possession_overlap_matrix: Record<string, Record<string, number>>;
}

export interface CustomCutRequest {
  district: string;
  tehsil: string;
  village: string;
  plot_no: string;
  cut_lines: number[][][]; // list of [[x1, y1], [x2, y2]]
  parties: CoSharerInput[];
}

export interface CustomCutResponse {
  scheme: PartitionScheme;
  success: boolean;
  message: string;
}
