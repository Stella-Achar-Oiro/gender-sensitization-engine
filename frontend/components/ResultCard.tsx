"use client";
import { useState } from "react";
import type { AnalyseResponse } from "../lib/api";

type ReviewAction = "pending" | "accepted" | "edited" | "rejected" | "flagged";

interface Props {
  result: AnalyseResponse;
  onExportData?: (data: ExportRow) => void;
}

export interface ExportRow {
  original_text: string;
  corrected_text: string;
  reviewer_action: ReviewAction;
  flag_note: string;
  qa_status: string;
  source: string;
  confidence: number;
}

// Word-level LCS diff
type DiffOp = { type: "keep" | "del" | "ins"; text: string };
function wordDiff(a: string, b: string): DiffOp[] {
  const aw = a.split(/(\s+)/);
  const bw = b.split(/(\s+)/);
  const m = aw.length, n = bw.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = m - 1; i >= 0; i--)
    for (let j = n - 1; j >= 0; j--)
      dp[i][j] = aw[i].toLowerCase() === bw[j].toLowerCase()
        ? 1 + dp[i + 1][j + 1]
        : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const ops: DiffOp[] = [];
  let i = 0, j = 0;
  while (i < m || j < n) {
    if (i < m && j < n && aw[i].toLowerCase() === bw[j].toLowerCase()) {
      ops.push({ type: "keep", text: aw[i++] }); j++;
    } else if (j < n && (i >= m || dp[i][j + 1] >= dp[i + 1][j])) {
      ops.push({ type: "ins", text: bw[j++] });
    } else {
      ops.push({ type: "del", text: aw[i++] });
    }
  }
  return ops;
}

function OriginalHighlight({ text, edits }: { text: string; edits: AnalyseResponse["edits"] }) {
  const replaceEdits = edits.filter((e) => e.severity === "replace" && e.from);
  if (!replaceEdits.length) return <span className="text-[#1a1a2e]">{text}</span>;
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;
  for (const edit of replaceEdits) {
    const idx = remaining.toLowerCase().indexOf(edit.from.toLowerCase());
    if (idx === -1) continue;
    if (idx > 0) parts.push(<span key={key++} className="text-[#1a1a2e]">{remaining.slice(0, idx)}</span>);
    parts.push(
      <span key={key++}
        className="bg-red-100 text-red-700 bias-underline rounded px-0.5 font-medium"
        title={edit.reason ?? "Gender bias"}>
        {remaining.slice(idx, idx + edit.from.length)}
      </span>
    );
    remaining = remaining.slice(idx + edit.from.length);
  }
  if (remaining) parts.push(<span key={key++} className="text-[#1a1a2e]">{remaining}</span>);
  return <>{parts}</>;
}

function CorrectedDiff({ original, corrected }: { original: string; corrected: string }) {
  if (original === corrected) return <span className="text-[#1a1a2e]">{corrected}</span>;
  const ops = wordDiff(original, corrected);
  return (
    <>
      {ops.map((op, i) => {
        if (op.type === "keep") return <span key={i} className="text-[#1a1a2e]">{op.text}</span>;
        if (op.type === "del")  return (
          <span key={i} className="bg-red-100 text-red-600 line-through rounded px-0.5 mx-px text-sm">
            {op.text}
          </span>
        );
        if (!op.text.trim()) return <span key={i}>{op.text}</span>;
        return (
          <span key={i} className="bg-emerald-100 text-emerald-800 rounded px-0.5 mx-px font-semibold">
            {op.text}
          </span>
        );
      })}
    </>
  );
}

const SOURCE_LABEL: Record<string, string> = {
  rules: "Lexicon",
  ml: "ML",
  disambiguated: "ML+Lexicon",
  low_confidence: "ML",
  preserved: "Rules",
};

const borderColor: Record<ReviewAction, string> = {
  pending:  "border-l-red-400",
  accepted: "border-l-emerald-400",
  edited:   "border-l-emerald-400",
  rejected: "border-l-slate-300",
  flagged:  "border-l-amber-400",
};

export default function ResultCard({ result, onExportData }: Props) {
  const { original_text, rewrite, edits, has_bias_detected, confidence, source, reason } = result;
  const corrected = rewrite !== original_text;
  const replaceEdits = edits.filter((e) => e.severity === "replace");
  const mlOnly = !corrected && has_bias_detected;

  const [action, setAction]       = useState<ReviewAction>("pending");
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(rewrite || original_text);
  const [isFlagging, setIsFlagging] = useState(false);
  const [flagNote, setFlagNote]   = useState("");
  const [savedFlag, setSavedFlag] = useState("");

  const displayText = action === "edited" ? editedText : (rewrite || original_text);

  const notifyExport = (a: ReviewAction, note = "") => {
    onExportData?.({
      original_text,
      corrected_text: a === "edited" ? editedText : (rewrite || original_text),
      reviewer_action: a,
      flag_note: note,
      qa_status: a === "accepted" || a === "edited" ? "approved"
               : a === "rejected" ? "rejected"
               : a === "flagged"  ? "needs_review"
               : "pending",
      source: source ?? "unknown",
      confidence,
    });
  };

  const doAccept = () => { setAction("accepted"); setIsEditing(false); setIsFlagging(false); notifyExport("accepted"); };
  const doReject = () => { setAction("rejected"); setIsEditing(false); setIsFlagging(false); notifyExport("rejected"); };
  const doEdit   = () => { setIsEditing(true); setIsFlagging(false); setAction("pending"); };
  const doSave   = () => { setIsEditing(false); setAction("edited"); notifyExport("edited"); };
  const doCancel = () => { setIsEditing(false); setEditedText(rewrite || original_text); };
  const doFlag   = () => { setIsFlagging(true); setIsEditing(false); };
  const doSaveFlag = () => {
    setSavedFlag(flagNote);
    setAction("flagged");
    setIsFlagging(false);
    notifyExport("flagged", flagNote);
  };
  const doReset = () => {
    setAction("pending"); setIsEditing(false); setIsFlagging(false);
    setEditedText(rewrite || original_text); setFlagNote(""); setSavedFlag("");
  };

  // No bias card
  if (!has_bias_detected) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 border-l-4 border-l-emerald-400 shadow-sm px-5 py-4">
        <div className="flex items-center gap-2.5">
          <span className="text-emerald-500">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </span>
          <span className="text-base font-semibold text-slate-800">No bias detected</span>
          <span className="ml-auto text-sm text-slate-400">Passes all checks</span>
        </div>
        <p className="mt-2 text-sm text-[#1a1a2e] leading-relaxed pl-7">{original_text}</p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl border border-slate-200 border-l-4 ${borderColor[action]} shadow-sm overflow-hidden`}>

      {/* Header */}
      <div className={`px-5 py-3 flex items-center gap-3 border-b ${
        action === "accepted" || action === "edited" ? "border-emerald-100 bg-emerald-50/50" :
        action === "rejected" ? "border-slate-100 bg-slate-50/50" :
        action === "flagged"  ? "border-amber-100 bg-amber-50/50" :
        "border-red-100 bg-red-50/40"
      }`}>
        {action === "pending" && (
          <>
            <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0 mt-0.5" />
            <span className="text-base font-semibold text-red-700">
              {mlOnly ? "Possible bias detected" : "Gender bias detected"}
            </span>
          </>
        )}
        {(action === "accepted" || action === "edited") && (
          <>
            <span className="text-emerald-600">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
              </svg>
            </span>
            <span className="text-base font-semibold text-emerald-700">
              {action === "edited" ? "Correction edited & accepted" : "Correction accepted"}
            </span>
          </>
        )}
        {action === "rejected" && (
          <>
            <span className="text-slate-400">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </span>
            <span className="text-base font-semibold text-slate-500">Correction rejected — original kept</span>
          </>
        )}
        {action === "flagged" && (
          <>
            <span className="text-amber-500">🚩</span>
            <span className="text-base font-semibold text-amber-700">Flagged for human review</span>
          </>
        )}

        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
            {SOURCE_LABEL[source ?? ""] ?? source}
          </span>
          <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
            {Math.round(confidence * 100)}%
          </span>
          {action !== "pending" && (
            <button onClick={doReset} className="text-xs text-slate-400 hover:text-slate-600 transition-colors">
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Original */}
      <div className="px-5 py-4 border-b border-slate-100">
        <div className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-2">Original</div>
        <p className="text-base leading-relaxed">
          <OriginalHighlight text={original_text} edits={edits} />
        </p>
        {replaceEdits.length > 0 && (
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {replaceEdits.map((edit, i) => (
              <span key={i} className="inline-flex items-center gap-1.5 text-xs bg-red-50
                                       border border-red-200 text-red-700 rounded-full px-2.5 py-1">
                <span className="font-mono font-semibold">{edit.from}</span>
                {edit.stereotype_category && (
                  <span className="text-red-400">· {edit.stereotype_category}</span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Corrected / ML-only */}
      {corrected && (
        <div className={`px-5 py-4 border-b border-slate-100 ${
          action === "rejected" ? "opacity-50" : ""
        }`}>
          <div className="text-xs font-semibold uppercase tracking-widest text-emerald-600 mb-2">
            {action === "edited" ? "Your correction" : "Suggested correction"}
          </div>

          {isEditing ? (
            <textarea
              autoFocus
              className="w-full text-base border-2 border-indigo-300 rounded-lg px-3 py-2.5 bg-white
                         focus:outline-none focus:border-indigo-400 resize-none text-[#1a1a2e] leading-relaxed"
              rows={3}
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
            />
          ) : (
            <p className={`text-base leading-relaxed ${action === "rejected" ? "line-through text-slate-400" : ""}`}>
              <CorrectedDiff original={original_text} corrected={displayText} />
            </p>
          )}

          {replaceEdits.length > 0 && action === "pending" && !isEditing && (
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {replaceEdits.filter(e => e.from && e.to).map((edit, i) => (
                <span key={i} className="inline-flex items-center gap-1.5 text-xs bg-slate-50
                                         border border-slate-200 rounded-full px-2.5 py-1">
                  <span className="text-red-500 line-through font-mono">{edit.from}</span>
                  <span className="text-slate-300 mx-0.5">→</span>
                  <span className="text-emerald-600 font-mono font-semibold">{edit.to || "∅"}</span>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ML-only — no correction available */}
      {mlOnly && (
        <div className="px-5 py-4 border-b border-slate-100 bg-amber-50/40">
          <div className="text-xs font-semibold uppercase tracking-widest text-amber-600 mb-2">
            ML Detection — No auto-correction
          </div>
          {isEditing ? (
            <textarea
              autoFocus
              className="w-full text-base border-2 border-indigo-300 rounded-lg px-3 py-2.5 bg-white
                         focus:outline-none focus:border-indigo-400 resize-none text-[#1a1a2e] leading-relaxed"
              rows={3}
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              placeholder="Write a corrected version…"
            />
          ) : (
            <p className="text-sm text-amber-800 leading-relaxed">
              {reason ?? "Bias pattern identified but automatic correction unavailable. Please rewrite manually."}
            </p>
          )}
        </div>
      )}

      {/* Reason */}
      {replaceEdits.some(e => e.reason) && action === "pending" && !isEditing && (
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/60">
          <div className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-1.5">Reason</div>
          {replaceEdits.filter(e => e.reason).map((edit, i) => (
            <p key={i} className="text-sm text-[#475569] leading-relaxed">{edit.reason}</p>
          ))}
        </div>
      )}

      {/* Flag note */}
      {action === "flagged" && savedFlag && (
        <div className="px-5 py-3 border-b border-amber-100 bg-amber-50/40">
          <div className="text-xs font-semibold uppercase tracking-widest text-amber-500 mb-1">Review note</div>
          <p className="text-sm text-amber-800">{savedFlag}</p>
        </div>
      )}

      {/* Flag input */}
      {isFlagging && (
        <div className="px-5 py-4 border-b border-amber-200 bg-amber-50/50">
          <div className="text-xs font-semibold uppercase tracking-widest text-amber-600 mb-2">
            🚩 Flag for review — add a note (optional)
          </div>
          <textarea
            autoFocus
            className="w-full text-sm border border-amber-300 rounded-lg px-3 py-2.5 bg-white
                       focus:outline-none focus:ring-2 focus:ring-amber-300 resize-none text-[#1a1a2e]"
            rows={2}
            placeholder="e.g. Correction sounds unnatural in Hausa context…"
            value={flagNote}
            onChange={(e) => setFlagNote(e.target.value)}
          />
          <div className="flex gap-2 mt-2.5">
            <button
              onClick={doSaveFlag}
              className="text-sm bg-amber-500 hover:bg-amber-600 text-white font-semibold
                         px-4 py-2 rounded-lg transition-colors"
            >
              Save flag
            </button>
            <button
              onClick={() => setIsFlagging(false)}
              className="text-sm text-slate-500 hover:text-slate-700 px-4 py-2 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Actions */}
      {action === "pending" && !isFlagging && (
        <div className="px-5 py-3.5 flex items-center gap-2 flex-wrap">
          {isEditing ? (
            <>
              <button
                onClick={doSave}
                disabled={!editedText.trim()}
                className="text-sm bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40
                           text-white font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                Save correction
              </button>
              <button
                onClick={doCancel}
                className="text-sm text-slate-500 hover:text-slate-700 px-4 py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={doAccept}
                className="flex items-center gap-1.5 text-sm bg-[#00a651] hover:bg-[#008f45]
                           text-white font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                </svg>
                Accept
              </button>
              <button
                onClick={doEdit}
                className="flex items-center gap-1.5 text-sm bg-indigo-50 hover:bg-indigo-100
                           text-indigo-700 border border-indigo-200 font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
                Edit
              </button>
              <button
                onClick={doFlag}
                className="flex items-center gap-1.5 text-sm bg-amber-50 hover:bg-amber-100
                           text-amber-700 border border-amber-200 font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                🚩 Flag
              </button>
              <button
                onClick={doReject}
                className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-600
                           border border-slate-200 hover:border-slate-300 px-4 py-2 rounded-lg transition-colors ml-auto"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
                </svg>
                Reject
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
