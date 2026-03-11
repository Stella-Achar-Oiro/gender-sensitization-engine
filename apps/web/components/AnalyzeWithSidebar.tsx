"use client"

import { useState, useCallback } from "react"
import Link from "next/link"
import Image from "next/image"
import { RewriteResponse } from "@/lib/types"
import { TextAnalyzer } from "./TextAnalyzer"
import { CorrectionPanel } from "./CorrectionPanel"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const LOGO_URL = "https://i.postimg.cc/L5mk9h1P/juakazi.png"

interface HistoryItem {
  id: string
  result: RewriteResponse
}

function truncate(s: string, maxLen: number) {
  const t = s.trim()
  if (t.length <= maxLen) return t
  return t.slice(0, maxLen).trim() + "…"
}

export function AnalyzeWithSidebar() {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const selected = selectedId ? history.find((h) => h.id === selectedId) : null

  const handleAnalyzed = useCallback((result: RewriteResponse) => {
    const id = `analysis-${Date.now()}`
    setHistory((prev) => [{ id, result }, ...prev])
    setSelectedId(id)
  }, [])

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-muted/30">
      {/* Sidebar: logo + analysed texts (hidden on mobile) */}
      <aside className="hidden md:flex w-72 shrink-0 border-r border-border bg-card flex-col">
        <div className="p-4 border-b border-border">
          <Link href="/" className="text-sm text-muted-foreground hover:underline">
            ← Back
          </Link>
          <Link href="/" className="mt-3 flex items-center gap-3">
            <Image
              src={LOGO_URL}
              alt="JuaKazi"
              width={40}
              height={40}
              className="rounded-lg shrink-0"
              unoptimized
            />
            <span className="font-bold text-foreground" style={{ color: "#1a5c2e" }}>
              JuaKazi
            </span>
          </Link>
          <h2 className="font-semibold mt-4 text-foreground">Analysed texts</h2>
          <p className="text-xs text-muted-foreground mt-1">
            Your analyses appear here. Click one to view.
          </p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground px-2 py-4">
              No analyses yet. Enter text and click Analyse.
            </p>
          ) : (
            <ul className="space-y-2">
              {history.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(item.id)}
                    className={`w-full text-left rounded-xl border p-3 transition-all duration-200 ${
                      selectedId === item.id
                        ? "glass border-primary/30 ring-1 ring-primary/20"
                        : "glass-subtle border-border hover:bg-white/50 dark:hover:bg-white/10"
                    }`}
                  >
                    <p className="text-sm line-clamp-2 text-foreground">
                      {truncate(item.result.original_text, 72)}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <Badge
                        variant={item.result.has_bias_detected ? "destructive" : "secondary"}
                        className="text-xs"
                      >
                        {item.result.has_bias_detected ? "Bias" : "OK"}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {item.result.edits.length} edit{item.result.edits.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* Main: current result + analyzer */}
      <main className="flex-1 overflow-y-auto min-w-0">
        <div className="max-w-2xl mx-auto px-4 py-4 sm:py-6 md:py-8">
          <h1 className="text-2xl font-bold text-foreground">Analyse text for gender bias</h1>
          <p className="text-muted-foreground mt-1 mb-6">
            Paste text in Swahili, English, French, or Kikuyu. The engine detects bias, explains why,
            and suggests a correction.
          </p>

          <Card className="glass mb-8">
            <CardContent className="pt-6">
              <TextAnalyzer onAnalyzed={handleAnalyzed} />
            </CardContent>
          </Card>

          {selected && (
            <Card className="mt-6 md:mt-8 glass">
              <CardContent className="pt-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-muted-foreground">
                    Selected result
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedId(null)}
                    className="text-muted-foreground"
                  >
                    Clear
                  </Button>
                </div>
                <CorrectionPanel result={selected.result} />
              </CardContent>
            </Card>
          )}

          {/* Mobile: recent analyses list (replaces sidebar) */}
          {history.length > 0 && (
            <details className="mt-6 md:hidden border rounded-xl bg-card overflow-hidden">
              <summary className="p-4 cursor-pointer font-medium text-sm text-foreground">
                Recent analyses ({history.length})
              </summary>
              <ul className="border-t divide-y divide-border max-h-64 overflow-y-auto">
                {history.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(item.id)}
                      className={`w-full text-left p-3 text-sm ${selectedId === item.id ? "bg-primary/10" : ""}`}
                    >
                      <p className="line-clamp-2 text-foreground">
                        {truncate(item.result.original_text, 72)}
                      </p>
                      <div className="mt-1 flex items-center gap-2">
                        <Badge
                          variant={item.result.has_bias_detected ? "destructive" : "secondary"}
                          className="text-xs"
                        >
                          {item.result.has_bias_detected ? "Bias" : "OK"}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {item.result.edits.length} edit{item.result.edits.length !== 1 ? "s" : ""}
                        </span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      </main>
    </div>
  )
}
