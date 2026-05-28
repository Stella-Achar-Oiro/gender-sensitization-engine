import type { AnalyseResponse } from "../lib/api";

interface Props {
  result: AnalyseResponse;
}

export default function DiffView({ result }: Props) {
  const { original_text, rewrite, edits, has_bias_detected } = result;
  const corrected = rewrite !== original_text;

  if (!has_bias_detected && !corrected) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white px-4 py-3.5 text-sm text-muted">
        No correction needed.
      </div>
    );
  }

  if (has_bias_detected && !corrected) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3.5">
        <p className="text-sm font-medium text-amber-800">
          ⚠️ Bias detected — no automatic correction available
        </p>
        <p className="mt-1 text-xs text-amber-700">
          This sentence needs human review.
        </p>
      </div>
    );
  }

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
