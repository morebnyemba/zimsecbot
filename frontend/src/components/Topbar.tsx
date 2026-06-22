"use client";

import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth-context";

export function Topbar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
      <div />
      <div className="flex items-center gap-4 text-sm">
        {user && (
          <span className="text-gray-600">
            {user.email} <span className="text-gray-400">({user.role})</span>
          </span>
        )}
        <button
          onClick={handleLogout}
          className="rounded-md border border-gray-300 px-3 py-1.5 font-medium text-gray-700 hover:bg-gray-50"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
