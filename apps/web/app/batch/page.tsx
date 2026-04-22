"use client"

import { useState, useCallback } from "react"
import Link from "next/link"
import { analyzeText } from "@/lib/api"
import { Language } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LanguageSelector } from "@/components/LanguageSelector"

const CONCURRENCY = 5
const TEXT_COL = "text"

interface Row {
  [key: string]: string
}

function parseCsv(file: File): Promise<Row[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const text = String(reader.result)
      const lines = text.split(/\r?\n/).filter((l) => l.trim())
      if (lines.length < 2) {
        resolve([])
        return
      }
      const headers = lines[0].split(",").map((h) => h.trim().replace(/^"|"$/g, ""))
      const rows: Row[] = []
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].match(/("([^"]*)")|([^,]+)/g)?.map((v) => v.replace(/^"|"$/g, "").trim()) ?? []
        const row: Row = {}
        headers.forEach((h, j) => {
          row[h] = values[j] ?? ""
        })
        rows.push(row)
      }
      resolve(rows)
    }
    reader.onerror = () => reject(reader.error)
    reader.readAsText(file, "utf-8")
  })
}

function pool<T, R>(items: T[], concurrency: number, fn: (item: T, i: number) => Promise<R>): Promise<R[]> {
  const results: R[] = []
  let index = 0
  async function run(): Promise<void> {
    while (index < items.length) {
      const i = index++
      const res = await fn(items[i], i)
      results[i] = res
    }
  }
  const workers = Array.from({ length: Math.min(concurrency, items.length) }, () => run())
  return Promise.all(workers).then(() => results)
}

export default function BatchPage() {
  const [lang, setLang] = useState<Language>("sw")
  const [file, setFile] = useState<File | null>(null)
  const [rows, setRows] = useState<Row[]>([])
  const [results, setResults] = useState<Row[]>([])
  const [progress, setProgress] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setResults([])
    setError(null)
    parseCsv(f).then((parsed) => {
      if (!parsed.length) {
        setError("CSV has no data rows")
        setRows([])
        return
      }
      if (!(TEXT_COL in parsed[0])) {
        setError(`CSV must have a "${TEXT_COL}" column`)
        setRows([])
        return
      }
      setRows(parsed)
    }).catch(() => setError("Failed to parse CSV"))
  }, [])

  const runBatch = useCallback(async () => {
    if (!rows.length) return
    setLoading(true)
    setError(null)
    setProgress(0)
    const total = rows.length
    const outRows: Row[] = []
    const ordered = await pool(rows, CONCURRENCY, async (row, i) => {
      const text = row[TEXT_COL]?.trim() ?? ""
      let rewrite = text
      let has_bias_detected = false
      let reason = ""
      let confidence = 0
      if (text) {
        try {
          const res = await analyzeText({
            id: `batch-${i}`,
            lang,
            text,
          })
          rewrite = res.rewrite
          has_bias_detected = res.has_bias_detected
          reason = res.reason
          confidence = res.confidence
        } catch {
          reason = "API error"
        }
      }
      setProgress((p) => Math.min(p + 1, total))
      return { index: i, row: { ...row, rewrite, has_bias_detected: String(has_bias_detected), reason, confidence: String(confidence) } }
    })
    const sorted = ordered.sort((a, b) => a.index - b.index).map((x) => x.row)
    setResults(sorted)
    setLoading(false)
  }, [rows, lang])

  const download = useCallback(() => {
    if (!results.length) return
    const headers = Object.keys(results[0])
    const line = (r: Row) => headers.map((h) => {
      const v = String(r[h] ?? "")
      return v.includes(",") || v.includes('"') ? `"${v.replace(/"/g, '""')}"` : v
    }).join(",")
    const csv = [headers.join(","), ...results.map(line)].join("\n")
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "juakazi_batch_results.csv"
    a.click()
    URL.revokeObjectURL(url)
  }, [results])

  return (
    <main className="min-h-screen max-w-3xl mx-auto px-4 py-12 space-y-6">
      <div>
        <Link href="/" className="text-sm text-muted-foreground hover:underline">← Back</Link>
        <h1 className="text-2xl font-bold mt-4">Batch CSV analysis</h1>
        <p className="text-muted-foreground mt-1">
          Upload a CSV with a <code className="bg-muted px-1 rounded">{TEXT_COL}</code> column. Each row is sent to the API; results include <code>rewrite</code>, <code>has_bias_detected</code>, <code>reason</code>, <code>confidence</code>.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Language</CardTitle>
        </CardHeader>
        <CardContent>
          <LanguageSelector value={lang} onChange={setLang} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Upload CSV</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            type="file"
            accept=".csv"
            onChange={handleFile}
            className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-primary file:text-primary-foreground"
          />
          {file && <p className="text-sm text-muted-foreground">{file.name} · {rows.length} rows</p>}
        </CardContent>
      </Card>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">{error}</p>
      )}

      {rows.length > 0 && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={runBatch} disabled={loading}>
              {loading ? `Processing… ${progress} / ${rows.length}` : "Run batch"}
            </Button>
            {results.length > 0 && (
              <Button variant="outline" onClick={download}>Download results CSV</Button>
            )}
          </div>
          {loading && (
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${(progress / rows.length) * 100}%` }}
              />
            </div>
          )}
        </>
      )}

      {results.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Preview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto max-h-64 overflow-y-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b">
                    {Object.keys(results[0]).map((h) => (
                      <th key={h} className="text-left p-2 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {results.slice(0, 10).map((r, i) => (
                    <tr key={i} className="border-b">
                      {Object.values(r).map((v, j) => (
                        <td key={j} className="p-2 max-w-[200px] truncate" title={String(v)}>{String(v)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-muted-foreground mt-2">{results.length} rows · Download for full results</p>
          </CardContent>
        </Card>
      )}
    </main>
  )
}
