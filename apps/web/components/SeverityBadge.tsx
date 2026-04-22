import { Badge } from "@/components/ui/badge"

export function SeverityBadge({ severity }: { severity: string }) {
  return severity === "replace" ? (
    <Badge className="bg-red-100 text-red-800 border-red-300">Bias detected</Badge>
  ) : (
    <Badge className="bg-yellow-100 text-yellow-800 border-yellow-300">Possible bias</Badge>
  )
}
