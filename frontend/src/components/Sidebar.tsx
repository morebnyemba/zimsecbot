"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

import { useAuth } from "@/lib/auth-context";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/subjects", label: "Subjects" },
  { href: "/topics", label: "Topics" },
  { href: "/subtopics", label: "Subtopics" },
  { href: "/papers", label: "Past Papers" },
  { href: "/marking-schemes", label: "Marking Schemes" },
  { href: "/notes", label: "Notes" },
  { href: "/questions", label: "Questions" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const items = [
    ...NAV_ITEMS,
    ...(user?.role === "superadmin"
      ? [{ href: "/audit-logs", label: "Audit Log" }]
      : []),
  ];

  return (
    <nav className="flex w-56 flex-col gap-1 border-r border-gray-200 bg-white p-4">
      <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        Admin Portal
      </p>
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={clsx(
            "rounded-md px-3 py-2 text-sm font-medium transition-colors",
            pathname === item.href
              ? "bg-blue-50 text-blue-700"
              : "text-gray-600 hover:bg-gray-100",
          )}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
