"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
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
  Wallet,
  Flame,
  PanelLeftClose,
  PanelLeftOpen,
  type LucideIcon,
} from "lucide-react";

import { Logo } from "@/components/Logo";
import { useNavBadges } from "@/lib/use-nav-badges";

type NavGroup = "learn" | "practice";

export const NAV_ITEMS: { href: string; label: string; icon: LucideIcon; group?: NavGroup }[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/subjects", label: "Subjects", icon: BookOpen, group: "learn" },
  { href: "/papers", label: "Past Papers", icon: FileText, group: "learn" },
  { href: "/notes", label: "Notes", icon: StickyNote, group: "learn" },
  { href: "/quiz", label: "Quizzes", icon: ListChecks, group: "practice" },
  { href: "/ask", label: "AI Tutor", icon: Sparkles, group: "practice" },
  { href: "/progress", label: "Progress", icon: TrendingUp, group: "practice" },
  { href: "/billing", label: "Upgrade", icon: Wallet },
  { href: "/profile", label: "Profile", icon: User },
];

/** The core destinations shown in the mobile bottom tab bar (max 5 per best practice). */
export const PRIMARY_NAV_ITEMS = NAV_ITEMS.filter((item) =>
  ["/dashboard", "/subjects", "/quiz", "/progress"].includes(item.href),
);

export const MORE_NAV_ITEMS = NAV_ITEMS.filter(
  (item) => !PRIMARY_NAV_ITEMS.some((p) => p.href === item.href),
);

const GROUP_LABELS: Record<NavGroup, string> = {
  learn: "Learn",
  practice: "Practice",
};

const LINK_BASE =
  "group flex items-center gap-3 rounded-md border-l-2 px-3 py-2 text-sm font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-gray-900";

export function Sidebar() {
  const pathname = usePathname();
  const { subjectCount, streak } = useNavBadges();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("sidebar-collapsed");
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reading persisted preference on mount
    if (stored === "true") setCollapsed(true);
  }, []);

  function toggleCollapsed() {
    setCollapsed((prev) => {
      const next = !prev;
      window.localStorage.setItem("sidebar-collapsed", String(next));
      return next;
    });
  }

  const dashboardItem = NAV_ITEMS.find((item) => item.href === "/dashboard")!;
  const billingItem = NAV_ITEMS.find((item) => item.href === "/billing")!;
  const profileItem = NAV_ITEMS.find((item) => item.href === "/profile")!;
  const learnItems = NAV_ITEMS.filter((item) => item.group === "learn");
  const practiceItems = NAV_ITEMS.filter((item) => item.group === "practice");

  function renderItem(item: (typeof NAV_ITEMS)[number]) {
    const active = pathname === item.href;
    const Icon = item.icon;
    const badge =
      item.href === "/dashboard" && streak
        ? streak
        : item.href === "/subjects" && subjectCount
          ? subjectCount
          : null;

    return (
      <Link
        key={item.href}
        href={item.href}
        title={collapsed ? item.label : undefined}
        className={clsx(
          LINK_BASE,
          collapsed && "justify-center px-0",
          active
            ? "border-brand-600 bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
            : "border-transparent text-gray-600 hover:border-gray-200 hover:bg-gray-50 dark:text-gray-400 dark:hover:border-gray-700 dark:hover:bg-gray-800",
        )}
      >
        <span className="relative shrink-0">
          <Icon
            size={17}
            strokeWidth={2}
            className={
              active
                ? "text-brand-600 dark:text-brand-300"
                : "text-gray-400 group-hover:text-gray-500 dark:text-gray-500"
            }
          />
          {collapsed && badge != null && (
            <span className="absolute -right-1.5 -top-1.5 h-1.5 w-1.5 rounded-full bg-amber-500" />
          )}
        </span>
        {!collapsed && (
          <>
            <span className="flex-1 truncate">{item.label}</span>
            {badge != null && (
              <span
                className={clsx(
                  "flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[11px] font-semibold",
                  item.href === "/dashboard"
                    ? "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                    : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
                )}
              >
                {item.href === "/dashboard" && <Flame size={10} />}
                {badge}
              </span>
            )}
          </>
        )}
      </Link>
    );
  }

  return (
    <nav
      className={clsx(
        "hidden shrink-0 flex-col gap-0.5 border-r border-gray-200 bg-white p-3 transition-[width] duration-150 lg:flex dark:border-gray-800 dark:bg-gray-900",
        collapsed ? "w-[4.5rem]" : "w-60",
      )}
    >
      <div className={clsx("mb-5 flex pt-1", collapsed ? "justify-center px-0" : "px-2")}>
        <Logo withWordmark={!collapsed} />
      </div>

      {renderItem(dashboardItem)}

      <div className="mt-3">
        {!collapsed && (
          <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-600">
            {GROUP_LABELS.learn}
          </p>
        )}
        <div className="flex flex-col gap-0.5">{learnItems.map(renderItem)}</div>
      </div>

      <div className="mt-3">
        {!collapsed && (
          <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-600">
            {GROUP_LABELS.practice}
          </p>
        )}
        <div className="flex flex-col gap-0.5">{practiceItems.map(renderItem)}</div>
      </div>

      <div className="mt-auto flex flex-col gap-0.5 border-t border-gray-100 pt-3 dark:border-gray-800">
        {renderItem(billingItem)}
        {renderItem(profileItem)}
        <button
          onClick={toggleCollapsed}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={clsx(
            LINK_BASE,
            "border-transparent text-gray-500 hover:border-gray-200 hover:bg-gray-50 dark:text-gray-500 dark:hover:border-gray-700 dark:hover:bg-gray-800",
            collapsed && "justify-center px-0",
          )}
        >
          {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
          {!collapsed && "Collapse"}
        </button>
      </div>
    </nav>
  );
}
