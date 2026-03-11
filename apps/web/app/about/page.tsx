import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

const TIER_HEADERS = ["Tier", "Min samples", "Double annotation", "κ", "F1"]
const TIER_ROWS = [
  ["Bronze", "1,200", "10%", "≥0.70", "≥0.75"],
  ["Silver", "5,000", "20%", "≥0.75", "≥0.80"],
  ["Gold", "10,000+", "30%", "≥0.80", "≥0.85"],
]

const TIER_BADGES = [
  { tier: "Bronze", color: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800", status: "SW/KI sample count met; κ pending for certification" },
  { tier: "Silver", color: "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800/50 dark:text-slate-200 dark:border-slate-600", status: "Target: 5K samples, 20% double-annotated, κ ≥ 0.75" },
  { tier: "Gold", color: "bg-amber-50 text-amber-900 border-amber-300 dark:bg-amber-900/30 dark:text-amber-100 dark:border-amber-700", status: "SW 64K+ samples; F1/κ improvements in progress" },
]

const CURRENT_METRICS = [
  { lang: "English", f1: "0.786", precision: "1.000", recall: "0.647", samples: "66", tier: "Pre-Bronze" },
  { lang: "Swahili", f1: "0.771", precision: "0.734", recall: "0.811", samples: "64,723", tier: "Gold (sample count)" },
  { lang: "French", f1: "0.542", precision: "1.000", recall: "0.371", samples: "50", tier: "Pre-Bronze" },
  { lang: "Kikuyu", f1: "0.352", precision: "0.926", recall: "0.217", samples: "11,848", tier: "Bronze (sample count)" },
]

const WHAT_WE_DETECT = [
  { label: "Gendered job titles", example: "daktari wa kiume → daktari" },
  { label: "Capability stereotypes", example: "kazi ya wanawake tu → kazi ya wote" },
  { label: "Family role prescriptions", example: "mwanamke anapaswa kupika → mtu anapaswa kupika" },
  { label: "Derogation & appearance reduction", example: "Detected and flagged; counter-stereotypes preserved" },
]

export default function AboutPage() {
  return (
    <main className="min-h-screen max-w-3xl mx-auto px-4 py-12 space-y-10">
      <div>
        <Link href="/" className="text-sm text-muted-foreground hover:underline">← Back</Link>
        <h1 className="text-2xl font-bold mt-4">About JuaKazi</h1>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">What we detect</h2>
        <div className="grid gap-3">
          {WHAT_WE_DETECT.map((w) => (
            <Card key={w.label}>
              <CardContent className="pt-4 pb-3">
                <p className="font-medium text-sm">{w.label}</p>
                <p className="text-xs text-muted-foreground mt-1 font-mono">{w.example}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Current metrics (Mar 2026)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Language</th>
                <th className="text-left p-2">F1</th>
                <th className="text-left p-2">Precision</th>
                <th className="text-left p-2">Recall</th>
                <th className="text-left p-2">Samples</th>
                <th className="text-left p-2">Tier</th>
              </tr>
            </thead>
            <tbody>
              {CURRENT_METRICS.map((r) => (
                <tr key={r.lang} className="border-b">
                  <td className="p-2">{r.lang}</td>
                  <td className="p-2">{r.f1}</td>
                  <td className="p-2">{r.precision}</td>
                  <td className="p-2">{r.recall}</td>
                  <td className="p-2">{r.samples}</td>
                  <td className="p-2"><Badge variant="secondary">{r.tier}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Our tier status</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {TIER_BADGES.map((b) => (
            <Card key={b.tier} className="border-2">
              <CardContent className="pt-4 pb-3">
                <Badge className={`${b.color} border font-semibold`}>{b.tier}</Badge>
                <p className="text-xs text-muted-foreground mt-2">{b.status}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">AIBRIDGE tier requirements</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b">
                {TIER_HEADERS.map((h) => (
                  <th key={h} className="text-left p-2">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {TIER_ROWS.map((row, i) => (
                <tr key={i} className="border-b">
                  {row.map((cell, j) => (
                    <td key={j} className="p-2">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">How detection works</h2>
        <Card>
          <CardContent className="pt-4 pb-3 space-y-2 text-sm text-muted-foreground">
            <p>1. <strong>Rules engine</strong> — lexicon of gender bias patterns across 4 languages</p>
            <p>2. <strong>Context checker</strong> — suppresses false positives in biographical, historical, and advocacy contexts</p>
            <p>3. <strong>ML classifier</strong> (Swahili) — afro-xlmr-base fine-tuned; warn-only</p>
            <p>4. <strong>Correction layer</strong> — neutral replacement with semantic preservation check</p>
            <p>5. <strong>Explanation</strong> — plain-language reason for every edit</p>
          </CardContent>
        </Card>
      </section>

      <div className="flex flex-wrap gap-3 pt-4">
        <Button asChild>
          <Link href="/analyze">Try it now</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/batch">Batch CSV</Link>
        </Button>
        <a href="https://github.com/Stella-Achar-Oiro/gender-sensitization-engine" target="_blank" rel="noopener noreferrer">
          <Button variant="outline">GitHub</Button>
        </a>
        <a href="https://huggingface.co/spaces/juakazike/gender-sensitization-engine" target="_blank" rel="noopener noreferrer">
          <Button variant="outline">HuggingFace</Button>
        </a>
      </div>
    </main>
  )
}
