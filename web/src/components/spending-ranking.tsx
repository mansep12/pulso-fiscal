import Link from "next/link";

import { formatClp, formatStatus } from "@/lib/format";
import type { InstitutionSummary } from "@/lib/types";

type SpendingRankingProps = {
  summaries: InstitutionSummary[];
};

export function SpendingRanking({ summaries }: SpendingRankingProps) {
  const max = Math.max(...summaries.map((summary) => summary.totalClp), 1);

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-lg font-black text-slate-950">Ranking demo de combustible</h2>
        <p className="mt-1 text-sm text-slate-600">
          Datos de ejemplo para validar interfaz. No usar como dato real.
        </p>
      </div>
      <div className="divide-y divide-slate-100">
        {summaries.map((summary, index) => (
          <Link
            className="grid gap-3 px-5 py-4 transition hover:bg-slate-50 sm:grid-cols-[44px_1fr_140px] sm:items-center"
            href={`/ministerios/${summary.institution.slug}`}
            key={summary.institution.slug}
          >
            <span className="grid size-9 place-items-center rounded-full bg-slate-100 text-sm font-black text-slate-700">
              {index + 1}
            </span>
            <span>
              <span className="flex flex-wrap items-center gap-2">
                <span className="font-bold text-slate-950">{summary.institution.name}</span>
                <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-bold text-amber-800">
                  {formatStatus(summary.confidence)}
                </span>
              </span>
              <span className="mt-2 block h-2 overflow-hidden rounded-full bg-slate-100">
                <span
                  className="block h-full rounded-full bg-slate-950"
                  style={{ width: `${Math.max((summary.totalClp / max) * 100, 4)}%` }}
                />
              </span>
            </span>
            <span className="text-left text-lg font-black text-slate-950 sm:text-right">
              {formatClp(summary.totalClp)}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
