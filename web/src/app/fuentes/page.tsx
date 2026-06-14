import { getCategories, getPeriodRange } from "@/lib/queries";
import { formatNumber, formatPeriod } from "@/lib/format";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Fuentes",
};

export default async function SourcesPage() {
  const [range, categories] = await Promise.all([getPeriodRange(), getCategories()]);

  return (
    <main className="mx-auto max-w-6xl px-5 py-14">
      <p className="text-sm font-black uppercase tracking-[0.28em] text-slate-500">Fuentes</p>
      <h1 className="mt-4 text-4xl font-black tracking-tight text-slate-950 sm:text-6xl">
        Fuente oficial usada por el MVP.
      </h1>
      <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600">
        La primera versión de Pulso Fiscal usa solo gastos operacionales publicados por el Senado
        de Chile. Los datos se descargan, normalizan y cargan a Supabase antes de aparecer en la web.
      </p>

      <section className="mt-10 grid gap-4 sm:grid-cols-3">
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Dataset</p>
          <p className="mt-3 text-2xl font-black text-slate-950">Senado</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">Gastos operacionales de senadores.</p>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Período web</p>
          <p className="mt-3 text-2xl font-black text-slate-950">
            {range ? `${formatPeriod(range.from)} - ${formatPeriod(range.to)}` : "Sin datos"}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-600">La web filtra desde 2021.</p>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Categorías</p>
          <p className="mt-3 text-2xl font-black text-slate-950">{formatNumber(categories.length)}</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">Categorías normalizadas disponibles.</p>
        </article>
      </section>

      <section className="mt-10 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-black text-slate-950">URL oficial</h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          La fuente visible para ciudadanos es la página de Transparencia Activa del Senado. El ETL
          usa la API pública que consume esa página y guarda URL, fecha de captura y hash del body.
        </p>
        <a
          className="mt-5 inline-flex rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white hover:bg-slate-800"
          href="https://www.senado.cl/transparencia/gastos-operacionales-senadores"
          rel="noreferrer"
          target="_blank"
        >
          Abrir fuente oficial
        </a>
      </section>

      <section className="mt-10 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-xl font-black text-slate-950">Categorías normalizadas</h2>
          <p className="mt-1 text-sm text-slate-600">Ordenadas por total acumulado desde 2021.</p>
        </div>
        <div className="divide-y divide-slate-100">
          {categories.length === 0 ? (
            <p className="px-5 py-4 text-sm text-slate-500">No hay categorías disponibles.</p>
          ) : (
            categories.slice(0, 20).map((category) => (
              <div className="grid gap-2 px-5 py-4 sm:grid-cols-[1fr_160px]" key={category.id}>
                <span>
                  <span className="block font-bold text-slate-950">{category.name}</span>
                  <span className="text-sm text-slate-500">
                    {formatNumber(category.recordCount)} registros, {formatNumber(category.activeMonths)} meses
                  </span>
                </span>
                <span className="font-black text-slate-950 sm:text-right">
                  {formatNumber(category.senatorCount)} senadores
                </span>
              </div>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
