"use client";
import { useState } from "react";
import type { AnalyseResponse } from "../lib/api";

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
    <div className="animate-pulse flex flex-col gap-1.5 py-3 border-b border-slate-100 last:border-0">
      <div className="h-3.5 bg-slate-200 rounded w-3/4" />
      <div className="h-3 bg-slate-100 rounded w-1/2" />
    </div>
  );
}

function SentenceRow({ sentence, result }: { sentence: string; result: AnalyseResponse | null }) {
  const [expanded, setExpanded] = useState(false);

  if (!result) return <SentenceSkeleton />;

  const biased = result.has_bias_detected;
  const changed = result.rewrite && result.rewrite !== result.original_text;

  return (
    <div className="py-3 border-b border-slate-100 last:border-0">
      <div className="flex items-start gap-2.5">
        <span className={`flex-shrink-0 mt-1 w-2 h-2 rounded-full ${biased ? "bg-red-400" : "bg-emerald-400"}`} />
        <div className="flex-1 min-w-0">
          {/* Original — strikethrough if corrected */}
          <p className={`text-sm leading-relaxed ${biased && changed ? "line-through text-slate-400" : "text-[#1a1a2e]"}`}>
            {sentence}
          </p>
          {/* Correction */}
          {biased && changed && (
            <p className="text-sm leading-relaxed text-[#1a1a2e] mt-1 font-medium">
              {result.rewrite}
            </p>
          )}
          {/* Reason — expandable */}
          {biased && result.reason && (
            <button
              onClick={() => setExpanded(e => !e)}
              className="text-xs text-[#00a651] hover:text-[#009040] mt-1 transition-colors"
            >
              {expanded ? "Hide reason ↑" : "Why? ↓"}
            </button>
          )}
          {expanded && result.reason && (
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">{result.reason}</p>
          )}
        </div>
        {/* Needs review badge */}
        {result.needs_review && (
          <span className="flex-shrink-0 text-xs bg-amber-50 text-amber-600 border border-amber-200 rounded-full px-2 py-0.5">
            Review
          </span>
        )}
      </div>
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

      {/* Sentence list */}
      <div className="px-4">
        {sentences.map((s, i) => (
          <SentenceRow key={i} sentence={s.text} result={s.result} />
        ))}
        {/* Skeleton rows for pending sentences */}
        {pending > 0 && Array.from({ length: pending }).map((_, i) => (
          <SentenceSkeleton key={`pending-${i}`} />
        ))}
      </div>
    </div>
  );
}
