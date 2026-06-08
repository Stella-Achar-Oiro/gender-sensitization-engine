import { useState, useCallback, useRef, useEffect, useLayoutEffect } from "react";
import Head from "next/head";
import Sidebar, { LANGUAGES, EXAMPLES } from "../components/Sidebar";
import ResultCard from "../components/ResultCard";
import type { ExportRow } from "../components/ResultCard";
import { analyse, analyseBatch, fetchMetrics } from "../lib/api";
import type { AnalyseResponse, LanguageMetrics } from "../lib/api";
import { saveToHistory } from "../lib/history";
import type { HistoryEntry } from "../lib/history";

type Mode = "text" | "pdf" | "csv";

const LANG_LOCALES: Record<string, string> = {
  sw: "sw-TZ", ha: "ha-NG", zu: "zu-ZA",
  ki: "ki-KE", fr: "fr-FR", en: "en-US",
};

function splitSentences(text: string): string[] {
  const raw = text
    .split(/(?<=[.!?؟。？！])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  return raw.length ? raw : [text.trim()];
}

interface ThreadItem {
  id: string;
  input: string;
  result: AnalyseResponse;
  lang: string;
  exportRow?: ExportRow;
}

function EmptyState({ lang, onExample }: { lang: string | null; onExample: (t: string) => void }) {
  const examples = lang ? (EXAMPLES[lang] ?? []) : [];
  const langMeta = lang ? LANGUAGES.find(l => l.code === lang) : null;

  return (
    <div className="flex flex-col items-center justify-center h-full px-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-[#00a651] flex items-center justify-center mb-5 shadow-lg">
        <span className="text-white font-bold text-3xl leading-none">J</span>
      </div>
      <h1 className="text-2xl font-bold text-[#1a1a2e] mb-2">JuaKazi</h1>
      <p className="text-base text-[#475569] mb-8 max-w-sm leading-relaxed">
        Gender bias detection and correction across 6 African languages.
        {!lang && " Select a language to begin."}
      </p>

      {lang && examples.length > 0 && (
        <div className="w-full max-w-lg">
          <p className="text-xs font-semibold uppercase tracking-widest text-[#94a3b8] mb-3">
            Try an example in {langMeta?.label}
          </p>
          <div className="flex flex-col gap-2">
            {examples.map((ex, i) => (
              <button
                key={i}
                onClick={() => onExample(ex)}
                className="text-left text-sm text-[#1a1a2e] bg-white border border-slate-200
                           rounded-xl px-4 py-3 hover:border-[#00a651] hover:shadow-sm
                           transition-all duration-150 leading-relaxed"
              >
                {langMeta?.flag} {ex}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Home() {
  const [lang, setLang]           = useState<string | null>(null);
  const [text, setText]           = useState("");
  const [mode, setMode]           = useState<Mode>("text");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [thread, setThread]       = useState<ThreadItem[]>([]);
  const [listening, setListening] = useState(false);
  const [historyVersion, setHistoryVersion] = useState(0);
  const [metrics, setMetrics]     = useState<Record<string, LanguageMetrics>>({});
  const [pdfName, setPdfName]     = useState<string | null>(null);
  const [exportRows, setExportRows] = useState<ExportRow[]>([]);

  const recognitionRef  = useRef<any>(null);
  const fileInputRef    = useRef<HTMLInputElement>(null);
  const csvInputRef     = useRef<HTMLInputElement>(null);
  const threadEndRef    = useRef<HTMLDivElement>(null);
  const textareaRef     = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchMetrics().then(setMetrics).catch(() => {});
  }, []);

  useLayoutEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread]);

  const langMeta = lang ? LANGUAGES.find(l => l.code === lang) : null;
  const noLang   = lang === null;

  const handleLangChange = useCallback((code: string) => {
    setLang(code); setThread([]); setText(""); setError(null);
  }, []);

  const handleHistoryClick = useCallback((entry: HistoryEntry) => {
    setLang(entry.lang);
    setThread([{ id: entry.id, input: entry.text, result: entry.result, lang: entry.lang }]);
    setMode("text");
  }, []);

  const addToThread = useCallback((input: string, result: AnalyseResponse, langCode: string) => {
    const id = crypto.randomUUID();
    setThread(prev => [...prev, { id, input, result, lang: langCode }]);
    saveToHistory({ id, lang: langCode, text: input, result, ts: Date.now() });
    setHistoryVersion(v => v + 1);
  }, []);

  const handleAnalyse = useCallback(async () => {
    if (!text.trim() || !lang) return;
    const input = text.trim();
    setText("");
    setLoading(true);
    setError(null);

    // Auto-detect: single sentence vs paragraph — no mode switch needed
    const sentences = splitSentences(input);
    try {
      if (sentences.length === 1) {
        const res = await analyse({ id: crypto.randomUUID(), lang, text: input });
        addToThread(input, res, lang);
      } else {
        const items = sentences.map(s => ({ id: crypto.randomUUID(), lang, text: s }));
        const results = await analyseBatch(items);
        results.forEach((res, i) => addToThread(sentences[i], res, lang));
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [lang, text, addToThread]);

  const handlePdfUpload = useCallback(async (file: File) => {
    if (!lang) return;
    setPdfName(file.name);
    setLoading(true);
    setError(null);
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
      data.forEach((r, i) => addToThread(`[PDF] sentence ${i + 1}`, r, lang));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "PDF processing failed");
    } finally {
      setLoading(false);
    }
  }, [lang, addToThread]);

  const handleCsvUpload = useCallback(async (file: File) => {
    if (!lang) return;
    setLoading(true);
    setError(null);
    try {
      const text = await file.text();
      const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
      const header = lines[0].toLowerCase().split(",");
      const textIdx = header.findIndex(h => h === "text" || h === "sentence" || h === "content");
      const rows = lines.slice(1).map(l => {
        const cols = l.split(",");
        return textIdx >= 0 ? cols[textIdx]?.replace(/^"|"$/g, "").trim() : cols[0]?.replace(/^"|"$/g, "").trim();
      }).filter(Boolean) as string[];
      const items = rows.map(s => ({ id: crypto.randomUUID(), lang: lang!, text: s }));
      const results = await analyseBatch(items);
      results.forEach((res, i) => addToThread(rows[i], res, lang!));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "CSV processing failed");
    } finally {
      setLoading(false);
    }
  }, [lang, addToThread]);

  const handleVoice = useCallback(() => {
    if (!lang) return;
    const SR = typeof window !== "undefined"
      ? ((window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition)
      : null;
    if (!SR) { setError("Voice input not supported. Try Chrome or Edge."); return; }
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

  const handleExport = useCallback(() => {
    if (!exportRows.length && !thread.length) return;
    const rows = thread.map(item => ({
      original_text: item.input,
      corrected_text: item.result.rewrite ?? item.input,
      reviewer_action: item.exportRow?.reviewer_action ?? "pending",
      flag_note: item.exportRow?.flag_note ?? "",
      qa_status: item.exportRow?.qa_status ?? "pending",
      source: item.result.source ?? "",
      confidence: item.result.confidence ?? 0,
      lang: item.lang,
    }));
    const header = ["original_text","corrected_text","reviewer_action","flag_note","qa_status","source","confidence","lang"];
    const csv = [header.join(","), ...rows.map(r =>
      header.map(k => `"${String((r as any)[k]).replace(/"/g, '""')}"`).join(",")
    )].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `juakazi_review_${lang}_${Date.now()}.csv`;
    a.click();
  }, [thread, exportRows, lang]);

  const placeholder = noLang
    ? "Select a language from the sidebar to begin…"
    : `Type or paste text in ${langMeta?.label}… (⌘+Enter to analyse)`;

  const biasCount   = thread.filter(t => t.result.has_bias_detected).length;
  const reviewedCount = exportRows.length;

  return (
    <>
      <Head><title>JuaKazi · Gender Bias Detection</title></Head>

      <div className="flex h-screen overflow-hidden">
        <Sidebar
          activeLang={lang ?? ""}
          onLangChange={handleLangChange}
          onHistoryClick={handleHistoryClick}
          metrics={metrics}
          historyVersion={historyVersion}
        />

        {/* Main area */}
        <div className="flex-1 flex flex-col overflow-hidden bg-[#f5f5f0]">

          {/* Top bar */}
          <div className="flex-shrink-0 bg-white border-b border-slate-200 px-6 py-3.5 flex items-center gap-3">
            {langMeta ? (
              <>
                <span className="text-xl leading-none">{langMeta.flag}</span>
                <span className="font-bold text-lg text-[#1a1a2e]">{langMeta.label}</span>
                <span className="text-slate-300">·</span>
                <span className="text-sm text-[#475569]">afro-xlmr-base + afriteva-v2</span>
              </>
            ) : (
              <span className="text-base font-semibold text-[#1a1a2e]">JuaKazi — Gender Bias Detection</span>
            )}

            {thread.length > 0 && (
              <div className="ml-auto flex items-center gap-3">
                <span className="text-sm text-[#475569]">
                  {thread.length} analysed · {biasCount} bias detected
                </span>
                <button
                  onClick={handleExport}
                  className="flex items-center gap-1.5 text-sm bg-[#1a1a2e] hover:bg-[#0f172a]
                             text-white font-semibold px-4 py-2 rounded-lg transition-colors"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round"
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                  </svg>
                  Export CSV
                </button>
                <button
                  onClick={() => setThread([])}
                  className="text-sm text-[#475569] hover:text-[#1a1a2e] border border-slate-200
                             hover:border-slate-300 px-3 py-2 rounded-lg transition-colors"
                >
                  Clear
                </button>
              </div>
            )}
          </div>

          {/* Thread */}
          <div className="flex-1 overflow-y-auto">
            {thread.length === 0 ? (
              <EmptyState lang={lang} onExample={(ex) => { setText(ex); textareaRef.current?.focus(); }} />
            ) : (
              <div className="max-w-3xl mx-auto px-5 py-6 flex flex-col gap-5">
                {thread.map((item) => (
                  <div key={item.id} className="flex flex-col gap-3">
                    {/* User bubble */}
                    <div className="flex justify-end">
                      <div className="max-w-xl bg-[#00a651] text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
                        <p className="text-base leading-relaxed">{item.input}</p>
                        <p className="text-xs text-white/60 mt-1 text-right">
                          {LANGUAGES.find(l => l.code === item.lang)?.flag} {item.lang.toUpperCase()}
                        </p>
                      </div>
                    </div>
                    {/* Result card */}
                    <div className="flex justify-start">
                      <div className="w-full max-w-2xl">
                        <ResultCard
                          result={item.result}
                          onExportData={(row) => {
                            setThread(prev => prev.map(t =>
                              t.id === item.id ? { ...t, exportRow: row } : t
                            ));
                            setExportRows(prev => {
                              const filtered = prev.filter(r => r.original_text !== row.original_text);
                              return [...filtered, row];
                            });
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm">
                      <div className="flex items-center gap-2 text-[#475569]">
                        <span className="inline-block w-4 h-4 border-2 border-[#00a651] border-t-transparent rounded-full animate-spin" />
                        <span className="text-sm">Analysing…</span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={threadEndRef} />
              </div>
            )}
          </div>

          {/* Fixed bottom input */}
          <div className="flex-shrink-0 bg-white border-t border-slate-200 px-5 py-4">
            <div className="max-w-3xl mx-auto">
              <div className={`rounded-2xl border-2 transition-colors bg-[#f5f5f0] ${
                noLang ? "border-slate-200 opacity-60" : "border-slate-300 focus-within:border-[#00a651]"
              }`}>
                {/* Textarea */}
                <div className="px-4 pt-3.5 pb-2">
                  <textarea
                    ref={textareaRef}
                    disabled={noLang || loading}
                    className="w-full text-base text-[#1a1a2e] resize-none outline-none bg-transparent
                               placeholder-[#94a3b8] leading-relaxed min-h-[28px] max-h-48
                               disabled:cursor-not-allowed"
                    rows={1}
                    placeholder={placeholder}
                    value={text}
                    onChange={e => {
                      setText(e.target.value);
                      e.target.style.height = "auto";
                      e.target.style.height = Math.min(e.target.scrollHeight, 192) + "px";
                    }}
                    onKeyDown={e => {
                      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleAnalyse();
                    }}
                  />
                </div>

                {/* Bottom toolbar */}
                <div className="flex items-center gap-1 px-3 pb-3">
                  {/* PDF */}
                  <button
                    onClick={() => !noLang && fileInputRef.current?.click()}
                    disabled={noLang}
                    title="Upload PDF"
                    className="flex items-center gap-1.5 text-sm text-[#64748b] hover:text-[#1a1a2e]
                               hover:bg-slate-200 px-2.5 py-1.5 rounded-lg transition-colors
                               disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path strokeLinecap="round" strokeLinejoin="round"
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <span className="text-xs font-medium">PDF</span>
                  </button>
                  <input ref={fileInputRef} type="file" accept="application/pdf" className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) handlePdfUpload(f); e.target.value = ""; }} />

                  {/* CSV */}
                  <button
                    onClick={() => !noLang && csvInputRef.current?.click()}
                    disabled={noLang}
                    title="Upload CSV"
                    className="flex items-center gap-1.5 text-sm text-[#64748b] hover:text-[#1a1a2e]
                               hover:bg-slate-200 px-2.5 py-1.5 rounded-lg transition-colors
                               disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path strokeLinecap="round" strokeLinejoin="round"
                        d="M3 10h18M3 14h18M10 3v18M14 3v18"/>
                      <rect x="3" y="3" width="18" height="18" rx="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    <span className="text-xs font-medium">CSV</span>
                  </button>
                  <input ref={csvInputRef} type="file" accept=".csv,text/csv" className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) handleCsvUpload(f); e.target.value = ""; }} />

                  {/* Voice */}
                  <button
                    onClick={handleVoice}
                    disabled={noLang}
                    title={listening ? "Stop recording" : "Voice input"}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-all
                               disabled:opacity-30 disabled:cursor-not-allowed ${
                      listening
                        ? "bg-red-100 text-red-500 animate-pulse"
                        : "text-[#64748b] hover:text-[#1a1a2e] hover:bg-slate-200"
                    }`}
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path strokeLinecap="round" strokeLinejoin="round"
                        d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
                      <path strokeLinecap="round" strokeLinejoin="round"
                        d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"/>
                    </svg>
                    <span className="text-xs font-medium">{listening ? "Stop" : "Voice"}</span>
                  </button>

                  {/* File label */}
                  {pdfName && (
                    <span className="text-xs text-[#00a651] bg-emerald-50 px-2 py-1 rounded-md font-medium truncate max-w-32">
                      {pdfName}
                    </span>
                  )}

                  {/* Analyse button — right aligned */}
                  <div className="ml-auto flex items-center gap-2">
                    {reviewedCount > 0 && (
                      <span className="text-xs text-[#64748b]">{reviewedCount} reviewed</span>
                    )}
                    <button
                      onClick={handleAnalyse}
                      disabled={loading || !text.trim() || noLang}
                      className="bg-[#00a651] hover:bg-[#008f45] active:bg-[#007a3a]
                                 text-white font-semibold text-sm px-5 py-2 rounded-xl transition-colors
                                 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {loading ? (
                        <>
                          <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          Analysing…
                        </>
                      ) : (
                        <>
                          Analyse
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7"/>
                          </svg>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {error && (
                <p className="mt-2 text-sm text-red-600 px-1">{error}</p>
              )}
              <p className="mt-2 text-xs text-[#94a3b8] text-center">
                {noLang
                  ? "Select a language from the sidebar to begin"
                  : "Type, paste, or upload · single sentence or full paragraph · Cmd+Enter to analyse"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
