import type { LanguageMetrics } from "../lib/api";

export const LANGUAGES = [
  { code: "en", label: "English",  flag: "🇬🇧" },
  { code: "sw", label: "Swahili",  flag: "🇹🇿" },
  { code: "fr", label: "French",   flag: "🇫🇷" },
  { code: "ki", label: "Gikuyu",   flag: "🇰🇪" },
  { code: "ha", label: "Hausa",    flag: "🇳🇬" },
  { code: "zu", label: "Zulu",     flag: "🇿🇦" },
];

export const EXAMPLES: Record<string, string[]> = {
  en: ["The chairman will lead the board meeting.", "The nurse said she would help."],
  sw: ["Daktari wa kiume alifika hospitalini.", "Mwalimu alitoa somo zuri leo asubuhi."],
  fr: ["Le président a dirigé la réunion.", "La directrice a présenté le rapport annuel."],
  ki: ["Mũndũ wa mũrũme nĩwe ũngĩ gũtwara mũciĩ.", "Mwarimu aarĩ na ũhoti mũnene."],
  ha: ["Likitan namiji ne kawai zai iya jagorantar asibiti.", "Gwamnati ta ba da sanarwa a yau."],
  zu: ["Udokotela wesilisa weza esibhedlela ekuseni.", "Imvula yaqala ukuna ekuseni."],
};

interface Props {
  activeLang: string;
  onLangChange: (code: string) => void;
  onExampleClick: (text: string) => void;
  metrics: Record<string, LanguageMetrics>;
}

export default function Sidebar({ activeLang, onLangChange, onExampleClick, metrics }: Props) {
  return (
    <aside
      style={{ width: "var(--sw)", minWidth: "var(--sw)" }}
      className="h-screen bg-sidebar flex flex-col flex-shrink-0 overflow-hidden"
    >
      {/* Logo */}
      <div className="px-4 py-5 border-b border-white/[0.06]">
        <div className="font-bold text-white text-sm tracking-tight">JuaKazi</div>
        <div className="text-white/40 text-[11px] mt-0.5">Gender Bias Engine</div>
      </div>

      {/* Language list */}
      <div className="px-2.5 pt-4 pb-2">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-white/25 px-2 mb-1.5">
          Languages
        </div>
        {LANGUAGES.map((lang) => {
          const m = metrics[lang.code];
          const isActive = lang.code === activeLang;
          return (
            <button
              key={lang.code}
              onClick={() => onLangChange(lang.code)}
              className={`flex items-center gap-2.5 w-full px-2.5 py-2 rounded-md text-left text-[13px] font-medium transition-all duration-150
                ${isActive
                  ? "bg-sidebar-active text-[#00a651] font-semibold"
                  : "text-white/55 hover:bg-[#1f2937] hover:text-white/85"
                }`}
              style={isActive ? { background: "rgba(0,166,81,.15)" } : {}}
            >
              <span className="text-base leading-none">{lang.flag}</span>
              <span className="flex-1">{lang.label}</span>
              {m && (
                <span className="text-[10px] opacity-50 ml-auto">
                  F1 {m.f1.toFixed(2)}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Examples */}
      <div className="flex-1 flex flex-col min-h-0 px-2.5 pb-2 mt-2">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-white/25 px-2 mb-1.5">
          Examples
        </div>
        <div className="flex-1 overflow-y-auto flex flex-col gap-px">
          {(EXAMPLES[activeLang] ?? []).map((ex, i) => (
            <button
              key={i}
              onClick={() => onExampleClick(ex)}
              className="flex items-start gap-2 px-2.5 py-1.5 rounded text-white/40 text-[12px] text-left hover:bg-[#1f2937] hover:text-white/75 transition-all duration-150 leading-snug"
            >
              <svg className="flex-shrink-0 mt-0.5 opacity-50" width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
                <circle cx="5" cy="5" r="2" />
              </svg>
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Bottom stats */}
      <div className="border-t border-white/[0.06] px-4 py-3 text-[11px] text-white/30">
        <div className="flex justify-between">
          <span>Languages</span>
          <span className="text-white/50">6</span>
        </div>
        <div className="flex justify-between mt-1">
          <span>Models</span>
          <span className="text-white/50">afro-xlmr</span>
        </div>
      </div>
    </aside>
  );
}
