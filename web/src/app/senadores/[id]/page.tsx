import Link from "next/link";
import { notFound } from "next/navigation";

import { MetricCard } from "@/components/metric-card";
import {
  getPeriodRange,
  getSenadorCategories,
  getSenadorPeriods,
  getSenadorSummary,
} from "@/lib/queries";
import { formatClp, formatNumber, formatPeriod } from "@/lib/format";

export const dynamic = "force-dynamic";

type SenatorPageProps = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({ params }: SenatorPageProps) {
  const { id } = await params;
  const summary = await getSenadorSummary(decodeURIComponent(id));

  return {
    title: summary ? summary.name : "Senador",
  };
}

export default async function SenatorPage({ params }: SenatorPageProps) {
  const { id } = await params;
  const senadorId = decodeURIComponent(id);
  const [summary, categories, periods, range] = await Promise.all([
    getSenadorSummary(senadorId),
    getSenadorCategories(senadorId),
    getSenadorPeriods(senadorId),
    getPeriodRange(),
  ]);

  if (!summary) {
    notFound();
  }

  const periodLabel = range
    ? `${formatPeriod(range.from)} - ${formatPeriod(range.to)}`
    : "desde 2021";

  return (
    <main className="mx-auto max-w-6xl px-5 py-14">
      <Link className="text-sm font-black text-slate-600 underline" href="/#ranking">
        Volver al ranking
      </Link>

      <section className="mt-8 grid gap-8 lg:grid-cols-[1fr_320px] lg:items-start">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.28em] text-slate-500">
            Ficha de senador
          </p>
          <h1 className="mt-4 text-4xl font-black tracking-tight text-slate-950 sm:text-6xl">
            {summary.name}
          </h1>
          <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-600">
            Resumen de gastos operacionales publicados por la fuente oficial del Senado. Esta ficha
            compara montos y registros; no interpreta causalidad ni irregularidad.
          </p>
        </div>

        <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Periodo</p>
          <p className="mt-3 text-2xl font-black text-slate-950">{periodLabel}</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Solo registros rankeables desde 2021 en el ultimo run cargado.
          </p>
        </aside>
      </section>

      <section className="mt-10 grid gap-4 sm:grid-cols-4">
        <MetricCard
          detail="Suma de gastos incluidos en ranking."
          label="Total"
          value={formatClp(summary.totalClp)}
        />
        <MetricCard
          detail="Total dividido por meses con datos."
          label="Promedio mensual"
          value={formatClp(summary.monthlyAverageClp)}
        />
        <MetricCard
          detail="Meses en que el senador aparece con registros."
          label="Meses con datos"
          value={formatNumber(summary.activeMonths)}
        />
        <MetricCard
          detail="Filas usadas para calcular la ficha."
          label="Registros"
          value={formatNumber(summary.recordCount)}
        />
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-xl font-black text-slate-950">Gasto por categoria</h2>
            <p className="mt-1 text-sm text-slate-600">Ordenado por total acumulado.</p>
          </div>
          <div className="divide-y divide-slate-100">
            {categories.map((category) => (
              <div className="grid gap-2 px-5 py-4 sm:grid-cols-[1fr_140px]" key={category.id}>
                <span>
                  <span className="block font-bold text-slate-950">{category.name}</span>
                  <span className="text-sm text-slate-500">
                    {formatNumber(category.recordCount)} registros en {formatNumber(category.activeMonths)} meses
                  </span>
                </span>
                <span className="font-black text-slate-950 sm:text-right">
                  {formatClp(category.totalClp)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-xl font-black text-slate-950">Serie mensual</h2>
            <p className="mt-1 text-sm text-slate-600">Periodos con registros desde 2021.</p>
          </div>
          <div className="max-h-155 divide-y divide-slate-100 overflow-y-auto">
            {periods.map((period) => (
              <div
                className="grid gap-2 px-5 py-4 sm:grid-cols-[1fr_150px] sm:items-center"
                key={period.period}
              >
                <span>
                  <span className="block font-bold text-slate-950">{formatPeriod(period.period)}</span>
                  <span className="text-sm text-slate-500">
                    {formatNumber(period.recordCount)} registros, {formatNumber(period.categoryCount)} categorias
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
