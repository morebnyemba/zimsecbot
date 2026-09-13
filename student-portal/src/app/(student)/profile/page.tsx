"use client";

import { useEffect, useState } from "react";
import { Save, User } from "lucide-react";

import { apiFetch } from "@/lib/api";
import type { StudentProfile } from "@/lib/types";

export default function ProfilePage() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      const data = await apiFetch<StudentProfile>("/api/v1/profile/me/");
      setProfile(data);
      setLoading(false);
    }

    loadProfile();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!profile) return;
    setSaving(true);
    setSaved(false);
    try {
      const updated = await apiFetch<StudentProfile>("/api/v1/profile/me/", {
        method: "PATCH",
        body: JSON.stringify({
          level: profile.level,
          exam_year: profile.exam_year,
          school_name: profile.school_name,
        }),
      });
      setProfile(updated);
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  if (loading || !profile) {
    return (
      <div className="max-w-md space-y-4">
        <div className="h-6 w-32 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="h-64 animate-pulse rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900" />
      </div>
    );
  }

  return (
    <div className="max-w-md space-y-6">
      <div className="flex items-center gap-3">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-100 text-lg font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
          {profile.email.slice(0, 2).toUpperCase()}
        </span>
        <div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">My Profile</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">{profile.email}</p>
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900"
      >
        {saved && (
          <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">
            Profile updated.
          </p>
        )}

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
          <div className="relative">
            <User size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={profile.email}
              disabled
              className="w-full rounded-md border border-gray-300 bg-gray-50 py-2 pl-9 pr-3 text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400"
            />
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Level</label>
          <select
            value={profile.level}
            onChange={(e) => setProfile({ ...profile, level: e.target.value })}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
          >
            <option value="">Select level</option>
            <option value="o_level">O-Level</option>
            <option value="a_level">A-Level</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Exam year</label>
          <input
            type="number"
            value={profile.exam_year ?? ""}
            onChange={(e) =>
              setProfile({ ...profile, exam_year: e.target.value ? Number(e.target.value) : null })
            }
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">School name</label>
          <input
            value={profile.school_name}
            onChange={(e) => setProfile({ ...profile, school_name: e.target.value })}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
          />
        </div>

        <button
          type="submit"
          disabled={saving}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          <Save size={15} />
          {saving ? "Saving..." : "Save changes"}
        </button>
      </form>
    </div>
  );
}
