import type { AnalyseResponse } from "./api";

const KEY = "juakazi_history";
const MAX = 20;

export interface HistoryEntry {
  id: string;
  lang: string;
  text: string;
  result: AnalyseResponse;
  ts: number;
}

export function loadHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function saveToHistory(entry: HistoryEntry): void {
  if (typeof window === "undefined") return;
  const current = loadHistory().filter((e) => e.id !== entry.id);
  const next = [entry, ...current].slice(0, MAX);
  localStorage.setItem(KEY, JSON.stringify(next));
}

export function deleteFromHistory(id: string): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  const next = loadHistory().filter((e) => e.id !== id);
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export function clearHistory(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(KEY);
}
