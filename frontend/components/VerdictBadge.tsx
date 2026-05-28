import type { AnalyseResponse } from "../lib/api";

interface Props {
  result: AnalyseResponse;
}

export default function VerdictBadge({ result }: Props) {
  const { has_bias_detected, edits, confidence } = result;
  const lowConf = has_bias_detected && confidence > 0 && confidence < 0.75;
  const warnOnly = !has_bias_detected && edits.some((e) => e.severity === "warn");
  const mlOnly   = !has_bias_detected && edits.some((e) => e.severity === "ml_fallback");

  if (has_bias_detected) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3.5">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">🔴</span>
          <span className="font-semibold text-red-800">Gender bias detected</span>
          <span className="ml-auto text-xs text-red-500">
            {edits.filter((e) => e.severity === "replace").length} rule(s) matched
            {confidence > 0 && ` · ${(confidence * 100).toFixed(0)}% confidence`}
          </span>
        </div>
        {lowConf && (
          <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
            ⚠️ Low confidence — flag for human review
          </p>
        )}
      </div>
    );
  }

  if (mlOnly) {
    return (
      <div className="rounded-lg border border-orange-200 bg-orange-50 px-4 py-3.5">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">🟠</span>
          <span className="font-semibold text-orange-800">Implicit bias detected (ML)</span>
        </div>
        <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
          ⚠️ Low confidence — flag for human review
        </p>
      </div>
    );
  }

  if (warnOnly) {
    return (
      <div className="rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3.5">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">🟡</span>
          <span className="font-semibold text-yellow-800">Advisory</span>
          <span className="ml-auto text-xs text-yellow-600">
            Gendered term noted — no correction applied
          </span>
        </div>
      </div>
    );
  }

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
