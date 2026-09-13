"use client";

import { usePathname, useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { NAV_ITEMS } from "@/components/Sidebar";
import { useAuth } from "@/lib/auth-context";

function initials(email: string) {
  const name = email.split("@")[0] ?? "";
  const parts = name.split(/[._-]/).filter(Boolean);
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
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white/80 px-6 py-3 backdrop-blur-sm">
      <p className="text-sm font-medium text-gray-500">{section}</p>
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">
              {initials(user.email)}
            </span>
            <span className="hidden text-sm text-gray-600 sm:inline">
              {user.email} <span className="text-gray-400">({user.role})</span>
            </span>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <LogOut size={15} />
          Sign out
        </button>
      </div>
    </header>
  );
}
