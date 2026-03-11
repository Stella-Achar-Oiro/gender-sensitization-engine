import { RewriteResponse } from "@/lib/types"
import { BiasSpans } from "./BiasSpans"
import { SeverityBadge } from "./SeverityBadge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Props {
  result: RewriteResponse
}

export function CorrectionPanel({ result }: Props) {
  const hasBias = result.has_bias_detected

  return (
    <div className="space-y-4">
      {/* Reason */}
      <Card className={`glass-subtle ${hasBias ? "border-red-200/50 bg-red-50/80" : "border-green-200/50 bg-green-50/80"}`}>
        <CardContent className="pt-4 pb-3">
          <p className="text-sm font-medium">
            {hasBias ? "⚠️ " : "✅ "}
            {result.reason}
          </p>
        </CardContent>
      </Card>

      {/* Side by side */}
      {hasBias && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="glass-subtle">
            <CardHeader className="pb-2 pt-4">
              <CardTitle className="text-sm text-muted-foreground">Original</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">
                <BiasSpans text={result.original_text} edits={result.edits} />
              </p>
            </CardContent>
          </Card>
          <Card className="glass-subtle border-green-200/50">
            <CardHeader className="pb-2 pt-4">
              <CardTitle className="text-sm text-muted-foreground">Suggested correction</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">{result.rewrite}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Edit list */}
      {result.edits.length > 0 && (
        <div className="space-y-2">
          {result.edits.map((edit, i) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <SeverityBadge severity={edit.severity} />
              <span className="text-muted-foreground">
                <span className="line-through text-red-700">{edit.from}</span>
                {edit.severity === "replace" && (
                  <> → <span className="text-green-700 font-medium">{edit.to}</span></>
                )}
                {edit.reason && <span className="ml-2 text-gray-500">— {edit.reason}</span>}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Confidence + source */}
      <p className="text-xs text-muted-foreground">
        Confidence: {Math.round(result.confidence * 100)}% · Detected by: {result.source}
        {result.semantic_score !== undefined && ` · Semantic score: ${result.semantic_score.toFixed(2)}`}
      </p>
    </div>
  )
}
