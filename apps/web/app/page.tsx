import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"

const LOGO_URL = "https://i.postimg.cc/L5mk9h1P/juakazi.png"
const FEATURES = [
  { title: "Detect", desc: "Rules + context checker + ML classifier for 4 languages" },
  { title: "Correct", desc: "Gender-neutral replacements with semantic preservation" },
  { title: "Explain", desc: "Plain-language reason and audit trail for every edit" },
]

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col">
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-12 text-center">
        <Image
          src={LOGO_URL}
          alt="JuaKazi"
          width={120}
          height={120}
          className="rounded-lg mb-6"
          unoptimized
          priority
        />
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight" style={{ color: "#1a5c2e" }}>
          JuaKazi
        </h1>
        <p className="text-xl text-muted-foreground mt-2 max-w-xl">
          Detect and correct gender bias in African-language text.
        </p>
        <div className="flex flex-wrap gap-2 justify-center mt-4 text-sm">
          {["SW", "EN", "FR", "KI"].map((lang) => (
            <span
              key={lang}
              className="px-3 py-1 rounded-full border bg-muted/50 text-muted-foreground"
            >
              {lang}
            </span>
          ))}
        </div>
        {/* Investor-ready impact strip: credibility at a glance */}
        <div className="mt-6 px-4 py-3 rounded-xl glass-subtle max-w-xl mx-auto flex flex-wrap items-center justify-center gap-x-6 gap-y-1 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">64K+</span>
          <span>sentences evaluated</span>
          <span className="text-border">·</span>
          <span>4 languages</span>
          <span className="text-border">·</span>
          <span className="font-medium" style={{ color: "#1a5c2e" }}>AIBRIDGE Gold track</span>
        </div>
        <div className="flex flex-wrap gap-3 justify-center mt-8">
          <Button asChild size="lg" style={{ backgroundColor: "#1a5c2e" }}>
            <Link href="/analyze">Analyse text</Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/batch">Batch CSV</Link>
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mt-12 w-full text-left">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="p-4 rounded-xl border glass-subtle"
            >
              <h3 className="font-semibold" style={{ color: "#38a169" }}>{f.title}</h3>
              <p className="text-sm text-muted-foreground mt-1">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <footer className="py-6 border-t text-center text-sm text-muted-foreground">
        <Link href="/about" className="hover:underline mr-4">About</Link>
        <a href="https://github.com/Stella-Achar-Oiro/gender-sensitization-engine" target="_blank" rel="noopener noreferrer" className="hover:underline mr-4">GitHub</a>
        <a href="https://huggingface.co/spaces/juakazike/gender-sensitization-engine" target="_blank" rel="noopener noreferrer" className="hover:underline mr-4">HuggingFace</a>
        <span>AIBRIDGE</span>
      </footer>
    </main>
  )
}
