import { RewriteRequest, RewriteResponse } from "./types"

// Production: set NEXT_PUBLIC_API_URL or we use HF Space. Localhost: use /api so Next.js dev proxy hits backend.
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ??
  "https://juakazike-gender-sensitization-engine.hf.space"

function getApiBase(): string {
  if (typeof window === "undefined") return API_BASE
  // When opened at localhost, use relative /api so Next.js rewrites to the backend (fixes 404)
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "/api"
  }
  return API_BASE
}

export async function analyzeText(req: RewriteRequest): Promise<RewriteResponse> {
  const res = await fetch(`${getApiBase()}/rewrite`, {
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
