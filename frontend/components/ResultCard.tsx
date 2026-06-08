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

const glassOverlay: Record<ReviewAction, string> = {
  pending:  "from-red-50/60 to-white/80",
  accepted: "from-emerald-50/60 to-white/80",
  edited:   "from-emerald-50/60 to-white/80",
  rejected: "from-slate-50/60 to-white/80",
  flagged:  "from-amber-50/60 to-white/80",
};

// Small SVG arc showing confidence (0–1) as a partial circle
function ConfidenceArc({ value }: { value: number }) {
  const r = 10, cx = 13, cy = 13, stroke = 2.2;
  const circ = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, value));
  const dash = pct * circ;
  const color = pct >= 0.75 ? "#10b981" : pct >= 0.50 ? "#f59e0b" : "#ef4444";
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" className="flex-shrink-0">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#e2e8f0" strokeWidth={stroke} />
      <circle
        cx={cx} cy={cy} r={r} fill="none"
        stroke={color} strokeWidth={stroke}
        strokeDasharray={`${dash} ${circ}`}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
      />
      <text x={cx} y={cy + 3.5} textAnchor="middle" fontSize="6.5" fontWeight="600"
            fill={color} fontFamily="ui-monospace,monospace">
        {Math.round(pct * 100)}
      </text>
    </svg>
  );
}

const STATUS_PILL: Record<ReviewAction, { label: string; cls: string }> = {
  pending:  { label: "",               cls: "" },
  accepted: { label: "Accepted",       cls: "bg-emerald-100 text-emerald-700" },
  edited:   { label: "Edited",         cls: "bg-emerald-100 text-emerald-700" },
  rejected: { label: "Rejected",       cls: "bg-slate-100 text-slate-500" },
  flagged:  { label: "Flagged",        cls: "bg-amber-100 text-amber-700" },
};

export default function ResultCard({ result, onExportData }: Props) {
  const { original_text, rewrite, edits, has_bias_detected, confidence, source, reason,
          aibridge_detected, aibridge_confidence } = result;
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
      <div className="relative rounded-2xl overflow-hidden shadow-sm"
           style={{ background: "rgba(255,255,255,0.72)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.6)", boxShadow: "0 4px 24px rgba(0,166,81,0.06), 0 1px 3px rgba(0,0,0,0.06)" }}>
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-50/50 to-transparent pointer-events-none rounded-2xl" />
        <div className="relative px-5 py-4">
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
      </div>
    );
  }

  return (
    <div className="relative rounded-2xl overflow-hidden"
         style={{ background: "rgba(255,255,255,0.75)", backdropFilter: "blur(14px)", WebkitBackdropFilter: "blur(14px)", border: "1px solid rgba(255,255,255,0.6)", boxShadow: "0 4px 24px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.05)" }}>
      <div className={`absolute inset-0 bg-gradient-to-br ${glassOverlay[action]} pointer-events-none rounded-2xl`} />

      {/* Compact header — status pill + source tag + confidence arc */}
      <div className="relative px-4 py-2.5 flex items-center gap-2 border-b border-slate-100/50">
        {/* Status indicator dot + label */}
        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
          action === "pending"  ? (mlOnly ? "bg-amber-400" : "bg-red-500") :
          action === "accepted" || action === "edited" ? "bg-emerald-500" :
          action === "rejected" ? "bg-slate-400" : "bg-amber-500"
        }`} />
        <span className={`text-sm font-semibold ${
          action === "pending"  ? (mlOnly ? "text-amber-700" : "text-red-700") :
          action === "accepted" || action === "edited" ? "text-emerald-700" :
          action === "rejected" ? "text-slate-500" : "text-amber-700"
        }`}>
          {action === "pending"
            ? (mlOnly ? "Possible bias" : "Gender bias detected")
            : STATUS_PILL[action].label}
        </span>

        {/* Source tag */}
        <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full ml-1">
          {SOURCE_LABEL[source ?? ""] ?? source}
        </span>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Confidence arc */}
        <ConfidenceArc value={confidence} />

        {/* Reset */}
        {action !== "pending" && (
          <button
            onClick={doReset}
            className="text-xs text-slate-400 hover:text-slate-600 transition-colors ml-1"
          >
            Reset
          </button>
        )}
      </div>

      {/* Original */}
      <div className="relative px-5 py-4 border-b border-slate-100/60">
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
        <div className={`relative px-5 py-4 border-b border-slate-100/60 ${
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

      {/* ML-only — flagged for human review */}
      {mlOnly && (() => {
        const flaggedEdit = edits[0];
        const flaggedTerm = flaggedEdit?.from;
        const category = flaggedEdit?.stereotype_category;
        const mlConfidence = aibridge_confidence ?? confidence;
        const mlPct = Math.round(mlConfidence * 100);
        return (
          <div className="relative border-b border-amber-100/50">
            {/* What bias was detected */}
            <div className="px-5 py-3.5 border-b border-amber-100/40 bg-amber-50/25">
              <div className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-2">What was detected</div>
              <div className="flex flex-wrap gap-2 mb-2">
                {flaggedTerm ? (
                  <span className="inline-flex items-center gap-1.5 text-sm bg-red-50 border border-red-200
                                   text-red-700 rounded-lg px-3 py-1.5 font-mono font-semibold">
                    &ldquo;{flaggedTerm}&rdquo;
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-sm bg-red-50 border border-red-200
                                   text-red-700 rounded-lg px-3 py-1.5">
                    <span className="bias-underline font-medium">{original_text}</span>
                  </span>
                )}
                {category && (
                  <span className="inline-flex items-center text-xs bg-amber-50 border border-amber-200
                                   text-amber-700 rounded-lg px-2.5 py-1.5 font-semibold uppercase tracking-wide">
                    {category.replace(/_/g, " ")}
                  </span>
                )}
                <span className="inline-flex items-center text-xs bg-slate-50 border border-slate-200
                                 text-slate-500 rounded-lg px-2.5 py-1.5">
                  ML confidence {mlPct}%
                </span>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">
                No specific term isolated — the full sentence was flagged as likely containing gender bias.
                Please rewrite with gender-neutral language.
              </p>
            </div>
            {/* Write correction */}
            <div className="px-5 py-4 bg-amber-50/20">
              <div className="text-xs font-semibold uppercase tracking-widest text-amber-600 mb-2">
                Human correction needed
              </div>
              {isEditing ? (
                <textarea
                  autoFocus
                  className="w-full text-base border-2 border-amber-300 rounded-xl px-3 py-2.5 bg-white
                             focus:outline-none focus:border-amber-400 resize-none text-[#1a1a2e] leading-relaxed"
                  rows={3}
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  placeholder="Write a gender-neutral version…"
                />
              ) : (
                <button
                  onClick={doEdit}
                  className="w-full text-left text-sm text-amber-700/60 bg-white border border-dashed border-amber-300
                             rounded-xl px-4 py-3 hover:border-amber-400 hover:text-amber-800 transition-all"
                >
                  + Write a gender-neutral correction…
                </button>
              )}
            </div>
          </div>
        );
      })()}

      {/* Reason */}
      {replaceEdits.some(e => e.reason) && action === "pending" && !isEditing && (
        <div className="relative px-5 py-3 border-b border-slate-100/60 bg-slate-50/40">
          <div className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-1.5">Reason</div>
          {replaceEdits.filter(e => e.reason).map((edit, i) => (
            <p key={i} className="text-sm text-[#475569] leading-relaxed">{edit.reason}</p>
          ))}
        </div>
      )}

      {/* Flag note */}
      {action === "flagged" && savedFlag && (
        <div className="relative px-5 py-3 border-b border-amber-100/50 bg-amber-50/30">
          <div className="text-xs font-semibold uppercase tracking-widest text-amber-500 mb-1">Review note</div>
          <p className="text-sm text-amber-800">{savedFlag}</p>
        </div>
      )}

      {/* Flag input */}
      {isFlagging && (
        <div className="relative px-5 py-4 border-b border-amber-200/50 bg-amber-50/30">
          <div className="text-xs font-semibold uppercase tracking-widest text-amber-600 mb-2">
            Flag for review — add a note (optional)
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
        <div className="relative px-5 py-3.5 flex items-center gap-2 flex-wrap">
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
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22v-7"/>
                </svg>
                Flag
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
