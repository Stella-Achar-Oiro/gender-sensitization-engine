"use client"

import { Edit } from "@/lib/types"
import { TooltipProvider } from "@/components/ui/tooltip"
import { ReasonTooltip } from "./ReasonTooltip"

interface Props {
  text: string
  edits: Edit[]
}

export function BiasSpans({ text, edits }: Props) {
  if (!edits.length) return <span>{text}</span>

  const segments: { text: string; edit?: Edit }[] = []
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
          <ReasonTooltip key={i} edit={seg.edit}>
            <mark
              className={
                seg.edit.severity === "replace"
                  ? "bg-red-100 border-b-2 border-red-400 rounded px-0.5 cursor-help"
                  : "bg-yellow-100 border-b-2 border-yellow-400 rounded px-0.5 cursor-help"
              }
            >
              {seg.text}
            </mark>
          </ReasonTooltip>
        ) : (
          <span key={i}>{seg.text}</span>
        )
        )}
      </span>
    </TooltipProvider>
  )
}
