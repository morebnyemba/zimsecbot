/** A row of thin bars showing recent scores (0-100), oldest to newest, left to right. */
export function Sparkline({ scores }: { scores: (number | null)[] }) {
  const known = scores.filter((s): s is number => s != null);
  const summary = known.length
    ? `Recent scores: ${known.map((s) => `${Math.round(s)}%`).join(", ")}`
    : "No recent scores";

  return (
    <div className="flex h-8 items-end gap-1" role="img" aria-label={summary}>
      {scores.map((score, i) => (
        <div
          key={i}
          title={score != null ? `${Math.round(score)}%` : "No attempt"}
          className={
            score != null
              ? "w-2 rounded-sm bg-brand-500 dark:bg-brand-400"
              : "w-2 rounded-sm bg-gray-100 dark:bg-gray-800"
          }
          style={{ height: score != null ? `${Math.max(score, 8)}%` : "15%" }}
        />
      ))}
    </div>
  );
}
