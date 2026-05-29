import type { AnalyseResponse } from "../lib/api";

interface Props {
  result: AnalyseResponse;
}

export default function VerdictBadge({ result }: Props) {
  const { has_bias_detected, aibridge_detected, aibridge_confidence, edits, confidence, needs_review } = result;

  // Only trust aibridge_detected if our own pipeline also found something (edits exist)
  // or has_bias_detected is true. Prevents false positives from low-confidence external API.
  const hasRealEdits = edits.some((e) => e.severity === "replace" || e.severity === "warn");
  const biasDetected = has_bias_detected || (aibridge_detected && hasRealEdits);
  const conf = aibridge_confidence ?? confidence;
  const lowConf = biasDetected && conf > 0 && conf < 0.75;
  const correctionSuppressed = aibridge_detected && !has_bias_detected;

  const warnOnly = !biasDetected && edits.some((e) => e.severity === "warn");
  const mlOnly   = !biasDetected && edits.some((e) => e.severity === "ml_fallback");

  if (biasDetected) {
    const replaceCount = edits.filter((e) => e.severity === "replace").length;
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3.5">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">🔴</span>
          <span className="font-semibold text-red-800">Gender bias detected</span>
          <span className="ml-auto text-xs text-red-500">
            {replaceCount > 0
              ? `${replaceCount} rule(s) matched`
              : `${(conf * 100).toFixed(0)}% confidence`}
          </span>
        </div>
        {correctionSuppressed && (
          <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
            ⚠️ Automatic correction unavailable — flag for human review
          </p>
        )}
        {!correctionSuppressed && lowConf && (
          <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
            ⚠️ Low confidence — flag for human review
          </p>
        )}
        {needs_review && !correctionSuppressed && !lowConf && (
          <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
            ⚠️ Flagged for human review
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
