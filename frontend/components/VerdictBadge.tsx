import type { AnalyseResponse } from "../lib/api";

interface Props {
  result: AnalyseResponse;
}

export default function VerdictBadge({ result }: Props) {
  const { has_bias_detected, edits, confidence } = result;

  const replaceEdits = edits.filter((e) => e.severity === "replace");
  const warnEdits    = edits.filter((e) => e.severity === "warn");
  const hasReplace   = replaceEdits.length > 0;
  const hasWarnOnly  = !hasReplace && warnEdits.length > 0;

  // No bias at all
  if (!has_bias_detected) {
    return (
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3.5">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">🟢</span>
          <span className="font-semibold text-emerald-800">No bias detected</span>
          <span className="ml-auto text-xs text-emerald-600">Passes all checks</span>
        </div>
      </div>
    );
  }

  // High-confidence bias with auto-correction available
  if (hasReplace) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3.5">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">🔴</span>
          <span className="font-semibold text-red-800">Gender bias detected</span>
          <span className="ml-auto text-xs text-red-500">
            {replaceEdits.length} term{replaceEdits.length > 1 ? "s" : ""} flagged
          </span>
        </div>
        <p className="mt-2 text-xs text-red-700">
          A correction has been suggested below. Accept, edit, or reject it.
        </p>
      </div>
    );
  }

  // Warn-only: bias detected but needs human judgment
  if (hasWarnOnly) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3.5">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">🟡</span>
          <span className="font-semibold text-amber-800">Possible bias — human review needed</span>
          <span className="ml-auto text-xs text-amber-600">
            {warnEdits.length} term{warnEdits.length > 1 ? "s" : ""} flagged
          </span>
        </div>
        <p className="mt-2 text-xs text-amber-700">
          The flagged term(s) may be gender-biased depending on context. Please review and correct if needed.
        </p>
      </div>
    );
  }

  // Fallback — bias detected but no specific edits (e.g. ML-only)
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3.5">
      <div className="flex items-center gap-2">
        <span className="text-lg leading-none">🟡</span>
        <span className="font-semibold text-amber-800">Possible bias — review recommended</span>
        <span className="ml-auto text-xs text-amber-600">{Math.round(confidence * 100)}% confidence</span>
      </div>
      <p className="mt-2 text-xs text-amber-700">
        No automatic correction available. Please rewrite manually.
      </p>
    </div>
  );
}
