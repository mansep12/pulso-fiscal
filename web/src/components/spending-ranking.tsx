import Link from "next/link";

import { formatClp } from "@/lib/format";
import type { RankingFilters, RankingSortKey, SenadorSummary } from "@/lib/types";

type SpendingRankingProps = {
  categoryName: string | null;
  filters: RankingFilters;
  periodLabel: string;
  summaries: SenadorSummary[];
};

const sortLabels: Record<RankingSortKey, string> = {
  promedio_mensual: "Promedio mensual",
  total_monto: "Total",
  registros: "Registros",
  meses_con_datos: "Meses",
  nombre: "Senador",
};

export function SpendingRanking({
  categoryName,
  filters,
  periodLabel,
  summaries,
}: SpendingRankingProps) {
  const max = Math.max(...summaries.map((summary) => summary.monthlyAverageClp), 1);

  if (summaries.length === 0) {
    return (
      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-slate-500">Sin datos disponibles.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-lg font-black text-slate-950">
          Ranking de senadores
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          {categoryName ? `Categoria: ${categoryName}. ` : "Todas las categorias. "}
          Periodo: {periodLabel}. Orden actual: {sortLabels[filters.sort]} {formatDirection(filters.direction)}.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-215 text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-[0.14em] text-slate-500">
            <tr>
              <th className="px-5 py-3" scope="col">#</th>
              <th className="px-5 py-3" scope="col">{sortLink("Senador", "nombre", filters)}</th>
              <th className="px-5 py-3 text-right" scope="col">{sortLink("Total", "total_monto", filters)}</th>
              <th className="px-5 py-3 text-right" scope="col">
                {sortLink("Promedio mensual", "promedio_mensual", filters)}
              </th>
              <th className="px-5 py-3 text-right" scope="col">
                {sortLink("Meses", "meses_con_datos", filters)}
              </th>
              <th className="px-5 py-3 text-right" scope="col">{sortLink("Registros", "registros", filters)}</th>
              <th className="px-5 py-3 text-right" scope="col">Ficha</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {summaries.map((summary, index) => (
              <tr key={summary.id}>
                <td className="px-5 py-4 align-top font-black text-slate-500">{index + 1}</td>
                <td className="px-5 py-4 align-top">
                  <span className="block font-black text-slate-950">{summary.name}</span>
                  <span className="mt-2 block h-2 overflow-hidden rounded-full bg-slate-100">
                    <span
                      className="block h-full rounded-full bg-slate-950"
                      style={{
                        width: `${Math.max((summary.monthlyAverageClp / max) * 100, 4)}%`,
                      }}
                    />
                  </span>
                </td>
                <td className="px-5 py-4 text-right align-top font-black text-slate-950">
                  {formatClp(summary.totalClp)}
                </td>
                <td className="px-5 py-4 text-right align-top font-black text-emerald-800">
                  {formatClp(summary.monthlyAverageClp)}
                </td>
                <td className="px-5 py-4 text-right align-top font-bold text-slate-700">
                  {summary.activeMonths}
                </td>
                <td className="px-5 py-4 text-right align-top font-bold text-slate-700">
                  {summary.recordCount}
                </td>
                <td className="px-5 py-4 text-right align-top">
                  <Link
                    className="font-black text-slate-950 underline"
                    href={`/senadores/${encodeURIComponent(summary.id)}`}
                  >
                    Ver
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatDirection(direction: "asc" | "desc") {
  return direction === "asc" ? "menor a mayor" : "mayor a menor";
}

function sortLink(label: string, sort: RankingSortKey, filters: RankingFilters) {
  const direction = filters.sort === sort && filters.direction === "desc" ? "asc" : "desc";
  const active = filters.sort === sort;

  return (
    <a
      className={active ? "text-slate-950" : "hover:text-slate-950"}
      href={rankingHref(filters, sort, direction)}
      target="_top"
    >
      {label}{active ? (filters.direction === "desc" ? " ↓" : " ↑") : ""}
    </a>
  );
}

function rankingHref(filters: RankingFilters, sort: RankingSortKey, direction: "asc" | "desc") {
  const params = new URLSearchParams();
  if (filters.query) params.set("q", filters.query);
  if (filters.categoryId) params.set("category", filters.categoryId);
  if (filters.periodFrom) params.set("from", filters.periodFrom);
  if (filters.periodTo) params.set("to", filters.periodTo);
  params.set("sort", sort);
  params.set("direction", direction);
  return `/?${params.toString()}#ranking`;
}
