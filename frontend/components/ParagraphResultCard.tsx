"use client";
import type { AnalyseResponse } from "../lib/api";
import ResultCard from "./ResultCard";

interface SentenceResult {
  text: string;
  result: AnalyseResponse | null; // null = still loading
}

interface Props {
  sentences: SentenceResult[];
  total: number;
}

function SentenceSkeleton() {
  return (
    <div className="animate-pulse flex flex-col gap-1.5 py-3 px-4 border-b border-slate-100 last:border-0">
      <div className="h-3.5 bg-slate-200 rounded w-3/4" />
      <div className="h-3 bg-slate-100 rounded w-1/2" />
    </div>
  );
}

export default function ParagraphResultCard({ sentences, total }: Props) {
  const done    = sentences.filter(s => s.result !== null).length;
  const biased  = sentences.filter(s => s.result?.has_bias_detected).length;
  const pending = total - done;
  const allDone = done === total;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
            !allDone ? "bg-amber-400 animate-pulse" :
            biased > 0 ? "bg-red-400" : "bg-emerald-400"
          }`} />
          <span className="text-sm font-semibold text-[#1a1a2e]">
            {!allDone
              ? `Analysing… ${done}/${total} sentences`
              : biased > 0
                ? `${biased} of ${total} sentence${total > 1 ? "s" : ""} had bias`
                : `${total} sentence${total > 1 ? "s" : ""} — no bias detected`
            }
          </span>
        </div>
        {allDone && (
          <span className="text-xs text-slate-400 font-mono">
            {Math.round((biased / total) * 100)}% bias rate
          </span>
        )}
      </div>

      {/* Sentence list — each uses the same ResultCard as single-sentence mode */}
      <div className="flex flex-col gap-3 p-4">
        {sentences.map((s, i) => (
          s.result
            ? <ResultCard key={i} result={s.result} />
            : <SentenceSkeleton key={i} />
        ))}
        {pending > 0 && Array.from({ length: pending }).map((_, i) => (
          <SentenceSkeleton key={`pending-${i}`} />
        ))}
      </div>
    </div>
  );
}
