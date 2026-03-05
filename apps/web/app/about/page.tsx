import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

const TIERS = [
  { tier: "Pre-Bronze", color: "secondary", langs: "EN, FR", f1: "0.54–0.79" },
  { tier: "Bronze", color: "default", langs: "SW (sample count)", f1: "0.771" },
  { tier: "Silver", color: "default", langs: "—", f1: "—" },
  { tier: "Gold", color: "default", langs: "SW (64K rows)", f1: "In progress" },
]

const WHAT_WE_DETECT = [
  { label: "Gendered job titles", example: "daktari wa kiume → daktari" },
  { label: "Capability stereotypes", example: "kazi ya wanawake tu → kazi ya wote" },
  { label: "Family role prescriptions", example: "mwanamke anapaswa kupika → mtu anapaswa kupika" },
  { label: "Appearance reduction", example: "mwanasiasa mzuri wa kike → mwanasiasa" },
  { label: "Derogatory terms", example: "Detected and flagged" },
  { label: "Counter-stereotypes", example: "Preserved — not corrected" },
]

export default function AboutPage() {
  return (
    <main className="min-h-screen max-w-3xl mx-auto px-4 py-12 space-y-10">
      <div>
        <Link href="/" className="text-sm text-muted-foreground hover:underline">← Back</Link>
        <h1 className="text-2xl font-bold mt-4">How it works</h1>
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
        <h2 className="text-lg font-semibold">Languages</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          {[
            { lang: "Kiswahili", f1: "F1 = 0.771", status: "Production" },
            { lang: "English", f1: "F1 = 0.786", status: "Production" },
            { lang: "Français", f1: "F1 = 0.542", status: "Beta" },
            { lang: "Gĩkũyũ", f1: "F1 = 0.352", status: "Beta" },
          ].map((l) => (
            <Card key={l.lang}>
              <CardContent className="pt-3 pb-3">
                <p className="font-medium">{l.lang}</p>
                <p className="text-muted-foreground text-xs">{l.f1} · {l.status}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">How detection works</h2>
        <Card>
          <CardContent className="pt-4 pb-3 space-y-2 text-sm text-muted-foreground">
            <p>1. <strong>Rules engine</strong> — lexicon of 2,000+ gender bias patterns across 4 languages</p>
            <p>2. <strong>Context checker</strong> — suppresses false positives in biographical, historical, and advocacy contexts</p>
            <p>3. <strong>ML classifier</strong> (Swahili) — afro-xlmr-base fine-tuned on 64,000+ annotated sentences</p>
            <p>4. <strong>Correction layer</strong> — generates neutral replacement, checks semantic preservation</p>
            <p>5. <strong>Explanation</strong> — plain-language reason for every edit</p>
          </CardContent>
        </Card>
      </section>

      <div className="pt-4">
        <Button asChild>
          <Link href="/analyze">Try it now</Link>
        </Button>
      </div>
    </main>
  )
}
