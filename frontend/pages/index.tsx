import { useState, useCallback } from "react";
import Head from "next/head";
import Sidebar, { LANGUAGES } from "../components/Sidebar";
import VerdictBadge from "../components/VerdictBadge";
import DiffView from "../components/DiffView";
import MetricsBar from "../components/MetricsBar";
import { analyse, fetchMetrics } from "../lib/api";
import type { AnalyseResponse, LanguageMetrics } from "../lib/api";
import type { GetStaticProps } from "next";

interface Props {
  initialMetrics: Record<string, LanguageMetrics>;
}

export default function Home({ initialMetrics }: Props) {
  const [lang, setLang]       = useState("sw");
  const [text, setText]       = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [result, setResult]   = useState<AnalyseResponse | null>(null);
  const metrics = initialMetrics;

  const handleAnalyse = useCallback(async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await analyse({ id: crypto.randomUUID(), lang, text: text.trim() });
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [lang, text]);

  const langLabel = LANGUAGES.find((l) => l.code === lang)?.label ?? lang;

  return (
    <>
      <Head>
        <title>JuaKazi · Gender Bias Detection</title>
      </Head>

      <div className="flex h-screen overflow-hidden">
        <Sidebar
          activeLang={lang}
          onLangChange={(code) => { setLang(code); setResult(null); setError(null); }}
          onExampleClick={(t) => { setText(t); setResult(null); }}
          metrics={metrics}
        />

        {/* Main */}
        <main className="flex-1 overflow-y-auto bg-[#f8fafc]">
          {/* Top bar */}
          <div className="sticky top-0 z-10 bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-3">
            <span className="font-semibold text-slate-800">{langLabel}</span>
            <span className="text-slate-300">·</span>
            <span className="text-xs text-muted">afro-xlmr-base</span>
            <a
              href="/languages"
              className="ml-auto text-xs text-[#00a651] hover:underline"
            >
              All metrics →
            </a>
          </div>

          <div className="max-w-3xl mx-auto px-6 py-8">
            {/* Input */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <textarea
                className="w-full px-4 pt-4 pb-2 text-sm text-slate-800 resize-none outline-none placeholder-slate-400"
                rows={4}
                placeholder="Paste or type a sentence to analyse…"
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleAnalyse();
                }}
              />
              <div className="px-4 pb-3 flex items-center justify-between">
                <span className="text-xs text-muted">⌘ + Enter to analyse</span>
                <button
                  onClick={handleAnalyse}
                  disabled={loading || !text.trim()}
                  className="bg-[#00a651] text-white text-sm font-semibold px-5 py-2 rounded-lg
                             hover:bg-[#009448] active:bg-[#007a3a] transition-colors
                             disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {loading ? "Analysing…" : "Analyse"}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="mt-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Results */}
            {result && (
              <div className="mt-6 flex flex-col gap-4">
                {/* Detection verdict — shown first, prominently */}
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-2">
                    Detection
                  </div>
                  <VerdictBadge result={result} />
                </div>

                {/* Edit detail */}
                {result.edits.filter((e) => e.severity === "replace").length > 0 && (
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-2">
                      Correction
                    </div>
                    <DiffView result={result} />
                  </div>
                )}

                {/* No edit detail when no replace edits but bias detected */}
                {result.has_bias_detected && result.edits.filter((e) => e.severity === "replace").length === 0 && (
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-2">
                      Correction
                    </div>
                    <DiffView result={result} />
                  </div>
                )}

                {/* Metrics */}
                <MetricsBar lang={lang} metrics={metrics[lang]} />
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: { initialMetrics: {} },
  };
};
