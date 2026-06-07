"use client";
import { useState } from "react";
import type { AnalyseResponse } from "../lib/api";

interface Props {
  result: AnalyseResponse;
}

type ReviewState = "pending" | "accepted" | "edited" | "rejected";

export default function DiffView({ result }: Props) {
  const { original_text, rewrite, edits, has_bias_detected, reason } = result;
  const biasDetected = has_bias_detected;
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
          <p className="text-sm text-slate-700 leading-relaxed">
            {highlightOriginal(original_text, edits)}
          </p>
        </div>

        {/* Flagged terms */}
        {edits.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {edits.map((edit, i) => (
              <span key={i} className="inline-flex items-center gap-1 text-xs bg-amber-100
                                       text-amber-800 border border-amber-300 rounded px-2 py-0.5">
                <span className="font-mono font-semibold">{edit.from}</span>
                {edit.reason && <span className="text-amber-600">— {edit.reason}</span>}
              </span>
            ))}
          </div>
        )}

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

  // Plain-language reason: "Changed 'chairman' → 'chair' — gendered job title"
  const plainReasons = replaceEdits
    .filter((e) => e.from && e.to)
    .map((e) => {
      const category = e.stereotype_category ?? e.bias_type ?? "";
      const label =
        category === "profession"  ? "gendered job title" :
        category === "family_role" ? "gendered family role" :
        category === "capability"  ? "gendered capability stereotype" :
        category === "daily_life"  ? "gendered pronoun" :
        "gender bias";
      return `Changed '${e.from}' → '${e.to}' — ${label}`;
    });

  const handleCopyCorrection = () => {
    navigator.clipboard.writeText(editedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const correctedBg =
    reviewState === "accepted" || reviewState === "edited"
      ? "bg-emerald-50 border-t-2 border-emerald-400"
      : reviewState === "rejected"
      ? "bg-slate-50 border-t border-slate-200"
      : "bg-emerald-50/60";

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      {/* Original with inline highlights */}
      <div className="px-4 py-3 border-b border-slate-100">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-muted mb-1.5">
          Original
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          {highlightOriginal(original_text, replaceEdits)}
        </p>
      </div>

      {/* Corrected */}
      <div className={`px-4 py-3 ${correctedBg}`}>
        <div className="flex items-center justify-between mb-1.5">
          <div className="text-[10px] font-semibold uppercase tracking-widest text-emerald-700">
            {reviewState === "accepted" && "✓ Accepted"}
            {reviewState === "edited"   && "✓ Edited & accepted"}
            {reviewState === "rejected" && "✗ Rejected — keeping original"}
            {reviewState === "pending"  && "Suggested correction"}
          </div>
          {reviewState !== "pending" && (
            <button onClick={handleReset} className="text-[10px] text-muted hover:underline">Reset</button>
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
            {reviewState === "rejected" ? editedText : (
              <WordDiffView original={original_text} corrected={editedText} />
            )}
          </p>
        )}

        {/* Plain-language reason */}
        {plainReasons.length > 0 && reviewState === "pending" && !isEditing && (
          <div className="mt-2 flex flex-col gap-0.5">
            {plainReasons.map((r, i) => (
              <p key={i} className="text-[11px] text-emerald-700 opacity-80">{r}</p>
            ))}
          </div>
        )}
      </div>

      {/* Actions row */}
      {reviewState === "pending" && !isEditing && (
        <div className="px-4 py-3 border-t border-slate-100 flex items-center gap-2">
          {/* Prominent copy button */}
          <button
            onClick={handleCopyCorrection}
            className="flex items-center gap-1.5 text-xs bg-[#00a651] hover:bg-[#009448]
                       text-white px-3 py-1.5 rounded-md font-semibold transition-colors"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <rect x="9" y="9" width="13" height="13" rx="2"/>
              <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
            </svg>
            {copied ? "Copied!" : "Copy correction"}
          </button>
          <button
            onClick={handleAccept}
            className="text-xs bg-white hover:bg-emerald-50 text-emerald-700
                       border border-emerald-300 px-3 py-1.5 rounded-md font-semibold transition-colors"
          >
            Accept
          </button>
          <button
            onClick={handleEdit}
            className="text-xs bg-white hover:bg-slate-50 text-slate-600
                       border border-slate-200 px-3 py-1.5 rounded-md font-medium transition-colors"
          >
            Edit
          </button>
          <button
            onClick={handleReject}
            className="text-xs text-slate-400 hover:text-slate-600 px-3 py-1.5
                       rounded-md font-medium transition-colors ml-auto"
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

      {/* Change detail chips */}
      {replaceEdits.length > 0 && (
        <div className="px-4 py-2.5 border-t border-slate-100 bg-slate-50/60 flex flex-wrap gap-1.5">
          {replaceEdits.map((edit, i) => (
            <span key={i} className="inline-flex items-center gap-1 text-[11px] bg-white
                                     border border-slate-200 rounded-full px-2 py-0.5 text-slate-600">
              <span className="text-red-500 line-through font-mono">{edit.from}</span>
              <span className="text-slate-300">→</span>
              <span className="text-emerald-600 font-mono">{edit.to || "∅"}</span>
            </span>
          ))}
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

// Word-level inline diff: tokens deleted in red strikethrough, inserted in green
type DiffOp = { type: "keep" | "del" | "ins"; text: string };

function wordDiff(original: string, corrected: string): DiffOp[] {
  const aWords = original.split(/(\s+)/);
  const bWords = corrected.split(/(\s+)/);
  const m = aWords.length;
  const n = bWords.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = m - 1; i >= 0; i--) {
    for (let j = n - 1; j >= 0; j--) {
      if (aWords[i].toLowerCase() === bWords[j].toLowerCase()) {
        dp[i][j] = 1 + dp[i + 1][j + 1];
      } else {
        dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
  }
  const ops: DiffOp[] = [];
  let i = 0, j = 0;
  while (i < m || j < n) {
    if (i < m && j < n && aWords[i].toLowerCase() === bWords[j].toLowerCase()) {
      ops.push({ type: "keep", text: aWords[i] });
      i++; j++;
    } else if (j < n && (i >= m || dp[i][j + 1] >= dp[i + 1][j])) {
      ops.push({ type: "ins", text: bWords[j] });
      j++;
    } else {
      ops.push({ type: "del", text: aWords[i] });
      i++;
    }
  }
  return ops;
}

export function WordDiffView({ original, corrected }: { original: string; corrected: string }) {
  if (original === corrected) return <span className="text-slate-700">{original}</span>;
  const ops = wordDiff(original, corrected);
  return (
    <span>
      {ops.map((op, i) => {
        if (op.type === "keep") return <span key={i}>{op.text}</span>;
        if (op.type === "del")
          return (
            <span key={i} className="bg-red-100 text-red-700 line-through rounded px-0.5 mx-px">
              {op.text}
            </span>
          );
        if (!op.text.trim()) return null;
        return (
          <span key={i} className="bg-emerald-100 text-emerald-800 rounded px-0.5 mx-px font-medium">
            {op.text}
          </span>
        );
      })}
    </span>
  );
}
