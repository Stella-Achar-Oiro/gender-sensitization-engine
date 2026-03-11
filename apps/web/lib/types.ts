export type Language = "sw" | "en" | "fr" | "ki"

export interface Edit {
  from: string
  to: string
  severity: "replace" | "warn"
  bias_type?: string
  stereotype_category?: string
  reason?: string
}

export interface RewriteRequest {
  id: string
  lang: Language
  text: string
  region_dialect?: string
}

export interface RewriteResponse {
  original_text: string
  rewrite: string
  edits: Edit[]
  confidence: number
  source: string
  reason: string
  semantic_score?: number
  has_bias_detected: boolean
}
