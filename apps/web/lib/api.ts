import { RewriteRequest, RewriteResponse } from "./types"

// Set NEXT_PUBLIC_API_URL to your JuaKazi FastAPI backend (e.g. Railway/Render). Localhost: /api proxy in dev.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? ""

function getApiBase(): string {
  if (typeof window === "undefined") return API_BASE
  // Localhost: use /api so Next.js dev proxy hits FastAPI on port 8000
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "/api"
  }
  return API_BASE
}

/** Call JuaKazi FastAPI POST /rewrite. Fails clearly if backend URL is wrong or missing. */
export async function analyzeText(req: RewriteRequest): Promise<RewriteResponse> {
  const base = getApiBase()
  if (!base && typeof window !== "undefined") {
    throw new Error(
      "Backend URL not set. Set NEXT_PUBLIC_API_URL to your JuaKazi FastAPI URL (e.g. from Railway or Render). It must be the app that serves /docs (Swagger), not another service."
    )
  }
  const url = `${base}/rewrite`
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
  const text = await res.text()
  if (!res.ok) {
    const isHtml = text.trimStart().toLowerCase().startsWith("<!doctype html") || text.trimStart().toLowerCase().startsWith("<html")
    if (res.status === 404 || isHtml) {
      throw new Error(
        "Backend returned 404 or an HTML page. Ensure NEXT_PUBLIC_API_URL points to the JuaKazi FastAPI app (the one that shows Swagger at /docs). Do not use a different service or port."
      )
    }
    throw new Error(`API error ${res.status}: ${text.slice(0, 200)}`)
  }
  return JSON.parse(text) as RewriteResponse
}
