import Link from "next/link";

import { getInstitutions } from "@/lib/data";
import { formatStatus } from "@/lib/format";

export const metadata = {
  title: "Fuentes",
};

export default function SourcesPage() {
  const institutions = getInstitutions();

  return (
    <main className="mx-auto max-w-6xl px-5 py-14">
      <p className="text-sm font-black uppercase tracking-[0.28em] text-slate-500">Fuentes</p>
      <h1 className="mt-4 text-4xl font-black tracking-tight text-slate-950 sm:text-6xl">
        Matriz inicial de instituciones piloto.
      </h1>
      <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600">
        Esta pagina refleja el estado de revision de fuentes. Mientras no existan URLs oficiales
        validadas, el estado se mantiene como pendiente.
      </p>

      <div className="mt-10 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="grid border-b border-slate-200 bg-slate-50 px-5 py-3 text-xs font-black uppercase tracking-[0.16em] text-slate-500 sm:grid-cols-[1fr_140px_140px]">
          <span>Institucion</span>
          <span>Estado</span>
          <span>Ficha</span>
        </div>
        <div className="divide-y divide-slate-100">
          {institutions.map((institution) => (
            <div className="grid gap-3 px-5 py-4 sm:grid-cols-[1fr_140px_140px] sm:items-center" key={institution.slug}>
              <div>
                <p className="font-bold text-slate-950">{institution.name}</p>
                <p className="mt-1 text-sm text-slate-600">{institution.description}</p>
              </div>
              <span className="w-fit rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
                {formatStatus(institution.sourceStatus)}
              </span>
              <Link className="text-sm font-bold text-slate-950 underline" href={`/ministerios/${institution.slug}`}>
                Ver ficha
              </Link>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
