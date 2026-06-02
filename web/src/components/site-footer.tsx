export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-slate-950 text-slate-300">
      <div className="mx-auto grid max-w-6xl gap-6 px-5 py-10 sm:grid-cols-[1.4fr_1fr]">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.24em] text-white">Pulso Fiscal</p>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Ranking neutral de gastos operacionales del Senado de Chile. Los datos provienen de una
            fuente oficial y se presentan como comparaciones tecnicas.
          </p>
        </div>
        <div className="text-sm leading-6 text-slate-400">
          <p>Codigo MIT. Datos publicados bajo CC-BY-4.0.</p>
          <p>Un monto alto no implica por si solo irregularidad.</p>
        </div>
      </div>
    </footer>
  );
}
