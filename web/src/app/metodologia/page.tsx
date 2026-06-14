export const metadata = {
  title: "Metodología",
};

const sections = [
  {
    title: "Fuente única",
    body: "El MVP usa solo la fuente oficial de gastos operacionales del Senado. La web no mezcla otros organismos ni datos de demostración.",
  },
  {
    title: "Desde 2021",
    body: "Las vistas usadas por la web filtran registros rankeables desde enero de 2021 hasta el último período cargado.",
  },
  {
    title: "Comparación justa",
    body: "El orden por defecto usa promedio mensual: total dividido por meses con datos. Así no se favorece automáticamente a quien aparece más tiempo.",
  },
  {
    title: "No acusatorio",
    body: "Los rankings son comparaciones técnicas sobre datos públicos. Un monto alto no implica por sí solo irregularidad.",
  },
];

export default function MethodologyPage() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-14">
      <p className="text-sm font-black uppercase tracking-[0.28em] text-slate-500">Metodología</p>
      <h1 className="mt-4 text-4xl font-black tracking-tight text-slate-950 sm:text-6xl">
        Cómo se calcula el ranking del Senado.
      </h1>
      <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600">
        El pipeline descarga la fuente oficial, conserva trazabilidad, normaliza categorías y carga
        a Supabase. La web consulta vistas agregadas del último run ok.
      </p>

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        {sections.map((section) => (
          <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" key={section.title}>
            <h2 className="text-xl font-black text-slate-950">{section.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{section.body}</p>
          </article>
        ))}
      </div>

      <section className="mt-10 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-black text-slate-950">Fórmula principal</h2>
        <div className="mt-4 rounded-2xl bg-slate-950 p-5 font-mono text-sm text-slate-100">
          promedio_mensual = total_monto / meses_con_datos
        </div>
        <p className="mt-4 text-sm leading-6 text-slate-600">
          `meses_con_datos` cuenta solo meses donde el senador tiene registros rankeables. El total
          y los registros se recalculan cuando se filtra por categoría o período.
        </p>
      </section>
    </main>
  );
}
