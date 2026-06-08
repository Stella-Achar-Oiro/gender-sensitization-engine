"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import type { LanguageMetrics } from "../lib/api";
import { loadHistory, deleteFromHistory, clearHistory } from "../lib/history";
import type { HistoryEntry } from "../lib/history";

export const LANGUAGES = [
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "sw", label: "Swahili", flag: "🇹🇿" },
  { code: "fr", label: "French",  flag: "🇫🇷" },
  { code: "ki", label: "Gikuyu",  flag: "🇰🇪" },
  { code: "ha", label: "Hausa",   flag: "🇳🇬" },
  { code: "zu", label: "Zulu",    flag: "🇿🇦" },
];

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

interface Props {
  activeLang: string;
  onLangChange: (code: string) => void;
  onHistoryClick: (entry: HistoryEntry) => void;
  metrics: Record<string, LanguageMetrics>;
  historyVersion: number;
}

function relativeTime(ts: number): string {
  const diff = Date.now() - ts;
  const m = Math.floor(diff / 60000);
  const h = Math.floor(diff / 3600000);
  const d = Math.floor(diff / 86400000);
  if (m < 1)  return "just now";
  if (m < 60) return `${m}m ago`;
  if (h < 24) return `${h}h ago`;
  return `${d}d ago`;
}

export default function Sidebar({ activeLang, onLangChange, onHistoryClick, metrics, historyVersion }: Props) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    setHistory(loadHistory());
  }, [historyVersion]);

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setHistory(deleteFromHistory(id));
  };

  return (
    <aside
      style={{ width: "var(--sw)", minWidth: "var(--sw)" }}
      className="h-screen bg-[#0f172a] flex flex-col flex-shrink-0 overflow-hidden"
    >
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/[0.07]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#00a651] flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-base leading-none">J</span>
          </div>
          <div>
            <div className="font-bold text-white text-base tracking-tight">JuaKazi</div>
            <div className="text-white/40 text-xs mt-0.5">Gender Bias Engine</div>
          </div>
        </div>
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
            return (
              <button
                key={l.code}
                onClick={() => onLangChange(l.code)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-left w-full transition-all duration-150 ${
                  isActive
                    ? "bg-[#00a651]/20 text-white"
                    : "text-white/60 hover:text-white hover:bg-white/[0.06]"
                }`}
              >
                <span className="text-xl leading-none">{l.flag}</span>
                <span className="flex-1 text-sm font-medium">{l.label}</span>
                {m && (
                  <span className={`text-xs font-mono tabular-nums ${isActive ? "text-[#00a651]" : "text-white/25"}`}>
                    {m.f1.toFixed(2)}
                  </span>
                )}
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#00a651] flex-shrink-0" />
                )}
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
        <Link
          href="/languages"
          className="block text-center text-xs text-[#00a651] hover:text-[#00c060] font-medium transition-colors mt-1"
        >
          All metrics →
        </Link>
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
                    <span className={`flex-shrink-0 mt-1.5 w-2 h-2 rounded-full ${
                      biased ? "bg-red-400" : "bg-emerald-400"
                    }`} />
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
