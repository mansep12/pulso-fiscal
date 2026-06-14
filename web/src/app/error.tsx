"use client";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main className="mx-auto max-w-3xl px-5 py-20">
      <div className="rounded-3xl border border-red-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-black uppercase tracking-[0.24em] text-red-700">
          Error de carga
        </p>
        <h1 className="mt-4 text-3xl font-black tracking-tight text-slate-950">
          No pudimos cargar los datos.
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Puede ser un problema temporal con la base de datos o con la configuración del
          servicio. Intenta nuevamente en unos momentos.
        </p>
        <button
          className="mt-6 rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white hover:bg-slate-800"
          onClick={reset}
          type="button"
        >
          Intentar nuevamente
        </button>
      </div>
    </main>
  );
}
