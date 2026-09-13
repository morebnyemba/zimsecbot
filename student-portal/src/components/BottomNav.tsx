"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import clsx from "clsx";
import { Menu, X, LogOut } from "lucide-react";

import { PRIMARY_NAV_ITEMS, MORE_NAV_ITEMS } from "@/components/Sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/lib/auth-context";

export function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuth();
  const [moreOpen, setMoreOpen] = useState(false);

  const moreActive = MORE_NAV_ITEMS.some((item) => pathname === item.href);

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <>
      {moreOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/30 lg:hidden"
          onClick={() => setMoreOpen(false)}
        />
      )}

      <div
        className={clsx(
          "fixed inset-x-0 bottom-0 z-40 rounded-t-2xl border-t border-gray-200 bg-white shadow-[0_-4px_16px_rgba(0,0,0,0.06)] transition-transform lg:hidden dark:border-gray-800 dark:bg-gray-900",
          moreOpen ? "translate-y-0" : "translate-y-full",
        )}
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3 dark:border-gray-800">
          <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">More</p>
          <button
            onClick={() => setMoreOpen(false)}
            aria-label="Close menu"
            className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <X size={18} />
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2 p-4">
          {MORE_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMoreOpen(false)}
                className={clsx(
                  "flex flex-col items-center gap-2 rounded-lg border p-4 text-sm font-medium",
                  active
                    ? "border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-800 dark:bg-brand-900/30 dark:text-brand-300"
                    : "border-gray-200 text-gray-600 dark:border-gray-800 dark:text-gray-300",
                )}
              >
                <Icon size={20} />
                {item.label}
              </Link>
            );
          })}
        </div>
        <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3 dark:border-gray-800">
          <ThemeToggle />
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
          >
            <LogOut size={15} />
            Sign out
          </button>
        </div>
      </div>

      <nav
        className="fixed inset-x-0 bottom-0 z-20 flex border-t border-gray-200 bg-white lg:hidden dark:border-gray-800 dark:bg-gray-900"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        {PRIMARY_NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium",
                active ? "text-brand-600 dark:text-brand-400" : "text-gray-500 dark:text-gray-400",
              )}
            >
              <Icon size={20} strokeWidth={active ? 2.4 : 2} />
              {item.label}
            </Link>
          );
        })}
        <button
          onClick={() => setMoreOpen(true)}
          className={clsx(
            "flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium",
            moreActive || moreOpen
              ? "text-brand-600 dark:text-brand-400"
              : "text-gray-500 dark:text-gray-400",
          )}
        >
          <Menu size={20} />
          More
        </button>
      </nav>
    </>
  );
}
