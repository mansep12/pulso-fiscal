import { notFound } from "next/navigation";

import { getEstimatedFuelRange, getInstitutionBySlug, getInstitutions, getMonthlySeries, getSpendingByInstitution } from "@/lib/data";
import { formatClp, formatNumber, formatPeriod, formatStatus } from "@/lib/format";

type MinisterioPageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return getInstitutions().map((institution) => ({ slug: institution.slug }));
}

export async function generateMetadata({ params }: MinisterioPageProps) {
  const { slug } = await params;
  const institution = getInstitutionBySlug(slug);

  return {
    title: institution ? institution.name : "Ministerio",
  };
}

export default async function MinisterioPage({ params }: MinisterioPageProps) {
  const { slug } = await params;
  const institution = getInstitutionBySlug(slug);

  if (!institution) {
    notFound();
  }

  const records = getSpendingByInstitution(institution.slug);
  const total = records.reduce((sum, record) => sum + record.amountClp, 0);
  const range = getEstimatedFuelRange(total);
  const monthly = getMonthlySeries(records);

  return (
    <main className="mx-auto max-w-6xl px-5 py-14">
      <p className="text-sm font-black uppercase tracking-[0.28em] text-slate-500">Ficha ministerial</p>
      <div className="mt-4 grid gap-8 lg:grid-cols-[1fr_320px] lg:items-start">
        <section>
          <h1 className="text-4xl font-black tracking-tight text-slate-950 sm:text-6xl">
            {institution.name}
          </h1>
          <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-600">{institution.description}</p>
        </section>

        <aside className="rounded-3xl border border-amber-200 bg-amber-50 p-5 text-amber-950">
          <p className="text-xs font-black uppercase tracking-[0.2em]">Estado de fuente</p>
          <p className="mt-3 text-2xl font-black">{formatStatus(institution.sourceStatus)}</p>
          <p className="mt-2 text-sm leading-6">
            Esta ficha usa datos sample hasta completar revision de fuentes oficiales.
          </p>
        </aside>
      </div>

      <section className="mt-10 grid gap-4 sm:grid-cols-3">
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Gasto demo</p>
          <p className="mt-3 text-3xl font-black text-slate-950">{formatClp(total)}</p>
          <p className="mt-2 text-sm text-slate-600">Suma de registros sample asociados.</p>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Litros estimados</p>
          <p className="mt-3 text-3xl font-black text-slate-950">
            {formatNumber(range.litersMin)} - {formatNumber(range.litersMax)}
          </p>
          <p className="mt-2 text-sm text-slate-600">Rango referencial, no hecho absoluto.</p>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Km estimados</p>
          <p className="mt-3 text-3xl font-black text-slate-950">
            {formatNumber(range.kmMin)} - {formatNumber(range.kmMax)}
          </p>
          <p className="mt-2 text-sm text-slate-600">Calculado con rendimiento 5-12 km/l.</p>
        </article>
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black text-slate-950">Serie mensual demo</h2>
          <div className="mt-5 space-y-4">
            {monthly.map((item) => (
              <div key={item.period}>
                <div className="flex justify-between gap-4 text-sm">
                  <span className="font-bold text-slate-700">{formatPeriod(item.period)}</span>
                  <span className="font-black text-slate-950">{formatClp(item.amountClp)}</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-slate-950"
                    style={{ width: `${Math.max((item.amountClp / Math.max(total, 1)) * 100, 6)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-xl font-black text-slate-950">Registros asociados</h2>
            <p className="mt-1 text-sm text-slate-600">Muestra tecnica para validar la tabla.</p>
          </div>
          <div className="divide-y divide-slate-100">
            {records.map((record) => (
              <div className="grid gap-2 px-5 py-4 sm:grid-cols-[120px_1fr_140px] sm:items-center" key={record.id}>
                <span className="text-sm font-bold text-slate-600">{formatPeriod(record.period)}</span>
                <span>
                  <span className="block font-bold text-slate-950">{record.category}</span>
                  <span className="block text-sm text-slate-500">{record.note}</span>
                </span>
                <span className="font-black text-slate-950 sm:text-right">{formatClp(record.amountClp)}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
