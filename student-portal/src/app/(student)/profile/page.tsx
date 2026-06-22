"use client";

import { useEffect, useState } from "react";

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

  if (loading || !profile) return <p className="text-gray-400">Loading…</p>;

  return (
    <div className="max-w-md space-y-6">
      <h1 className="text-xl font-semibold">My Profile</h1>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
      >
        {saved && (
          <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
            Profile updated.
          </p>
        )}

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Email</label>
          <input
            value={profile.email}
            disabled
            className="w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-500"
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Level</label>
          <select
            value={profile.level}
            onChange={(e) => setProfile({ ...profile, level: e.target.value })}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">Select level</option>
            <option value="o_level">O-Level</option>
            <option value="a_level">A-Level</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Exam year</label>
          <input
            type="number"
            value={profile.exam_year ?? ""}
            onChange={(e) =>
              setProfile({ ...profile, exam_year: e.target.value ? Number(e.target.value) : null })
            }
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">School name</label>
          <input
            value={profile.school_name}
            onChange={(e) => setProfile({ ...profile, school_name: e.target.value })}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {saving ? "Saving..." : "Save changes"}
        </button>
      </form>
    </div>
  );
}
