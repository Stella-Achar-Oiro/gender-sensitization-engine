"use client"

import { useState } from "react"
import { RewriteResponse } from "@/lib/types"
import { BiasSpans } from "./BiasSpans"
import { SeverityBadge } from "./SeverityBadge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

interface Props {
  result: RewriteResponse
}

type ReviewState = "pending" | "accepted" | "edited" | "rejected"

export function CorrectionPanel({ result }: Props) {
  const hasBias = result.has_bias_detected
  const [reviewState, setReviewState] = useState<ReviewState>("pending")
  const [editedText, setEditedText] = useState(result.rewrite)
  const [isEditing, setIsEditing] = useState(false)

  const handleAccept = () => {
    setReviewState("accepted")
    setIsEditing(false)
  }

  const handleEdit = () => {
    setIsEditing(true)
    setReviewState("pending")
  }

  const handleSaveEdit = () => {
    setIsEditing(false)
    setReviewState("edited")
  }

  const handleReject = () => {
    setReviewState("rejected")
    setIsEditing(false)
    setEditedText(result.original_text)
  }

  const handleReset = () => {
    setReviewState("pending")
    setIsEditing(false)
    setEditedText(result.rewrite)
  }

  return (
    <div className="space-y-4">
      {/* Status banner */}
      <Card className={`glass-subtle ${hasBias ? "border-red-200/50 bg-red-50/80" : "border-green-200/50 bg-green-50/80"}`}>
        <CardContent className="pt-4 pb-3">
          <p className="text-sm font-medium">
            {hasBias ? "⚠️ " : "✅ "}
            {result.reason}
          </p>
        </CardContent>
      </Card>

      {/* Side by side: original + correction */}
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
          <Card className={`glass-subtle ${
            reviewState === "accepted" || reviewState === "edited"
              ? "border-green-400/60 bg-green-50/80"
              : reviewState === "rejected"
              ? "border-gray-300/50 bg-gray-50/60"
              : "border-green-200/50"
          }`}>
            <CardHeader className="pb-2 pt-4 flex flex-row items-center justify-between">
              <CardTitle className="text-sm text-muted-foreground">
                {reviewState === "accepted" && "✓ Accepted"}
                {reviewState === "edited" && "✓ Edited & accepted"}
                {reviewState === "rejected" && "✗ Rejected — keeping original"}
                {reviewState === "pending" && "Suggested correction"}
              </CardTitle>
              {reviewState !== "pending" && (
                <button onClick={handleReset} className="text-xs text-muted-foreground hover:underline">
                  Reset
                </button>
              )}
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <Textarea
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  rows={3}
                  className="resize-none text-sm"
                  autoFocus
                />
              ) : (
                <p className={`text-sm leading-relaxed ${reviewState === "rejected" ? "line-through text-muted-foreground" : ""}`}>
                  {editedText}
                </p>
              )}
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

      {/* Human review actions — only shown when bias detected and review pending/editing */}
      {hasBias && (reviewState === "pending" || isEditing) && (
        <div className="flex items-center gap-2 pt-1">
          {isEditing ? (
            <>
              <Button size="sm" onClick={handleSaveEdit} disabled={!editedText.trim()}>
                Save edit
              </Button>
              <Button size="sm" variant="ghost" onClick={() => { setIsEditing(false); setEditedText(result.rewrite) }}>
                Cancel
              </Button>
            </>
          ) : (
            <>
              <Button size="sm" onClick={handleAccept}>
                Accept
              </Button>
              <Button size="sm" variant="outline" onClick={handleEdit}>
                Edit correction
              </Button>
              <Button size="sm" variant="ghost" onClick={handleReject} className="text-muted-foreground">
                Reject
              </Button>
            </>
          )}
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
