import type { LanguageMetrics } from "../lib/api";

interface Props {
  lang: string;
  metrics: LanguageMetrics | undefined;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-center bg-white border border-slate-200 rounded-lg px-4 py-2.5 min-w-[80px]">
      <span className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-1">
        {label}
      </span>
      <span className="text-base font-bold text-slate-800">{value}</span>
    </div>
  );
}

export default function MetricsBar({ lang, metrics }: Props) {
  if (!metrics) return null;

  const tier =
    metrics.f1 >= 0.85 ? "Gold" :
    metrics.f1 >= 0.70 ? "Silver" :
    metrics.f1 >= 0.50 ? "Bronze" : "Pre-Bronze";

  const tierColor =
    tier === "Gold"   ? "text-yellow-600 bg-yellow-50 border-yellow-200" :
    tier === "Silver" ? "text-slate-600  bg-slate-50  border-slate-200"  :
    tier === "Bronze" ? "text-orange-600 bg-orange-50 border-orange-200" :
                        "text-red-600    bg-red-50     border-red-200";

  return (
    <div className="flex items-center gap-2 mt-3 flex-wrap">
      <Stat label="F1"        value={metrics.f1.toFixed(3)} />
      <Stat label="Precision" value={metrics.precision.toFixed(3)} />
      <Stat label="Recall"    value={metrics.recall.toFixed(3)} />
      <Stat label="Samples"   value={metrics.samples.toLocaleString()} />
      <div className={`flex flex-col items-center border rounded-lg px-4 py-2.5 min-w-[80px] ${tierColor}`}>
        <span className="text-[10px] font-semibold uppercase tracking-widest mb-1">Tier</span>
        <span className="text-base font-bold">{tier}</span>
      </div>
    </div>
  );
}
