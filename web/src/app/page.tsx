import Link from "next/link";

import { MetricCard } from "@/components/metric-card";
import { SpendingRanking } from "@/components/spending-ranking";
import {
  getCategories,
  getPeriodRange,
  getPeriodSummaries,
  getSenadorSummaries,
  selectedPeriodRange,
} from "@/lib/queries";
import { formatClp, formatNumber, formatPeriod } from "@/lib/format";
import {
  DEFAULT_PERIOD_FROM,
  RANKING_SORT_KEYS,
  type RankingFilters,
  type RankingSortKey,
} from "@/lib/types";

export const dynamic = "force-dynamic";

type HomePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const filters = parseFilters(await searchParams);
  const [summaries, categories, range, periods] = await Promise.all([
    getSenadorSummaries(filters),
    getCategories(),
    getPeriodRange(),
    getPeriodSummaries(6),
  ]);

  const selectedRange = selectedPeriodRange(filters, range);
  const selectedCategory = categories.find((category) => category.id === filters.categoryId);
  const total = summaries.reduce((sum, summary) => sum + summary.totalClp, 0);
  const records = summaries.reduce((sum, summary) => sum + summary.recordCount, 0);
  const periodoLabel = selectedRange.to
    ? `${formatPeriod(selectedRange.from)} - ${formatPeriod(selectedRange.to)}`
    : "Sin datos";

  return (
    <main>
      <section className="mx-auto grid max-w-6xl gap-10 px-5 py-16 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.28em] text-slate-500">
            Transparencia operacional
          </p>
          <h1 className="mt-5 max-w-4xl text-5xl font-black tracking-tight text-slate-950 sm:text-7xl">
            Ranking neutral de gastos operacionales del Senado.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            Pulso Fiscal convierte la fuente oficial del Senado en tablas comparables. El orden por
            defecto usa promedio mensual para no favorecer a quienes aparecen mas meses.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              className="rounded-full bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-sm hover:bg-slate-800"
              href="#ranking"
            >
              Ver ranking
            </Link>
            <Link
              className="rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-bold text-slate-950 hover:border-slate-950"
              href="/fuentes"
            >
              Revisar fuente
            </Link>
          </div>
        </div>

        <aside className="rounded-4xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.24em] text-emerald-700">
            Datos reales
          </p>
          <p className="mt-4 text-2xl font-black text-slate-950">
            Gastos desde 2021
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Se incluyen registros rankeables desde enero de 2021 hasta el ultimo periodo cargado en
            Supabase. Las cifras no implican irregularidad.
          </p>
          <p className="mt-3 text-xs font-bold text-slate-500">Periodo: {periodoLabel}</p>
        </aside>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-5 pb-8 sm:grid-cols-3">
        <MetricCard
          detail="Suma filtrada de registros incluidos en ranking."
          label="Total filtrado"
          value={formatClp(total)}
        />
        <MetricCard
          detail="Senadores con registros en el periodo o categoria seleccionada."
          label="Senadores"
          value={formatNumber(summaries.length)}
        />
        <MetricCard
          detail="Cantidad de filas usadas para la comparacion actual."
          label="Registros"
          value={formatNumber(records)}
        />
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-8" id="ranking">
        <form
          action="/#ranking"
          className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
          method="get"
        >
          <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr_0.7fr_0.7fr_0.8fr_0.7fr_auto] lg:items-end">
            <label className="text-sm font-bold text-slate-700">
              Buscar senador
              <input
                className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium outline-none focus:border-slate-950"
                defaultValue={filters.query ?? ""}
                name="q"
                placeholder="Ej: Lagos, Allamand"
                type="search"
              />
            </label>

            <label className="text-sm font-bold text-slate-700">
              Categoria
              <select
                className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium outline-none focus:border-slate-950"
                defaultValue={filters.categoryId ?? ""}
                name="category"
              >
                <option value="">Todas</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm font-bold text-slate-700">
              Desde
              <input
                className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium outline-none focus:border-slate-950"
                defaultValue={selectedRange.from}
                max={range?.to}
                min={range?.from ?? DEFAULT_PERIOD_FROM}
                name="from"
                type="month"
              />
            </label>

            <label className="text-sm font-bold text-slate-700">
              Hasta
              <input
                className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium outline-none focus:border-slate-950"
                defaultValue={selectedRange.to}
                max={range?.to}
                min={range?.from ?? DEFAULT_PERIOD_FROM}
                name="to"
                type="month"
              />
            </label>

            <label className="text-sm font-bold text-slate-700">
              Orden
              <select
                className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium outline-none focus:border-slate-950"
                defaultValue={filters.sort}
                name="sort"
              >
                <option value="promedio_mensual">Promedio mensual</option>
                <option value="total_monto">Total</option>
                <option value="registros">Registros</option>
                <option value="meses_con_datos">Meses con datos</option>
                <option value="nombre">Nombre</option>
              </select>
            </label>

            <label className="text-sm font-bold text-slate-700">
              Direccion
              <select
                className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium outline-none focus:border-slate-950"
                defaultValue={filters.direction}
                name="direction"
              >
                <option value="desc">Mayor a menor</option>
                <option value="asc">Menor a mayor</option>
              </select>
            </label>

            <div className="flex gap-2">
              <button className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-black text-white hover:bg-slate-800">
                Filtrar
              </button>
              <a
                className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-black text-slate-700 hover:border-slate-950"
                href="/"
                target="_top"
              >
                Limpiar
              </a>
            </div>
          </div>
        </form>
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-10">
        <SpendingRanking
          categoryName={selectedCategory?.name ?? null}
          filters={filters}
          periodLabel={periodoLabel}
          summaries={summaries}
        />
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-5 pb-16 lg:grid-cols-2">
        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-black text-slate-950">Categorias con mas gasto</h2>
            <p className="mt-1 text-sm text-slate-600">Vista general desde 2021.</p>
          </div>
          <div className="divide-y divide-slate-100">
            {categories.slice(0, 8).map((category) => (
              <a
                className="grid gap-2 px-5 py-4 hover:bg-slate-50 sm:grid-cols-[1fr_150px] sm:items-center"
                href={`/?category=${encodeURIComponent(category.id)}&sort=promedio_mensual&direction=desc#ranking`}
                key={category.id}
                target="_top"
              >
                <span>
                  <span className="block font-bold text-slate-950">{category.name}</span>
                  <span className="text-sm text-slate-500">
                    {formatNumber(category.recordCount)} registros, {formatNumber(category.senatorCount)} senadores
                  </span>
                </span>
                <span className="font-black text-slate-950 sm:text-right">
                  {formatClp(category.totalClp)}
                </span>
              </a>
            ))}
          </div>
        </div>

        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-black text-slate-950">Ultimos periodos</h2>
            <p className="mt-1 text-sm text-slate-600">Totales mensuales del ultimo run cargado.</p>
          </div>
          <div className="divide-y divide-slate-100">
            {periods.map((period) => (
              <div
                className="grid gap-2 px-5 py-4 sm:grid-cols-[1fr_150px] sm:items-center"
                key={period.period}
              >
                <span>
                  <span className="block font-bold text-slate-950">{formatPeriod(period.period)}</span>
                  <span className="text-sm text-slate-500">
                    {formatNumber(period.recordCount)} registros, {formatNumber(period.senatorCount)} senadores
                  </span>
                </span>
                <span className="font-black text-slate-950 sm:text-right">
                  {formatClp(period.totalClp)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

function parseFilters(params?: Record<string, string | string[] | undefined>): RankingFilters {
  const sort = readParam(params, "sort");
  const direction = readParam(params, "direction");
  const periodFrom = normalizePeriod(readParam(params, "from"));
  const periodTo = normalizePeriod(readParam(params, "to"));
  const [normalizedFrom, normalizedTo] = normalizePeriodRange(periodFrom, periodTo);

  return {
    query: emptyToUndefined(readParam(params, "q")),
    categoryId: emptyToUndefined(readParam(params, "category")),
    periodFrom: normalizedFrom,
    periodTo: normalizedTo,
    sort: isSortKey(sort) ? sort : "promedio_mensual",
    direction: direction === "asc" ? "asc" : "desc",
  };
}

function readParam(
  params: Record<string, string | string[] | undefined> | undefined,
  key: string,
) {
  const value = params?.[key];
  return Array.isArray(value) ? value[0] : value;
}

function emptyToUndefined(value: string | undefined) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

function isSortKey(value: string | undefined): value is RankingSortKey {
  return RANKING_SORT_KEYS.includes(value as RankingSortKey);
}

function normalizePeriod(value: string | undefined) {
  const trimmed = emptyToUndefined(value);
  if (!trimmed || !/^\d{4}-\d{2}$/.test(trimmed)) return undefined;

  const month = Number(trimmed.slice(5, 7));
  return month >= 1 && month <= 12 ? trimmed : undefined;
}

function normalizePeriodRange(from: string | undefined, to: string | undefined) {
  if (from && to && from > to) return [to, from] as const;
  return [from, to] as const;
}
