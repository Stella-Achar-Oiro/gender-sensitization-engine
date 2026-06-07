import { useState, useCallback, useRef } from "react";
import Head from "next/head";
import Sidebar, { LANGUAGES } from "../components/Sidebar";
import VerdictBadge from "../components/VerdictBadge";
import DiffView from "../components/DiffView";
import BatchView from "../components/BatchView";
import MetricsBar from "../components/MetricsBar";
import { analyse, analyseBatch, fetchMetrics } from "../lib/api";
import type { AnalyseResponse, LanguageMetrics } from "../lib/api";
import type { GetStaticProps } from "next";

interface Props {
  initialMetrics: Record<string, LanguageMetrics>;
}

type Mode = "single" | "paragraph" | "pdf";

function splitSentences(text: string): string[] {
  // Split on sentence-ending punctuation followed by whitespace or end-of-string
  const raw = text
    .split(/(?<=[.!?؟。？！])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  return raw.length ? raw : [text.trim()];
}

export default function Home({ initialMetrics }: Props) {
  const [lang, setLang]         = useState("sw");
  const [text, setText]         = useState("");
  const [mode, setMode]         = useState<Mode>("single");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [result, setResult]     = useState<AnalyseResponse | null>(null);
  const [batchResults, setBatchResults] = useState<AnalyseResponse[]>([]);
  const [pdfName, setPdfName]   = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const recognitionRef          = useRef<any>(null);
  const fileInputRef            = useRef<HTMLInputElement>(null);
  const metrics = initialMetrics;

  const resetResults = () => { setResult(null); setBatchResults([]); setError(null); };

  const handleAnalyse = useCallback(async () => {
    if (!text.trim()) return;
    setLoading(true);
    resetResults();

    if (mode === "single") {
      try {
        const res = await analyse({ id: crypto.randomUUID(), lang, text: text.trim() });
        setResult(res);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Analysis failed");
      } finally {
        setLoading(false);
      }
      return;
    }

    // Paragraph mode — split and batch
    try {
      const sentences = splitSentences(text.trim());
      const items = sentences.map((s) => ({ id: crypto.randomUUID(), lang, text: s }));
      const res = await analyseBatch(items);
      setBatchResults(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Batch analysis failed");
    } finally {
      setLoading(false);
    }
  }, [lang, text, mode]);

  // PDF upload handler
  const handlePdfUpload = useCallback(async (file: File) => {
    setPdfName(file.name);
    setLoading(true);
    resetResults();
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("lang", lang);
      const res = await fetch(`${(process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "")}/rewrite/pdf`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error(`PDF upload failed (${res.status})`);
      const data: AnalyseResponse[] = await res.json();
      setBatchResults(data);
      setMode("paragraph");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "PDF processing failed");
    } finally {
      setLoading(false);
    }
  }, [lang]);

  // Voice input handler
  const handleVoice = useCallback(() => {
    const SR = (typeof window !== "undefined")
      ? ((window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition)
      : null;
    if (!SR) {
      setError("Voice input not supported in this browser. Try Chrome or Edge.");
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const recognition = new SR();
    recognition.lang = lang === "sw" ? "sw-TZ" : lang === "fr" ? "fr-FR" : lang === "ha" ? "ha-NG" : "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setText(transcript);
      setListening(false);
    };
    recognition.onerror = () => { setListening(false); };
    recognition.onend = () => { setListening(false); };
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, [lang, listening]);

  const langLabel = LANGUAGES.find((l) => l.code === lang)?.label ?? lang;

  return (
    <>
      <Head>
        <title>JuaKazi · Gender Bias Detection</title>
      </Head>

      <div className="flex h-screen overflow-hidden">
        <Sidebar
          activeLang={lang}
          onLangChange={(code) => { setLang(code); resetResults(); }}
          onExampleClick={(t) => { setText(t); resetResults(); }}
          metrics={metrics}
        />

        {/* Main */}
        <main className="flex-1 overflow-y-auto bg-[#f8fafc]">
          {/* Top bar */}
          <div className="sticky top-0 z-10 bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-3">
            <span className="font-semibold text-slate-800">{langLabel}</span>
            <span className="text-slate-300">·</span>
            <span className="text-xs text-muted">afro-xlmr-base</span>
            <a href="/languages" className="ml-auto text-xs text-[#00a651] hover:underline">
              All metrics →
            </a>
          </div>

          <div className="max-w-3xl mx-auto px-6 py-8">
            {/* Mode tabs */}
            <div className="flex items-center gap-1 mb-4 bg-slate-100 rounded-lg p-1 w-fit">
              {(["single", "paragraph", "pdf"] as Mode[]).map((m) => (
                <button
                  key={m}
                  onClick={() => { setMode(m); resetResults(); setPdfName(null); }}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors capitalize ${
                    mode === m
                      ? "bg-white text-slate-800 shadow-sm"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  {m === "pdf" ? "PDF Upload" : m === "paragraph" ? "Paragraph" : "Sentence"}
                </button>
              ))}
            </div>

            {/* PDF mode */}
            {mode === "pdf" ? (
              <div
                className="bg-white rounded-xl border-2 border-dashed border-slate-200 shadow-sm p-8
                           flex flex-col items-center justify-center gap-3 cursor-pointer
                           hover:border-[#00a651] hover:bg-emerald-50/30 transition-colors"
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const f = e.dataTransfer.files[0];
                  if (f?.type === "application/pdf") handlePdfUpload(f);
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handlePdfUpload(f);
                  }}
                />
                <svg className="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {pdfName ? (
                  <p className="text-sm font-semibold text-slate-700">{pdfName}</p>
                ) : (
                  <>
                    <p className="text-sm font-semibold text-slate-600">Drop a PDF here</p>
                    <p className="text-xs text-muted">or click to browse · max 10 MB</p>
                  </>
                )}
                {loading && (
                  <div className="flex items-center gap-2 text-xs text-[#00a651]">
                    <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    Processing…
                  </div>
                )}
              </div>
            ) : (
              /* Text input (single + paragraph) */
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="relative">
                  <textarea
                    className="w-full px-4 pt-4 pb-2 text-sm text-slate-800 resize-none outline-none placeholder-slate-400"
                    rows={mode === "paragraph" ? 6 : 4}
                    placeholder={
                      mode === "paragraph"
                        ? "Paste a paragraph or multiple sentences…"
                        : "Paste or type a sentence to analyse…"
                    }
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleAnalyse();
                    }}
                  />
                  {/* Voice button — inside textarea top-right */}
                  <button
                    onClick={handleVoice}
                    title={listening ? "Stop listening" : "Speak a sentence"}
                    className={`absolute top-3 right-3 p-1.5 rounded-full transition-colors ${
                      listening
                        ? "bg-red-100 text-red-600 animate-pulse"
                        : "text-slate-300 hover:text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2H3v2a9 9 0 0 0 8 8.94V22h2v-1.06A9 9 0 0 0 21 12v-2h-2z"/>
                    </svg>
                  </button>
                </div>
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
            )}

            {/* Error */}
            {error && (
              <div className="mt-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Single sentence results */}
            {mode === "single" && result && (
              <div className="mt-6 flex flex-col gap-4">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-2">
                    Detection
                  </div>
                  <VerdictBadge result={result} />
                </div>

                {(result.edits.filter((e) => e.severity === "replace").length > 0 || result.has_bias_detected) && (
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-2">
                      Correction
                    </div>
                    <DiffView result={result} />
                  </div>
                )}

                <MetricsBar lang={lang} metrics={metrics[lang]} />
              </div>
            )}

            {/* Batch / paragraph / PDF results */}
            {(mode === "paragraph" || mode === "pdf") && (
              <BatchView results={batchResults} loading={loading} />
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
