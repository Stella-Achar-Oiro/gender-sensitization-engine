"use client";
import { useState, useEffect } from "react";
import type { LanguageMetrics } from "../lib/api";
import { loadHistory, deleteFromHistory, clearHistory } from "../lib/history";
import type { HistoryEntry } from "../lib/history";

const _ALL_LANGUAGES = [
  { code: "sw", label: "Swahili", flag: "🇹🇿", threshold: 0.85 },
  { code: "ha", label: "Hausa",   flag: "🇳🇬", threshold: 0.70 },
  { code: "zu", label: "Zulu",    flag: "🇿🇦", threshold: 0.68 },
  // hidden for demo — re-enable by adding codes below
  { code: "en", label: "English", flag: "🇬🇧", threshold: 0.70 },
  { code: "fr", label: "French",  flag: "🇫🇷", threshold: 0.75 },
  { code: "ki", label: "Gikuyu",  flag: "🇰🇪", threshold: 0.70 },
];

const DEMO_LANGS = ["sw", "ha", "zu"];

export const LANGUAGES = _ALL_LANGUAGES.filter(l => DEMO_LANGS.includes(l.code));

export const EXAMPLES: Record<string, string[]> = {
  en: [
    "The chairman will lead the board meeting.",
    "Every nurse should know her patients well.",
    "The fireman saved the building in time.",
  ],
  sw: [
    "Daktari wa kiume alifika hospitalini.",
    "Wanawake hawafai kuongoza makampuni.",
    "Mwalimu alitoa somo zuri leo asubuhi.",
  ],
  fr: [
    "Le président a dirigé la réunion.",
    "Les femmes sont trop émotionnelles pour ce rôle.",
    "La directrice a présenté le rapport annuel.",
  ],
  ki: [
    "Mũndũ wa mũrũme nĩwe ũngĩ gũtwara mũciĩ.",
    "Mwarimu aarĩ na ũhoti mũnene.",
  ],
  ha: [
    "Likitan namiji ne kawai zai iya jagorantar asibiti.",
    "Mata suna yin aiki a gida kawai, ba a ofis ba.",
  ],
  zu: [
    "Udokotela wesilisa weza esibhedlela ekuseni.",
    "Abesifazane abanakho ukuba abaholi.",
  ],
};

function f1Color(f1: number, threshold: number) {
  if (f1 >= threshold)         return { dot: "bg-emerald-400", text: "text-emerald-400" };
  if (f1 >= threshold - 0.10)  return { dot: "bg-amber-400",   text: "text-amber-400"   };
  return                              { dot: "bg-red-400",     text: "text-red-400"     };
}

interface Props {
  activeLang: string;
  onLangChange: (code: string) => void;
  onHistoryClick: (entry: HistoryEntry) => void;
  metrics: Record<string, LanguageMetrics>;
  historyVersion: number;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  onShowMetrics?: () => void;
}

function relativeTime(ts: number): string {
  const diff = Date.now() - ts;
  const m = Math.floor(diff / 60000);
  const h = Math.floor(diff / 3600000);
  const d = Math.floor(diff / 86400000);
  if (m < 1)  return "now";
  if (m < 60) return `${m}m`;
  if (h < 24) return `${h}h`;
  return `${d}d`;
}

export default function Sidebar({
  activeLang, onLangChange, onHistoryClick, metrics, historyVersion,
  collapsed = false, onToggleCollapse, onShowMetrics,
}: Props) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => { setHistory(loadHistory()); }, [historyVersion]);

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setHistory(deleteFromHistory(id));
  };

  /* ── Collapsed (icon-rail) mode ── */
  if (collapsed) {
    return (
      <aside
        style={{ width: "64px", minWidth: "64px" }}
        className="h-screen bg-[#0f172a] flex flex-col flex-shrink-0 overflow-hidden border-r border-white/[0.06]"
      >
        <div className="flex items-center justify-center py-5 border-b border-white/[0.07]">
          <div className="w-8 h-8 rounded-lg bg-[#00a651] flex items-center justify-center">
            <span className="text-white font-bold text-base leading-none">J</span>
          </div>
        </div>

        <button
          onClick={onToggleCollapse}
          title="Expand sidebar"
          className="flex items-center justify-center py-3 text-white/30 hover:text-white/60 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 18l6-6-6-6"/>
          </svg>
        </button>

        <div className="flex flex-col items-center gap-1 px-2 pt-1">
          {LANGUAGES.map((l) => {
            const m = metrics[l.code];
            const isActive = l.code === activeLang;
            const color = m ? f1Color(m.f1, l.threshold) : { dot: "bg-white/20", text: "" };
            return (
              <button
                key={l.code}
                onClick={() => onLangChange(l.code)}
                title={`${l.label}${m ? ` · F1 ${m.f1.toFixed(2)}` : ""}`}
                className={`w-10 h-10 rounded-xl flex flex-col items-center justify-center gap-0.5 transition-all ${
                  isActive ? "bg-white/10" : "hover:bg-white/[0.06]"
                }`}
              >
                <span className="text-base leading-none">{l.flag}</span>
                <span className={`w-1.5 h-1.5 rounded-full ${color.dot}`} />
              </button>
            );
          })}
        </div>
      </aside>
    );
  }

  /* ── Expanded mode ── */
  return (
    <aside
      style={{ width: "var(--sw)", minWidth: "var(--sw)" }}
      className="h-screen bg-[#0f172a] flex flex-col flex-shrink-0 overflow-hidden"
    >
      {/* Logo + collapse toggle */}
      <div className="px-5 py-5 border-b border-white/[0.07] flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[#00a651] flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-base leading-none">J</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-bold text-white text-base tracking-tight">JuaKazi</div>
          <div className="text-white/40 text-xs mt-0.5">Gender Bias Detection & Correction</div>
        </div>
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            title="Collapse sidebar"
            className="text-white/25 hover:text-white/60 transition-colors flex-shrink-0"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 18l-6-6 6-6"/>
            </svg>
          </button>
        )}
      </div>

      {/* Languages */}
      <div className="px-3 pt-4 pb-2">
        <div className="text-xs font-semibold uppercase tracking-widest text-white/30 px-2 mb-2">
          Languages
        </div>
        <div className="flex flex-col gap-0.5">
          {LANGUAGES.map((l) => {
            const m = metrics[l.code];
            const isActive = l.code === activeLang;
            const color = m ? f1Color(m.f1, l.threshold) : { dot: "bg-white/20", text: "text-white/25" };
            return (
              <button
                key={l.code}
                onClick={() => onLangChange(l.code)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-left w-full transition-all duration-150 ${
                  isActive ? "bg-[#00a651]/20 text-white" : "text-white/60 hover:text-white hover:bg-white/[0.06]"
                }`}
              >
                <span className="text-xl leading-none">{l.flag}</span>
                <span className="flex-1 text-sm font-medium">{l.label}</span>
                {m && (
                  <span className={`text-xs font-mono tabular-nums ${isActive ? color.text : "text-white/30"}`}>
                    {m.f1.toFixed(2)}
                  </span>
                )}
                {/* Threshold status dot */}
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  m ? color.dot : (isActive ? "bg-[#00a651]" : "bg-white/10")
                }`} />
              </button>
            );
          })}
        </div>
      </div>

      {/* Model info */}
      <div className="px-5 py-3 mx-3 mt-2 rounded-lg bg-white/[0.04] border border-white/[0.06]">
        <div className="text-xs font-semibold text-white/30 uppercase tracking-widest mb-2">Model</div>
        <div className="flex justify-between text-xs mb-1">
          <span className="text-white/40">Detector</span>
          <span className="text-white/70 font-mono">afro-xlmr</span>
        </div>
        <div className="flex justify-between text-xs mb-2">
          <span className="text-white/40">Corrector</span>
          <span className="text-white/70 font-mono">afriteva-v2</span>
        </div>
      </div>

      {/* Recent history */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden mt-4">
        <div className="flex items-center justify-between px-5 mb-2">
          <span className="text-xs font-semibold uppercase tracking-widest text-white/30">Recent</span>
          {history.length > 0 && (
            <button
              onClick={() => { clearHistory(); setHistory([]); }}
              className="text-xs text-white/25 hover:text-white/50 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
        <div className="flex-1 overflow-y-auto px-3 pb-4">
          {history.length === 0 ? (
            <p className="text-xs text-white/20 px-2 py-3 text-center leading-relaxed">
              Analysed sentences<br />will appear here
            </p>
          ) : (
            <div className="flex flex-col gap-px">
              {history.map((entry) => {
                const entryLang = LANGUAGES.find((l) => l.code === entry.lang);
                const biased = entry.result.has_bias_detected;
                return (
                  <button
                    key={entry.id}
                    onClick={() => onHistoryClick(entry)}
                    className="group flex items-start gap-2.5 px-3 py-2.5 rounded-lg text-left
                               hover:bg-white/[0.05] transition-all duration-150"
                  >
                    <span className={`flex-shrink-0 mt-1.5 w-2 h-2 rounded-full ${biased ? "bg-red-400" : "bg-emerald-400"}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/65 group-hover:text-white/90 truncate leading-snug transition-colors">
                        {entry.text.length > 38 ? entry.text.slice(0, 38) + "…" : entry.text}
                      </p>
                      <p className="text-xs text-white/30 mt-0.5">
                        {entryLang?.flag} {relativeTime(entry.ts)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDelete(entry.id, e)}
                      className="flex-shrink-0 opacity-0 group-hover:opacity-100 text-white/25
                                 hover:text-white/60 transition-all p-0.5 rounded mt-0.5"
                    >
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none"
                           stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                        <path d="M18 6L6 18M6 6l12 12"/>
                      </svg>
                    </button>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
