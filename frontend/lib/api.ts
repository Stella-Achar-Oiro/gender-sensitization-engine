// Strip trailing slash to avoid "//rewrite" double-slash when API_BASE="/"
const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

export interface AnalyseRequest {
  id: string;
  lang: string;
  text: string;
}

export interface Edit {
  from: string;
  to: string;
  severity: string;
  bias_type?: string;
  stereotype_category?: string;
  reason?: string;
}

export interface AnalyseResponse {
  original_text: string;
  rewrite: string;
  edits: Edit[];
  confidence: number;
  source: string;
  has_bias_detected: boolean;
  aibridge_detected?: boolean;
  aibridge_confidence?: number;
  needs_review?: boolean;
  reason?: string;
}

export interface LanguageMetrics {
  f1: number;
  precision: number;
  recall: number;
  samples: number;
}

export async function analyse(req: AnalyseRequest): Promise<AnalyseResponse> {
  const res = await fetch(`${API_BASE}/rewrite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchMetrics(): Promise<Record<string, LanguageMetrics>> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) return {};
  return res.json();
}

export async function analyseBatch(
  items: AnalyseRequest[]
): Promise<AnalyseResponse[]> {
  return Promise.all(items.map((item) => analyse(item)));
}

// ── Async inference (paragraph / PDF mode) ──────────────────────────────────
// Submits job, polls until done. Each sentence gets its own job so results
// stream in one by one as they complete — no waiting for the slowest sentence.

const _POLL_INTERVAL_MS = 800;
const _POLL_TIMEOUT_MS  = 180_000; // 180s max per sentence (corrector cold-start)

async function _submitAndPoll(req: AnalyseRequest): Promise<AnalyseResponse> {
  const submitRes = await fetch(`${API_BASE}/rewrite/async`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!submitRes.ok) throw new Error(`Submit error ${submitRes.status}`);
  const { job_id } = await submitRes.json();

  const deadline = Date.now() + _POLL_TIMEOUT_MS;
  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, _POLL_INTERVAL_MS));
    const pollRes = await fetch(`${API_BASE}/rewrite/status/${job_id}`);
    if (!pollRes.ok) throw new Error(`Poll error ${pollRes.status}`);
    const data = await pollRes.json();
    if (data.status === "done")   return data.result as AnalyseResponse;
    if (data.status === "error")  throw new Error(data.error ?? "Job failed");
    // status === "queued" | "processing" — keep polling
  }
  throw new Error("Timed out waiting for result");
}

// Submit sentences in parallel with a concurrency cap so the job queue never
// backs up beyond CONCURRENCY × poll-time, keeping every sentence within the
// 180s timeout even for large documents.
const _CONCURRENCY = 8;

export async function analyseStream(
  items: AnalyseRequest[],
  onResult: (index: number, result: AnalyseResponse) => void,
): Promise<void> {
  let next = 0;
  async function worker() {
    while (next < items.length) {
      const i = next++;
      const result = await _submitAndPoll(items[i]);
      onResult(i, result);
    }
  }
  await Promise.all(Array.from({ length: Math.min(_CONCURRENCY, items.length) }, worker));
}
