"use client"

import { useState, useCallback } from "react"
import { Language, RewriteResponse } from "@/lib/types"
import { analyzeText } from "@/lib/api"
import { LanguageSelector } from "./LanguageSelector"
import { CorrectionPanel } from "./CorrectionPanel"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

const EXAMPLES: Record<Language, string> = {
  sw: "Daktari wa kiume aliwasili hospitalini asubuhi na mapema.",
  en: "The chairman opened the meeting with the stewardess.",
  fr: "Le médecin homme est arrivé à l'hôpital tôt le matin.",
  ki: "Mũndũ-mũrũme nĩ we mũtongoria wa nyũmba.",
}

interface TextAnalyzerProps {
  /** When set (e.g. analyze page with sidebar), parent shows the result; we don’t render CorrectionPanel here. */
  onAnalyzed?: (result: RewriteResponse) => void
}

export function TextAnalyzer({ onAnalyzed }: TextAnalyzerProps) {
  const [lang, setLang] = useState<Language>("sw")
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RewriteResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = useCallback(async () => {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await analyzeText({
        id: `web-${Date.now()}`,
        lang,
        text: text.trim(),
      })
      setResult(res)
      onAnalyzed?.(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }, [text, lang, onAnalyzed])

  const handleExample = () => {
    setText(EXAMPLES[lang])
    setResult(null)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <LanguageSelector value={lang} onChange={(l) => { setLang(l); setResult(null) }} />
        <Button variant="ghost" size="sm" onClick={handleExample} className="text-muted-foreground">
          Try an example
        </Button>
      </div>

      <Textarea
        placeholder="Enter text to analyse for gender bias…"
        value={text}
        onChange={(e) => { setText(e.target.value); setResult(null) }}
        rows={5}
        className="resize-none text-base min-h-[120px] sm:min-h-[140px]"
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleAnalyze()
        }}
      />

      <Button
        onClick={handleAnalyze}
        disabled={!text.trim() || loading}
        className="w-full"
      >
        {loading ? "Analysing…" : "Analyse"}
      </Button>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
          {error}
        </p>
      )}

      {result && !onAnalyzed && <CorrectionPanel result={result} />}
    </div>
  )
}
