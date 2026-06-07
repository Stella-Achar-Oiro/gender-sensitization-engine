import Head from "next/head";
import Link from "next/link";
import { LANGUAGES } from "../components/Sidebar";
import type { LanguageMetrics } from "../lib/api";
import type { GetStaticProps } from "next";

interface Props {
  metrics: Record<string, LanguageMetrics>;
}

function tier(f1: number) {
  if (f1 >= 0.85) return { label: "Gold",       color: "text-yellow-700 bg-yellow-50 border-yellow-200" };
  if (f1 >= 0.70) return { label: "Silver",      color: "text-slate-600  bg-slate-50  border-slate-200" };
  if (f1 >= 0.50) return { label: "Bronze",      color: "text-orange-600 bg-orange-50 border-orange-200" };
  return           { label: "Pre-Bronze",         color: "text-red-600   bg-red-50    border-red-200" };
}

function Bar({ value, max = 1 }: { value: number; max?: number }) {
  const pct = Math.round((value / max) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-[#00a651] transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-600 w-10 text-right">{value.toFixed(3)}</span>
    </div>
  );
}

export default function Languages({ metrics }: Props) {
  return (
    <>
      <Head>
        <title>JuaKazi · Language Metrics</title>
      </Head>

      <div className="min-h-screen bg-[#f8fafc]">
        <div className="max-w-4xl mx-auto px-6 py-10">
          <div className="flex items-center gap-4 mb-8">
            <Link href="/" className="text-sm text-[#00a651] hover:underline">← Back</Link>
            <h1 className="text-xl font-bold text-slate-800">Language Metrics</h1>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {LANGUAGES.map((lang) => {
              const m = metrics[lang.code];
              const t = m ? tier(m.f1) : null;
              return (
                <div key={lang.code} className="bg-white rounded-xl border border-slate-200 shadow-sm px-6 py-5">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-2xl">{lang.flag}</span>
                    <div>
                      <div className="font-semibold text-slate-800">{lang.label}</div>
                      <div className="text-xs text-muted">afro-xlmr-base · {lang.code}</div>
                    </div>
                    {t && (
                      <span className={`ml-auto text-xs font-semibold border px-2.5 py-1 rounded-full ${t.color}`}>
                        {t.label}
                      </span>
                    )}
                    {!m && (
                      <span className="ml-auto text-xs text-muted border border-slate-200 px-2.5 py-1 rounded-full">
                        Training…
                      </span>
                    )}
                  </div>

                  {m ? (
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] text-muted w-16">F1</span>
                        <Bar value={m.f1} />
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] text-muted w-16">Precision</span>
                        <Bar value={m.precision} />
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] text-muted w-16">Recall</span>
                        <Bar value={m.recall} />
                      </div>
                      <div className="text-xs text-muted mt-1">
                        {m.samples.toLocaleString()} test samples
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-muted">
                      Classifier training in progress — metrics available after model upload.
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  try {
    const fs = await import("fs");
    const path = await import("path");
    const p = path.join(process.cwd(), "..", "eval", "metrics.json");
    const metrics = JSON.parse(fs.readFileSync(p, "utf-8"));
    return { props: { metrics } };
  } catch {
    return { props: { metrics: {} } };
  }
};
