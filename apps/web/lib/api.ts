import { RewriteRequest, RewriteResponse } from "./types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ||
  "https://juakazike-gender-sensitization-engine.hf.space"

export async function analyzeText(req: RewriteRequest): Promise<RewriteResponse> {
  const res = await fetch(`${API_BASE}/rewrite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`API error ${res.status}: ${err}`)
  }
  return res.json()
}
