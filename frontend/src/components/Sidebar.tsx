"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  LayoutDashboard,
  BookOpen,
  ListTree,
  Layers,
  FileText,
  ClipboardCheck,
  StickyNote,
  HelpCircle,
  School,
  CreditCard,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

import { Logo } from "@/components/Logo";
import { useAuth } from "@/lib/auth-context";

export const NAV_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/subjects", label: "Subjects", icon: BookOpen },
  { href: "/topics", label: "Topics", icon: ListTree },
  { href: "/subtopics", label: "Subtopics", icon: Layers },
  { href: "/papers", label: "Past Papers", icon: FileText },
  { href: "/marking-schemes", label: "Marking Schemes", icon: ClipboardCheck },
  { href: "/notes", label: "Notes", icon: StickyNote },
  { href: "/questions", label: "Questions", icon: HelpCircle },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const items = [
    ...NAV_ITEMS,
    ...(user?.role === "school_admin" || user?.role === "superadmin"
      ? [
          { href: "/schools", label: "Schools", icon: School },
          { href: "/billing", label: "Billing", icon: CreditCard },
        ]
      : []),
    ...(user?.role === "superadmin"
      ? [{ href: "/audit-logs", label: "Audit Log", icon: ShieldCheck }]
      : []),
  ];

  return (
    <nav className="flex w-64 shrink-0 flex-col gap-0.5 border-r border-gray-200 bg-white p-3">
      <div className="mb-5 px-2 pt-1">
        <Logo />
        <p className="mt-1.5 text-[11px] font-medium uppercase tracking-wide text-gray-400">
          Admin Portal
        </p>
      </div>
      {items.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "group flex items-center gap-3 rounded-md border-l-2 px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "border-brand-600 bg-brand-50 text-brand-700"
                : "border-transparent text-gray-600 hover:border-gray-200 hover:bg-gray-50",
            )}
          >
            <Icon
              size={17}
              strokeWidth={2}
              className={clsx(
                "shrink-0",
                active ? "text-brand-600" : "text-gray-400 group-hover:text-gray-500",
              )}
            />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
