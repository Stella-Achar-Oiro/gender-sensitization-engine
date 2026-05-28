const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

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
