import { createServerClient } from "@/lib/supabase";
import {
  DEFAULT_PERIOD_FROM,
  type PeriodRange,
  type RankingFilters,
  type RankingSortKey,
  type SenadoCategory,
  type SenadoPeriodSummary,
  type SenadorCategorySummary,
  type SenadorPeriodSummary,
  type SenadorSummary,
  type SortDirection,
} from "@/lib/types";

type SenadorSummaryRow = {
  parlamentario_id: string;
  parlamentario_nombre: string;
  total_monto: number;
  registros: number;
  meses_con_datos: number;
  promedio_mensual: number;
};

type CategoryRow = {
  categoria_id: string;
  categoria_nombre: string;
  total_monto: number;
  registros: number;
  meses_con_datos: number;
  parlamentarios?: number;
};

type PeriodRow = {
  periodo: string;
  ano: number;
  mes: number;
  total_monto: number;
  registros: number;
  parlamentarios?: number;
  categorias?: number;
};

class DataQueryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DataQueryError";
  }
}

export async function getSenadorSummaries(
  filters: RankingFilters,
): Promise<SenadorSummary[]> {
  const supabase = createServerClient();

  const { data, error } = await supabase.rpc("senado_resumen_senadores_filtrado", {
    p_busqueda: filters.query || null,
    p_categoria_id: filters.categoryId || null,
    p_periodo_desde: filters.periodFrom || DEFAULT_PERIOD_FROM,
    p_periodo_hasta: filters.periodTo || null,
  });

  if (error) {
    console.error("Error consultando resumen de senadores:", error.message);
    throw new DataQueryError("No pudimos consultar el ranking de senadores.");
  }

  return ((data ?? []) as SenadorSummaryRow[])
    .map(mapSenadorSummary)
    .sort((a, b) => compareSummaries(a, b, filters.sort, filters.direction));
}

export async function getSenadorSummary(id: string): Promise<SenadorSummary | null> {
  const supabase = createServerClient();

  const { data, error } = await supabase
    .from("senado_resumen_senadores_latest")
    .select(
      "parlamentario_id, parlamentario_nombre, total_monto, registros, "
        + "meses_con_datos, promedio_mensual",
    )
    .eq("parlamentario_id", id)
    .maybeSingle();

  if (error) {
    console.error("Error consultando senador:", error.message);
    throw new DataQueryError("No pudimos consultar la ficha del senador.");
  }

  return data ? mapSenadorSummary(data as unknown as SenadorSummaryRow) : null;
}

export async function getCategories(): Promise<SenadoCategory[]> {
  const supabase = createServerClient();

  const { data, error } = await supabase
    .from("senado_categorias_latest")
    .select(
      "categoria_id, categoria_nombre, total_monto, registros, meses_con_datos, parlamentarios",
    )
    .order("total_monto", { ascending: false });

  if (error) {
    console.error("Error consultando categorias:", error.message);
    throw new DataQueryError("No pudimos consultar las categorias.");
  }

  return ((data ?? []) as CategoryRow[]).map((row) => ({
    id: row.categoria_id,
    name: row.categoria_nombre,
    totalClp: row.total_monto ?? 0,
    recordCount: row.registros ?? 0,
    activeMonths: row.meses_con_datos ?? 0,
    senatorCount: row.parlamentarios ?? 0,
  }));
}

export async function getPeriodRange(): Promise<{ from: string; to: string } | null> {
  const supabase = createServerClient();

  const { data, error } = await supabase
    .from("senado_period_range_latest")
    .select("period_from, period_to")
    .limit(1)
    .single();

  if (error) {
    console.error("Error consultando rango de periodos:", error.message);
    throw new DataQueryError("No pudimos consultar el rango de periodos.");
  }

  if (!data) return null;
  const from = (data.period_from as string | null)?.trim();
  const to = (data.period_to as string | null)?.trim();
  if (!from || !to) return null;

  return {
    from,
    to,
  };
}

export async function getPeriodSummaries(limit = 8): Promise<SenadoPeriodSummary[]> {
  const supabase = createServerClient();

  const { data, error } = await supabase
    .from("senado_periodos_latest")
    .select("periodo, ano, mes, total_monto, registros, parlamentarios")
    .order("periodo", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("Error consultando periodos:", error.message);
    throw new DataQueryError("No pudimos consultar los periodos.");
  }

  return ((data ?? []) as PeriodRow[]).map((row) => ({
    period: row.periodo,
    year: row.ano,
    month: row.mes,
    totalClp: row.total_monto ?? 0,
    recordCount: row.registros ?? 0,
    senatorCount: row.parlamentarios ?? 0,
  }));
}

export async function getSenadorCategories(
  id: string,
): Promise<SenadorCategorySummary[]> {
  const supabase = createServerClient();

  const { data, error } = await supabase.rpc("senado_resumen_categorias_senador", {
    p_parlamentario_id: id,
    p_periodo_desde: DEFAULT_PERIOD_FROM,
    p_periodo_hasta: null,
  });

  if (error) {
    console.error("Error consultando categorias de senador:", error.message);
    throw new DataQueryError("No pudimos consultar las categorias del senador.");
  }

  return ((data ?? []) as CategoryRow[])
    .map((row) => ({
      id: row.categoria_id,
      name: row.categoria_nombre,
      totalClp: row.total_monto ?? 0,
      recordCount: row.registros ?? 0,
      activeMonths: row.meses_con_datos ?? 0,
    }))
    .sort((a, b) => b.totalClp - a.totalClp);
}

export async function getSenadorPeriods(id: string): Promise<SenadorPeriodSummary[]> {
  const supabase = createServerClient();

  const { data, error } = await supabase.rpc("senado_resumen_periodos_senador", {
    p_parlamentario_id: id,
    p_periodo_desde: DEFAULT_PERIOD_FROM,
    p_periodo_hasta: null,
  });

  if (error) {
    console.error("Error consultando periodos de senador:", error.message);
    throw new DataQueryError("No pudimos consultar los periodos del senador.");
  }

  return ((data ?? []) as PeriodRow[])
    .map((row) => ({
      period: row.periodo,
      year: row.ano,
      month: row.mes,
      totalClp: row.total_monto ?? 0,
      recordCount: row.registros ?? 0,
      categoryCount: row.categorias ?? 0,
    }))
    .sort((a, b) => b.period.localeCompare(a.period));
}

export function selectedPeriodRange(filters: RankingFilters, range: PeriodRange | null) {
  return {
    from: filters.periodFrom || range?.from || DEFAULT_PERIOD_FROM,
    to: filters.periodTo || range?.to || "",
  };
}

function mapSenadorSummary(row: SenadorSummaryRow): SenadorSummary {
  return {
    id: row.parlamentario_id,
    name: row.parlamentario_nombre,
    totalClp: row.total_monto ?? 0,
    recordCount: row.registros ?? 0,
    activeMonths: row.meses_con_datos ?? 0,
    monthlyAverageClp: row.promedio_mensual ?? 0,
  };
}

function compareSummaries(
  a: SenadorSummary,
  b: SenadorSummary,
  sort: RankingSortKey,
  direction: SortDirection,
) {
  if (sort === "nombre") {
    return direction === "asc"
      ? a.name.localeCompare(b.name, "es-CL")
      : b.name.localeCompare(a.name, "es-CL");
  }

  const aValue = summaryValue(a, sort);
  const bValue = summaryValue(b, sort);
  if (aValue !== bValue) {
    return direction === "asc" ? aValue - bValue : bValue - aValue;
  }

  return a.name.localeCompare(b.name, "es-CL");
}

function summaryValue(summary: SenadorSummary, sort: RankingSortKey) {
  if (sort === "total_monto") return summary.totalClp;
  if (sort === "registros") return summary.recordCount;
  if (sort === "meses_con_datos") return summary.activeMonths;
  return summary.monthlyAverageClp;
}
