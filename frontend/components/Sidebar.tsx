"use client";
import { useState, useEffect } from "react";
import type { LanguageMetrics } from "../lib/api";
import type { AnalyseResponse } from "../lib/api";
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
    "Mwalimu alitoa somo zuri leo asubuhi.",
    "Wanawake hawafai kuongoza makampuni.",
  ],
  fr: [
    "Le président a dirigé la réunion.",
    "La directrice a présenté le rapport annuel.",
    "Les femmes sont trop émotionnelles pour ce rôle.",
  ],
  ki: [
    "Mũndũ wa mũrũme nĩwe ũngĩ gũtwara mũciĩ.",
    "Mwarimu aarĩ na ũhoti mũnene.",
  ],
  ha: [
    "Likitan namiji ne kawai zai iya jagorantar asibiti.",
    "Gwamnati ta ba da sanarwa a yau.",
  ],
  zu: [
    "Udokotela wesilisa weza esibhedlela ekuseni.",
    "Imvula yaqala ukuna ekuseni.",
  ],
};

interface Props {
  activeLang: string;
  onLangChange: (code: string) => void;
  onHistoryClick: (entry: HistoryEntry) => void;
  onMetricsClick: () => void;
  metrics: Record<string, LanguageMetrics>;
  historyVersion: number;
  metricsOpen: boolean;
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

export default function Sidebar({
  activeLang, onHistoryClick, onMetricsClick, metrics, historyVersion, metricsOpen,
}: Props) {
  const topLang = LANGUAGES.find((l) => l.code === activeLang);
  const m = metrics[activeLang];

  const [history, setHistory] = useState<HistoryEntry[]>([]);

  // Load history on mount and whenever historyVersion changes
  useEffect(() => {
    setHistory(loadHistory());
  }, [historyVersion]);

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setHistory(deleteFromHistory(id));
  };

  const handleClear = () => {
    clearHistory();
    setHistory([]);
  };

  return (
    <aside
      style={{ width: "var(--sw)", minWidth: "var(--sw)" }}
      className="h-screen bg-sidebar flex flex-col flex-shrink-0 overflow-hidden"
    >
      {/* Logo */}
      <div className="px-4 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#00a651] flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm leading-none">J</span>
          </div>
          <div>
            <div className="font-bold text-white text-sm tracking-tight">JuaKazi</div>
            <div className="text-white/35 text-[10px]">Gender Bias Engine</div>
          </div>
        </div>
      </div>

      {/* Current language metrics */}
      {m && topLang && (
        <div className="px-4 py-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-base leading-none">{topLang.flag}</span>
            <span className="text-white/70 text-xs font-semibold">{topLang.label}</span>
          </div>
          <div className="grid grid-cols-3 gap-1.5">
            {([["F1", m.f1], ["Prec.", m.precision], ["Rec.", m.recall]] as [string, number][]).map(([label, val]) => (
              <div key={label} className="bg-white/[0.05] rounded-lg px-2 py-1.5 text-center">
                <div className="text-[9px] text-white/30 uppercase tracking-wider">{label}</div>
                <div className="text-white/80 text-xs font-bold mt-0.5">{val.toFixed(2)}</div>
              </div>
            ))}
          </div>
          <button
            onClick={onMetricsClick}
            className={`mt-2 w-full text-center text-[11px] font-medium transition-colors rounded-md py-1 ${
              metricsOpen
                ? "text-white/70 bg-white/[0.07]"
                : "text-[#00a651] hover:text-[#00c060]"
            }`}
          >
            {metricsOpen ? "← Back to analysis" : "All metrics →"}
          </button>
        </div>
      )}

      {/* Recent sessions */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="flex items-center justify-between px-4 pt-3 pb-1.5">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-white/25">
            Recent
          </span>
          {history.length > 0 && (
            <button onClick={handleClear} className="text-[10px] text-white/20 hover:text-white/50 transition-colors">
              Clear
            </button>
          )}
        </div>
        <div className="flex-1 overflow-y-auto px-2.5 pb-2">
          {history.length === 0 ? (
            <p className="text-[11px] text-white/20 px-2 py-4 text-center leading-relaxed">
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
                    className="group flex items-start gap-2 px-2.5 py-2 rounded-lg text-left
                               hover:bg-white/[0.06] transition-all duration-150"
                  >
                    <span className={`flex-shrink-0 mt-1 w-1.5 h-1.5 rounded-full ${
                      biased ? "bg-red-400" : "bg-emerald-400"
                    }`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] text-white/60 group-hover:text-white/85 truncate leading-snug transition-colors">
                        {entry.text.length > 42 ? entry.text.slice(0, 42) + "…" : entry.text}
                      </p>
                      <p className="text-[10px] text-white/25 mt-0.5">
                        {entryLang?.flag} {relativeTime(entry.ts)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDelete(entry.id, e)}
                      className="flex-shrink-0 opacity-0 group-hover:opacity-100 text-white/30
                                 hover:text-white/70 transition-all p-0.5 rounded mt-0.5"
                      title="Remove"
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

      {/* Bottom */}
      <div className="border-t border-white/[0.06] px-4 py-3 text-[10px] text-white/25 space-y-0.5">
        <div className="flex justify-between">
          <span>Languages</span><span className="text-white/40">6</span>
        </div>
        <div className="flex justify-between">
          <span>Bias detector model</span><span className="text-white/40">afro-xlmr</span>
        </div>
        <div className="flex justify-between">
          <span>Bias corrector model</span><span className="text-white/40">afriteva-v2</span>
        </div>
        {/* Always-visible metrics button when no language is selected */}
        {!m && (
          <button
            onClick={onMetricsClick}
            className={`mt-2 w-full text-center text-[11px] font-medium transition-colors rounded-md py-1 ${
              metricsOpen
                ? "text-white/70 bg-white/[0.07]"
                : "text-[#00a651] hover:text-[#00c060]"
            }`}
          >
            {metricsOpen ? "← Back to analysis" : "All metrics →"}
          </button>
        )}
      </div>
    </aside>
  );
}
