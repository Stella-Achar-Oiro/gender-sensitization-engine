"use client";
import { useState } from "react";
import type { AnalyseResponse } from "../lib/api";

interface Props {
  result: AnalyseResponse;
}

type ReviewState = "pending" | "accepted" | "edited" | "rejected";

export default function DiffView({ result }: Props) {
  const { original_text, rewrite, edits, has_bias_detected, aibridge_detected, reason } = result;
  const hasRealEdits = edits.some((e) => e.severity === "replace" || e.severity === "warn");
  const biasDetected = has_bias_detected || (aibridge_detected && hasRealEdits);
  const corrected = rewrite !== original_text;

  const [copied, setCopied] = useState(false);
  const [reviewState, setReviewState] = useState<ReviewState>("pending");
  const [editedText, setEditedText] = useState(rewrite);
  const [isEditing, setIsEditing] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(
      `[BIAS FLAGGED FOR REVIEW]\n\nOriginal: ${original_text}\n\nReason: ${reason ?? "Gender bias detected — automatic correction unavailable"}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleAccept = () => { setReviewState("accepted"); setIsEditing(false); };
  const handleReject = () => { setReviewState("rejected"); setIsEditing(false); };
  const handleEdit   = () => { setIsEditing(true); setReviewState("pending"); };
  const handleSave   = () => { setIsEditing(false); setReviewState("edited"); };
  const handleCancel = () => { setIsEditing(false); setEditedText(rewrite); };
  const handleReset  = () => { setReviewState("pending"); setIsEditing(false); setEditedText(rewrite); };

  // No bias, no correction needed
  if (!biasDetected && !corrected) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white px-4 py-3.5 text-sm text-muted">
        No correction needed.
      </div>
    );
  }

  // Bias detected but no automatic correction available
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
              → Rewrite manually below or copy for a reviewer.
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

        <div className="mt-3 bg-white rounded border border-amber-100 px-3 py-2">
          <div className="text-[10px] font-semibold uppercase tracking-widest text-amber-600 mb-1">
            Original (needs review)
          </div>
          <p className="text-sm text-slate-700 leading-relaxed">{original_text}</p>
        </div>

        {/* Manual rewrite box */}
        <div className="mt-3">
          <div className="text-[10px] font-semibold uppercase tracking-widest text-amber-600 mb-1">
            Your correction
          </div>
          <textarea
            className="w-full text-sm border border-amber-200 rounded-lg px-3 py-2 bg-white
                       focus:outline-none focus:ring-2 focus:ring-amber-300 resize-none"
            rows={2}
            placeholder="Write a corrected version…"
            value={editedText === rewrite ? "" : editedText}
            onChange={(e) => setEditedText(e.target.value)}
          />
        </div>
      </div>
    );
  }

  // Full correction available — with human review actions
  const replaceEdits = edits.filter((e) => e.severity === "replace");

  const correctedBg =
    reviewState === "accepted" || reviewState === "edited"
      ? "bg-emerald-100/80 border-t-2 border-emerald-400"
      : reviewState === "rejected"
      ? "bg-slate-50/80 border-t border-slate-200"
      : "bg-emerald-50/50";

  return (
    <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
      {/* Original */}
      <div className="px-4 py-3 border-b border-slate-100">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-1.5">
          Original
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          {highlightOriginal(original_text, replaceEdits)}
        </p>
      </div>

      {/* Corrected / editable */}
      <div className={`px-4 py-3 ${correctedBg}`}>
        <div className="flex items-center justify-between mb-1.5">
          <div className="text-[10px] font-semibold uppercase tracking-widest text-emerald-700">
            {reviewState === "accepted" && "✓ Accepted"}
            {reviewState === "edited"   && "✓ Edited & accepted"}
            {reviewState === "rejected" && "✗ Rejected — keeping original"}
            {reviewState === "pending"  && "Corrected"}
          </div>
          {reviewState !== "pending" && (
            <button onClick={handleReset} className="text-[10px] text-muted hover:underline">
              Reset
            </button>
          )}
        </div>

        {isEditing ? (
          <textarea
            autoFocus
            className="w-full text-sm border border-emerald-300 rounded-lg px-3 py-2 bg-white
                       focus:outline-none focus:ring-2 focus:ring-emerald-400 resize-none"
            rows={3}
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
          />
        ) : (
          <p className={`text-sm font-medium leading-relaxed ${
            reviewState === "rejected" ? "line-through text-slate-400" : "text-emerald-900"
          }`}>
            {editedText}
          </p>
        )}
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

      {/* Human review actions */}
      {reviewState === "pending" && !isEditing && (
        <div className="px-4 py-3 border-t border-slate-100 flex items-center gap-2">
          <button
            onClick={handleAccept}
            className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white
                       px-3 py-1.5 rounded-md font-semibold transition-colors"
          >
            Accept
          </button>
          <button
            onClick={handleEdit}
            className="text-xs bg-white hover:bg-slate-50 text-slate-700
                       border border-slate-300 px-3 py-1.5 rounded-md font-medium transition-colors"
          >
            Edit
          </button>
          <button
            onClick={handleReject}
            className="text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5
                       rounded-md font-medium transition-colors"
          >
            Reject
          </button>
        </div>
      )}

      {isEditing && (
        <div className="px-4 py-3 border-t border-slate-100 flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={!editedText.trim()}
            className="text-xs bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40
                       text-white px-3 py-1.5 rounded-md font-semibold transition-colors"
          >
            Save
          </button>
          <button
            onClick={handleCancel}
            className="text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5
                       rounded-md font-medium transition-colors"
          >
            Cancel
          </button>
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
