import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 text-center">
      <div className="max-w-2xl space-y-6">
        <h1 className="text-4xl font-bold tracking-tight">
          JuaKazi Gender Sensitization Engine
        </h1>
        <p className="text-xl text-muted-foreground">
          Detect and correct gender bias in African-language text.
          Swahili, Kikuyu, English, and French.
        </p>
        <p className="text-muted-foreground">
          The only tool in East Africa that does{" "}
          <strong>detection → correction → plain-language explanation</strong>{" "}
          with an audit trail.
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Button asChild size="lg">
            <Link href="/analyze">Try it now</Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/about">How it works</Link>
          </Button>
        </div>
        <p className="text-xs text-muted-foreground pt-4">
          Supported by AIBRIDGE · East Africa
        </p>
      </div>
    </main>
  )
}
