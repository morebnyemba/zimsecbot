const SUBJECT_PALETTE = [
  {
    bg: "bg-indigo-50 dark:bg-indigo-900/30",
    text: "text-indigo-700 dark:text-indigo-300",
    dot: "bg-indigo-500",
    ring: "ring-indigo-200 dark:ring-indigo-800",
  },
  {
    bg: "bg-orange-50 dark:bg-orange-900/30",
    text: "text-orange-700 dark:text-orange-300",
    dot: "bg-orange-500",
    ring: "ring-orange-200 dark:ring-orange-800",
  },
  {
    bg: "bg-cyan-50 dark:bg-cyan-900/30",
    text: "text-cyan-700 dark:text-cyan-300",
    dot: "bg-cyan-500",
    ring: "ring-cyan-200 dark:ring-cyan-800",
  },
  {
    bg: "bg-amber-50 dark:bg-amber-900/30",
    text: "text-amber-700 dark:text-amber-300",
    dot: "bg-amber-500",
    ring: "ring-amber-200 dark:ring-amber-800",
  },
  {
    bg: "bg-pink-50 dark:bg-pink-900/30",
    text: "text-pink-700 dark:text-pink-300",
    dot: "bg-pink-500",
    ring: "ring-pink-200 dark:ring-pink-800",
  },
  {
    bg: "bg-emerald-50 dark:bg-emerald-900/30",
    text: "text-emerald-700 dark:text-emerald-300",
    dot: "bg-emerald-500",
    ring: "ring-emerald-200 dark:ring-emerald-800",
  },
  {
    bg: "bg-violet-50 dark:bg-violet-900/30",
    text: "text-violet-700 dark:text-violet-300",
    dot: "bg-violet-500",
    ring: "ring-violet-200 dark:ring-violet-800",
  },
  {
    bg: "bg-rose-50 dark:bg-rose-900/30",
    text: "text-rose-700 dark:text-rose-300",
    dot: "bg-rose-500",
    ring: "ring-rose-200 dark:ring-rose-800",
  },
];

/** Deterministic color slot for a subject, keyed by its id/code so it stays stable across renders. */
export function subjectColor(seed: string) {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) | 0;
  }
  const index = Math.abs(hash) % SUBJECT_PALETTE.length;
  return SUBJECT_PALETTE[index];
}
