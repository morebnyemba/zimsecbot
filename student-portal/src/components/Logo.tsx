import clsx from "clsx";

/**
 * Zimfundi brand lockup: a graduation-cap mark plus the wordmark.
 * Pass `withWordmark={false}` for a compact icon-only mark.
 */
export function Logo({
  withWordmark = true,
  className,
}: {
  withWordmark?: boolean;
  className?: string;
}) {
  return (
    <span className={clsx("inline-flex items-center gap-2.5", className)}>
      <svg
        viewBox="0 0 32 32"
        role="img"
        aria-label="Zimfundi"
        className="h-8 w-8 shrink-0"
      >
        <rect width="32" height="32" rx="8" fill="url(#zf-mark)" />
        <path d="M16 7 27 12 16 17 5 12Z" fill="#ffffff" />
        <path d="M9.5 15.1 16 18 22.5 15.1V19Q16 22.4 9.5 19Z" fill="#ffffff" fillOpacity="0.82" />
        <path d="M27 12V18.4" stroke="#ffffff" strokeWidth="1.2" strokeLinecap="round" />
        <circle cx="27" cy="19.4" r="1.35" fill="#ffffff" />
        <defs>
          <linearGradient id="zf-mark" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop stopColor="#14b8a6" />
            <stop offset="1" stopColor="#0f766e" />
          </linearGradient>
        </defs>
      </svg>
      {withWordmark && (
        <span className="text-lg font-semibold tracking-tight text-gray-900">
          Zim<span className="text-brand-600">fundi</span>
        </span>
      )}
    </span>
  );
}
