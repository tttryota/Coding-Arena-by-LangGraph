export type ScoreKey = "not_started" | "insufficient" | "partial" | "sufficient";

export interface ScoreLevel {
  key: ScoreKey;
  label: string;
  fg: string;
  bg: string;
}

const LEVELS: readonly ScoreLevel[] = [
  { key: "not_started", label: "未着手", fg: "var(--color-score-not-started-fg)", bg: "var(--color-score-not-started-bg)" },
  { key: "insufficient", label: "不十分", fg: "var(--color-score-insufficient-fg)", bg: "var(--color-score-insufficient-bg)" },
  { key: "partial", label: "部分的", fg: "var(--color-score-partial-fg)", bg: "var(--color-score-partial-bg)" },
  { key: "sufficient", label: "十分", fg: "var(--color-score-sufficient-fg)", bg: "var(--color-score-sufficient-bg)" },
] as const;

// 閾値はバックエンド Settings と同期する前提。バックエンド側で変更された場合はここも更新する。
export function scoreLevel(score: number | null | undefined): ScoreLevel {
  if (score == null) return LEVELS[0];
  if (score <= 25) return LEVELS[0];
  if (score <= 50) return LEVELS[1];
  if (score <= 75) return LEVELS[2];
  return LEVELS[3];
}
