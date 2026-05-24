import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-slate-200/70 bg-white/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <Link className="group flex items-center gap-3" href="/">
          <span className="grid size-9 place-items-center rounded-full bg-slate-950 text-sm font-black text-white">
            PF
          </span>
          <span>
            <span className="block text-sm font-black uppercase tracking-[0.24em] text-slate-950">
              Pulso Fiscal
            </span>
            <span className="block text-xs text-slate-500">datos publicos claros</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-medium text-slate-600 sm:flex">
          <Link className="hover:text-slate-950" href="/fuentes">
            Fuentes
          </Link>
          <Link className="hover:text-slate-950" href="/metodologia">
            Metodologia
          </Link>
          <a
            className="rounded-full border border-slate-300 px-4 py-2 hover:border-slate-950 hover:text-slate-950"
            href="https://github.com/mansep12/pulso-fiscal"
            rel="noreferrer"
            target="_blank"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
