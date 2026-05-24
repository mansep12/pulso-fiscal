import Link from "next/link";

import { MetricCard } from "@/components/metric-card";
import { SpendingRanking } from "@/components/spending-ranking";
import { getInstitutionSummaries, getInstitutions, getNationalTotal } from "@/lib/data";
import { formatClp } from "@/lib/format";

export default function HomePage() {
  const institutions = getInstitutions();
  const summaries = getInstitutionSummaries();
  const total = getNationalTotal();

  return (
    <main>
      <section className="mx-auto grid max-w-6xl gap-10 px-5 py-16 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.28em] text-slate-500">
            Transparencia operacional
          </p>
          <h1 className="mt-5 max-w-4xl text-5xl font-black tracking-tight text-slate-950 sm:text-7xl">
            Gasto publico explicado sin tecnicismos.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            Pulso Fiscal recopila fuentes oficiales, normaliza datos dificiles de revisar y los
            transforma en metricas verificables para ciudadanos.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              className="rounded-full bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-sm hover:bg-slate-800"
              href="/fuentes"
            >
              Revisar fuentes
            </Link>
            <Link
              className="rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-bold text-slate-950 hover:border-slate-950"
              href="/metodologia"
            >
              Ver metodologia
            </Link>
          </div>
        </div>

        <aside className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.24em] text-amber-700">Estado MVP</p>
          <p className="mt-4 text-2xl font-black text-slate-950">Datos de demostracion</p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Esta version deja lista la interfaz. Las cifras actuales no representan datos reales y
            deben reemplazarse por fuentes oficiales procesadas por el ETL.
          </p>
        </aside>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-5 pb-8 sm:grid-cols-3">
        <MetricCard
          detail="Suma de registros sample para validar componentes."
          label="Gasto demo"
          value={formatClp(total)}
        />
        <MetricCard
          detail="Primer grupo para revisar disponibilidad real de fuentes."
          label="Instituciones piloto"
          value={String(institutions.length)}
        />
        <MetricCard
          detail="Se reemplazaran por reglas reproducibles con fuentes oficiales."
          label="Alertas reales"
          value="0"
        />
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-16">
        <SpendingRanking summaries={summaries} />
      </section>
    </main>
  );
}
