"use client";
import type { AnalyseResponse } from "../lib/api";

interface Props {
  results: AnalyseResponse[];
  loading: boolean;
}

export default function BatchView({ results, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2 mt-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-10 bg-slate-100 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (!results.length) return null;

  const biasedCount = results.filter((r) => r.has_bias_detected).length;

  return (
    <div className="mt-4">
      {/* Summary bar */}
      <div className="mb-3 flex items-center gap-3 text-xs text-muted">
        <span className="font-semibold text-slate-700">{results.length} sentences</span>
        <span className="text-slate-300">·</span>
        {biasedCount > 0 ? (
          <span className="font-semibold text-red-600">{biasedCount} biased</span>
        ) : (
          <span className="font-semibold text-emerald-600">No bias found</span>
        )}
        <span className="text-slate-300">·</span>
        <span>{results.length - biasedCount} clean</span>
      </div>

      {/* Sentence rows */}
      <div className="flex flex-col gap-2">
        {results.map((r, i) => (
          <SentenceRow key={i} result={r} index={i} />
        ))}
      </div>
    </div>
  );
}

function SentenceRow({ result, index }: { result: AnalyseResponse; index: number }) {
  const biased = result.has_bias_detected;
  const corrected = result.rewrite !== result.original_text;

  return (
    <div
      className={`rounded-lg border px-4 py-3 text-sm ${
        biased
          ? "border-red-200 bg-red-50"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Index */}
        <span className="text-[10px] font-mono text-muted mt-0.5 flex-shrink-0 w-4">
          {index + 1}
        </span>

        <div className="flex-1 min-w-0">
          {/* Original with inline highlights */}
          <p className="leading-relaxed text-slate-700">
            {renderHighlighted(result.original_text, result.edits)}
          </p>

          {/* Correction */}
          {corrected && (
            <div className="mt-1.5 flex items-start gap-1.5">
              <span className="text-[10px] text-emerald-600 mt-0.5 flex-shrink-0">→</span>
              <p className="text-emerald-800 font-medium leading-relaxed">
                {result.rewrite}
              </p>
            </div>
          )}

          {/* Reason tag */}
          {biased && result.edits.length > 0 && (
            <div className="mt-1.5 flex flex-wrap gap-1">
              {result.edits.filter((e) => e.severity === "replace").map((e, j) => (
                <span
                  key={j}
                  className="inline-flex items-center gap-1 text-[10px] bg-red-100
                             text-red-700 border border-red-200 rounded px-1.5 py-0.5"
                >
                  <span className="font-mono line-through">{e.from}</span>
                  {e.to && <><span className="opacity-50">→</span><span className="font-mono">{e.to}</span></>}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Status dot */}
        <span
          className={`flex-shrink-0 mt-1 w-2 h-2 rounded-full ${
            biased ? "bg-red-400" : "bg-emerald-400"
          }`}
        />
      </div>
    </div>
  );
}

function renderHighlighted(text: string, edits: AnalyseResponse["edits"]) {
  const replaceEdits = edits.filter((e) => e.severity === "replace");
  if (!replaceEdits.length) return <>{text}</>;

  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  for (const edit of replaceEdits) {
    const idx = remaining.toLowerCase().indexOf(edit.from.toLowerCase());
    if (idx === -1) continue;
    if (idx > 0) parts.push(<span key={key++}>{remaining.slice(0, idx)}</span>);
    parts.push(
      <mark key={key++} className="bg-red-100 text-red-700 rounded px-0.5 not-italic">
        {remaining.slice(idx, idx + edit.from.length)}
      </mark>
    );
    remaining = remaining.slice(idx + edit.from.length);
  }
  if (remaining) parts.push(<span key={key++}>{remaining}</span>);
  return <>{parts}</>;
}
