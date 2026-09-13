"use client";

import { usePathname, useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { NAV_ITEMS } from "@/components/Sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/lib/auth-context";

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const chars = parts.length >= 2 ? [parts[0][0], parts[1][0]] : [name.slice(0, 2)];
  return chars.join("").toUpperCase();
}

export function Topbar() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const section = NAV_ITEMS.find((item) => pathname?.startsWith(item.href))?.label ?? "";

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white/80 px-4 py-3 backdrop-blur-sm lg:px-6 dark:border-gray-800 dark:bg-gray-900/80">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{section}</p>
      <div className="flex items-center gap-2 lg:gap-4">
        <ThemeToggle />
        {user && (
          <span className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700 sm:flex dark:bg-brand-900/40 dark:text-brand-300">
            {initials(user.first_name || user.email)}
          </span>
        )}
        <button
          onClick={handleLogout}
          className="hidden items-center gap-1.5 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 lg:flex dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
        >
          <LogOut size={15} />
          Sign out
        </button>
      </div>
    </header>
  );
}
