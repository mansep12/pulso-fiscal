import Link from "next/link";

export default function NotFoundPage() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-20">
      <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-black uppercase tracking-[0.24em] text-slate-500">
          No encontrado
        </p>
        <h1 className="mt-4 text-3xl font-black tracking-tight text-slate-950">
          Página no encontrada.
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          El recurso solicitado no existe o ya no está disponible en el último run cargado.
        </p>
        <Link
          className="mt-6 inline-flex rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white hover:bg-slate-800"
          href="/"
        >
          Volver al ranking
        </Link>
      </div>
    </main>
  );
}
