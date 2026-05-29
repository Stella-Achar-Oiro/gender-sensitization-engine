"use client";
import { useState } from "react";
import type { AnalyseResponse } from "../lib/api";

interface Props {
  result: AnalyseResponse;
}

export default function DiffView({ result }: Props) {
  const { original_text, rewrite, edits, has_bias_detected, aibridge_detected, reason } = result;
  const hasRealEdits = edits.some((e) => e.severity === "replace" || e.severity === "warn");
  const biasDetected = has_bias_detected || (aibridge_detected && hasRealEdits);
  const corrected = rewrite !== original_text;
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(
      `[BIAS FLAGGED FOR REVIEW]\n\nOriginal: ${original_text}\n\nReason: ${reason ?? "Gender bias detected — automatic correction unavailable"}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // No bias, no correction needed
  if (!biasDetected && !corrected) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white px-4 py-3.5 text-sm text-muted">
        No correction needed.
      </div>
    );
  }

  // Bias detected but correction not available
  if (biasDetected && !corrected) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-amber-800">
              Automatic correction unavailable
            </p>
            <p className="mt-1 text-xs text-amber-700 leading-relaxed">
              {reason
                ? reason.replace("Bias detected by external classifier but correction suppressed — ", "")
                : "The bias pattern was identified but could not be automatically rewritten without changing the meaning."}
            </p>
            <p className="mt-2 text-xs text-amber-600 font-medium">
              → Send to a human reviewer or rewrite manually.
            </p>
          </div>
          <button
            onClick={handleCopy}
            className="flex-shrink-0 text-xs bg-amber-100 hover:bg-amber-200 text-amber-800
                       border border-amber-300 rounded-md px-3 py-1.5 font-medium transition-colors"
          >
            {copied ? "Copied ✓" : "Copy for review"}
          </button>
        </div>

        {/* Show original highlighted */}
        <div className="mt-3 bg-white rounded border border-amber-100 px-3 py-2">
          <div className="text-[10px] font-semibold uppercase tracking-widest text-amber-600 mb-1">
            Original (needs review)
          </div>
          <p className="text-sm text-slate-700 leading-relaxed">{original_text}</p>
        </div>
      </div>
    );
  }

  // Full correction available
  const replaceEdits = edits.filter((e) => e.severity === "replace");

  return (
    <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
      {/* Original with struck-through biased terms */}
      <div className="px-4 py-3 border-b border-slate-100">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-1.5">
          Original
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          {highlightOriginal(original_text, replaceEdits)}
        </p>
      </div>

      {/* Corrected text */}
      <div className="px-4 py-3 bg-emerald-50/50">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-emerald-700 mb-1.5">
          Corrected
        </div>
        <p className="text-sm text-emerald-900 font-medium leading-relaxed">
          {rewrite}
        </p>
      </div>

      {/* Edit list */}
      {replaceEdits.length > 0 && (
        <div className="px-4 py-3 border-t border-slate-100 bg-slate-50/50">
          <div className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-2">
            Changes ({replaceEdits.length})
          </div>
          <div className="flex flex-col gap-1.5">
            {replaceEdits.map((edit, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className="bg-red-100 text-red-700 px-1.5 py-0.5 rounded line-through font-mono">
                  {edit.from}
                </span>
                <span className="text-slate-400">→</span>
                <span className="bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-mono">
                  {edit.to || "(removed)"}
                </span>
                {edit.reason && (
                  <span className="text-muted italic flex-1">{edit.reason}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function highlightOriginal(text: string, edits: AnalyseResponse["edits"]) {
  if (!edits.length) return <>{text}</>;
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  for (const edit of edits) {
    const idx = remaining.toLowerCase().indexOf(edit.from.toLowerCase());
    if (idx === -1) continue;
    if (idx > 0) parts.push(<span key={key++}>{remaining.slice(0, idx)}</span>);
    parts.push(
      <span key={key++} className="bg-red-100 text-red-700 line-through rounded px-0.5">
        {remaining.slice(idx, idx + edit.from.length)}
      </span>
    );
    remaining = remaining.slice(idx + edit.from.length);
  }
  if (remaining) parts.push(<span key={key++}>{remaining}</span>);
  return <>{parts}</>;
}
