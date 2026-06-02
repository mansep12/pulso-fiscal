export const DEFAULT_PERIOD_FROM = "2021-01";

export const RANKING_SORT_KEYS = [
  "promedio_mensual",
  "total_monto",
  "registros",
  "meses_con_datos",
  "nombre",
] as const;

export type RankingSortKey = (typeof RANKING_SORT_KEYS)[number];

export type SortDirection = "asc" | "desc";

export type RankingFilters = {
  query?: string;
  categoryId?: string;
  periodFrom?: string;
  periodTo?: string;
  sort: RankingSortKey;
  direction: SortDirection;
};

export type PeriodRange = {
  from: string;
  to: string;
};

export type SenadoCategory = {
  id: string;
  name: string;
  totalClp: number;
  recordCount: number;
  activeMonths: number;
  senatorCount: number;
};

export type SenadoPeriodSummary = {
  period: string;
  year: number;
  month: number;
  totalClp: number;
  recordCount: number;
  senatorCount: number;
};

export type SenadorSummary = {
  id: string;
  name: string;
  totalClp: number;
  recordCount: number;
  activeMonths: number;
  monthlyAverageClp: number;
};

export type SenadorCategorySummary = {
  id: string;
  name: string;
  totalClp: number;
  recordCount: number;
  activeMonths: number;
};

export type SenadorPeriodSummary = {
  period: string;
  year: number;
  month: number;
  totalClp: number;
  recordCount: number;
  categoryCount: number;
};
