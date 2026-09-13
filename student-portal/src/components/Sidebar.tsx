"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  StickyNote,
  ListChecks,
  Sparkles,
  TrendingUp,
  User,
  type LucideIcon,
} from "lucide-react";

import { Logo } from "@/components/Logo";

export const NAV_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/subjects", label: "Subjects", icon: BookOpen },
  { href: "/papers", label: "Past Papers", icon: FileText },
  { href: "/notes", label: "Notes", icon: StickyNote },
  { href: "/quiz", label: "Quizzes", icon: ListChecks },
  { href: "/ask", label: "AI Tutor", icon: Sparkles },
  { href: "/progress", label: "Progress", icon: TrendingUp },
  { href: "/profile", label: "Profile", icon: User },
];

/** The core destinations shown in the mobile bottom tab bar (max 5 per best practice). */
export const PRIMARY_NAV_ITEMS = NAV_ITEMS.filter((item) =>
  ["/dashboard", "/subjects", "/quiz", "/progress"].includes(item.href),
);

export const MORE_NAV_ITEMS = NAV_ITEMS.filter(
  (item) => !PRIMARY_NAV_ITEMS.some((p) => p.href === item.href),
);

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="hidden w-60 shrink-0 flex-col gap-0.5 border-r border-gray-200 bg-white p-3 lg:flex dark:border-gray-800 dark:bg-gray-900">
      <div className="mb-5 px-2 pt-1">
        <Logo />
      </div>
      {NAV_ITEMS.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "group flex items-center gap-3 rounded-md border-l-2 px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "border-brand-600 bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                : "border-transparent text-gray-600 hover:border-gray-200 hover:bg-gray-50 dark:text-gray-400 dark:hover:border-gray-700 dark:hover:bg-gray-800",
            )}
          >
            <Icon
              size={17}
              strokeWidth={2}
              className={clsx(
                "shrink-0",
                active
                  ? "text-brand-600 dark:text-brand-300"
                  : "text-gray-400 group-hover:text-gray-500 dark:text-gray-500",
              )}
            />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
