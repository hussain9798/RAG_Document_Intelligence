import { Link } from "react-router-dom";
import {
  ArrowRight,
  BrainCircuit,
  Check,
  FileSearch,
  MessageSquareText,
  Sparkles,
  UploadCloud,
} from "lucide-react";

const STEPS = [
  {
    icon: UploadCloud,
    number: "01",
    title: "Add your knowledge",
    description: "Upload PDFs and documents in seconds. Your workspace keeps everything organised.",
  },
  {
    icon: FileSearch,
    number: "02",
    title: "Retrieve the right context",
    description: "DocIntel searches your content semantically, not just by matching keywords.",
  },
  {
    icon: MessageSquareText,
    number: "03",
    title: "Ask and get answers",
    description: "Chat naturally and see the exact sources behind every answer.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#080b1d] text-white selection:bg-fuchsia-400/30">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="home-orb home-orb-blue" />
        <div className="home-orb home-orb-pink" />
        <div className="home-orb home-orb-cyan" />
        <div className="absolute inset-0 opacity-[0.07] [background-image:linear-gradient(rgba(255,255,255,.8)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.8)_1px,transparent_1px)] [background-size:64px_64px]" />
      </div>

      <nav className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-10">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-300 via-indigo-500 to-fuchsia-500 shadow-lg shadow-indigo-500/30">
            <Sparkles size={20} />
          </span>
          <span className="text-xl font-bold tracking-tight">DocIntel</span>
        </Link>
        <div className="flex items-center gap-3">
          <Link to="/login" className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-white/10 hover:text-white">
            Log in
          </Link>
          <Link to="/register" className="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-indigo-950 shadow-lg shadow-white/10 transition hover:-translate-y-0.5 hover:bg-cyan-100">
            Get started
          </Link>
        </div>
      </nav>

      <section className="relative z-10 mx-auto grid max-w-7xl items-center gap-14 px-6 pb-24 pt-14 lg:grid-cols-[1.05fr_.95fr] lg:px-10 lg:pb-32 lg:pt-20">
        <div className="animate-slide-up">
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3.5 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-300" />
            Retrieval augmented intelligence
          </div>
          <h1 className="max-w-3xl break-words text-4xl font-bold leading-[1.05] tracking-[-0.04em] sm:text-6xl lg:text-7xl">
            Your documents.
            <span className="block bg-gradient-to-r from-cyan-200 via-indigo-300 to-fuchsia-300 bg-clip-text text-transparent">
              Supercharged.
            </span>
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-8 text-slate-300">
            Turn scattered files into a source of truth. DocIntel uses RAG to find relevant context and deliver grounded, intelligent answers in seconds.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link to="/register" className="group inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-400 via-indigo-500 to-fuchsia-500 px-5 py-3.5 font-semibold shadow-xl shadow-indigo-500/25 transition hover:-translate-y-1">
              Start building your knowledge base
              <ArrowRight size={18} className="transition group-hover:translate-x-1" />
            </Link>
            <Link to="/login" className="inline-flex items-center justify-center rounded-2xl border border-white/15 bg-white/[0.06] px-5 py-3.5 font-semibold text-slate-200 backdrop-blur transition hover:bg-white/10">
              Explore workspace
            </Link>
          </div>
          <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-400">
            {["Source-backed answers", "Private workspaces", "Instant setup"].map((item) => (
              <span key={item} className="flex items-center gap-2">
                <Check size={15} className="text-cyan-300" />
                {item}
              </span>
            ))}
          </div>
        </div>

        <div className="relative animate-slide-up [animation-delay:120ms]">
          <div className="absolute -inset-5 rounded-[2.5rem] bg-gradient-to-r from-cyan-400/20 via-indigo-500/20 to-fuchsia-500/20 blur-3xl" />
          <div className="relative rounded-[2rem] border border-white/15 bg-white/[0.08] p-4 shadow-2xl shadow-indigo-950/50 backdrop-blur-xl">
            <div className="rounded-[1.4rem] border border-white/10 bg-[#10142d]/90 p-5 sm:p-7">
              <div className="mb-8 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-300 to-indigo-500">
                    <BrainCircuit size={17} />
                  </span>
                  Ask your knowledge base
                </div>
                <span className="rounded-full bg-emerald-400/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-300">Live</span>
              </div>
              <div className="mb-5 ml-auto max-w-[88%] rounded-2xl rounded-br-md bg-gradient-to-r from-indigo-500 to-fuchsia-500 px-4 py-3 text-sm leading-6 shadow-lg">
                Summarise the key risks from our latest product report.
              </div>
              <div className="flex gap-3 rounded-2xl rounded-bl-md border border-white/10 bg-white/[0.06] p-4 text-sm leading-6 text-slate-300">
                <Sparkles size={16} className="mt-1 shrink-0 text-cyan-300" />
                <div>
                  <p>Three key risks surfaced from your documents, with evidence from <span className="font-medium text-cyan-200">Product Report.pdf</span>.</p>
                  <div className="mt-4 flex items-center gap-2 border-t border-white/10 pt-3 text-xs text-slate-400">
                    <FileSearch size={13} /> 4 sources found <span className="text-emerald-300">• 94% relevance</span>
                  </div>
                </div>
              </div>
              <div className="mt-7 flex items-center gap-2 text-xs text-slate-500">
                <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-300" />
                RAG engine is thinking...
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="relative z-10 border-t border-white/10 bg-white/[0.03] px-6 py-20 lg:px-10">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 max-w-2xl">
            <p className="mb-3 text-sm font-bold uppercase tracking-[0.2em] text-cyan-300">How it works</p>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">From raw files to reliable answers.</h2>
            <p className="mt-4 text-slate-400">A focused RAG workflow that keeps your team moving and your answers grounded in real context.</p>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            {STEPS.map(({ icon: Icon, number, title, description }) => (
              <article key={number} className="group rounded-3xl border border-white/10 bg-white/[0.06] p-6 transition duration-300 hover:-translate-y-2 hover:border-cyan-300/30 hover:bg-white/[0.1]">
                <div className="mb-8 flex items-center justify-between">
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-300/20 to-indigo-500/30 text-cyan-200 transition group-hover:scale-110">
                    <Icon size={22} />
                  </span>
                  <span className="text-sm font-bold text-white/30">{number}</span>
                </div>
                <h3 className="text-lg font-semibold">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <footer className="relative z-10 flex flex-col items-center justify-between gap-4 border-t border-white/10 px-6 py-7 text-sm text-slate-500 sm:flex-row lg:px-10">
        <span>© {new Date().getFullYear()} DocIntel</span>
        <span>Intelligence grounded in your knowledge.</span>
      </footer>
    </main>
  );
}
