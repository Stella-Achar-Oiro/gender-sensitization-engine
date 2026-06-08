import Head from "next/head";
import Link from "next/link";
import { useEffect, useState } from "react";
import { LANGUAGES } from "../components/Sidebar";
import { fetchMetrics } from "../lib/api";
import type { LanguageMetrics } from "../lib/api";

function tier(f1: number) {
  if (f1 >= 0.85) return { label: "Gold",       color: "text-yellow-700 bg-yellow-50 border-yellow-200" };
  if (f1 >= 0.70) return { label: "Silver",      color: "text-slate-600  bg-slate-50  border-slate-200" };
  if (f1 >= 0.50) return { label: "Bronze",      color: "text-orange-600 bg-orange-50 border-orange-200" };
  return           { label: "Pre-Bronze",         color: "text-red-600   bg-red-50    border-red-200" };
}

function Bar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-[#00a651] transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-mono text-slate-600 w-12 text-right">{value.toFixed(3)}</span>
    </div>
  );
}

export default function Languages() {
  const [metrics, setMetrics] = useState<Record<string, LanguageMetrics>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics()
      .then(setMetrics)
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Head>
        <title>JuaKazi · Language Metrics</title>
      </Head>

      <div className="min-h-screen bg-[#f8fafc]">
        <div className="max-w-4xl mx-auto px-6 py-10">
          <div className="flex items-center gap-4 mb-8">
            <Link href="/" className="text-base text-[#00a651] hover:underline">← Back to analysis</Link>
            <h1 className="text-2xl font-bold text-slate-800">Language Metrics</h1>
          </div>

          {loading ? (
            <div className="text-base text-slate-500 py-12 text-center">Loading metrics…</div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {LANGUAGES.map((lang) => {
                const m = metrics[lang.code];
                const t = m ? tier(m.f1) : null;
                return (
                  <div key={lang.code} className="bg-white rounded-xl border border-slate-200 shadow-sm px-6 py-5">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="text-3xl">{lang.flag}</span>
                      <div>
                        <div className="text-lg font-semibold text-slate-800">{lang.label}</div>
                        <div className="text-sm text-slate-500">multilingual-bias-classifier-v1 · {lang.code}</div>
                      </div>
                      {t && (
                        <span className={`ml-auto text-sm font-semibold border px-3 py-1 rounded-full ${t.color}`}>
                          {t.label}
                        </span>
                      )}
                      {!m && (
                        <span className="ml-auto text-sm text-slate-400 border border-slate-200 px-3 py-1 rounded-full">
                          No data
                        </span>
                      )}
                    </div>

                    {m ? (
                      <div className="flex flex-col gap-3">
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-slate-500 w-20">F1</span>
                          <Bar value={m.f1} />
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-slate-500 w-20">Precision</span>
                          <Bar value={m.precision} />
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-slate-500 w-20">Recall</span>
                          <Bar value={m.recall} />
                        </div>
                        <div className="text-sm text-slate-400 mt-1">
                          {m.samples.toLocaleString()} validation samples
                        </div>
                      </div>
                    ) : (
                      <div className="text-base text-slate-400">
                        Metrics not available — check API connection.
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
