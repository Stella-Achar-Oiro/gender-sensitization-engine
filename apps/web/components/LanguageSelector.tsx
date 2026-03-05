"use client"

import { Language } from "@/lib/types"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const LANGUAGES: { value: Language; label: string }[] = [
  { value: "sw", label: "Kiswahili" },
  { value: "en", label: "English" },
  { value: "fr", label: "Français" },
  { value: "ki", label: "Gĩkũyũ" },
]

interface Props {
  value: Language
  onChange: (lang: Language) => void
}

export function LanguageSelector({ value, onChange }: Props) {
  return (
    <Select value={value} onValueChange={(v) => onChange(v as Language)}>
      <SelectTrigger className="w-40">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {LANGUAGES.map((l) => (
          <SelectItem key={l.value} value={l.value}>
            {l.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
