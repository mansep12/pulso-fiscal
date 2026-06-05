export default function LoadingPage() {
  return (
    <main className="mx-auto max-w-6xl px-5 py-20">
      <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-black uppercase tracking-[0.24em] text-slate-500">
          Cargando datos
        </p>
        <div className="mt-6 h-6 max-w-sm rounded-full bg-slate-100" />
        <div className="mt-4 h-24 rounded-2xl bg-slate-100" />
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="h-28 rounded-2xl bg-slate-100" />
          <div className="h-28 rounded-2xl bg-slate-100" />
          <div className="h-28 rounded-2xl bg-slate-100" />
        </div>
      </div>
    </main>
  );
}
