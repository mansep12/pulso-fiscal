export type SourceStatus = "pendiente" | "parcial" | "revisada";

export type ConfidenceLevel = "alto" | "medio" | "bajo";

export type SpendingCategory =
  | "combustible"
  | "arriendo_vehiculos"
  | "mantencion"
  | "tag_peajes"
  | "viaticos"
  | "viajes";

export type Institution = {
  slug: string;
  name: string;
  shortName: string;
  type: "ministerio";
  description: string;
  sourceStatus: SourceStatus;
  sourceUrl: string | null;
  lastChecked: string | null;
};

export type SpendingRecord = {
  id: string;
  institutionSlug: string;
  period: string;
  category: SpendingCategory;
  amountClp: number;
  provider: string | null;
  sourceUrl: string;
  capturedAt: string;
  confidence: ConfidenceLevel;
  note: string;
};

export type InstitutionSummary = {
  institution: Institution;
  totalClp: number;
  recordCount: number;
  confidence: ConfidenceLevel;
};
