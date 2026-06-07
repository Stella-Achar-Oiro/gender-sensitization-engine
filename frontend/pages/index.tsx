import { useState, useCallback, useRef } from "react";
import Head from "next/head";
import Link from "next/link";
import Sidebar from "../components/Sidebar";
import { LANGUAGES } from "../components/Sidebar";
import VerdictBadge from "../components/VerdictBadge";
import DiffView from "../components/DiffView";
import BatchView from "../components/BatchView";
import MetricsBar from "../components/MetricsBar";
import { analyse, analyseBatch } from "../lib/api";
import type { AnalyseResponse, LanguageMetrics } from "../lib/api";
import { saveToHistory } from "../lib/history";
import type { HistoryEntry } from "../lib/history";
import type { GetStaticProps } from "next";

interface Props {
  initialMetrics: Record<string, LanguageMetrics>;
}

type Mode = "single" | "paragraph" | "pdf";

function splitSentences(text: string): string[] {
  const raw = text
    .split(/(?<=[.!?؟。？！])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  return raw.length ? raw : [text.trim()];
}

const LANG_LOCALES: Record<string, string> = {
  sw: "sw-TZ", ha: "ha-NG", zu: "zu-ZA",
  ki: "ki-KE", fr: "fr-FR", en: "en-US",
};

export default function Home({ initialMetrics }: Props) {
  const [lang, setLang]               = useState("sw");
  const [text, setText]               = useState("");
  const [mode, setMode]               = useState<Mode>("single");
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState<string | null>(null);
  const [result, setResult]           = useState<AnalyseResponse | null>(null);
  const [batchResults, setBatchResults] = useState<AnalyseResponse[]>([]);
  const [pdfName, setPdfName]         = useState<string | null>(null);
  const [listening, setListening]     = useState(false);
  const [historyVersion, setHistoryVersion] = useState(0);
  const recognitionRef                = useRef<any>(null);
  const fileInputRef                  = useRef<HTMLInputElement>(null);
  const metrics = initialMetrics;

  const resetResults = useCallback(() => {
    setResult(null); setBatchResults([]); setError(null);
  }, []);

  const handleLangChange = useCallback((code: string) => {
    setLang(code); resetResults();
  }, [resetResults]);

  const handleAnalyse = useCallback(async () => {
    if (!text.trim()) return;
    setLoading(true);
    resetResults();

    if (mode === "single") {
      try {
        const id = crypto.randomUUID();
        const res = await analyse({ id, lang, text: text.trim() });
        setResult(res);
        saveToHistory({ id, lang, text: text.trim(), result: res, ts: Date.now() });
        setHistoryVersion((v) => v + 1);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Analysis failed");
      } finally {
        setLoading(false);
      }
      return;
    }

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
  }, [lang, text, mode, resetResults]);

  const handlePdfUpload = useCallback(async (file: File) => {
    setPdfName(file.name);
    setLoading(true);
    resetResults();
    setMode("pdf");
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("lang", lang);
      const res = await fetch(
        `${(process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "")}/rewrite/pdf`,
        { method: "POST", body: form }
      );
      if (!res.ok) throw new Error(`PDF upload failed (${res.status})`);
      const data: AnalyseResponse[] = await res.json();
      setBatchResults(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "PDF processing failed");
    } finally {
      setLoading(false);
    }
  }, [lang, resetResults]);

  const handleHistoryClick = useCallback((entry: HistoryEntry) => {
    setLang(entry.lang);
    setText(entry.text);
    setResult(entry.result);
    setMode("single");
    setBatchResults([]);
    setError(null);
  }, []);

  const handleVoice = useCallback(() => {
    const SR = typeof window !== "undefined"
      ? ((window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition)
      : null;
    if (!SR) { setError("Voice input not supported in this browser. Try Chrome or Edge."); return; }
    if (listening) { recognitionRef.current?.stop(); setListening(false); return; }
    const recognition = new SR();
    recognition.lang = LANG_LOCALES[lang] ?? "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (e: any) => { setText(e.results[0][0].transcript); setListening(false); };
    recognition.onerror = () => setListening(false);
    recognition.onend   = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, [lang, listening]);

  const showBatch = mode === "paragraph" || mode === "pdf";
  const langMeta = LANGUAGES.find((l) => l.code === lang);

  return (
    <>
      <Head><title>JuaKazi · Gender Bias Detection</title></Head>

      <div className="flex h-screen overflow-hidden">
        <Sidebar
          activeLang={lang}
          onLangChange={handleLangChange}
          onExampleClick={(t) => { setText(t); resetResults(); setMode("single"); }}
          onHistoryClick={handleHistoryClick}
          metrics={metrics}
          historyVersion={historyVersion}
        />

        <main className="flex-1 overflow-y-auto bg-[#f8fafc]">
          {/* Top bar */}
          <div className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b border-slate-200 px-6 py-3 flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-base leading-none">{langMeta?.flag}</span>
              <span className="font-semibold text-slate-800 text-sm">{langMeta?.label}</span>
            </div>
            <span className="text-slate-300 text-xs">·</span>
            <span className="text-xs text-muted">afro-xlmr-base</span>
            <Link href="/languages" className="ml-auto text-xs text-[#00a651] hover:underline font-medium">
              All metrics →
            </Link>
          </div>

          <div className="max-w-2xl mx-auto px-5 py-7">

            {/* Language pills */}
            <div className="flex flex-wrap gap-1.5 mb-5">
              {LANGUAGES.map((l) => {
                const m = metrics[l.code];
                const isActive = l.code === lang;
                return (
                  <button
                    key={l.code}
                    onClick={() => handleLangChange(l.code)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold
                                border transition-all duration-150 ${
                      isActive
                        ? "bg-[#00a651] text-white border-[#00a651] shadow-sm"
                        : "bg-white text-slate-600 border-slate-200 hover:border-[#00a651] hover:text-[#00a651]"
                    }`}
                  >
                    <span>{l.flag}</span>
                    <span>{l.label}</span>
                    {m && (
                      <span className={`text-[10px] ${isActive ? "opacity-75" : "opacity-40"}`}>
                        {m.f1.toFixed(2)}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Input card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

              {/* Mode tabs */}
              <div className="flex border-b border-slate-100">
                {([["single","Sentence"],["paragraph","Paragraph"],["pdf","PDF"]] as [Mode,string][]).map(([m, label]) => (
                  <button
                    key={m}
                    onClick={() => { setMode(m); resetResults(); setPdfName(null); }}
                    className={`flex-1 py-2.5 text-xs font-semibold transition-colors ${
                      mode === m
                        ? "text-[#00a651] border-b-2 border-[#00a651] bg-emerald-50/40"
                        : "text-slate-400 hover:text-slate-600"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {/* PDF drop zone */}
              {mode === "pdf" ? (
                <div
                  className="flex flex-col items-center justify-center gap-3 py-10 px-6 cursor-pointer
                             hover:bg-emerald-50/30 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const f = e.dataTransfer.files[0];
                    if (f?.type === "application/pdf") handlePdfUpload(f);
                  }}
                >
                  <input ref={fileInputRef} type="file" accept="application/pdf" className="hidden"
                    onChange={(e) => { const f = e.target.files?.[0]; if (f) handlePdfUpload(f); }} />
                  <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center">
                    <svg className="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  {pdfName ? (
                    <p className="text-sm font-semibold text-slate-700">{pdfName}</p>
                  ) : (
                    <>
                      <p className="text-sm font-semibold text-slate-700">Drop a PDF here</p>
                      <p className="text-xs text-muted">or click to browse · max 10 MB</p>
                    </>
                  )}
                  {loading && (
                    <div className="flex items-center gap-2 text-xs text-[#00a651]">
                      <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      Analysing document…
                    </div>
                  )}
                </div>
              ) : (
                /* Text input */
                <>
                  <div className="relative">
                    <textarea
                      className="w-full px-4 pt-4 pb-3 text-sm text-slate-800 resize-none outline-none
                                 placeholder-slate-300 leading-relaxed"
                      rows={mode === "paragraph" ? 6 : 4}
                      placeholder={
                        mode === "paragraph"
                          ? "Paste a paragraph — each sentence will be checked…"
                          : `Type or paste a ${langMeta?.label ?? ""} sentence…`
                      }
                      value={text}
                      onChange={(e) => setText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleAnalyse();
                      }}
                    />
                    {/* Voice mic */}
                    <button
                      onClick={handleVoice}
                      title={listening ? "Stop" : "Speak"}
                      className={`absolute top-3 right-3 p-2 rounded-full transition-all ${
                        listening
                          ? "bg-red-100 text-red-500 animate-pulse shadow-sm"
                          : "text-slate-300 hover:text-slate-500 hover:bg-slate-100"
                      }`}
                    >
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2H3v2a9 9 0 0 0 8 8.94V22h2v-1.06A9 9 0 0 0 21 12v-2h-2z"/>
                      </svg>
                    </button>
                  </div>

                  <div className="px-4 pb-3 flex items-center justify-between border-t border-slate-50">
                    <span className="text-[11px] text-muted">
                      {listening ? "🔴 Listening…" : "⌘ + Enter to analyse"}
                    </span>
                    <button
                      onClick={handleAnalyse}
                      disabled={loading || !text.trim()}
                      className="bg-[#00a651] text-white text-sm font-semibold px-5 py-2 rounded-lg
                                 hover:bg-[#009448] active:bg-[#007a3a] transition-colors
                                 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {loading && (
                        <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      )}
                      {loading ? "Analysing…" : "Analyse"}
                    </button>
                  </div>
                </>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="mt-3 rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Single results */}
            {mode === "single" && result && (
              <div className="mt-5 flex flex-col gap-3">
                <VerdictBadge result={result} />
                {(result.edits.length > 0 || result.has_bias_detected) && (
                  <DiffView result={result} />
                )}
                <MetricsBar lang={lang} metrics={metrics[lang]} />
              </div>
            )}

            {/* Batch results */}
            {showBatch && <BatchView results={batchResults} loading={loading} />}
          </div>
        </main>
      </div>
    </>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  try {
    const fs = await import("fs");
    const path = await import("path");
    const p = path.join(process.cwd(), "..", "eval", "metrics.json");
    const initialMetrics = JSON.parse(fs.readFileSync(p, "utf-8"));
    return { props: { initialMetrics } };
  } catch {
    return { props: { initialMetrics: {} } };
  }
};
