export interface ParsedBody {
  roadmap: string | null
  accuracy: string | null
  suggestions: string[]
}

export function parseFeedbackBody(body: string): ParsedBody {
  const out: ParsedBody = { roadmap: null, accuracy: null, suggestions: [] }
  const lines = body.split("\n")
  let mode: "accuracy" | "sugg" | null = null

  for (const line of lines) {
    const t = line.trim()
    if (!t) {
      if (mode === "accuracy") mode = null
      continue
    }

    const rmBracket = t.match(/^\[反映先ロードマップ:\s*(.+?)\]$/)
    if (rmBracket) {
      out.roadmap = rmBracket[1]
      mode = null
      continue
    }

    const rmPlain = t.match(/^反映先ロードマップ:\s*(.+)$/)
    if (rmPlain && !out.roadmap) {
      out.roadmap = rmPlain[1]
      mode = null
      continue
    }

    const acInline = t.match(/^正確性チェック:\s*(.+)$/)
    if (acInline) {
      out.accuracy = acInline[1]
      mode = "accuracy"
      continue
    }
    if (t === "正確性チェック:" || t === "正確性チェック：") {
      mode = "accuracy"
      continue
    }

    if (t === "改善提案:" || t === "改善提案：") {
      mode = "sugg"
      continue
    }

    if (mode === "sugg" && t.startsWith("-")) {
      out.suggestions.push(t.replace(/^-\s*/, ""))
      continue
    }

    if (mode === "accuracy") {
      out.accuracy = out.accuracy ? out.accuracy + " " + t : t
    }
  }

  return out
}
