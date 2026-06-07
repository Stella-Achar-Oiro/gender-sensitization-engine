import Link from "next/link";
import type { LanguageMetrics } from "../lib/api";

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
  onExampleClick: (text: string) => void;
  metrics: Record<string, LanguageMetrics>;
}

export default function Sidebar({ activeLang, onExampleClick, metrics }: Props) {
  const topLang = LANGUAGES.find((l) => l.code === activeLang);
  const m = metrics[activeLang];

  return (
    <aside
      style={{ width: "var(--sw)", minWidth: "var(--sw)" }}
      className="h-screen bg-sidebar flex flex-col flex-shrink-0 overflow-hidden"
    >
      {/* Logo */}
      <div className="px-4 py-5 border-b border-white/[0.06]">
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
            {[["F1", m.f1], ["Prec.", m.precision], ["Rec.", m.recall]].map(([label, val]) => (
              <div key={label as string} className="bg-white/[0.05] rounded-lg px-2 py-1.5 text-center">
                <div className="text-[9px] text-white/30 uppercase tracking-wider">{label}</div>
                <div className="text-white/80 text-xs font-bold mt-0.5">
                  {(val as number).toFixed(2)}
                </div>
              </div>
            ))}
          </div>
          <Link
            href="/languages"
            className="mt-2 block text-center text-[11px] text-[#00a651] hover:underline"
          >
            All languages →
          </Link>
        </div>
      )}

      {/* Examples */}
      <div className="flex-1 flex flex-col min-h-0 px-2.5 py-3 overflow-hidden">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-white/25 px-2 mb-1.5">
          Examples
        </div>
        <div className="flex-1 overflow-y-auto flex flex-col gap-px">
          {(EXAMPLES[activeLang] ?? []).map((ex, i) => (
            <button
              key={i}
              onClick={() => onExampleClick(ex)}
              className="flex items-start gap-2 px-2.5 py-2 rounded-lg text-white/45 text-[11px]
                         text-left hover:bg-white/[0.06] hover:text-white/80 transition-all duration-150
                         leading-snug"
            >
              <span className="flex-shrink-0 mt-0.5 opacity-40 text-[10px]">›</span>
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Bottom */}
      <div className="border-t border-white/[0.06] px-4 py-3 text-[10px] text-white/25 space-y-0.5">
        <div className="flex justify-between">
          <span>Languages</span><span className="text-white/40">6</span>
        </div>
        <div className="flex justify-between">
          <span>Model</span><span className="text-white/40">afro-xlmr</span>
        </div>
        <div className="flex justify-between">
          <span>Corrector</span><span className="text-white/40">afriteva-v2</span>
        </div>
      </div>
    </aside>
  );
}
