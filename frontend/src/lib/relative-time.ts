const MINUTE = 60_000;
const HOUR = 3_600_000;
const DAY = 86_400_000;

const dateFormat = new Intl.DateTimeFormat("ja-JP", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

export function formatRelativeTime(
  isoString: string | null | undefined,
): string {
  if (isoString == null) return "—";

  const then = new Date(isoString).getTime();
  if (Number.isNaN(then)) return "—";

  const diff = Date.now() - then;
  if (diff < 0) return "—";

  if (diff < MINUTE) return "たった今";
  if (diff < HOUR) return `${Math.floor(diff / MINUTE)}分前`;
  if (diff < DAY) return `${Math.floor(diff / HOUR)}時間前`;
  if (diff < DAY * 2) return "昨日";
  if (diff < DAY * 7) return `${Math.floor(diff / DAY)}日前`;

  return dateFormat.format(then).replace(/\//g, "/");
}
