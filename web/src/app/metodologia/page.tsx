export const metadata = {
  title: "Metodologia",
};

const sections = [
  {
    title: "Trazabilidad",
    body: "Cada dato debe conservar URL fuente, fecha de captura, institucion emisora y hash del documento cuando exista un archivo descargable.",
  },
  {
    title: "Estimaciones como rangos",
    body: "Litros y kilometros equivalentes no se muestran como hechos exactos. Se calculan con supuestos publicados y se presentan como rangos.",
  },
  {
    title: "Alertas tecnicas",
    body: "Una alerta es una regla reproducible sobre datos publicos. No representa una acusacion ni una conclusion legal.",
  },
  {
    title: "Niveles de confianza",
    body: "Alto indica dato directo con documento oficial; medio indica calculo desde fuente oficial; bajo indica dato incompleto o pendiente de validacion.",
  },
];

export default function MethodologyPage() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-14">
      <p className="text-sm font-black uppercase tracking-[0.28em] text-slate-500">Metodologia</p>
      <h1 className="mt-4 text-4xl font-black tracking-tight text-slate-950 sm:text-6xl">
        Como se convierte una fuente oficial en una metrica clara.
      </h1>
      <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600">
        La metodologia completa vive en `docs/metodologia.md`. Esta pagina resume las reglas que
        debe cumplir cualquier dato antes de aparecer en el sitio publico.
      </p>

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        {sections.map((section) => (
          <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" key={section.title}>
            <h2 className="text-xl font-black text-slate-950">{section.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{section.body}</p>
          </article>
        ))}
      </div>
    </main>
  );
}
