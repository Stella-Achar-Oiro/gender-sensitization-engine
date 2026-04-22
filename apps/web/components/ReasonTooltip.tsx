"use client"

import { Edit } from "@/lib/types"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { SeverityBadge } from "./SeverityBadge"

interface Props {
  children: React.ReactNode
  edit: Edit
}

/** Shadcn Tooltip wrapper showing bias type, plain-language reason, and severity badge. */
export function ReasonTooltip({ children, edit }: Props) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <div className="space-y-1.5">
            <SeverityBadge severity={edit.severity} />
            <p className="font-semibold text-sm capitalize">{(edit.bias_type ?? "stereotype").replace(/_/g, " ")}</p>
            <p className="text-sm text-muted-foreground">{edit.reason ?? edit.stereotype_category}</p>
            {edit.severity === "replace" && edit.to && (
              <p className="text-sm text-green-700">
                Suggestion: <strong>{edit.to}</strong>
              </p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
  )
}
