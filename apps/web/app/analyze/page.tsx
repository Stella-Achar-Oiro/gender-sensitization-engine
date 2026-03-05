import { TextAnalyzer } from "@/components/TextAnalyzer"
import Link from "next/link"

export default function AnalyzePage() {
  return (
    <main className="min-h-screen max-w-3xl mx-auto px-4 py-12">
      <div className="mb-8">
        <Link href="/" className="text-sm text-muted-foreground hover:underline">
          ← Back
        </Link>
        <h1 className="text-2xl font-bold mt-4">Analyse text for gender bias</h1>
        <p className="text-muted-foreground mt-1">
          Paste any text in Swahili, English, French, or Kikuyu. The engine detects bias,
          explains why, and suggests a correction.
        </p>
      </div>
      <TextAnalyzer />
    </main>
  )
}
