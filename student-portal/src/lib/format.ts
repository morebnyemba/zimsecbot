/** Status color for an accuracy/score percentage (0-100). Always pair with a visible numeric label. */
export function accuracyStatus(pct: number) {
  if (pct >= 70) {
    return { bar: "bg-emerald-500", text: "text-emerald-700 dark:text-emerald-400" };
  }
  if (pct >= 40) {
    return { bar: "bg-amber-500", text: "text-amber-700 dark:text-amber-400" };
  }
  return { bar: "bg-red-500", text: "text-red-700 dark:text-red-400" };
}

export function relativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.round(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}
