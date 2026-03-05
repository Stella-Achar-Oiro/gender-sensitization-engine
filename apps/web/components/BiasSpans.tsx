"use client"

import { Edit } from "@/lib/types"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface Props {
  text: string
  edits: Edit[]
}

export function BiasSpans({ text, edits }: Props) {
  if (!edits.length) return <span>{text}</span>

  // Build segments: highlight matched spans
  const segments: { text: string; edit?: Edit }[] = []
  let remaining = text

  // Sort edits by position in text
  const positioned = edits
    .map((e) => ({ edit: e, idx: text.toLowerCase().indexOf(e.from.toLowerCase()) }))
    .filter((e) => e.idx >= 0)
    .sort((a, b) => a.idx - b.idx)

  let cursor = 0
  for (const { edit, idx } of positioned) {
    if (idx < cursor) continue
    if (idx > cursor) segments.push({ text: text.slice(cursor, idx) })
    segments.push({ text: text.slice(idx, idx + edit.from.length), edit })
    cursor = idx + edit.from.length
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor) })

  return (
    <TooltipProvider>
      <span>
        {segments.map((seg, i) =>
          seg.edit ? (
            <Tooltip key={i}>
              <TooltipTrigger asChild>
                <mark
                  className={
                    seg.edit.severity === "replace"
                      ? "bg-red-200 text-red-900 rounded px-0.5 cursor-help"
                      : "bg-yellow-200 text-yellow-900 rounded px-0.5 cursor-help"
                  }
                >
                  {seg.text}
                </mark>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="font-semibold text-sm">
                  {seg.edit.severity === "replace" ? "🔴 Bias detected" : "🟡 Possible bias"}
                </p>
                <p className="text-sm mt-1">{seg.edit.reason || seg.edit.stereotype_category}</p>
                {seg.edit.severity === "replace" && (
                  <p className="text-sm mt-1 text-green-700">
                    Suggestion: <strong>{seg.edit.to}</strong>
                  </p>
                )}
              </TooltipContent>
            </Tooltip>
          ) : (
            <span key={i}>{seg.text}</span>
          )
        )}
      </span>
    </TooltipProvider>
  )
}
